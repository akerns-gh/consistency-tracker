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
COACH_TABLE = os.environ.get("COACH_TABLE", "ConsistencyTracker-Coaches")
CLUB_ADMIN_TABLE = os.environ.get("CLUB_ADMIN_TABLE", "ConsistencyTracker-ClubAdmins")
EMAIL_VERIFICATION_TABLE = os.environ.get("EMAIL_VERIFICATION_TABLE", "ConsistencyTracker-EmailVerifications")
VERIFICATION_ATTEMPTS_TABLE = os.environ.get("VERIFICATION_ATTEMPTS_TABLE", "ConsistencyTracker-VerificationAttempts")
RESEND_TRACKING_TABLE = os.environ.get("RESEND_TRACKING_TABLE", "ConsistencyTracker-ResendTracking")

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


def get_player_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a player by email (requires scan, email should be indexed in production)."""
    try:
        table = get_table(PLAYER_TABLE)
        response = table.scan(
            FilterExpression="email = :email",
            ExpressionAttributeValues={":email": email},
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError as e:
        print(f"Error getting player by email {email}: {e}")
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


def get_teams_by_club(club_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
    """Get all teams for a club, optionally filtered to active only."""
    try:
        table = get_table(TEAM_TABLE)
        response = table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id},
        )
        teams = response.get("Items", [])
        
        if active_only:
            teams = [t for t in teams if t.get("isActive", True)]
        
        return teams
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


def get_all_content_pages_by_club(club_id: str, published_only: bool = True) -> List[Dict[str, Any]]:
    """Get ALL content pages for a club (both club-wide and team-specific).
    
    This function returns all content pages for a club regardless of scope,
    unlike get_content_pages_by_club() which only returns club-wide content.
    Use this for slug validation and other operations that need to check
    against all content in a club.
    
    Args:
        club_id: The club ID
        published_only: If True, only return published content
    
    Returns:
        List of content page dictionaries, sorted by displayOrder
    """
    try:
        table = get_table(CONTENT_PAGES_TABLE)
        response = table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id},
        )
        pages = response.get("Items", [])
        
        # No filtering by teamId - includes both club-wide and team-specific
        
        if published_only:
            pages = [p for p in pages if p.get("isPublished", False)]
        
        # Sort by displayOrder
        pages.sort(key=lambda x: x.get("displayOrder", 999))
        return pages
    except ClientError as e:
        print(f"Error getting all content pages for club {club_id}: {e}")
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


def get_coach_by_id(coach_id: str) -> Optional[Dict[str, Any]]:
    """Get a coach by coachId."""
    try:
        table = get_table(COACH_TABLE)
        response = table.get_item(Key={"coachId": coach_id})
        return response.get("Item")
    except ClientError as e:
        print(f"Error getting coach {coach_id}: {e}")
        return None


def get_coach_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a coach by email using email-index GSI."""
    try:
        table = get_table(COACH_TABLE)
        response = table.query(
            IndexName="email-index",
            KeyConditionExpression="email = :email",
            ExpressionAttributeValues={":email": email},
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError as e:
        print(f"Error getting coach by email {email}: {e}")
        return None


def get_coaches_by_team(team_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """Get all coaches for a team."""
    try:
        table = get_table(COACH_TABLE)
        response = table.query(
            IndexName="teamId-index",
            KeyConditionExpression="teamId = :teamId",
            ExpressionAttributeValues={":teamId": team_id},
        )
        coaches = response.get("Items", [])
        
        if active_only:
            coaches = [c for c in coaches if c.get("isActive", True)]
        
        return coaches
    except ClientError as e:
        print(f"Error getting coaches for team {team_id}: {e}")
        return []


def get_coaches_by_club(club_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """Get all coaches for a club."""
    try:
        table = get_table(COACH_TABLE)
        response = table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id},
        )
        coaches = response.get("Items", [])
        
        if active_only:
            coaches = [c for c in coaches if c.get("isActive", True)]
        
        return coaches
    except ClientError as e:
        print(f"Error getting coaches for club {club_id}: {e}")
        return []


def get_club_admin_by_id(admin_id: str) -> Optional[Dict[str, Any]]:
    """Get a club admin by adminId."""
    try:
        table = get_table(CLUB_ADMIN_TABLE)
        response = table.get_item(Key={"adminId": admin_id})
        return response.get("Item")
    except ClientError as e:
        print(f"Error getting club admin {admin_id}: {e}")
        return None


def get_club_admin_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a club admin by email using email-index GSI."""
    try:
        table = get_table(CLUB_ADMIN_TABLE)
        response = table.query(
            IndexName="email-index",
            KeyConditionExpression="email = :email",
            ExpressionAttributeValues={":email": email},
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError as e:
        print(f"Error getting club admin by email {email}: {e}")
        return None


def get_club_admins_by_club(club_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """Get all club admins for a club."""
    try:
        table = get_table(CLUB_ADMIN_TABLE)
        response = table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id},
        )
        admins = response.get("Items", [])
        
        if active_only:
            admins = [a for a in admins if a.get("isActive", True)]
        
        return admins
    except ClientError as e:
        print(f"Error getting club admins for club {club_id}: {e}")
        return []


def update_user_verification_status(email: str, status: str, user_type: str = None) -> dict:
    """
    Update verificationStatus for a user.
    
    Args:
        email: User's email address
        status: "pending" | "verified"
        user_type: "player" | "coach" | "club_admin" | None (auto-detect)
    
    Returns:
        dict with 'success' (bool), 'user_type' (str), and optional 'error'
    """
    if status not in ["pending", "verified"]:
        return {
            "success": False,
            "error": f"Invalid status: {status}. Must be 'pending' or 'verified'"
        }
    
    # Auto-detect user type if not provided
    if not user_type:
        # Try to find user in each table
        player = get_player_by_email(email)
        if player:
            user_type = "player"
            user_id = player.get("playerId")
            table_name = PLAYER_TABLE
            key_name = "playerId"
        else:
            coach = get_coach_by_email(email)
            if coach:
                user_type = "coach"
                user_id = coach.get("coachId")
                table_name = COACH_TABLE
                key_name = "coachId"
            else:
                admin = get_club_admin_by_email(email)
                if admin:
                    user_type = "club_admin"
                    user_id = admin.get("adminId")
                    table_name = CLUB_ADMIN_TABLE
                    key_name = "adminId"
                else:
                    return {
                        "success": False,
                        "error": f"User with email {email} not found in any table"
                    }
    else:
        # Use provided user_type
        if user_type == "player":
            player = get_player_by_email(email)
            if not player:
                return {"success": False, "error": f"Player with email {email} not found"}
            user_id = player.get("playerId")
            table_name = PLAYER_TABLE
            key_name = "playerId"
        elif user_type == "coach":
            coach = get_coach_by_email(email)
            if not coach:
                return {"success": False, "error": f"Coach with email {email} not found"}
            user_id = coach.get("coachId")
            table_name = COACH_TABLE
            key_name = "coachId"
        elif user_type == "club_admin":
            admin = get_club_admin_by_email(email)
            if not admin:
                return {"success": False, "error": f"Club admin with email {email} not found"}
            user_id = admin.get("adminId")
            table_name = CLUB_ADMIN_TABLE
            key_name = "adminId"
        else:
            return {
                "success": False,
                "error": f"Invalid user_type: {user_type}. Must be 'player', 'coach', or 'club_admin'"
            }
    
    # Update the verification status
    try:
        table = get_table(table_name)
        from datetime import datetime
        
        update_expression = "SET verificationStatus = :status, updatedAt = :updatedAt"
        expression_attribute_values = {
            ":status": status,
            ":updatedAt": datetime.utcnow().isoformat() + "Z"
        }
        
        # If status is "verified", we can optionally remove the field instead
        # For now, we'll set it to "verified" explicitly
        
        table.update_item(
            Key={key_name: user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        print(f"Updated verificationStatus to '{status}' for {user_type} {email} ({user_id})")
        return {
            "success": True,
            "user_type": user_type,
            "user_id": user_id,
            "email": email
        }
    except ClientError as e:
        error_msg = f"Error updating verification status for {user_type} {email}: {e}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "user_type": user_type
        }
    except Exception as e:
        error_msg = f"Unexpected error updating verification status for {user_type} {email}: {e}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "user_type": user_type
        }

