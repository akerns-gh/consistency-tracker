#!/usr/bin/env python3
"""
Script to complete the Flask migration by:
1. Ensuring Flask app functions are created
2. Updating API Gateway routes to use Flask apps
3. Cleaning up old individual Lambda functions
"""

import boto3
import sys
import json
from botocore.exceptions import ClientError

# Initialize AWS clients
cf = boto3.client('cloudformation', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
apigw = boto3.client('apigateway', region_name='us-east-1')

STACK_NAME = 'ConsistencyTracker-API'
API_NAME = 'Consistency Tracker API'

def get_stack_resources():
    """Get all resources from the stack."""
    try:
        response = cf.describe_stack_resources(StackName=STACK_NAME)
        return {r['LogicalResourceId']: r for r in response['StackResources']}
    except ClientError as e:
        print(f"Error getting stack resources: {e}")
        sys.exit(1)

def get_api_id():
    """Get the API Gateway REST API ID."""
    try:
        apis = apigw.get_rest_apis()
        for api in apis['items']:
            if api['name'] == API_NAME:
                return api['id']
        print(f"❌ API '{API_NAME}' not found")
        sys.exit(1)
    except ClientError as e:
        print(f"Error getting API: {e}")
        sys.exit(1)

def check_flask_functions(resources):
    """Check if Flask app functions exist."""
    player_app = resources.get('PlayerAppFunction43CFFB00')
    admin_app = resources.get('AdminAppFunction4B3D5714')
    
    player_exists = player_app is not None and player_app.get('PhysicalResourceId')
    admin_exists = admin_app is not None and admin_app.get('PhysicalResourceId')
    
    return player_exists, admin_exists, player_app, admin_app

def verify_lambda_function(function_arn):
    """Verify a Lambda function actually exists."""
    try:
        lambda_client.get_function(FunctionName=function_arn)
        return True
    except ClientError:
        return False

def update_api_gateway_routes(api_id, player_function_arn, admin_function_arn):
    """Update API Gateway routes to use Flask app functions."""
    print("\n📡 Updating API Gateway routes...")
    
    # Get all resources
    resources = apigw.get_resources(restApiId=api_id)
    resource_map = {r['path']: r for r in resources['items']}
    
    # Update /player route
    if '/player' in resource_map:
        player_resource_id = resource_map['/player']['id']
        print(f"  Updating /player resource ({player_resource_id})...")
        
        # Add GET method if it doesn't exist
        try:
            apigw.get_method(restApiId=api_id, resourceId=player_resource_id, httpMethod='GET')
            print("    GET method already exists")
        except ClientError:
            print("    Creating GET method...")
            apigw.put_method(
                restApiId=api_id,
                resourceId=player_resource_id,
                httpMethod='GET',
                authorizationType='NONE'
            )
            
            # Add integration
            integration_uri = f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{player_function_arn}/invocations"
            apigw.put_integration(
                restApiId=api_id,
                resourceId=player_resource_id,
                httpMethod='GET',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=integration_uri
            )
            
            # Add permission
            try:
                lambda_client.add_permission(
                    FunctionName=player_function_arn,
                    StatementId='apigateway-get-player',
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com',
                    SourceArn=f"arn:aws:execute-api:us-east-1:707406431671:{api_id}/*/GET/player"
                )
            except ClientError as e:
                if 'already exists' not in str(e).lower():
                    print(f"    Warning: Could not add permission: {e}")
            
            print("    ✅ GET method created")
        
        # Add ANY method if it doesn't exist
        try:
            method = apigw.get_method(restApiId=api_id, resourceId=player_resource_id, httpMethod='ANY')
            print(f"    ANY method exists, checking integration...")
            # Check if integration points to Flask app
            integration_uri = method.get('methodIntegration', {}).get('uri', '')
            if player_function_arn in integration_uri:
                print("    ✅ ANY method already configured correctly")
            else:
                print(f"    ⚠️  ANY method exists but points to different function, updating...")
                # Update integration
                integration_uri = f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{player_function_arn}/invocations"
                apigw.put_integration(
                    restApiId=api_id,
                    resourceId=player_resource_id,
                    httpMethod='ANY',
                    type='AWS_PROXY',
                    integrationHttpMethod='POST',
                    uri=integration_uri
                )
                print("    ✅ ANY method updated")
        except ClientError as e:
            if 'NotFoundException' in str(type(e).__name__):
                print("    Creating ANY method...")
            apigw.put_method(
                restApiId=api_id,
                resourceId=player_resource_id,
                httpMethod='ANY',
                authorizationType='NONE'
            )
            
            # Add integration
            integration_uri = f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{player_function_arn}/invocations"
            apigw.put_integration(
                restApiId=api_id,
                resourceId=player_resource_id,
                httpMethod='ANY',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=integration_uri
            )
            
            # Add permission
            try:
                lambda_client.add_permission(
                    FunctionName=player_function_arn,
                    StatementId='apigateway-any-player',
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com',
                    SourceArn=f"arn:aws:execute-api:us-east-1:707406431671:{api_id}/*/ANY/player"
                )
            except ClientError as e:
                if 'already exists' not in str(e).lower():
                    print(f"    Warning: Could not add permission: {e}")
            
            print("    ✅ ANY method created")
    
    # Deploy to prod stage
    print("  Deploying to prod stage...")
    apigw.create_deployment(
        restApiId=api_id,
        stageName='prod',
        description='Flask migration - update routes to use Flask apps'
    )
    print("  ✅ API Gateway updated")

def main():
    print("🚀 Starting Flask Migration Completion...")
    print("=" * 80)
    
    # Get stack resources
    print("\n📦 Checking stack resources...")
    resources = get_stack_resources()
    
    # Check Flask functions
    player_exists, admin_exists, player_app, admin_app = check_flask_functions(resources)
    
    print(f"\n✅ PlayerAppFunction exists in stack: {player_exists}")
    print(f"✅ AdminAppFunction exists in stack: {admin_exists}")
    
    if not player_exists or not admin_exists:
        print("\n❌ Flask app functions not found in stack!")
        print("   Please deploy the stack first: cdk deploy ConsistencyTracker-API")
        sys.exit(1)
    
    # Verify functions actually exist in Lambda
    player_arn = player_app['PhysicalResourceId']
    admin_arn = admin_app['PhysicalResourceId']
    
    print(f"\n🔍 Verifying Lambda functions exist...")
    player_verified = verify_lambda_function(player_arn)
    admin_verified = verify_lambda_function(admin_arn)
    
    print(f"   PlayerAppFunction: {'✅' if player_verified else '❌'} {player_arn}")
    print(f"   AdminAppFunction: {'✅' if admin_verified else '❌'} {admin_arn}")
    
    if not player_verified or not admin_verified:
        print("\n❌ Lambda functions don't exist! Deploying stack...")
        print("   Run: cdk deploy ConsistencyTracker-API")
        sys.exit(1)
    
    # Get API Gateway ID
    api_id = get_api_id()
    print(f"\n📡 Found API Gateway: {api_id}")
    
    # Update API Gateway routes
    update_api_gateway_routes(api_id, player_arn, admin_arn)
    
    print("\n" + "=" * 80)
    print("✅ Flask migration completion script finished!")
    print("\nNext steps:")
    print("1. Test the /player endpoint")
    print("2. Monitor CloudWatch logs for any issues")
    print("3. Once verified, old individual functions can be removed from the stack")

if __name__ == '__main__':
    main()

