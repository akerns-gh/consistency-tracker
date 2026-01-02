#!/usr/bin/env python3
"""
Check for discrepancies between coaches in Cognito groups and Cognito users.

Coaches are stored ONLY in Cognito (not in DynamoDB), so we check:
1. Cognito users in coach groups that don't exist as users
2. Coach groups that might be empty or have issues
"""

import boto3
import sys
from botocore.exceptions import ClientError
from typing import Dict, List, Set

# Configuration
AWS_REGION = "us-east-1"
USER_POOL_ID = None  # Will be fetched from CloudFormation

def get_user_pool_id():
    """Get User Pool ID from CloudFormation stack."""
    global USER_POOL_ID
    if USER_POOL_ID:
        return USER_POOL_ID
    
    try:
        cf = boto3.client('cloudformation', region_name=AWS_REGION)
        response = cf.describe_stacks(
            StackName="ConsistencyTracker-Auth"
        )
        
        for output in response['Stacks'][0]['Outputs']:
            if output['OutputKey'] == 'UserPoolId':
                USER_POOL_ID = output['OutputValue']
                return USER_POOL_ID
        
        print("❌ Could not find UserPoolId in CloudFormation stack")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error fetching User Pool ID: {e}")
        sys.exit(1)

def get_all_cognito_groups() -> List[Dict]:
    """Get all groups from Cognito User Pool."""
    cognito = boto3.client('cognito-idp', region_name=AWS_REGION)
    user_pool_id = get_user_pool_id()
    
    groups = []
    next_token = None
    
    while True:
        try:
            if next_token:
                response = cognito.list_groups(
                    UserPoolId=user_pool_id,
                    NextToken=next_token
                )
            else:
                response = cognito.list_groups(UserPoolId=user_pool_id)
            
            groups.extend(response.get('Groups', []))
            
            next_token = response.get('NextToken')
            if not next_token:
                break
        except ClientError as e:
            print(f"❌ Error listing Cognito groups: {e}")
            return []
    
    return groups

def get_users_in_group(group_name: str) -> List[Dict]:
    """Get all users in a Cognito group."""
    cognito = boto3.client('cognito-idp', region_name=AWS_REGION)
    user_pool_id = get_user_pool_id()
    
    users = []
    next_token = None
    
    while True:
        try:
            if next_token:
                response = cognito.list_users_in_group(
                    UserPoolId=user_pool_id,
                    GroupName=group_name,
                    NextToken=next_token
                )
            else:
                response = cognito.list_users_in_group(
                    UserPoolId=user_pool_id,
                    GroupName=group_name
                )
            
            users.extend(response.get('Users', []))
            
            next_token = response.get('NextToken')
            if not next_token:
                break
        except ClientError as e:
            print(f"❌ Error listing users in group {group_name}: {e}")
            return []
    
    return users

def get_user_email(user: Dict) -> str:
    """Extract email from Cognito user attributes."""
    for attr in user.get('Attributes', []):
        if attr['Name'] == 'email':
            return attr['Value']
    # Fallback to username if email not found
    return user.get('Username', '')

def check_coach_discrepancies():
    """Check for discrepancies in coach groups."""
    print("🔍 Checking coach groups and Cognito users...")
    print("=" * 70)
    
    # Get all Cognito groups
    print("\n📊 Fetching Cognito groups...")
    all_groups = get_all_cognito_groups()
    print(f"✅ Found {len(all_groups)} groups in Cognito")
    
    # Filter coach groups
    coach_groups = [g for g in all_groups if g['GroupName'].startswith('coach-')]
    print(f"✅ Found {len(coach_groups)} coach groups")
    
    # Get all Cognito users
    print("\n👥 Fetching all Cognito users...")
    cognito = boto3.client('cognito-idp', region_name=AWS_REGION)
    user_pool_id = get_user_pool_id()
    
    all_users = []
    pagination_token = None
    
    while True:
        try:
            if pagination_token:
                response = cognito.list_users(
                    UserPoolId=user_pool_id,
                    PaginationToken=pagination_token
                )
            else:
                response = cognito.list_users(UserPoolId=user_pool_id)
            
            all_users.extend(response.get('Users', []))
            
            pagination_token = response.get('PaginationToken')
            if not pagination_token:
                break
        except ClientError as e:
            print(f"❌ Error listing Cognito users: {e}")
            break
    
    print(f"✅ Found {len(all_users)} users in Cognito")
    
    # Build user lookup
    user_emails = set()
    user_username_map = {}  # username -> user
    
    for user in all_users:
        email = get_user_email(user).strip().lower()
        username = user.get('Username', '').strip()
        if email:
            user_emails.add(email)
        if username:
            user_username_map[username] = user
    
    # Check coach groups
    print("\n" + "=" * 70)
    print("📋 COACH GROUP REPORT")
    print("=" * 70)
    
    issues_found = False
    total_coaches = 0
    coaches_without_users = []
    empty_groups = []
    
    for group in coach_groups:
        group_name = group['GroupName']
        users_in_group = get_users_in_group(group_name)
        
        if len(users_in_group) == 0:
            empty_groups.append(group_name)
            continue
        
        total_coaches += len(users_in_group)
        
        for user in users_in_group:
            username = user.get('Username', '')
            email = get_user_email(user)
            
            # Check if user still exists
            if username not in user_username_map:
                coaches_without_users.append({
                    'group': group_name,
                    'username': username,
                    'email': email
                })
                issues_found = True
    
    # Report findings
    if empty_groups:
        print(f"\n⚠️  EMPTY COACH GROUPS ({len(empty_groups)}):")
        print("-" * 70)
        for group_name in sorted(empty_groups):
            print(f"  • {group_name}")
        issues_found = True
    else:
        print("\n✅ No empty coach groups")
    
    if coaches_without_users:
        print(f"\n⚠️  COACHES IN GROUPS WITHOUT USER RECORDS ({len(coaches_without_users)}):")
        print("-" * 70)
        for coach in coaches_without_users:
            print(f"  • Group: {coach['group']}")
            print(f"    Username: {coach['username']}")
            print(f"    Email: {coach['email']}")
            print()
        issues_found = True
    else:
        print("\n✅ All coaches in groups have valid user records")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total coach groups: {len(coach_groups)}")
    print(f"Total coaches in groups: {total_coaches}")
    print(f"Empty coach groups: {len(empty_groups)}")
    print(f"Coaches without user records: {len(coaches_without_users)}")
    
    # List all coach groups with their members
    print("\n" + "=" * 70)
    print("📋 COACH GROUPS DETAIL")
    print("=" * 70)
    for group in sorted(coach_groups, key=lambda x: x['GroupName']):
        group_name = group['GroupName']
        users_in_group = get_users_in_group(group_name)
        print(f"\n{group_name}:")
        if len(users_in_group) == 0:
            print("  (empty)")
        else:
            for user in users_in_group:
                email = get_user_email(user)
                username = user.get('Username', '')
                status = user.get('UserStatus', 'N/A')
                enabled = user.get('Enabled', False)
                enabled_str = "Enabled" if enabled else "Disabled"
                print(f"  • {email} ({username}) - {status} - {enabled_str}")
    
    if issues_found:
        print("\n⚠️  ISSUES FOUND!")
        return False
    else:
        print("\n✅ No issues found with coach groups!")
        return True

if __name__ == "__main__":
    try:
        success = check_coach_discrepancies()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

