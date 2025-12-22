#!/usr/bin/env python3
"""
Create First Admin User in Cognito User Pool

This script creates the first admin user in the Consistency Tracker Cognito User Pool
and adds them to the specified admin group.

Group Options:
- "app-admin": Platform-wide administrators who can create clubs
- "club-{sanitizedClubName}-admins": Club-scoped administrators (created automatically when clubs are created, uses sanitized club name)
- "coach-{clubId}-{teamId}": Team-scoped coaches (created automatically when teams are created)
"""

import boto3
import sys
from botocore.exceptions import ClientError

# ============================================================================
# CONFIGURATION - Update these values
# ============================================================================

# AWS Configuration
AWS_REGION = "us-east-1"
STACK_NAME = "ConsistencyTracker-Auth"

# Admin User Configuration
ADMIN_EMAIL = ""  # Change to your admin email
ADMIN_USERNAME = ""  # Usually same as email
TEMPORARY_PASSWORD = ""  # Must meet password policy (12+ chars, uppercase, lowercase, number)

# Group Configuration
# Options:
#   - "app-admin" (singular): Platform-wide admins who can create clubs
#   - "club-{sanitizedClubName}-admins": Club-scoped admins (created automatically when club is created, uses sanitized club name)
#   - "coach-{clubId}-{teamId}": Team-scoped coaches (created automatically when team is created)
ADMIN_GROUP_NAME = "app-admin"  # Change to "app-admin" for platform administrators, or use dynamic group name

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

def create_admin_user(cognito_client, user_pool_id, username, email, temp_password):
    """Create admin user in Cognito User Pool"""
    try:
        print(f"👤 Creating admin user: {username}")
        
        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'}
            ],
            TemporaryPassword=temp_password,
            MessageAction='SUPPRESS',  # Don't send welcome email
            DesiredDeliveryMediums=['EMAIL']
        )
        
        print(f"✅ Admin user created successfully")
        print(f"   Username: {response['User']['Username']}")
        print(f"   User Status: {response['User']['UserStatus']}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UsernameExistsException':
            print(f"⚠️  User '{username}' already exists")
            return True  # User exists, continue to add to group
        else:
            print(f"❌ Error creating user: {e}")
            return False

def add_user_to_group(cognito_client, user_pool_id, username, group_name):
    """Add user to admin group"""
    try:
        print(f"👥 Adding user to '{group_name}' group...")
        
        cognito_client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name
        )
        
        print(f"✅ User added to '{group_name}' group successfully")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            print(f"❌ Group '{group_name}' not found. Make sure the Auth stack was deployed correctly.")
            return False
        elif error_code == 'InvalidParameterException' and 'already a member' in str(e):
            print(f"⚠️  User is already a member of '{group_name}' group")
            return True  # Already in group, that's fine
        else:
            print(f"❌ Error adding user to group: {e}")
            return False

def main():
    print("🔐 Creating First Admin User for Consistency Tracker")
    print("=" * 60)
    print(f"\n📋 Configuration:")
    print(f"   Region: {AWS_REGION}")
    print(f"   Stack: {STACK_NAME}")
    print(f"   Admin Email: {ADMIN_EMAIL}")
    print(f"   Admin Username: {ADMIN_USERNAME}")
    print(f"   Group: {ADMIN_GROUP_NAME}")
    print()
    
    # Initialize AWS clients
    cf_client = boto3.client('cloudformation', region_name=AWS_REGION)
    cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)
    
    # Step 1: Get User Pool ID
    print("🔍 Step 1: Getting User Pool ID from CloudFormation stack...")
    user_pool_id = get_user_pool_id(cf_client, STACK_NAME, AWS_REGION)
    
    if not user_pool_id:
        print("❌ Failed to get User Pool ID")
        sys.exit(1)
    
    print(f"✅ User Pool ID: {user_pool_id}")
    
    # Step 2: Create admin user
    print(f"\n👤 Step 2: Creating admin user...")
    user_created = create_admin_user(
        cognito_client,
        user_pool_id,
        ADMIN_USERNAME,
        ADMIN_EMAIL,
        TEMPORARY_PASSWORD
    )
    
    if not user_created:
        print("❌ Failed to create admin user")
        sys.exit(1)
    
    # Step 3: Add user to Admins group
    print(f"\n👥 Step 3: Adding user to '{ADMIN_GROUP_NAME}' group...")
    group_added = add_user_to_group(
        cognito_client,
        user_pool_id,
        ADMIN_USERNAME,
        ADMIN_GROUP_NAME
    )
    
    if not group_added:
        print("❌ Failed to add user to group")
        sys.exit(1)
    
    # Success summary
    print("\n" + "=" * 60)
    print("🎉 Admin user setup completed successfully!")
    print("\n📝 Next Steps:")
    print(f"   1. User '{ADMIN_USERNAME}' has been created")
    print(f"   2. Temporary password: {TEMPORARY_PASSWORD}")
    print(f"   3. User must change password on first login")
    print(f"   4. User is now a member of the '{ADMIN_GROUP_NAME}' group")
    print("\n💡 To login:")
    print(f"   - Email: {ADMIN_EMAIL}")
    print(f"   - Temporary Password: {TEMPORARY_PASSWORD}")
    print("   - User will be prompted to change password on first login")
    print("\n⚠️  Remember to update the password in this script after first use!")

if __name__ == "__main__":
    main()

