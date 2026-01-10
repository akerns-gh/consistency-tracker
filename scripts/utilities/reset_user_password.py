#!/usr/bin/env python3
"""
Reset User Password in Cognito User Pool

This script allows admins to programmatically reset a user's password
without requiring email verification or the manual password reset flow.

Usage:
    python3 reset_user_password.py <email> <new_password>
    
Or run interactively:
    python3 reset_user_password.py
"""

import boto3
import sys
import getpass
from botocore.exceptions import ClientError

# ============================================================================
# CONFIGURATION
# ============================================================================

AWS_REGION = "us-east-1"
STACK_NAME = "ConsistencyTracker-Auth"

# ============================================================================
# Script Logic
# ============================================================================

def get_user_pool_id(cloudformation_client, stack_name, region):
    """Get User Pool ID from CloudFormation stack outputs"""
    try:
        response = cloudformation_client.describe_stacks(
            StackName=stack_name
        )
        
        stacks = response['Stacks']
        if not stacks:
            print(f"❌ Stack '{stack_name}' not found")
            return None
        
        outputs = stacks[0].get('Outputs', [])
        for output in outputs:
            if output['OutputKey'] == 'UserPoolId':
                return output['OutputValue']
        
        print(f"❌ UserPoolId output not found in stack '{stack_name}'")
        return None
        
    except ClientError as e:
        print(f"❌ Error getting stack outputs: {e}")
        return None


def validate_password(password):
    """Validate password meets Cognito requirements"""
    errors = []
    
    if len(password) < 12:
        errors.append("Password must be at least 12 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    return errors


def find_user_by_email(cognito_client, user_pool_id, email):
    """Find a user by email address (searches by email attribute)"""
    try:
        # First, try using email as username (in case email is used as username)
        try:
            response = cognito_client.admin_get_user(
                UserPoolId=user_pool_id,
                Username=email
            )
            return response['Username']
        except ClientError as e:
            if e.response['Error']['Code'] != 'UserNotFoundException':
                raise
        
        # If not found, search by listing users and matching email attribute
        print(f"   🔍 Searching for user by email attribute...")
        paginator = cognito_client.get_paginator('list_users')
        
        found_users = []
        for page in paginator.paginate(UserPoolId=user_pool_id):
            for user in page.get('Users', []):
                # Check user attributes for email
                for attr in user.get('Attributes', []):
                    if attr['Name'] == 'email':
                        user_email = attr['Value']
                        found_users.append({
                            'username': user['Username'],
                            'email': user_email
                        })
                        if user_email.lower() == email.lower():
                            username = user['Username']
                            print(f"   ✅ Found user with username: {username}")
                            return username
        
        # If not found, show available users for debugging
        if found_users:
            print(f"   ⚠️  Email '{email}' not found. Available users:")
            for user_info in found_users[:10]:  # Show first 10
                print(f"      - {user_info['email']} (username: {user_info['username'][:20]}...)")
            if len(found_users) > 10:
                print(f"      ... and {len(found_users) - 10} more users")
        
        return None
        
    except ClientError as e:
        print(f"   ⚠️  Error searching for user: {e}")
        return None


def reset_user_password(cognito_client, user_pool_id, email, new_password, permanent=True):
    """Reset a user's password in Cognito"""
    try:
        print(f"🔄 Resetting password for user: {email}")
        
        # Validate password
        password_errors = validate_password(new_password)
        if password_errors:
            print("❌ Password does not meet requirements:")
            for error in password_errors:
                print(f"   - {error}")
            return False
        
        # Find user by email (username may be UUID, email is an attribute)
        username = find_user_by_email(cognito_client, user_pool_id, email)
        
        if not username:
            print(f"❌ User with email '{email}' not found in Cognito User Pool")
            print("   💡 Make sure the email address is correct")
            return False
        
        # Reset password using the actual username
        if username != email:
            print(f"   Using username: {username}")
        
        cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=new_password,
            Permanent=permanent
        )
        
        # Also verify email to ensure user can log in
        try:
            cognito_client.admin_update_user_attributes(
                UserPoolId=user_pool_id,
                Username=username,
                UserAttributes=[
                    {'Name': 'email_verified', 'Value': 'true'}
                ]
            )
            print(f"   ✅ Email verified")
        except ClientError as e:
            print(f"   ⚠️  Could not verify email: {e}")
        
        password_type = "permanent" if permanent else "temporary"
        print(f"✅ Password reset successfully ({password_type})")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'UserNotFoundException':
            print(f"❌ User not found in Cognito User Pool")
        elif error_code == 'InvalidPasswordException':
            print(f"❌ Password does not meet Cognito requirements: {error_message}")
        elif error_code == 'InvalidParameterException':
            print(f"❌ Invalid parameter: {error_message}")
        else:
            print(f"❌ Error resetting password: {error_code} - {error_message}")
        
        return False


def main():
    print("=" * 70)
    print("🔐 RESET USER PASSWORD")
    print("=" * 70)
    print()
    
    # Initialize AWS clients
    cf_client = boto3.client('cloudformation', region_name=AWS_REGION)
    cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)
    
    # Get User Pool ID
    print("🔍 Getting User Pool ID from CloudFormation stack...")
    user_pool_id = get_user_pool_id(cf_client, STACK_NAME, AWS_REGION)
    
    if not user_pool_id:
        print("❌ Failed to get User Pool ID")
        sys.exit(1)
    
    print(f"✅ User Pool ID: {user_pool_id}")
    print()
    
    # Get email and password from command line or interactively
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        new_password = sys.argv[2]
        permanent = True  # Default to permanent
        if len(sys.argv) >= 4:
            permanent = sys.argv[3].lower() in ['true', '1', 'yes', 'permanent']
    else:
        # Interactive mode
        email = input("Enter user email address: ").strip()
        if not email:
            print("❌ Email address is required")
            sys.exit(1)
        
        print("\nPassword Requirements:")
        print("  - Minimum 12 characters")
        print("  - At least one uppercase letter (A-Z)")
        print("  - At least one lowercase letter (a-z)")
        print("  - At least one number (0-9)")
        print()
        
        new_password = getpass.getpass("Enter new password: ")
        if not new_password:
            print("❌ Password is required")
            sys.exit(1)
        
        confirm_password = getpass.getpass("Confirm new password: ")
        if new_password != confirm_password:
            print("❌ Passwords do not match")
            sys.exit(1)
        
        permanent_input = input("Set as permanent password? (y/n, default: y): ").strip().lower()
        permanent = permanent_input != 'n'
    
    print()
    print(f"📋 Configuration:")
    print(f"   Email: {email}")
    print(f"   Password Type: {'Permanent' if permanent else 'Temporary'}")
    print()
    
    # Reset password
    success = reset_user_password(
        cognito_client,
        user_pool_id,
        email,
        new_password,
        permanent=permanent
    )
    
    if not success:
        sys.exit(1)
    
    # Success summary
    print()
    print("=" * 70)
    print("🎉 Password reset completed successfully!")
    print()
    print("📝 Next Steps:")
    if permanent:
        print(f"   - User '{email}' can now log in with the new password")
    else:
        print(f"   - User '{email}' must change password on next login")
        print(f"   - Temporary password: {new_password}")
    print("=" * 70)


if __name__ == "__main__":
    main()

