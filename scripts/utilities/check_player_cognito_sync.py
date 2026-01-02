#!/usr/bin/env python3
"""
Check for discrepancies between players in DynamoDB and Cognito users.

This script identifies:
1. Players in DynamoDB without corresponding Cognito users
2. Cognito users without corresponding player records
3. Email mismatches between player records and Cognito users
"""

import boto3
import sys
from botocore.exceptions import ClientError
from typing import Dict, List, Set, Tuple

# Configuration
AWS_REGION = "us-east-1"
USER_POOL_ID = None  # Will be fetched from CloudFormation
PLAYER_TABLE = "ConsistencyTracker-Players"

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

def get_all_players() -> List[Dict]:
    """Get all players from DynamoDB."""
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(PLAYER_TABLE)
    
    players = []
    last_evaluated_key = None
    
    while True:
        if last_evaluated_key:
            response = table.scan(ExclusiveStartKey=last_evaluated_key)
        else:
            response = table.scan()
        
        players.extend(response.get('Items', []))
        
        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break
    
    return players

def get_all_cognito_users() -> List[Dict]:
    """Get all users from Cognito User Pool."""
    cognito = boto3.client('cognito-idp', region_name=AWS_REGION)
    user_pool_id = get_user_pool_id()
    
    users = []
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
            
            users.extend(response.get('Users', []))
            
            pagination_token = response.get('PaginationToken')
            if not pagination_token:
                break
        except ClientError as e:
            print(f"❌ Error listing Cognito users: {e}")
            return []
    
    return users

def get_user_email(user: Dict) -> str:
    """Extract email from Cognito user attributes."""
    for attr in user.get('Attributes', []):
        if attr['Name'] == 'email':
            return attr['Value']
    # Fallback to username if email not found
    return user.get('Username', '')

def check_discrepancies():
    """Check for discrepancies between players and Cognito users."""
    print("🔍 Checking for discrepancies between players and Cognito users...")
    print("=" * 70)
    
    # Get all players
    print("\n📊 Fetching players from DynamoDB...")
    players = get_all_players()
    print(f"✅ Found {len(players)} players in DynamoDB")
    
    # Get all Cognito users
    print("\n👥 Fetching users from Cognito...")
    cognito_users = get_all_cognito_users()
    print(f"✅ Found {len(cognito_users)} users in Cognito")
    
    # Build sets for comparison
    player_emails = set()
    player_email_map = {}  # email -> player record
    
    for player in players:
        email = player.get('email', '').strip().lower()
        if email:
            player_emails.add(email)
            player_email_map[email] = player
    
    cognito_emails = set()
    cognito_email_map = {}  # email -> cognito user
    
    for user in cognito_users:
        email = get_user_email(user).strip().lower()
        username = user.get('Username', '').strip().lower()
        
        if email:
            cognito_emails.add(email)
            cognito_email_map[email] = user
        elif username and '@' in username:
            # Username might be the email
            cognito_emails.add(username)
            cognito_email_map[username] = user
    
    # Find discrepancies
    print("\n" + "=" * 70)
    print("📋 DISCREPANCY REPORT")
    print("=" * 70)
    
    # 1. Players without Cognito users
    players_without_cognito = player_emails - cognito_emails
    if players_without_cognito:
        print(f"\n⚠️  PLAYERS WITHOUT COGNITO USERS ({len(players_without_cognito)}):")
        print("-" * 70)
        for email in sorted(players_without_cognito):
            player = player_email_map[email]
            player_id = player.get('playerId', 'N/A')
            name = player.get('name', f"{player.get('firstName', '')} {player.get('lastName', '')}".strip() or 'N/A')
            is_active = player.get('isActive', True)
            status = "Active" if is_active else "Inactive"
            print(f"  • {email}")
            print(f"    Player ID: {player_id}")
            print(f"    Name: {name}")
            print(f"    Status: {status}")
            print()
    else:
        print("\n✅ All players have corresponding Cognito users")
    
    # 2. Cognito users without player records
    cognito_without_players = cognito_emails - player_emails
    if cognito_without_players:
        print(f"\n⚠️  COGNITO USERS WITHOUT PLAYER RECORDS ({len(cognito_without_players)}):")
        print("-" * 70)
        for email in sorted(cognito_without_players):
            user = cognito_email_map[email]
            username = user.get('Username', 'N/A')
            status = user.get('UserStatus', 'N/A')
            enabled = user.get('Enabled', False)
            enabled_str = "Enabled" if enabled else "Disabled"
            print(f"  • {email}")
            print(f"    Username: {username}")
            print(f"    Status: {status}")
            print(f"    Enabled: {enabled_str}")
            print()
    else:
        print("\n✅ All Cognito users have corresponding player records")
    
    # 3. Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total players in DynamoDB: {len(players)}")
    print(f"Total users in Cognito: {len(cognito_users)}")
    print(f"Players without Cognito users: {len(players_without_cognito)}")
    print(f"Cognito users without player records: {len(cognito_without_players)}")
    print(f"Players with matching Cognito users: {len(player_emails & cognito_emails)}")
    
    if players_without_cognito or cognito_without_players:
        print("\n⚠️  DISCREPANCIES FOUND!")
        print("\nRecommendations:")
        if players_without_cognito:
            print("  • For players without Cognito users:")
            print("    - Use the 'Invite' button in the admin dashboard to create Cognito users")
            print("    - Or manually create Cognito users for these players")
        if cognito_without_players:
            print("  • For Cognito users without player records:")
            print("    - These may be admin/coach users (not players)")
            print("    - Or orphaned accounts that should be cleaned up")
        return False
    else:
        print("\n✅ No discrepancies found! All players and Cognito users are in sync.")
        return True

if __name__ == "__main__":
    try:
        success = check_discrepancies()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

