#!/usr/bin/env python3
"""
Check User Status in Cognito

This script checks a user's status in Cognito User Pool, including:
- User status (CONFIRMED, FORCE_CHANGE_PASSWORD, etc.)
- Email verification status
- Account enabled/disabled status
- User attributes
"""

import boto3
import sys
from botocore.exceptions import ClientError

AWS_REGION = "us-east-1"
STACK_NAME = "ConsistencyTracker-Auth"

def get_user_pool_id(cloudformation_client, stack_name):
    """Get User Pool ID from CloudFormation stack outputs"""
    try:
        response = cloudformation_client.describe_stacks(StackName=stack_name)
        stacks = response['Stacks']
        if not stacks:
            return None
        
        outputs = stacks[0].get('Outputs', [])
        for output in outputs:
            if output['OutputKey'] == 'UserPoolId':
                return output['OutputValue']
        return None
    except ClientError:
        return None

def find_user_by_email(cognito_client, user_pool_id, email):
    """Find a user by email address"""
    try:
        # Try email as username first
        try:
            response = cognito_client.admin_get_user(
                UserPoolId=user_pool_id,
                Username=email
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] != 'UserNotFoundException':
                raise
        
        # Search by email attribute
        paginator = cognito_client.get_paginator('list_users')
        for page in paginator.paginate(UserPoolId=user_pool_id):
            for user in page.get('Users', []):
                for attr in user.get('Attributes', []):
                    if attr['Name'] == 'email' and attr['Value'].lower() == email.lower():
                        # Get full user details
                        return cognito_client.admin_get_user(
                            UserPoolId=user_pool_id,
                            Username=user['Username']
                        )
        return None
    except ClientError as e:
        print(f"Error finding user: {e}")
        return None

def check_user_status(email):
    """Check user status in Cognito"""
    print("=" * 70)
    print("👤 CHECK USER STATUS")
    print("=" * 70)
    print()
    
    cf_client = boto3.client('cloudformation', region_name=AWS_REGION)
    cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)
    
    # Get User Pool ID
    user_pool_id = get_user_pool_id(cf_client, STACK_NAME)
    if not user_pool_id:
        print("❌ Failed to get User Pool ID")
        sys.exit(1)
    
    print(f"✅ User Pool ID: {user_pool_id}")
    print()
    
    # Find user
    print(f"🔍 Looking up user: {email}")
    user = find_user_by_email(cognito_client, user_pool_id, email)
    
    if not user:
        print(f"❌ User '{email}' not found")
        sys.exit(1)
    
    print(f"✅ User found")
    print()
    
    # Display user information
    print("📋 User Information:")
    print(f"   Username: {user['Username']}")
    print(f"   User Status: {user.get('UserStatus', 'N/A')}")
    print(f"   Enabled: {'✅ Yes' if user.get('Enabled', False) else '❌ No'}")
    print()
    
    # Check attributes
    print("📧 Attributes:")
    email_verified = False
    attributes = user.get('UserAttributes', []) or user.get('Attributes', [])
    if not attributes:
        print("   (No attributes found)")
    else:
        for attr in attributes:
            attr_name = attr.get('Name', '')
            attr_value = attr.get('Value', '')
            print(f"   {attr_name}: {attr_value}")
            if attr_name == 'email_verified':
                email_verified = attr_value == 'true'
    
    print()
    
    # Status analysis
    print("🔍 Status Analysis:")
    user_status = user.get('UserStatus', '')
    enabled = user.get('Enabled', False)
    
    issues = []
    
    if not enabled:
        issues.append("❌ Account is DISABLED - user cannot log in")
    
    if user_status == 'FORCE_CHANGE_PASSWORD':
        issues.append("⚠️  User status is FORCE_CHANGE_PASSWORD - user must change password on first login")
    
    if not email_verified:
        issues.append("⚠️  Email is not verified - may prevent login")
    
    if user_status == 'UNCONFIRMED':
        issues.append("❌ User is UNCONFIRMED - account not activated")
    
    if issues:
        print("   Issues found:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("   ✅ No obvious issues found")
    
    print()
    print("=" * 70)
    print("💡 Troubleshooting:")
    if not enabled:
        print("   - Enable the user account in Cognito Console")
    if user_status == 'FORCE_CHANGE_PASSWORD':
        print("   - User needs to log in and change password")
        print("   - Or use reset_user_password.py with Permanent=True")
    if not email_verified:
        print("   - User needs to verify email before login")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        email = input("Enter user email address: ").strip()
    else:
        email = sys.argv[1]
    
    if not email:
        print("❌ Email address is required")
        sys.exit(1)
    
    check_user_status(email)

