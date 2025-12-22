#!/usr/bin/env python3
"""
Update a user's custom:clubId attribute based on their group membership.

This script:
1. Gets the user's groups from Cognito
2. Extracts the club name from a club-{name}-admins group
3. Looks up the club in DynamoDB
4. Updates the user's custom:clubId attribute
"""

import boto3
import sys
import re
from botocore.exceptions import ClientError

# Configuration
AWS_REGION = "us-east-1"
STACK_NAME = "ConsistencyTracker-Auth"
USER_EMAIL = "test-club-admin@repwarrior.net"  # Change to the user email
MANUAL_CLUB_ID = None  # If set, use this club ID instead of looking it up

def get_user_pool_id(cloudformation_client, stack_name, region):
    """Get User Pool ID from CloudFormation stack outputs"""
    try:
        response = cloudformation_client.describe_stacks(StackName=stack_name)
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

def sanitize_for_group(name: str) -> str:
    """Sanitize club name for group name comparison (matches auth_utils logic)"""
    if not name:
        return ""
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    sanitized = sanitized.lower()
    if not sanitized or not sanitized[0].isalpha():
        sanitized = 'club_' + sanitized
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    if not sanitized:
        sanitized = "club"
    if len(sanitized) > 100:
        sanitized = sanitized[:100].rstrip('_')
    return sanitized

def get_user_groups(cognito_client, user_pool_id, username):
    """Get all groups for a user"""
    try:
        response = cognito_client.admin_list_groups_for_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        return [group['GroupName'] for group in response.get('Groups', [])]
    except ClientError as e:
        print(f"❌ Error getting user groups: {e}")
        return []

def find_club_from_group(group_name, dynamodb_client):
    """Find club ID from group name by looking up in DynamoDB"""
    # Pattern: club-{sanitizedName}-admins
    club_admin_pattern = re.compile(r'^club-([a-z0-9_-]+)-admins$')
    match = club_admin_pattern.match(group_name)
    if not match:
        return None
    
    sanitized_name = match.group(1)
    print(f"🔍 Looking up club with sanitized name: {sanitized_name}")
    
    # Scan clubs table
    try:
        table_name = "ConsistencyTracker-Clubs"
        table = dynamodb_client.Table(table_name)
        response = table.scan()
        clubs = response.get('Items', [])
        
        for club in clubs:
            club_name = club.get('clubName', '')
            if club_name:
                club_sanitized = sanitize_for_group(club_name)
                if club_sanitized == sanitized_name:
                    club_id = club.get('clubId')
                    print(f"✅ Found club: {club_name} (ID: {club_id})")
                    return club_id
        
        print(f"⚠️  No club found matching sanitized name: {sanitized_name}")
        return None
    except Exception as e:
        print(f"❌ Error looking up club: {e}")
        return None

def update_user_club_id(cognito_client, user_pool_id, username, club_id):
    """Update user's custom:clubId attribute"""
    try:
        print(f"🔄 Updating custom:clubId for user {username} to {club_id}...")
        cognito_client.admin_update_user_attributes(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[
                {'Name': 'custom:clubId', 'Value': club_id}
            ]
        )
        print(f"✅ Successfully updated custom:clubId attribute")
        return True
    except ClientError as e:
        print(f"❌ Error updating user attributes: {e}")
        return False

def main():
    print("🔧 Update User Club ID Attribute")
    print("=" * 60)
    print(f"User Email: {USER_EMAIL}")
    print()
    
    # Initialize AWS clients
    cf_client = boto3.client('cloudformation', region_name=AWS_REGION)
    cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    
    # Get User Pool ID
    print("🔍 Getting User Pool ID...")
    user_pool_id = get_user_pool_id(cf_client, STACK_NAME, AWS_REGION)
    if not user_pool_id:
        sys.exit(1)
    print(f"✅ User Pool ID: {user_pool_id}")
    
    # Get user's username (use email as username)
    username = USER_EMAIL
    
    # Get user's groups
    print(f"\n👥 Getting groups for user {username}...")
    groups = get_user_groups(cognito_client, user_pool_id, username)
    if not groups:
        print("❌ User has no groups")
        sys.exit(1)
    
    print(f"✅ User groups: {', '.join(groups)}")
    
    # Find club-admin group
    club_admin_group = None
    for group in groups:
        if group.startswith('club-') and group.endswith('-admins'):
            club_admin_group = group
            break
    
    if not club_admin_group:
        print("❌ User is not in a club-admin group")
        sys.exit(1)
    
    print(f"✅ Found club-admin group: {club_admin_group}")
    
    # Find club ID from group name
    print(f"\n🔍 Looking up club ID from group name...")
    club_id = find_club_from_group(club_admin_group, dynamodb)
    if not club_id:
        print("❌ Could not find club ID")
        sys.exit(1)
    
    # Update user's custom:clubId attribute
    print(f"\n🔄 Updating user's custom:clubId attribute...")
    success = update_user_club_id(cognito_client, user_pool_id, username, club_id)
    if not success:
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Successfully updated user's custom:clubId attribute!")
    print(f"\n📝 User {username} now has custom:clubId = {club_id}")
    print("\n💡 User should log out and log back in to get a new JWT token with the updated attribute")

if __name__ == "__main__":
    main()

