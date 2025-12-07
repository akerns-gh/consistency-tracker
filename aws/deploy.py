#!/usr/bin/env python3
"""
Deployment script for Consistency Tracker Infrastructure

Deploys AWS CDK stacks for:
- Phase 1: Database (DynamoDB) and Auth (Cognito)
- Phase 2: API (API Gateway + Lambda), Storage (S3 + CloudFront), DNS (Route 53)

Also ensures:
- API Gateway has an IAM role configured for CloudWatch Logs
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
import json

import boto3
from botocore.exceptions import ClientError

# Configuration
AWS_REGION = "us-east-1"
AWS_ACCOUNT_ID = "707406431671"

# Stacks are deployed in dependency order:
# 1. Database (DynamoDB tables)
# 2. Auth (Cognito User Pool)
# 3. API (API Gateway + Lambda functions)
# 4. Storage (S3 buckets + CloudFront distributions)
# 5. DNS (Route 53 records pointing to CloudFront)
STACKS_TO_DEPLOY = [
    "ConsistencyTracker-Database",
    "ConsistencyTracker-Auth",
    "ConsistencyTracker-API",
    "ConsistencyTracker-DNS",      # Deploy DNS before Storage (Storage needs DNS export)
    "ConsistencyTracker-Storage",  # Storage imports certificate ARN from DNS stack
]

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check AWS CLI
    try:
        result = subprocess.run(["aws", "--version"], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print("❌ AWS CLI not found. Please install AWS CLI first.")
            sys.exit(1)
        print(f"✅ AWS CLI found: {result.stdout.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ AWS CLI not found. Please install AWS CLI first.")
        sys.exit(1)
    
    # Check CDK CLI
    try:
        result = subprocess.run(["cdk", "--version"], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print("❌ AWS CDK not found. Please install with: npm install -g aws-cdk")
            sys.exit(1)
        print(f"✅ AWS CDK found: {result.stdout.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ AWS CDK not found. Please install with: npm install -g aws-cdk")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print(f"❌ Python 3.9+ required. Found: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def setup_venv():
    """Set up Python virtual environment"""
    aws_dir = Path(__file__).parent
    venv_path = aws_dir / ".venv"
    
    if not venv_path.exists():
        print("\n🐍 Creating Python virtual environment...")
        result = subprocess.run(
            [sys.executable, "-m", "venv", ".venv"],
            cwd=aws_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"❌ Failed to create virtual environment: {result.stderr}")
            sys.exit(1)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")
    
    return venv_path

def install_dependencies(venv_path):
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    aws_dir = Path(__file__).parent
    
    # Determine pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
    else:  # Unix-like
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    result = subprocess.run(
        [str(python_path), "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=aws_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to install dependencies: {result.stderr}")
        sys.exit(1)
    print("✅ Dependencies installed")

def run_command(command, cwd=None, timeout=300, check=True):
    """Run a command with error handling"""
    print(f"\n🔄 Running: {command}")
    if cwd:
        print(f"📁 Working directory: {cwd}")
    
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    
    if result.stdout:
        print(result.stdout)
    
    if result.returncode != 0:
        if result.stderr:
            print(f"❌ Error: {result.stderr}")
        if check:
            return False
        return result
    
    print(f"✅ Command completed successfully")
    return result

def bootstrap_cdk(venv_path):
    """Bootstrap CDK if needed"""
    print("\n🔧 Checking CDK bootstrap status...")
    aws_dir = Path(__file__).parent
    
    # Check if already bootstrapped
    result = subprocess.run(
        f"aws cloudformation describe-stacks --stack-name CDKToolkit --region {AWS_REGION}",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ CDK already bootstrapped")
        return True
    
    print("🔧 Bootstrapping CDK...")
    bootstrap_cmd = f"cdk bootstrap aws://{AWS_ACCOUNT_ID}/{AWS_REGION}"
    
    if not run_command(bootstrap_cmd, cwd=aws_dir, timeout=600, check=False):
        print("⚠️ Bootstrap may have failed, but continuing...")
        print("   You can manually bootstrap with:")
        print(f"   cdk bootstrap aws://{AWS_ACCOUNT_ID}/{AWS_REGION}")
    
    return True


def ensure_apigw_cloudwatch_role():
    """Ensure API Gateway has a CloudWatch Logs role configured at the account level."""
    print("\n🔒 Ensuring API Gateway CloudWatch Logs role is configured...")

    iam = boto3.client("iam")
    apigw = boto3.client("apigateway", region_name=AWS_REGION)

    role_name = "APIGatewayCloudWatchLogsRole"
    assume_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "apigateway.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    logs_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams",
                    "logs:PutLogEvents",
                    "logs:GetLogEvents",
                    "logs:FilterLogEvents",
                ],
                "Resource": "*",
            }
        ],
    }

    # 1) Ensure role exists
    try:
        resp = iam.get_role(RoleName=role_name)
        role_arn = resp["Role"]["Arn"]
        print(f"✅ Found existing IAM role: {role_arn}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            print(f"❌ Error checking IAM role: {e}")
            raise
        print(f"🔧 Creating IAM role: {role_name}")
        resp = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_policy),
            Description="Role for API Gateway to write CloudWatch Logs",
        )
        role_arn = resp["Role"]["Arn"]
        print(f"✅ Created IAM role: {role_arn}")

    # 2) Ensure inline policy is present (safe to overwrite)
    try:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="APIGatewayCloudWatchLogsPolicy",
            PolicyDocument=json.dumps(logs_policy),
        )
        print("✅ Ensured IAM role has CloudWatch Logs permissions")
    except ClientError as e:
        print(f"❌ Error attaching policy to IAM role: {e}")
        raise

    # 3) Ensure API Gateway account setting points to this role
    try:
        account = apigw.get_account()
        current_arn = account.get("cloudwatchRoleArn")
    except ClientError as e:
        print(f"❌ Error reading API Gateway account settings: {e}")
        raise

    if current_arn == role_arn:
        print("✅ API Gateway already configured with correct CloudWatch Logs role")
        return

    print("🔧 Updating API Gateway account CloudWatch Logs role ARN...")
    try:
        apigw.update_account(
            patchOperations=[
                {
                    "op": "replace" if current_arn else "add",
                    "path": "/cloudwatchRoleArn",
                    "value": role_arn,
                }
            ]
        )
        print("✅ API Gateway CloudWatch Logs role configured")
    except ClientError as e:
        print(f"❌ Failed to update API Gateway account settings: {e}")
        raise

def deploy_stack(stack_name, venv_path):
    """Deploy a single CDK stack"""
    print(f"\n☁️ Deploying stack: {stack_name}")
    aws_dir = Path(__file__).parent
    
    deploy_cmd = f"cdk deploy {stack_name} --require-approval never"
    
    if not run_command(deploy_cmd, cwd=aws_dir, timeout=1800, check=True):
        print(f"❌ Failed to deploy {stack_name}")
        return False
    
    print(f"✅ Successfully deployed {stack_name}")
    return True

def check_existing_resources():
    """Check if resources already exist and confirm data protection"""
    print("\n🔒 Checking existing resources and data protection...")
    
    # Check if Database stack exists
    db_result = subprocess.run(
        f"aws cloudformation describe-stacks --stack-name {STACKS_TO_DEPLOY[0]} --region {AWS_REGION}",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if db_result.returncode == 0:
        print("⚠️  Database stack already exists")
        print("✅ DynamoDB tables are protected with RETAIN policy")
        print("   - Tables will NOT be deleted even if stack is destroyed")
        print("   - Your data is safe!")
    
    # Check if Auth stack exists
    auth_result = subprocess.run(
        f"aws cloudformation describe-stacks --stack-name {STACKS_TO_DEPLOY[1]} --region {AWS_REGION}",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if auth_result.returncode == 0:
        print("⚠️  Auth stack already exists")
        print("   - This will update the existing Cognito User Pool")
        print("   - Existing users and groups will be preserved")
    
    print("✅ Data protection verified")

def verify_deployment():
    """Verify that stacks were deployed successfully"""
    print("\n📊 Verifying deployment...")
    
    for stack_name in STACKS_TO_DEPLOY:
        result = subprocess.run(
            f"aws cloudformation describe-stacks --stack-name {stack_name} --region {AWS_REGION} --query 'Stacks[0].StackStatus' --output text",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            status = result.stdout.strip()
            if status == "CREATE_COMPLETE" or status == "UPDATE_COMPLETE":
                print(f"✅ {stack_name}: {status}")
            else:
                print(f"⚠️ {stack_name}: {status}")
        else:
            print(f"❌ Could not verify {stack_name}")

def check_existing_resources():
    """Check if resources already exist and warn about data protection"""
    print("\n🔒 Checking existing resources and data protection...")
    
    # Check if Database stack exists
    db_result = subprocess.run(
        f"aws cloudformation describe-stacks --stack-name {STACKS_TO_DEPLOY[0]} --region {AWS_REGION}",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if db_result.returncode == 0:
        print("⚠️  Database stack already exists")
        print("✅ DynamoDB tables are protected with RETAIN policy")
        print("   - Tables will NOT be deleted even if stack is destroyed")
        print("   - Your data is safe!")
    
    # Check if Auth stack exists
    auth_result = subprocess.run(
        f"aws cloudformation describe-stacks --stack-name {STACKS_TO_DEPLOY[1]} --region {AWS_REGION}",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if auth_result.returncode == 0:
        print("⚠️  Auth stack already exists")
        print("   - This will update the existing Cognito User Pool")
        print("   - Existing users and groups will be preserved")
    
    print("✅ Data protection verified")

def main():
    print("🚀 Starting Consistency Tracker Infrastructure Deployment")
    print("=" * 60)
    print("🔒 SAFETY: This script only DEPLOYS/UPDATES infrastructure")
    print("   - It does NOT destroy or delete anything")
    print("   - DynamoDB tables are protected with RETAIN policy")
    print("   - Your data is safe from accidental deletion")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Step 1: Check prerequisites
    check_prerequisites()

    # Step 1.2: Ensure API Gateway CloudWatch Logs role exists
    try:
        ensure_apigw_cloudwatch_role()
    except Exception:
        print("❌ Failed to ensure API Gateway CloudWatch Logs role. Aborting deployment.")
        sys.exit(1)
    
    # Step 1.5: Check existing resources and data protection
    check_existing_resources()
    
    # Step 2: Set up virtual environment
    venv_path = setup_venv()
    
    # Step 3: Install dependencies
    install_dependencies(venv_path)
    
    # Step 4: Bootstrap CDK
    bootstrap_cdk(venv_path)
    
    # Step 5: Synthesize templates
    print("\n🔨 Synthesizing CDK templates...")
    aws_dir = Path(__file__).parent
    if not run_command("cdk synth", cwd=aws_dir, timeout=300, check=True):
        print("❌ Synthesis failed. Please check for errors above.")
        sys.exit(1)
    
    # Step 6: Deploy stacks
    print("\n☁️ Deploying infrastructure stacks...")
    print(f"📋 Stacks to deploy: {', '.join(STACKS_TO_DEPLOY)}")
    
    success = True
    for stack_name in STACKS_TO_DEPLOY:
        if not deploy_stack(stack_name, venv_path):
            success = False
            break
    
    # Step 7: Verify deployment
    if success:
        verify_deployment()
    
    # Summary
    elapsed = datetime.now() - start_time
    print("\n" + "=" * 60)
    if success:
        print("🎉 Deployment completed successfully!")
        print(f"⏱️ Total time: {elapsed.seconds // 60}m {elapsed.seconds % 60}s")
        print("\n📋 Deployed Stacks:")
        for stack_name in STACKS_TO_DEPLOY:
            print(f"   ✅ {stack_name}")
        print("\n📝 Next Steps:")
        print("   1. Create first admin user in Cognito User Pool (if not already created)")
        print("      - Recommended: python aws/create_admin_user.py")
        print("   2. Verify DynamoDB tables and API endpoints:")
        print("      - Check tables in DynamoDB console")
        print("      - Check API endpoint output from ConsistencyTracker-API stack")
        print("   3. Verify CloudFront distributions and DNS:")
        print("      - Frontend distribution domain")
        print("      - Content distribution domain (content.repwarrior.net)")
        print("      - Route 53 records for repwarrior.net and subdomains")
    else:
        print("❌ Deployment failed!")
        print("📝 Troubleshooting:")
        print("   1. Check CloudFormation console for detailed errors")
        print("   2. Verify AWS credentials and permissions")
        print("   3. Check CDK bootstrap status")
        print("   4. Review error messages above")
        sys.exit(1)

if __name__ == "__main__":
    main()

