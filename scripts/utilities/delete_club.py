#!/usr/bin/env python3
"""
Delete a club and all related data (teams, players, coaches, club admins, Cognito groups).

WARNING: This is a destructive operation that cannot be undone.
"""

import boto3
import sys
from botocore.exceptions import ClientError
from typing import List, Dict

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

def delete_club_and_related_data(club_id: str, club_name: str = None):
    """Delete club and all related data."""
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    cognito = boto3.client('cognito-idp', region_name=AWS_REGION)
    user_pool_id = get_user_pool_id()
    
    print(f"🗑️  Deleting club: {club_name or club_id}")
    print("=" * 70)
    
    deleted_items = {
        'club': 0,
        'teams': 0,
        'players': 0,
        'coaches': 0,
        'club_admins': 0,
        'cognito_groups': 0,
    }
    
    # 1. Delete all players for this club
    print("\n📋 Deleting players...")
    player_table = dynamodb.Table("ConsistencyTracker-Players")
    try:
        response = player_table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id}
        )
        players = response.get('Items', [])
        
        for player in players:
            player_id = player.get('playerId')
            email = player.get('email', '')
            try:
                player_table.delete_item(Key={"playerId": player_id})
                print(f"  ✅ Deleted player: {player_id} ({email})")
                deleted_items['players'] += 1
                
                # Also delete Cognito user if exists
                if email:
                    try:
                        cognito.admin_delete_user(
                            UserPoolId=user_pool_id,
                            Username=email
                        )
                        print(f"     Deleted Cognito user: {email}")
                    except ClientError as e:
                        if e.response['Error']['Code'] != 'UserNotFoundException':
                            print(f"     ⚠️  Could not delete Cognito user {email}: {e}")
            except Exception as e:
                print(f"  ❌ Error deleting player {player_id}: {e}")
    except Exception as e:
        print(f"  ❌ Error querying players: {e}")
    
    # 2. Delete all coaches for this club
    print("\n📋 Deleting coaches...")
    coach_table = dynamodb.Table("ConsistencyTracker-Coaches")
    try:
        response = coach_table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id}
        )
        coaches = response.get('Items', [])
        
        for coach in coaches:
            coach_id = coach.get('coachId')
            email = coach.get('email', '')
            team_id = coach.get('teamId', '')
            
            try:
                coach_table.delete_item(Key={"coachId": coach_id})
                print(f"  ✅ Deleted coach: {coach_id} ({email})")
                deleted_items['coaches'] += 1
                
                # Remove from Cognito group
                if email and team_id:
                    group_name = f"coach-{club_id}-{team_id}"
                    try:
                        cognito.admin_remove_user_from_group(
                            UserPoolId=user_pool_id,
                            Username=email,
                            GroupName=group_name
                        )
                        print(f"     Removed from group: {group_name}")
                    except ClientError as e:
                        if e.response['Error']['Code'] != 'ResourceNotFoundException':
                            print(f"     ⚠️  Could not remove from group: {e}")
                
                # Delete Cognito user
                if email:
                    try:
                        cognito.admin_delete_user(
                            UserPoolId=user_pool_id,
                            Username=email
                        )
                        print(f"     Deleted Cognito user: {email}")
                    except ClientError as e:
                        if e.response['Error']['Code'] != 'UserNotFoundException':
                            print(f"     ⚠️  Could not delete Cognito user {email}: {e}")
            except Exception as e:
                print(f"  ❌ Error deleting coach {coach_id}: {e}")
    except Exception as e:
        print(f"  ❌ Error querying coaches: {e}")
    
    # 3. Delete all teams for this club
    print("\n📋 Deleting teams...")
    team_table = dynamodb.Table("ConsistencyTracker-Teams")
    try:
        response = team_table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id}
        )
        teams = response.get('Items', [])
        
        for team in teams:
            team_id = team.get('teamId')
            try:
                team_table.delete_item(Key={"teamId": team_id})
                print(f"  ✅ Deleted team: {team_id}")
                deleted_items['teams'] += 1
            except Exception as e:
                print(f"  ❌ Error deleting team {team_id}: {e}")
    except Exception as e:
        print(f"  ❌ Error querying teams: {e}")
    
    # 4. Delete all club admins for this club
    print("\n📋 Deleting club admins...")
    admin_table = dynamodb.Table("ConsistencyTracker-ClubAdmins")
    try:
        response = admin_table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id}
        )
        admins = response.get('Items', [])
        
        for admin in admins:
            admin_id = admin.get('adminId')
            email = admin.get('email', '')
            
            try:
                admin_table.delete_item(Key={"adminId": admin_id})
                print(f"  ✅ Deleted club admin: {admin_id} ({email})")
                deleted_items['club_admins'] += 1
                
                # Remove from Cognito group
                if club_name:
                    # Sanitize club name for group name (replace spaces and special chars with underscores, lowercase)
                    sanitized_name = club_name.lower().replace(' ', '_').replace('-', '_')
                    sanitized_name = ''.join(c if c.isalnum() or c == '_' else '' for c in sanitized_name)
                    group_name = f"club-{sanitized_name}-admins"
                    try:
                        cognito.admin_remove_user_from_group(
                            UserPoolId=user_pool_id,
                            Username=email,
                            GroupName=group_name
                        )
                        print(f"     Removed from group: {group_name}")
                    except ClientError as e:
                        if e.response['Error']['Code'] != 'ResourceNotFoundException':
                            print(f"     ⚠️  Could not remove from group: {e}")
                
                # Delete Cognito user
                if email:
                    try:
                        cognito.admin_delete_user(
                            UserPoolId=user_pool_id,
                            Username=email
                        )
                        print(f"     Deleted Cognito user: {email}")
                    except ClientError as e:
                        if e.response['Error']['Code'] != 'UserNotFoundException':
                            print(f"     ⚠️  Could not delete Cognito user {email}: {e}")
            except Exception as e:
                print(f"  ❌ Error deleting club admin {admin_id}: {e}")
    except Exception as e:
        print(f"  ❌ Error querying club admins: {e}")
    
    # 5. Delete Cognito groups for this club
    print("\n📋 Deleting Cognito groups...")
    try:
        # List all groups
        groups = []
        next_token = None
        while True:
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
        
        # Find and delete groups related to this club
        for group in groups:
            group_name = group['GroupName']
            sanitized_name = None
            if club_name:
                sanitized_name = club_name.lower().replace(' ', '_').replace('-', '_')
                sanitized_name = ''.join(c if c.isalnum() or c == '_' else '' for c in sanitized_name)
            
            if club_id in group_name or (sanitized_name and sanitized_name in group_name):
                try:
                    cognito.delete_group(
                        UserPoolId=user_pool_id,
                        GroupName=group_name
                    )
                    print(f"  ✅ Deleted Cognito group: {group_name}")
                    deleted_items['cognito_groups'] += 1
                except ClientError as e:
                    print(f"  ⚠️  Could not delete group {group_name}: {e}")
    except Exception as e:
        print(f"  ❌ Error deleting Cognito groups: {e}")
    
    # 6. Delete the club itself
    print("\n📋 Deleting club...")
    club_table = dynamodb.Table("ConsistencyTracker-Clubs")
    try:
        club_table.delete_item(Key={"clubId": club_id})
        print(f"  ✅ Deleted club: {club_id}")
        deleted_items['club'] = 1
    except Exception as e:
        print(f"  ❌ Error deleting club: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 DELETION SUMMARY")
    print("=" * 70)
    print(f"Club deleted: {deleted_items['club']}")
    print(f"Teams deleted: {deleted_items['teams']}")
    print(f"Players deleted: {deleted_items['players']}")
    print(f"Coaches deleted: {deleted_items['coaches']}")
    print(f"Club admins deleted: {deleted_items['club_admins']}")
    print(f"Cognito groups deleted: {deleted_items['cognito_groups']}")
    print("\n✅ Club deletion completed!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Delete a club and all related data')
    parser.add_argument('club_id', help='Club ID to delete')
    parser.add_argument('--club-name', help='Club name (for group name matching)')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation')
    args = parser.parse_args()
    
    if not args.yes:
        print("⚠️  WARNING: This will permanently delete the club and ALL related data!")
        print("   This includes:")
        print("   - The club record")
        print("   - All teams")
        print("   - All players")
        print("   - All coaches")
        print("   - All club admins")
        print("   - All Cognito groups")
        print("   - All Cognito users for players, coaches, and admins")
        print("\n   This action CANNOT be undone!")
        response = input(f"\nAre you sure you want to delete club {args.club_id}? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Aborted.")
            sys.exit(0)
    
    try:
        delete_club_and_related_data(args.club_id, args.club_name)
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

