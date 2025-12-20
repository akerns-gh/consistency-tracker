#!/usr/bin/env python3
"""
Migration Script: Rename Cognito Club Groups to Use Club Names

This script renames existing Cognito groups from:
  club-{clubId}-admins
to:
  club-{sanitizedClubName}-admins

It migrates all users from the old groups to the new groups.

IMPORTANT: Run this script after updating the code to use club names in group names.
"""

import boto3
import sys
import re
from botocore.exceptions import ClientError
from typing import Dict, List, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

AWS_REGION = "us-east-1"
CLUB_TABLE = "ConsistencyTracker-Clubs"

# ============================================================================
# Helper Functions
# ============================================================================

def sanitize_club_name_for_group(club_name: str) -> str:
    """
    Sanitize club name for use in Cognito group names.
    
    Cognito group names must:
    - Start with a letter
    - Contain only alphanumeric characters, underscores, and hyphens
    - Be between 1 and 128 characters
    
    Args:
        club_name: Original club name
    
    Returns:
        Sanitized club name safe for Cognito group names
    """
    if not club_name:
        return "club"
    
    # Convert to lowercase and replace spaces/special chars with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', club_name)
    sanitized = sanitized.lower()
    
    # Ensure it starts with a letter (prepend 'club' if it starts with a number or underscore)
    if not sanitized or not sanitized[0].isalpha():
        sanitized = 'club_' + sanitized
    
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure it's not empty and limit length (Cognito max is 128, but we need room for 'club-' and '-admins')
    if not sanitized:
        sanitized = "club"
    
    # Limit to 100 chars to leave room for 'club-' prefix and '-admins' suffix
    if len(sanitized) > 100:
        sanitized = sanitized[:100].rstrip('_')
    
    return sanitized


def get_user_pool_id(cloudformation_client, stack_name: str, region: str) -> Optional[str]:
    """Get User Pool ID from CloudFormation stack."""
    try:
        response = cloudformation_client.describe_stacks(StackName=stack_name)
        outputs = response["Stacks"][0].get("Outputs", [])
        for output in outputs:
            if output["OutputKey"] == "UserPoolId":
                return output["OutputValue"]
        return None
    except Exception as e:
        print(f"⚠️  Could not get User Pool ID from stack {stack_name}: {e}")
        return None


def get_all_clubs(dynamodb) -> List[Dict]:
    """Get all clubs from DynamoDB."""
    try:
        table = dynamodb.Table(CLUB_TABLE)
        response = table.scan()
        return response.get("Items", [])
    except ClientError as e:
        print(f"❌ Error getting clubs: {e}")
        return []


def get_group_users(cognito_client, user_pool_id: str, group_name: str) -> List[str]:
    """Get all usernames in a Cognito group."""
    try:
        users = []
        paginator = cognito_client.get_paginator('list_users_in_group')
        for page in paginator.paginate(UserPoolId=user_pool_id, GroupName=group_name):
            for user in page.get('Users', []):
                users.append(user['Username'])
        return users
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            # Group doesn't exist - that's fine
            return []
        print(f"⚠️  Error getting users from group {group_name}: {e}")
        return []


def group_exists(cognito_client, user_pool_id: str, group_name: str) -> bool:
    """Check if a Cognito group exists."""
    try:
        cognito_client.get_group(UserPoolId=user_pool_id, GroupName=group_name)
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            return False
        raise


def create_group(cognito_client, user_pool_id: str, group_name: str, description: str) -> bool:
    """Create a Cognito group."""
    try:
        cognito_client.create_group(
            UserPoolId=user_pool_id,
            GroupName=group_name,
            Description=description
        )
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceConflictException':
            # Group already exists
            return True
        print(f"❌ Error creating group {group_name}: {e}")
        return False


def add_user_to_group(cognito_client, user_pool_id: str, username: str, group_name: str) -> bool:
    """Add a user to a Cognito group."""
    try:
        cognito_client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name
        )
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'InvalidParameterException' and 'already a member' in str(e):
            # User already in group - that's fine
            return True
        print(f"⚠️  Error adding user {username} to group {group_name}: {e}")
        return False


def remove_user_from_group(cognito_client, user_pool_id: str, username: str, group_name: str) -> bool:
    """Remove a user from a Cognito group."""
    try:
        cognito_client.admin_remove_user_from_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name
        )
        return True
    except ClientError as e:
        print(f"⚠️  Error removing user {username} from group {group_name}: {e}")
        return False


def delete_group(cognito_client, user_pool_id: str, group_name: str) -> bool:
    """Delete a Cognito group."""
    try:
        cognito_client.delete_group(
            UserPoolId=user_pool_id,
            GroupName=group_name
        )
        return True
    except ClientError as e:
        print(f"⚠️  Error deleting group {group_name}: {e}")
        return False


def migrate_club_group(
    cognito_client,
    user_pool_id: str,
    club: Dict,
    dry_run: bool = False
) -> bool:
    """
    Migrate a single club's Cognito group from UUID-based to name-based.
    
    Args:
        cognito_client: Boto3 Cognito client
        user_pool_id: Cognito User Pool ID
        club: Club dictionary with clubId and clubName
        dry_run: If True, only print what would be done without making changes
    
    Returns:
        True if successful, False otherwise
    """
    club_id = club.get("clubId")
    club_name = club.get("clubName")
    
    if not club_id:
        print(f"⚠️  Skipping club with no clubId: {club}")
        return False
    
    if not club_name:
        print(f"⚠️  Skipping club {club_id} with no clubName")
        return False
    
    # Generate old and new group names
    old_group_name = f"club-{club_id}-admins"
    sanitized_name = sanitize_club_name_for_group(club_name)
    new_group_name = f"club-{sanitized_name}-admins"
    description = f"Administrators for club {club_name}"
    
    print(f"\n📦 Migrating club: {club_name} ({club_id})")
    print(f"   Old group: {old_group_name}")
    print(f"   New group: {new_group_name}")
    
    # Check if old group exists
    if not group_exists(cognito_client, user_pool_id, old_group_name):
        print(f"   ⚠️  Old group does not exist, skipping")
        return True  # Not an error - group might not have been created yet
    
    # Get users from old group
    users = get_group_users(cognito_client, user_pool_id, old_group_name)
    print(f"   Found {len(users)} user(s) in old group")
    
    if dry_run:
        print(f"   [DRY RUN] Would:")
        print(f"     1. Create group: {new_group_name}")
        print(f"     2. Add {len(users)} user(s) to new group")
        print(f"     3. Delete old group: {old_group_name}")
        return True
    
    # Create new group if it doesn't exist
    if not group_exists(cognito_client, user_pool_id, new_group_name):
        if not create_group(cognito_client, user_pool_id, new_group_name, description):
            print(f"   ❌ Failed to create new group")
            return False
        print(f"   ✅ Created new group")
    else:
        print(f"   ℹ️  New group already exists")
    
    # Add all users to new group
    added_count = 0
    for username in users:
        if add_user_to_group(cognito_client, user_pool_id, username, new_group_name):
            added_count += 1
        else:
            print(f"   ⚠️  Failed to add user {username} to new group")
    
    print(f"   ✅ Added {added_count}/{len(users)} user(s) to new group")
    
    # Remove users from old group
    removed_count = 0
    for username in users:
        if remove_user_from_group(cognito_client, user_pool_id, username, old_group_name):
            removed_count += 1
    
    print(f"   ✅ Removed {removed_count}/{len(users)} user(s) from old group")
    
    # Delete old group
    if delete_group(cognito_client, user_pool_id, old_group_name):
        print(f"   ✅ Deleted old group")
    else:
        print(f"   ⚠️  Failed to delete old group (may still have users)")
    
    return True


# ============================================================================
# Main Migration Function
# ============================================================================

def main():
    """Run the migration."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Rename Cognito club groups to use club names')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--region', default=AWS_REGION, help=f'AWS region (default: {AWS_REGION})')
    parser.add_argument('--user-pool-id', help='Cognito User Pool ID (will try to get from CloudFormation if not provided)')
    parser.add_argument('--stack-name', default='ConsistencyTracker-Auth', help='CloudFormation stack name to get User Pool ID from')
    args = parser.parse_args()
    
    print("🚀 Starting Cognito club group migration...")
    print("=" * 60)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("=" * 60)
    
    # Initialize AWS clients
    dynamodb = boto3.resource("dynamodb", region_name=args.region)
    cognito_client = boto3.client("cognito-idp", region_name=args.region)
    
    # Get User Pool ID
    user_pool_id = args.user_pool_id
    if not user_pool_id:
        print(f"\n📋 Getting User Pool ID from CloudFormation stack: {args.stack_name}")
        cf_client = boto3.client("cloudformation", region_name=args.region)
        user_pool_id = get_user_pool_id(cf_client, args.stack_name, args.region)
    
    if not user_pool_id:
        print("❌ Could not get User Pool ID. Please provide --user-pool-id or ensure stack exists.")
        sys.exit(1)
    
    print(f"✅ Using User Pool ID: {user_pool_id}")
    
    # Get all clubs
    print("\n📦 Fetching clubs from DynamoDB...")
    clubs = get_all_clubs(dynamodb)
    print(f"✅ Found {len(clubs)} club(s)")
    
    if not clubs:
        print("⚠️  No clubs found. Nothing to migrate.")
        sys.exit(0)
    
    # Migrate each club
    success_count = 0
    error_count = 0
    
    for club in clubs:
        if migrate_club_group(cognito_client, user_pool_id, club, dry_run=args.dry_run):
            success_count += 1
        else:
            error_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Migration Summary")
    print("=" * 60)
    print(f"✅ Successfully migrated: {success_count}")
    print(f"❌ Failed: {error_count}")
    print(f"📦 Total clubs: {len(clubs)}")
    
    if args.dry_run:
        print("\n🔍 This was a dry run. Run without --dry-run to apply changes.")
    
    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

