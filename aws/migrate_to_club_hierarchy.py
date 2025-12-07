#!/usr/bin/env python3
"""
Migration Script: Add Club Hierarchy to Existing Data

This script migrates existing data to support the club > team > player hierarchy.
It creates a default club and updates all existing records to include clubId.

IMPORTANT: Run this script AFTER deploying the updated database stack with Club table.
"""

import boto3
import sys
from botocore.exceptions import ClientError
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

AWS_REGION = "us-east-1"
DEFAULT_CLUB_ID = "default-club"
DEFAULT_CLUB_NAME = "Default Club"

# Table names
PLAYER_TABLE = "ConsistencyTracker-Players"
ACTIVITY_TABLE = "ConsistencyTracker-Activities"
TRACKING_TABLE = "ConsistencyTracker-Tracking"
REFLECTION_TABLE = "ConsistencyTracker-Reflections"
CONTENT_PAGES_TABLE = "ConsistencyTracker-ContentPages"
TEAM_TABLE = "ConsistencyTracker-Teams"
CLUB_TABLE = "ConsistencyTracker-Clubs"

# ============================================================================
# Migration Functions
# ============================================================================

def create_default_club(dynamodb):
    """Create default club if it doesn't exist."""
    try:
        table = dynamodb.Table(CLUB_TABLE)
        
        # Check if club already exists
        response = table.get_item(Key={"clubId": DEFAULT_CLUB_ID})
        if "Item" in response:
            print(f"✅ Default club '{DEFAULT_CLUB_ID}' already exists")
            return True
        
        # Create default club
        now = datetime.utcnow().isoformat() + "Z"
        club = {
            "clubId": DEFAULT_CLUB_ID,
            "clubName": DEFAULT_CLUB_NAME,
            "createdAt": now,
            "settings": {},
        }
        
        table.put_item(Item=club)
        print(f"✅ Created default club: {DEFAULT_CLUB_ID}")
        return True
        
    except ClientError as e:
        print(f"❌ Error creating default club: {e}")
        return False


def update_teams_with_club_id(dynamodb):
    """Update all teams to have clubId = default-club."""
    try:
        table = dynamodb.Table(TEAM_TABLE)
        
        # Scan all teams
        response = table.scan()
        teams = response.get("Items", [])
        
        updated_count = 0
        for team in teams:
            team_id = team.get("teamId")
            if not team.get("clubId"):
                # Update team with clubId
                table.update_item(
                    Key={"teamId": team_id},
                    UpdateExpression="SET clubId = :clubId, updatedAt = :updatedAt",
                    ExpressionAttributeValues={
                        ":clubId": DEFAULT_CLUB_ID,
                        ":updatedAt": datetime.utcnow().isoformat() + "Z",
                    },
                )
                updated_count += 1
                print(f"  ✅ Updated team: {team_id}")
        
        print(f"✅ Updated {updated_count} teams with clubId")
        return True
        
    except ClientError as e:
        print(f"❌ Error updating teams: {e}")
        return False


def update_players_with_club_id(dynamodb):
    """Update all players to have clubId derived from their team."""
    try:
        player_table = dynamodb.Table(PLAYER_TABLE)
        team_table = dynamodb.Table(TEAM_TABLE)
        
        # Scan all players
        response = player_table.scan()
        players = response.get("Items", [])
        
        updated_count = 0
        for player in players:
            player_id = player.get("playerId")
            team_id = player.get("teamId")
            
            if not player.get("clubId") and team_id:
                # Get team to find clubId
                team_response = team_table.get_item(Key={"teamId": team_id})
                if "Item" in team_response:
                    team = team_response["Item"]
                    club_id = team.get("clubId", DEFAULT_CLUB_ID)
                    
                    # Update player with clubId
                    player_table.update_item(
                        Key={"playerId": player_id},
                        UpdateExpression="SET clubId = :clubId, updatedAt = :updatedAt",
                        ExpressionAttributeValues={
                            ":clubId": club_id,
                            ":updatedAt": datetime.utcnow().isoformat() + "Z",
                        },
                    )
                    updated_count += 1
                    print(f"  ✅ Updated player: {player_id}")
                else:
                    # Team not found, use default club
                    player_table.update_item(
                        Key={"playerId": player_id},
                        UpdateExpression="SET clubId = :clubId, updatedAt = :updatedAt",
                        ExpressionAttributeValues={
                            ":clubId": DEFAULT_CLUB_ID,
                            ":updatedAt": datetime.utcnow().isoformat() + "Z",
                        },
                    )
                    updated_count += 1
                    print(f"  ⚠️  Updated player {player_id} with default club (team not found)")
        
        print(f"✅ Updated {updated_count} players with clubId")
        return True
        
    except ClientError as e:
        print(f"❌ Error updating players: {e}")
        return False


def update_activities_with_club_id(dynamodb):
    """Update all activities to have clubId and scope."""
    try:
        table = dynamodb.Table(ACTIVITY_TABLE)
        
        # Scan all activities
        response = table.scan()
        activities = response.get("Items", [])
        
        updated_count = 0
        for activity in activities:
            activity_id = activity.get("activityId")
            team_id = activity.get("teamId")
            
            if not activity.get("clubId"):
                # Get clubId from team
                if team_id:
                    team_table = dynamodb.Table(TEAM_TABLE)
                    team_response = team_table.get_item(Key={"teamId": team_id})
                    if "Item" in team_response:
                        club_id = team_response["Item"].get("clubId", DEFAULT_CLUB_ID)
                    else:
                        club_id = DEFAULT_CLUB_ID
                else:
                    club_id = DEFAULT_CLUB_ID
                
                # Update activity with clubId and scope
                update_expr = "SET clubId = :clubId, scope = :scope, updatedAt = :updatedAt"
                expr_values = {
                    ":clubId": club_id,
                    ":scope": "team" if team_id else "club",
                    ":updatedAt": datetime.utcnow().isoformat() + "Z",
                }
                
                table.update_item(
                    Key={"activityId": activity_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeValues=expr_values,
                )
                updated_count += 1
                print(f"  ✅ Updated activity: {activity_id}")
        
        print(f"✅ Updated {updated_count} activities with clubId and scope")
        return True
        
    except ClientError as e:
        print(f"❌ Error updating activities: {e}")
        return False


def update_content_with_club_id(dynamodb):
    """Update all content pages to have clubId and scope."""
    try:
        table = dynamodb.Table(CONTENT_PAGES_TABLE)
        
        # Scan all content pages
        response = table.scan()
        pages = response.get("Items", [])
        
        updated_count = 0
        for page in pages:
            page_id = page.get("pageId")
            team_id = page.get("teamId")
            
            if not page.get("clubId"):
                # Get clubId from team
                if team_id:
                    team_table = dynamodb.Table(TEAM_TABLE)
                    team_response = team_table.get_item(Key={"teamId": team_id})
                    if "Item" in team_response:
                        club_id = team_response["Item"].get("clubId", DEFAULT_CLUB_ID)
                    else:
                        club_id = DEFAULT_CLUB_ID
                else:
                    club_id = DEFAULT_CLUB_ID
                
                # Update content page with clubId and scope
                update_expr = "SET clubId = :clubId, scope = :scope, updatedAt = :updatedAt"
                expr_values = {
                    ":clubId": club_id,
                    ":scope": "team" if team_id else "club",
                    ":updatedAt": datetime.utcnow().isoformat() + "Z",
                }
                
                table.update_item(
                    Key={"pageId": page_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeValues=expr_values,
                )
                updated_count += 1
                print(f"  ✅ Updated content page: {page_id}")
        
        print(f"✅ Updated {updated_count} content pages with clubId and scope")
        return True
        
    except ClientError as e:
        print(f"❌ Error updating content pages: {e}")
        return False


def update_tracking_with_club_team_ids(dynamodb):
    """Update all tracking records to include clubId and teamId from player."""
    try:
        tracking_table = dynamodb.Table(TRACKING_TABLE)
        player_table = dynamodb.Table(PLAYER_TABLE)
        
        # Scan all tracking records
        response = tracking_table.scan()
        records = response.get("Items", [])
        
        updated_count = 0
        for record in records:
            tracking_id = record.get("trackingId")
            player_id = record.get("playerId")
            
            if not record.get("clubId") or not record.get("teamId"):
                # Get player to find clubId and teamId
                player_response = player_table.get_item(Key={"playerId": player_id})
                if "Item" in player_response:
                    player = player_response["Item"]
                    club_id = player.get("clubId", DEFAULT_CLUB_ID)
                    team_id = player.get("teamId")
                    
                    # Update tracking record
                    update_parts = []
                    expr_values = {}
                    
                    if not record.get("clubId"):
                        update_parts.append("clubId = :clubId")
                        expr_values[":clubId"] = club_id
                    
                    if not record.get("teamId") and team_id:
                        update_parts.append("teamId = :teamId")
                        expr_values[":teamId"] = team_id
                    
                    if update_parts:
                        update_parts.append("updatedAt = :updatedAt")
                        expr_values[":updatedAt"] = datetime.utcnow().isoformat() + "Z"
                        
                        tracking_table.update_item(
                            Key={"trackingId": tracking_id},
                            UpdateExpression="SET " + ", ".join(update_parts),
                            ExpressionAttributeValues=expr_values,
                        )
                        updated_count += 1
                        print(f"  ✅ Updated tracking record: {tracking_id}")
        
        print(f"✅ Updated {updated_count} tracking records with clubId and teamId")
        return True
        
    except ClientError as e:
        print(f"❌ Error updating tracking records: {e}")
        return False


def update_reflections_with_club_team_ids(dynamodb):
    """Update all reflection records to include clubId and teamId from player."""
    try:
        reflection_table = dynamodb.Table(REFLECTION_TABLE)
        player_table = dynamodb.Table(PLAYER_TABLE)
        
        # Scan all reflection records
        response = reflection_table.scan()
        records = response.get("Items", [])
        
        updated_count = 0
        for record in records:
            reflection_id = record.get("reflectionId")
            player_id = record.get("playerId")
            
            if not record.get("clubId") or not record.get("teamId"):
                # Get player to find clubId and teamId
                player_response = player_table.get_item(Key={"playerId": player_id})
                if "Item" in player_response:
                    player = player_response["Item"]
                    club_id = player.get("clubId", DEFAULT_CLUB_ID)
                    team_id = player.get("teamId")
                    
                    # Update reflection record
                    update_parts = []
                    expr_values = {}
                    
                    if not record.get("clubId"):
                        update_parts.append("clubId = :clubId")
                        expr_values[":clubId"] = club_id
                    
                    if not record.get("teamId") and team_id:
                        update_parts.append("teamId = :teamId")
                        expr_values[":teamId"] = team_id
                    
                    if update_parts:
                        update_parts.append("updatedAt = :updatedAt")
                        expr_values[":updatedAt"] = datetime.utcnow().isoformat() + "Z"
                        
                        reflection_table.update_item(
                            Key={"reflectionId": reflection_id},
                            UpdateExpression="SET " + ", ".join(update_parts),
                            ExpressionAttributeValues=expr_values,
                        )
                        updated_count += 1
                        print(f"  ✅ Updated reflection record: {reflection_id}")
        
        print(f"✅ Updated {updated_count} reflection records with clubId and teamId")
        return True
        
    except ClientError as e:
        print(f"❌ Error updating reflection records: {e}")
        return False


def update_cognito_users_with_club_id(cognito_client, user_pool_id):
    """Update existing Cognito users to have custom:clubId attribute."""
    try:
        print("📋 Updating Cognito users with clubId attribute...")
        
        # List all users
        paginator = cognito_client.get_paginator("list_users")
        users_updated = 0
        
        for page in paginator.paginate(UserPoolId=user_pool_id):
            for user in page.get("Users", []):
                username = user.get("Username")
                
                # Check if user already has clubId
                has_club_id = any(
                    attr.get("Name") == "custom:clubId"
                    for attr in user.get("Attributes", [])
                )
                
                if not has_club_id:
                    try:
                        cognito_client.admin_update_user_attributes(
                            UserPoolId=user_pool_id,
                            Username=username,
                            UserAttributes=[
                                {"Name": "custom:clubId", "Value": DEFAULT_CLUB_ID}
                            ],
                        )
                        users_updated += 1
                        print(f"  ✅ Updated user: {username}")
                    except ClientError as e:
                        print(f"  ⚠️  Could not update user {username}: {e}")
        
        print(f"✅ Updated {users_updated} Cognito users with clubId attribute")
        return True
        
    except ClientError as e:
        print(f"❌ Error updating Cognito users: {e}")
        return False


# ============================================================================
# Main Migration Function
# ============================================================================

def main():
    """Run the migration."""
    print("🚀 Starting migration to club hierarchy...")
    print("=" * 60)
    
    # Initialize AWS clients
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    cognito_client = boto3.client("cognito-idp", region_name=AWS_REGION)
    
    # Get User Pool ID (you may need to update this)
    # For now, we'll skip Cognito update if pool ID is not available
    user_pool_id = None
    try:
        # Try to get from CloudFormation stack
        cf_client = boto3.client("cloudformation", region_name=AWS_REGION)
        response = cf_client.describe_stacks(StackName="ConsistencyTracker-Auth")
        outputs = response["Stacks"][0].get("Outputs", [])
        for output in outputs:
            if output["OutputKey"] == "UserPoolId":
                user_pool_id = output["OutputValue"]
                break
    except Exception as e:
        print(f"⚠️  Could not get User Pool ID: {e}")
        print("   Skipping Cognito user updates")
    
    success = True
    
    # Step 1: Create default club
    print("\n📦 Step 1: Creating default club...")
    if not create_default_club(dynamodb):
        success = False
    
    # Step 2: Update teams
    print("\n📦 Step 2: Updating teams with clubId...")
    if not update_teams_with_club_id(dynamodb):
        success = False
    
    # Step 3: Update players
    print("\n📦 Step 3: Updating players with clubId...")
    if not update_players_with_club_id(dynamodb):
        success = False
    
    # Step 4: Update activities
    print("\n📦 Step 4: Updating activities with clubId and scope...")
    if not update_activities_with_club_id(dynamodb):
        success = False
    
    # Step 5: Update content pages
    print("\n📦 Step 5: Updating content pages with clubId and scope...")
    if not update_content_with_club_id(dynamodb):
        success = False
    
    # Step 6: Update tracking records
    print("\n📦 Step 6: Updating tracking records with clubId and teamId...")
    if not update_tracking_with_club_team_ids(dynamodb):
        success = False
    
    # Step 7: Update reflection records
    print("\n📦 Step 7: Updating reflection records with clubId and teamId...")
    if not update_reflections_with_club_team_ids(dynamodb):
        success = False
    
    # Step 8: Update Cognito users (optional)
    if user_pool_id:
        print("\n📦 Step 8: Updating Cognito users with clubId attribute...")
        if not update_cognito_users_with_club_id(cognito_client, user_pool_id):
            print("⚠️  Cognito user update failed, but migration can continue")
    else:
        print("\n⚠️  Step 8: Skipping Cognito user updates (User Pool ID not found)")
        print("   You can manually update Cognito users with custom:clubId attribute")
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Verify data in DynamoDB tables")
        print("   2. Update Cognito users with custom:clubId if not done automatically")
        print("   3. Test the application with the new club hierarchy")
    else:
        print("❌ Migration completed with errors. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

