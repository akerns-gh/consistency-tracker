"""
DynamoDB helper utilities for Lambda functions.
"""

import os
import boto3
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError

# DynamoDB table names (must match database_stack.py)
PLAYER_TABLE = os.environ.get("PLAYER_TABLE", "ConsistencyTracker-Players")
ACTIVITY_TABLE = os.environ.get("ACTIVITY_TABLE", "ConsistencyTracker-Activities")
TRACKING_TABLE = os.environ.get("TRACKING_TABLE", "ConsistencyTracker-Tracking")
REFLECTION_TABLE = os.environ.get("REFLECTION_TABLE", "ConsistencyTracker-Reflections")
CONTENT_PAGES_TABLE = os.environ.get("CONTENT_PAGES_TABLE", "ConsistencyTracker-ContentPages")
TEAM_TABLE = os.environ.get("TEAM_TABLE", "ConsistencyTracker-Teams")
CLUB_TABLE = os.environ.get("CLUB_TABLE", "ConsistencyTracker-Clubs")

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")


def get_table(table_name: str):
    """Get a DynamoDB table resource."""
    return dynamodb.Table(table_name)


def get_player_by_id(player_id: str) -> Optional[Dict[str, Any]]:
    """Get a player by playerId."""
    try:
        table = get_table(PLAYER_TABLE)
        response = table.get_item(Key={"playerId": player_id})
        return response.get("Item")
    except ClientError as e:
        print(f"Error getting player {player_id}: {e}")
        return None


def get_player_by_unique_link(unique_link: str) -> Optional[Dict[str, Any]]:
    """Get a player by uniqueLink (requires scan, but uniqueLink should be indexed in production)."""
    try:
        table = get_table(PLAYER_TABLE)
        response = table.scan(
            FilterExpression="uniqueLink = :link",
            ExpressionAttributeValues={":link": unique_link},
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError as e:
        print(f"Error getting player by unique link {unique_link}: {e}")
        return None


def get_activities_by_team(team_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """Get all activities for a team, optionally filtered to active only."""
    try:
        table = get_table(ACTIVITY_TABLE)
        response = table.query(
            IndexName="teamId-index",
            KeyConditionExpression="teamId = :teamId",
            ExpressionAttributeValues={":teamId": team_id},
        )
        activities = response.get("Items", [])
        
        if active_only:
            activities = [a for a in activities if a.get("isActive", True)]
        
        # Sort by displayOrder
        activities.sort(key=lambda x: x.get("displayOrder", 999))
        return activities
    except ClientError as e:
        print(f"Error getting activities for team {team_id}: {e}")
        return []


def get_tracking_by_player_week(player_id: str, week_id: str) -> List[Dict[str, Any]]:
    """Get all tracking records for a player in a specific week."""
    try:
        table = get_table(TRACKING_TABLE)
        response = table.query(
            IndexName="playerId-index",
            KeyConditionExpression="playerId = :playerId",
            FilterExpression="weekId = :weekId",
            ExpressionAttributeValues={
                ":playerId": player_id,
                ":weekId": week_id,
            },
        )
        return response.get("Items", [])
    except ClientError as e:
        print(f"Error getting tracking for player {player_id}, week {week_id}: {e}")
        return []


def get_tracking_by_week(week_id: str) -> List[Dict[str, Any]]:
    """Get all tracking records for a specific week (for leaderboard)."""
    try:
        table = get_table(TRACKING_TABLE)
        response = table.query(
            IndexName="weekId-index",
            KeyConditionExpression="weekId = :weekId",
            ExpressionAttributeValues={":weekId": week_id},
        )
        return response.get("Items", [])
    except ClientError as e:
        print(f"Error getting tracking for week {week_id}: {e}")
        return []


def get_reflection_by_player_week(player_id: str, week_id: str) -> Optional[Dict[str, Any]]:
    """Get a reflection for a player in a specific week."""
    try:
        table = get_table(REFLECTION_TABLE)
        reflection_id = f"{player_id}#{week_id}"
        response = table.get_item(Key={"reflectionId": reflection_id})
        return response.get("Item")
    except ClientError as e:
        print(f"Error getting reflection for player {player_id}, week {week_id}: {e}")
        return None


def get_content_pages_by_team(team_id: str, published_only: bool = True) -> List[Dict[str, Any]]:
    """Get all content pages for a team, optionally filtered to published only."""
    try:
        table = get_table(CONTENT_PAGES_TABLE)
        response = table.query(
            IndexName="teamId-index",
            KeyConditionExpression="teamId = :teamId",
            ExpressionAttributeValues={":teamId": team_id},
        )
        pages = response.get("Items", [])
        
        if published_only:
            pages = [p for p in pages if p.get("isPublished", False)]
        
        # Sort by displayOrder
        pages.sort(key=lambda x: x.get("displayOrder", 999))
        return pages
    except ClientError as e:
        print(f"Error getting content pages for team {team_id}: {e}")
        return []


def get_content_page_by_slug(team_id: str, slug: str) -> Optional[Dict[str, Any]]:
    """Get a content page by slug for a team."""
    try:
        pages = get_content_pages_by_team(team_id, published_only=False)
        for page in pages:
            if page.get("slug") == slug:
                return page
        return None
    except Exception as e:
        print(f"Error getting content page by slug {slug}: {e}")
        return None


def get_club_by_id(club_id: str) -> Optional[Dict[str, Any]]:
    """Get a club by clubId."""
    try:
        table = get_table(CLUB_TABLE)
        response = table.get_item(Key={"clubId": club_id})
        return response.get("Item")
    except ClientError as e:
        print(f"Error getting club {club_id}: {e}")
        return None


def get_team_by_id(team_id: str) -> Optional[Dict[str, Any]]:
    """Get a team by teamId."""
    try:
        table = get_table(TEAM_TABLE)
        response = table.get_item(Key={"teamId": team_id})
        return response.get("Item")
    except ClientError as e:
        print(f"Error getting team {team_id}: {e}")
        return None


def get_teams_by_club(club_id: str) -> List[Dict[str, Any]]:
    """Get all teams for a club."""
    try:
        table = get_table(TEAM_TABLE)
        response = table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id},
        )
        return response.get("Items", [])
    except ClientError as e:
        print(f"Error getting teams for club {club_id}: {e}")
        return []


def get_players_by_club(club_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """Get all players for a club."""
    try:
        table = get_table(PLAYER_TABLE)
        response = table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id},
        )
        players = response.get("Items", [])
        if active_only:
            players = [p for p in players if p.get("isActive", True)]
        return players
    except ClientError as e:
        print(f"Error getting players for club {club_id}: {e}")
        return []


def get_activities_by_club(club_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """Get all club-wide activities (where teamId is null or empty)."""
    try:
        table = get_table(ACTIVITY_TABLE)
        response = table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id},
        )
        activities = response.get("Items", [])
        
        # Filter to club-wide only (teamId is null or empty)
        activities = [a for a in activities if not a.get("teamId")]
        
        if active_only:
            activities = [a for a in activities if a.get("isActive", True)]
        
        # Sort by displayOrder
        activities.sort(key=lambda x: x.get("displayOrder", 999))
        return activities
    except ClientError as e:
        print(f"Error getting activities for club {club_id}: {e}")
        return []


def get_content_pages_by_club(club_id: str, published_only: bool = True) -> List[Dict[str, Any]]:
    """Get all club-wide content pages (where teamId is null or empty)."""
    try:
        table = get_table(CONTENT_PAGES_TABLE)
        response = table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id},
        )
        pages = response.get("Items", [])
        
        # Filter to club-wide only (teamId is null or empty)
        pages = [p for p in pages if not p.get("teamId")]
        
        if published_only:
            pages = [p for p in pages if p.get("isPublished", False)]
        
        # Sort by displayOrder
        pages.sort(key=lambda x: x.get("displayOrder", 999))
        return pages
    except ClientError as e:
        print(f"Error getting content pages for club {club_id}: {e}")
        return []


def create_tracking_record(
    player_id: str,
    week_id: str,
    date: str,
    completed_activities: List[str],
    daily_score: int,
    team_id: str,
    club_id: str,
) -> Dict[str, Any]:
    """Create or update a tracking record."""
    try:
        table = get_table(TRACKING_TABLE)
        tracking_id = f"{player_id}#{week_id}#{date}"
        
        from datetime import datetime
        now = datetime.utcnow().isoformat() + "Z"
        
        item = {
            "trackingId": tracking_id,
            "playerId": player_id,
            "weekId": week_id,
            "date": date,
            "completedActivities": completed_activities,
            "dailyScore": daily_score,
            "teamId": team_id,
            "clubId": club_id,
            "updatedAt": now,
        }
        
        # Check if record exists
        existing = table.get_item(Key={"trackingId": tracking_id})
        if "Item" in existing:
            item["createdAt"] = existing["Item"].get("createdAt", now)
        else:
            item["createdAt"] = now
        
        table.put_item(Item=item)
        return item
    except ClientError as e:
        print(f"Error creating tracking record: {e}")
        raise


def create_or_update_reflection(
    player_id: str,
    week_id: str,
    went_well: str,
    do_better: str,
    plan_for_week: str,
    team_id: str,
    club_id: str,
) -> Dict[str, Any]:
    """Create or update a reflection."""
    try:
        table = get_table(REFLECTION_TABLE)
        reflection_id = f"{player_id}#{week_id}"
        
        from datetime import datetime
        now = datetime.utcnow().isoformat() + "Z"
        
        # Check if reflection exists
        existing = table.get_item(Key={"reflectionId": reflection_id})
        created_at = existing.get("Item", {}).get("createdAt", now) if "Item" in existing else now
        
        item = {
            "reflectionId": reflection_id,
            "playerId": player_id,
            "weekId": week_id,
            "wentWell": went_well,
            "doBetter": do_better,
            "planForWeek": plan_for_week,
            "teamId": team_id,
            "clubId": club_id,
            "createdAt": created_at,
            "updatedAt": now,
        }
        
        table.put_item(Item=item)
        return item
    except ClientError as e:
        print(f"Error creating/updating reflection: {e}")
        raise

