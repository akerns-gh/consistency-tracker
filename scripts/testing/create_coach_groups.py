#!/usr/bin/env python3
"""
Script to create Cognito groups for teams and add coaches to them.
"""

import boto3
import re

cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
COGNITO_USER_POOL_ID = 'us-east-1_1voH0LIGL'
CLUB_ID = 'd86b7201-b491-49e7-805d-f47777353336'  # Demo Club 1

def sanitize_club_name_for_group(club_name: str) -> str:
    """Sanitize club name for use in Cognito group names."""
    if not club_name:
        return ""
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', club_name)
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

def create_cognito_group(user_pool_id: str, group_name: str, description: str) -> bool:
    """Create a Cognito group if it doesn't exist."""
    try:
        cognito_client.create_group(
            GroupName=group_name,
            UserPoolId=user_pool_id,
            Description=description
        )
        print(f"✅ Created group: {group_name}")
        return True
    except Exception as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceConflictException':
            print(f"✅ Group {group_name} already exists")
            return True
        else:
            print(f"❌ Failed to create group {group_name}: {e}")
            return False

def add_user_to_group(user_pool_id: str, username: str, group_name: str) -> bool:
    """Add user to Cognito group."""
    try:
        cognito_client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name
        )
        print(f"✅ Added {username} to group {group_name}")
        return True
    except Exception as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if 'already a member' in str(e) or error_code == 'InvalidParameterException':
            print(f"✅ {username} already in group {group_name}")
            return True
        else:
            print(f"❌ Failed to add {username} to group {group_name}: {e}")
            return False

def main():
    print("🚀 Creating Cognito groups and adding coaches...")
    
    teams = [
        ('2031', 'Team 2031'),
        ('2030', 'Team 2030'),
    ]
    
    coaches = [
        ('test-coach-1@repwarrior.net', '2031'),
        ('test-coach-2@repwarrior.net', '2030'),
    ]
    
    for team_id, team_name in teams:
        group_name = f"coach-{CLUB_ID}-{team_id}"
        description = f"Coaches for team {team_name} in club Demo Club 1"
        
        # Create group
        if create_cognito_group(COGNITO_USER_POOL_ID, group_name, description):
            # Find coach for this team
            for coach_email, coach_team_id in coaches:
                if coach_team_id == team_id:
                    add_user_to_group(COGNITO_USER_POOL_ID, coach_email, group_name)
    
    print("\n✅ Done!")

if __name__ == '__main__':
    main()

