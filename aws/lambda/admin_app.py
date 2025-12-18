"""
Flask application for admin endpoints.

Consolidates all admin Lambda functions into a single Flask app.
All routes require admin authentication via Cognito authorizer.
"""

import json
import uuid
import os
import re
import csv
import io
import base64
import secrets
import boto3
from datetime import datetime, timedelta
from flask import Flask, request, g
from serverless_wsgi import handle_request

from shared.flask_auth import (
    require_admin,
    require_club,
    require_club_access,
    require_resource_access,
    flask_success_response,
    flask_error_response,
)
from shared.db_utils import (
    get_table,
    get_club_by_id,
    get_team_by_id,
    get_teams_by_club,
    get_player_by_id,
    get_activities_by_team,
    get_activities_by_club,
    get_all_content_pages_by_club,
    get_tracking_by_week,
)
from shared.auth_utils import extract_user_info_from_event, verify_admin_role
from shared.flask_auth import get_api_gateway_event
from shared.html_sanitizer import sanitize_html
from shared.week_utils import get_current_week_id, get_week_id, get_week_dates

app = Flask(__name__)

# S3 client for image uploads
CONTENT_IMAGES_BUCKET = os.environ.get("CONTENT_IMAGES_BUCKET", "consistency-tracker-content-images")
s3_client = boto3.client("s3")


@app.after_request
def after_request(response):
    """Add CORS headers to all responses."""
    # Get origin from request
    origin = request.headers.get('Origin')
    
    # Only allow specific origins
    allowed_origins = ['https://repwarrior.net', 'https://www.repwarrior.net']
    if origin and origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        # Default to first allowed origin if no origin or invalid origin
        response.headers['Access-Control-Allow-Origin'] = 'https://repwarrior.net'
    
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS,PATCH'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    if not text:
        return ""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


# Error handlers (specific errors first)
@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(500)
def handle_error(error):
    """Handle HTTP errors with consistent format."""
    # Get error description or default message
    if hasattr(error, 'description') and error.description:
        message = error.description
    elif hasattr(error, 'code'):
        message = f"HTTP {error.code} error occurred"
    else:
        message = "An error occurred"
    
    # Get status code
    status_code = error.code if hasattr(error, 'code') else 500
    
    return flask_error_response(
        message,
        status_code=status_code
    )

# Global exception handler to catch all unhandled exceptions (must be last)
@app.errorhandler(Exception)
def handle_unhandled_exception(error):
    """Handle all unhandled exceptions with CORS headers."""
    import traceback
    print(f"Unhandled exception: {error}")
    traceback.print_exc()
    
    # Check if this is an HTTPException (already handled by specific handlers)
    from werkzeug.exceptions import HTTPException
    if isinstance(error, HTTPException):
        return handle_error(error)
    
    return flask_error_response(
        "An internal server error occurred",
        status_code=500
    )


# ============================================================================
# Check Role Endpoint
# ============================================================================

@app.route('/admin/check-role', methods=['GET'])
def check_role():
    """Verify user's admin role (for frontend navigation)."""
    try:
        event = get_api_gateway_event()
        user_info = extract_user_info_from_event(event)
        
        if not user_info:
            return flask_error_response("Authentication required", status_code=401)
        
        is_admin = verify_admin_role(event)
        
        response_data = {
            "authenticated": True,
            "isAdmin": is_admin,
            "user": {
                "username": user_info.get("username"),
                "email": user_info.get("email"),
            },
        }
        
        return flask_success_response(response_data)
    except Exception as e:
        import traceback
        print(f"Error in check_role: {e}")
        traceback.print_exc()
        return flask_error_response(
            "An error occurred while checking role",
            status_code=500
        )


# ============================================================================
# Club Management Endpoints
# ============================================================================

@app.route('/admin/clubs', methods=['GET'])
@require_admin
def list_clubs():
    """List clubs (for now, only return user's club)."""
    user_club_id = g.club_id
    
    if user_club_id:
        club = get_club_by_id(user_club_id)
        clubs = [club] if club else []
    else:
        clubs = []
    
    return flask_success_response({"clubs": clubs, "total": len(clubs)})


@app.route('/admin/clubs/<club_id>', methods=['GET'])
@require_admin
@require_club_access('club_id')
def get_club(club_id):
    """Get club details."""
    club = get_club_by_id(club_id)
    if not club:
        return flask_error_response("Club not found", status_code=404)
    
    return flask_success_response({"club": club})


@app.route('/admin/clubs', methods=['POST'])
@require_admin
def create_club():
    """Create new club (restricted - for now, allow if user doesn't have a club)."""
    user_club_id = g.club_id
    
    if user_club_id:
        return flask_error_response(
            "User already associated with a club. Club creation restricted.",
            status_code=403
        )
    
    body = request.get_json() or {}
    club_name = body.get("clubName")
    
    if not club_name:
        return flask_error_response("Missing required field: clubName", status_code=400)
    
    # Create club
    new_club_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    
    club = {
        "clubId": new_club_id,
        "clubName": club_name,
        "createdAt": now,
        "settings": body.get("settings", {}),
    }
    
    table = get_table("ConsistencyTracker-Clubs")
    table.put_item(Item=club)
    
    return flask_success_response({"club": club}, status_code=201)


@app.route('/admin/clubs/<club_id>', methods=['PUT'])
@require_admin
@require_club_access('club_id')
def update_club(club_id):
    """Update club settings."""
    body = request.get_json() or {}
    
    # Get existing club
    existing = get_club_by_id(club_id)
    if not existing:
        return flask_error_response("Club not found", status_code=404)
    
    # Update allowed fields
    update_expression_parts = []
    expression_attribute_values = {}
    
    if "clubName" in body:
        update_expression_parts.append("clubName = :clubName")
        expression_attribute_values[":clubName"] = body["clubName"]
    
    if "settings" in body:
        update_expression_parts.append("settings = :settings")
        expression_attribute_values[":settings"] = body["settings"]
    
    if not update_expression_parts:
        return flask_error_response("No fields to update", status_code=400)
    
    # Add updatedAt
    update_expression_parts.append("updatedAt = :updatedAt")
    expression_attribute_values[":updatedAt"] = datetime.utcnow().isoformat() + "Z"
    
    # Perform update
    table = get_table("ConsistencyTracker-Clubs")
    table.update_item(
        Key={"clubId": club_id},
        UpdateExpression="SET " + ", ".join(update_expression_parts),
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="ALL_NEW",
    )
    
    # Get updated club
    updated = get_club_by_id(club_id)
    return flask_success_response({"club": updated})


# ============================================================================
# Team Management Endpoints
# ============================================================================

@app.route('/admin/teams', methods=['GET'])
@require_admin
@require_club
def list_teams():
    """List teams in coach's club."""
    club_id = g.club_id
    teams = get_teams_by_club(club_id)
    
    # Format response
    team_list = []
    for team in teams:
        team_list.append({
            "teamId": team.get("teamId"),
            "teamName": team.get("teamName"),
            "coachName": team.get("coachName"),
            "clubId": team.get("clubId"),
            "settings": team.get("settings", {}),
            "createdAt": team.get("createdAt"),
        })
    
    return flask_success_response({"teams": team_list, "total": len(team_list)})


@app.route('/admin/teams/<team_id>', methods=['GET'])
@require_admin
@require_club
def get_team(team_id):
    """Get team details."""
    team = get_team_by_id(team_id)
    if not team:
        return flask_error_response("Team not found", status_code=404)
    
    # Validate team belongs to coach's club
    if team.get("clubId") != g.club_id:
        return flask_error_response("Team not found or access denied", status_code=403)
    
    return flask_success_response({"team": team})


@app.route('/admin/teams', methods=['POST'])
@require_admin
@require_club
def create_team():
    """Create new team."""
    club_id = g.club_id
    body = request.get_json() or {}
    
    team_name = body.get("teamName")
    coach_name = body.get("coachName", "")
    request_club_id = body.get("clubId")
    
    if not team_name:
        return flask_error_response("Missing required field: teamName", status_code=400)
    
    # Validate clubId matches coach's club (never trust client)
    if request_club_id and request_club_id != club_id:
        return flask_error_response("Invalid clubId. Team must belong to your club.", status_code=403)
    
    # Create team
    new_team_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    
    team = {
        "teamId": new_team_id,
        "clubId": club_id,  # Set from coach's club (never trust client)
        "teamName": team_name,
        "coachName": coach_name,
        "settings": body.get("settings", {
            "weekStartDay": "Monday",
            "autoAdvanceWeek": False,
            "scoringMethod": "points",
        }),
        "createdAt": now,
    }
    
    table = get_table("ConsistencyTracker-Teams")
    table.put_item(Item=team)
    
    return flask_success_response({"team": team}, status_code=201)


@app.route('/admin/teams/<team_id>', methods=['PUT'])
@require_admin
@require_club
def update_team(team_id):
    """Update team settings."""
    club_id = g.club_id
    body = request.get_json() or {}
    
    # Get existing team
    existing = get_team_by_id(team_id)
    if not existing:
        return flask_error_response("Team not found", status_code=404)
    
    # Validate team belongs to coach's club
    if existing.get("clubId") != club_id:
        return flask_error_response("Team not found or access denied", status_code=403)
    
    # Update allowed fields
    update_expression_parts = []
    expression_attribute_values = {}
    
    if "teamName" in body:
        update_expression_parts.append("teamName = :teamName")
        expression_attribute_values[":teamName"] = body["teamName"]
    
    if "coachName" in body:
        update_expression_parts.append("coachName = :coachName")
        expression_attribute_values[":coachName"] = body["coachName"]
    
    if "settings" in body:
        update_expression_parts.append("settings = :settings")
        expression_attribute_values[":settings"] = body["settings"]
    
    if not update_expression_parts:
        return flask_error_response("No fields to update", status_code=400)
    
    # Add updatedAt
    update_expression_parts.append("updatedAt = :updatedAt")
    expression_attribute_values[":updatedAt"] = datetime.utcnow().isoformat() + "Z"
    
    # Perform update
    table = get_table("ConsistencyTracker-Teams")
    table.update_item(
        Key={"teamId": team_id},
        UpdateExpression="SET " + ", ".join(update_expression_parts),
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="ALL_NEW",
    )
    
    # Get updated team
    updated = get_team_by_id(team_id)
    return flask_success_response({"team": updated})


# ============================================================================
# Player Management Endpoints
# ============================================================================

@app.route('/admin/players', methods=['GET'])
@require_admin
@require_club
def list_players():
    """List all players in coach's club."""
    club_id = g.club_id
    table = get_table("ConsistencyTracker-Players")
    
    # Query by clubId using GSI
    response = table.query(
        IndexName="clubId-index",
        KeyConditionExpression="clubId = :clubId",
        ExpressionAttributeValues={":clubId": club_id},
    )
    players = response.get("Items", [])
    
    # Format response
    player_list = []
    for player in players:
        player_list.append({
            "playerId": player.get("playerId"),
            "name": player.get("name"),
            "email": player.get("email"),
            "uniqueLink": player.get("uniqueLink"),
            "isActive": player.get("isActive", True),
            "createdAt": player.get("createdAt"),
        })
    
    return flask_success_response({"players": player_list, "total": len(player_list)})


@app.route('/admin/players', methods=['POST'])
@require_admin
@require_club
def create_player():
    """Create new player."""
    club_id = g.club_id
    body = request.get_json() or {}
    
    name = body.get("name")
    email = body.get("email", "")
    team_id = body.get("teamId")
    
    if not name:
        return flask_error_response("Missing required field: name", status_code=400)
    
    if not team_id:
        return flask_error_response("Missing required field: teamId", status_code=400)
    
    # Validate team belongs to coach's club
    team = get_team_by_id(team_id)
    if not team:
        return flask_error_response("Team not found", status_code=404)
    
    if team.get("clubId") != club_id:
        return flask_error_response("Team not found or access denied", status_code=403)
    
    # Generate unique link (secure random token)
    unique_link = secrets.token_urlsafe(32)
    
    # Create player
    player_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    
    player = {
        "playerId": player_id,
        "name": name,
        "email": email,
        "uniqueLink": unique_link,
        "clubId": club_id,  # Set from coach's club
        "teamId": team_id,  # From request body (validated above)
        "isActive": True,
        "createdAt": now,
    }
    
    table = get_table("ConsistencyTracker-Players")
    table.put_item(Item=player)
    
    return flask_success_response({"player": player}, status_code=201)


@app.route('/admin/players/<player_id>', methods=['PUT'])
@require_admin
@require_club
@require_resource_access('player', 'player_id', get_player_by_id)
def update_player(player_id):
    """Update player."""
    club_id = g.club_id
    body = request.get_json() or {}
    
    # Get existing player (already validated by decorator)
    existing = g.current_resource
    
    # Update allowed fields
    update_expression_parts = []
    expression_attribute_values = {}
    
    if "name" in body:
        update_expression_parts.append("name = :name")
        expression_attribute_values[":name"] = body["name"]
    
    if "email" in body:
        update_expression_parts.append("email = :email")
        expression_attribute_values[":email"] = body["email"]
    
    if not update_expression_parts:
        return flask_error_response("No fields to update", status_code=400)
    
    # Add updatedAt
    update_expression_parts.append("updatedAt = :updatedAt")
    expression_attribute_values[":updatedAt"] = datetime.utcnow().isoformat() + "Z"
    
    # Perform update
    table = get_table("ConsistencyTracker-Players")
    table.update_item(
        Key={"playerId": player_id},
        UpdateExpression="SET " + ", ".join(update_expression_parts),
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="ALL_NEW",
    )
    
    # Get updated player
    updated = get_player_by_id(player_id)
    return flask_success_response({"player": updated})


@app.route('/admin/players/<player_id>', methods=['DELETE'])
@require_admin
@require_club
@require_resource_access('player', 'player_id', get_player_by_id)
def delete_player(player_id):
    """Deactivate player (soft delete)."""
    # Get existing player (already validated by decorator)
    existing = g.current_resource
    
    # Update isActive flag
    table = get_table("ConsistencyTracker-Players")
    table.update_item(
        Key={"playerId": player_id},
        UpdateExpression="SET isActive = :isActive, updatedAt = :updatedAt",
        ExpressionAttributeValues={
            ":isActive": False,
            ":updatedAt": datetime.utcnow().isoformat() + "Z",
        },
        ReturnValues="ALL_NEW",
    )
    
    return flask_success_response({"message": "Player deactivated successfully"})


# ============================================================================
# Activity Management Endpoints
# ============================================================================

@app.route('/admin/activities', methods=['GET'])
@require_admin
@require_club
def list_activities():
    """List all activities in coach's club."""
    club_id = g.club_id
    
    # List all activities in coach's club (club-wide + team-specific)
    club_activities = get_activities_by_club(club_id, active_only=False)
    activities = club_activities
    
    # Format response
    activity_list = []
    for activity in activities:
        activity_list.append({
            "activityId": activity.get("activityId"),
            "name": activity.get("name"),
            "description": activity.get("description"),
            "frequency": activity.get("frequency"),
            "pointValue": activity.get("pointValue", 1),
            "displayOrder": activity.get("displayOrder", 999),
            "isActive": activity.get("isActive", True),
        })
    
    return flask_success_response({"activities": activity_list, "total": len(activity_list)})


@app.route('/admin/activities', methods=['POST'])
@require_admin
@require_club
def create_activity():
    """Create activity."""
    club_id = g.club_id
    body = request.get_json() or {}
    
    name = body.get("name")
    description = body.get("description", "")
    frequency = body.get("frequency", "daily")
    point_value = body.get("pointValue", 1)
    display_order = body.get("displayOrder", 999)
    scope = body.get("scope", "team")  # "club" or "team"
    team_id = body.get("teamId")  # Required if scope is "team"
    
    if not name:
        return flask_error_response("Missing required field: name", status_code=400)
    
    # Validate scope and team
    if scope == "team":
        if not team_id:
            return flask_error_response("Missing required field: teamId for team-specific activity", status_code=400)
        # Validate team belongs to coach's club
        team = get_team_by_id(team_id)
        if not team:
            return flask_error_response("Team not found", status_code=404)
        if team.get("clubId") != club_id:
            return flask_error_response("Team not found or access denied", status_code=403)
    elif scope == "club":
        team_id = None  # Club-wide activity
    else:
        return flask_error_response("Invalid scope (must be 'club' or 'team')", status_code=400)
    
    # Get max displayOrder to append new activity
    existing_activities = get_activities_by_club(club_id, active_only=False)
    if display_order == 999 and existing_activities:
        max_order = max(a.get("displayOrder", 0) for a in existing_activities)
        display_order = max_order + 1
    
    # Create activity
    activity_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    
    activity = {
        "activityId": activity_id,
        "name": name,
        "description": description,
        "frequency": frequency,
        "pointValue": point_value,
        "displayOrder": display_order,
        "clubId": club_id,
        "teamId": team_id,  # None for club-wide, teamId for team-specific
        "scope": scope,
        "isActive": True,
        "createdAt": now,
    }
    
    table = get_table("ConsistencyTracker-Activities")
    table.put_item(Item=activity)
    
    return flask_success_response({"activity": activity}, status_code=201)


@app.route('/admin/activities/<activity_id>', methods=['PUT'])
@require_admin
@require_club
def update_activity(activity_id):
    """Update activity."""
    club_id = g.club_id
    body = request.get_json() or {}
    
    table = get_table("ConsistencyTracker-Activities")
    
    # Get existing activity
    existing = table.get_item(Key={"activityId": activity_id})
    if "Item" not in existing:
        return flask_error_response("Activity not found", status_code=404)
    
    existing_activity = existing["Item"]
    # Validate activity belongs to coach's club
    if existing_activity.get("clubId") != club_id:
        return flask_error_response("Activity not found or access denied", status_code=403)
    
    # Update allowed fields
    update_expression_parts = []
    expression_attribute_values = {}
    
    if "name" in body:
        update_expression_parts.append("name = :name")
        expression_attribute_values[":name"] = body["name"]
    
    if "description" in body:
        update_expression_parts.append("description = :description")
        expression_attribute_values[":description"] = body["description"]
    
    if "frequency" in body:
        update_expression_parts.append("#freq = :frequency")
        expression_attribute_values[":frequency"] = body["frequency"]
    
    if "pointValue" in body:
        update_expression_parts.append("pointValue = :pointValue")
        expression_attribute_values[":pointValue"] = body["pointValue"]
    
    if "displayOrder" in body:
        update_expression_parts.append("displayOrder = :displayOrder")
        expression_attribute_values[":displayOrder"] = body["displayOrder"]
    
    if "isActive" in body:
        update_expression_parts.append("isActive = :isActive")
        expression_attribute_values[":isActive"] = body["isActive"]
    
    if not update_expression_parts:
        return flask_error_response("No fields to update", status_code=400)
    
    # Add updatedAt
    update_expression_parts.append("updatedAt = :updatedAt")
    expression_attribute_values[":updatedAt"] = datetime.utcnow().isoformat() + "Z"
    
    # Build update expression with attribute name mapping for reserved words
    update_expression = "SET " + ", ".join(update_expression_parts)
    expression_attribute_names = {}
    if "#freq" in update_expression:
        expression_attribute_names["#freq"] = "frequency"
    
    # Perform update
    update_kwargs = {
        "Key": {"activityId": activity_id},
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": expression_attribute_values,
        "ReturnValues": "ALL_NEW",
    }
    if expression_attribute_names:
        update_kwargs["ExpressionAttributeNames"] = expression_attribute_names
    
    table.update_item(**update_kwargs)
    
    # Get updated activity
    updated = table.get_item(Key={"activityId": activity_id})
    return flask_success_response({"activity": updated.get("Item")})


@app.route('/admin/activities/<activity_id>', methods=['DELETE'])
@require_admin
@require_club
def delete_activity(activity_id):
    """Delete activity (hard delete)."""
    club_id = g.club_id
    table = get_table("ConsistencyTracker-Activities")
    
    # Get existing activity
    existing = table.get_item(Key={"activityId": activity_id})
    if "Item" not in existing:
        return flask_error_response("Activity not found", status_code=404)
    
    existing_activity = existing["Item"]
    # Validate activity belongs to coach's club
    if existing_activity.get("clubId") != club_id:
        return flask_error_response("Activity not found or access denied", status_code=403)
    
    # Delete activity
    table.delete_item(Key={"activityId": activity_id})
    
    return flask_success_response({"message": "Activity deleted successfully"})


# ============================================================================
# Content Management Endpoints
# ============================================================================

@app.route('/admin/content', methods=['GET'])
@require_admin
@require_club
def list_content():
    """List all content pages in club."""
    club_id = g.club_id
    content_pages = get_all_content_pages_by_club(club_id, published_only=False)
    
    # Format response (exclude full HTML content from list view)
    content_list = []
    for page in content_pages:
        content_list.append({
            "pageId": page.get("pageId"),
            "slug": page.get("slug"),
            "title": page.get("title"),
            "category": page.get("category"),
            "isPublished": page.get("isPublished", False),
            "displayOrder": page.get("displayOrder"),
            "createdAt": page.get("createdAt"),
            "updatedAt": page.get("updatedAt"),
            "createdBy": page.get("createdBy"),
            "lastEditedBy": page.get("lastEditedBy"),
            "clubId": page.get("clubId"),
            "teamId": page.get("teamId"),
            "scope": page.get("scope"),
        })
    
    return flask_success_response({"content": content_list, "total": len(content_list)})


@app.route('/admin/content/<content_id>', methods=['GET'])
@require_admin
@require_club
def get_content(content_id):
    """Get specific content for editing."""
    club_id = g.club_id
    table = get_table("ConsistencyTracker-ContentPages")
    
    # Get specific content page
    response = table.get_item(Key={"pageId": content_id})
    if "Item" not in response:
        return flask_error_response("Content page not found", status_code=404)
    
    content = response["Item"]
    # Validate content belongs to coach's club
    if content.get("clubId") != club_id:
        return flask_error_response("Content page not found or access denied", status_code=403)
    
    return flask_success_response({"content": content})


@app.route('/admin/content', methods=['POST'])
@require_admin
@require_club
def create_content():
    """Create new content page."""
    club_id = g.club_id
    user_email = g.current_user.get("email") or g.current_user.get("username")
    body = request.get_json() or {}
    
    title = body.get("title")
    category = body.get("category", "general")
    html_content = body.get("htmlContent", "")
    slug = body.get("slug") or slugify(title)
    display_order = body.get("displayOrder", 999)
    is_published = body.get("isPublished", False)
    scope = body.get("scope", "team")  # "club" or "team"
    team_id = body.get("teamId")  # Required if scope is "team"
    
    if not title:
        return flask_error_response("Missing required field: title", status_code=400)
    
    # Validate scope and team
    if scope == "team":
        if not team_id:
            return flask_error_response("Missing required field: teamId for team-specific content", status_code=400)
        # Validate team belongs to coach's club
        team = get_team_by_id(team_id)
        if not team:
            return flask_error_response("Team not found", status_code=404)
        if team.get("clubId") != club_id:
            return flask_error_response("Team not found or access denied", status_code=403)
    elif scope == "club":
        team_id = None  # Club-wide content
    else:
        return flask_error_response("Invalid scope (must be 'club' or 'team')", status_code=400)
    
    # Sanitize HTML content
    sanitized_html = sanitize_html(html_content)
    
    # Get max displayOrder to append new content (check against all club content)
    existing_content = get_all_content_pages_by_club(club_id, published_only=False)
    if display_order == 999 and existing_content:
        max_order = max(c.get("displayOrder", 0) for c in existing_content)
        display_order = max_order + 1
    
    # Check if slug already exists (check against all club content)
    for content in existing_content:
        if content.get("slug") == slug:
            return flask_error_response(f"Slug '{slug}' already exists", status_code=400)
    
    # Create content page
    page_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    
    content = {
        "pageId": page_id,
        "clubId": club_id,
        "teamId": team_id,  # None for club-wide, teamId for team-specific
        "scope": scope,
        "slug": slug,
        "title": title,
        "category": category,
        "htmlContent": sanitized_html,
        "isPublished": is_published,
        "displayOrder": display_order,
        "createdBy": user_email,
        "createdAt": now,
        "updatedAt": now,
        "lastEditedBy": user_email,
    }
    
    table = get_table("ConsistencyTracker-ContentPages")
    table.put_item(Item=content)
    
    return flask_success_response({"content": content}, status_code=201)


@app.route('/admin/content/<content_id>', methods=['PUT'])
@require_admin
@require_club
def update_content(content_id):
    """Update content page."""
    club_id = g.club_id
    user_email = g.current_user.get("email") or g.current_user.get("username")
    body = request.get_json() or {}
    
    table = get_table("ConsistencyTracker-ContentPages")
    
    # Get existing content
    existing = table.get_item(Key={"pageId": content_id})
    if "Item" not in existing:
        return flask_error_response("Content page not found", status_code=404)
    
    existing_content = existing["Item"]
    
    # Validate content belongs to coach's club
    if existing_content.get("clubId") != club_id:
        return flask_error_response("Content page not found or access denied", status_code=403)
    
    # Update allowed fields
    update_expression_parts = []
    expression_attribute_values = {}
    
    if "title" in body:
        update_expression_parts.append("title = :title")
        expression_attribute_values[":title"] = body["title"]
    
    if "category" in body:
        update_expression_parts.append("category = :category")
        expression_attribute_values[":category"] = body["category"]
    
    if "htmlContent" in body:
        # Sanitize HTML content
        sanitized_html = sanitize_html(body["htmlContent"])
        update_expression_parts.append("htmlContent = :htmlContent")
        expression_attribute_values[":htmlContent"] = sanitized_html
    
    if "slug" in body:
        # Check if new slug already exists (check against all club content)
        new_slug = body["slug"]
        existing_content_list = get_all_content_pages_by_club(club_id, published_only=False)
        for content in existing_content_list:
            if content.get("pageId") != content_id and content.get("slug") == new_slug:
                return flask_error_response(f"Slug '{new_slug}' already exists", status_code=400)
        
        update_expression_parts.append("slug = :slug")
        expression_attribute_values[":slug"] = new_slug
    
    if "scope" in body:
        # Allow changing scope, but validate
        new_scope = body["scope"]
        new_team_id = body.get("teamId")  # Can be null for club scope
        
        if new_scope == "team":
            if not new_team_id:
                return flask_error_response("Missing teamId for team-scoped content update", status_code=400)
            new_team = get_team_by_id(new_team_id)
            if not new_team or new_team.get("clubId") != club_id:
                return flask_error_response("New target team not found or access denied", status_code=403)
            update_expression_parts.append("teamId = :teamId")
            expression_attribute_values[":teamId"] = new_team_id
        else:  # new_scope == "club"
            update_expression_parts.append("teamId = :teamId")
            expression_attribute_values[":teamId"] = None  # Set teamId to null for club-wide
        
        update_expression_parts.append("scope = :scope")
        expression_attribute_values[":scope"] = new_scope
    
    if "displayOrder" in body:
        update_expression_parts.append("displayOrder = :displayOrder")
        expression_attribute_values[":displayOrder"] = body["displayOrder"]
    
    if "isPublished" in body:
        update_expression_parts.append("isPublished = :isPublished")
        expression_attribute_values[":isPublished"] = body["isPublished"]
    
    if not update_expression_parts:
        return flask_error_response("No fields to update", status_code=400)
    
    # Add updatedAt and lastEditedBy
    update_expression_parts.append("updatedAt = :updatedAt")
    update_expression_parts.append("lastEditedBy = :lastEditedBy")
    expression_attribute_values[":updatedAt"] = datetime.utcnow().isoformat() + "Z"
    expression_attribute_values[":lastEditedBy"] = user_email
    
    # Perform update
    table.update_item(
        Key={"pageId": content_id},
        UpdateExpression="SET " + ", ".join(update_expression_parts),
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="ALL_NEW",
    )
    
    # Get updated content
    updated = table.get_item(Key={"pageId": content_id})
    return flask_success_response({"content": updated.get("Item")})


@app.route('/admin/content/<content_id>', methods=['DELETE'])
@require_admin
@require_club
def delete_content(content_id):
    """Delete content page."""
    club_id = g.club_id
    table = get_table("ConsistencyTracker-ContentPages")
    
    # Get existing content
    existing = table.get_item(Key={"pageId": content_id})
    if "Item" not in existing:
        return flask_error_response("Content page not found", status_code=404)
    
    existing_content = existing["Item"]
    # Validate content belongs to coach's club
    if existing_content.get("clubId") != club_id:
        return flask_error_response("Content page not found or access denied", status_code=403)
    
    # Delete content
    table.delete_item(Key={"pageId": content_id})
    
    return flask_success_response({"message": "Content page deleted successfully"})


@app.route('/admin/content/<content_id>/publish', methods=['PUT'])
@require_admin
@require_club
def publish_content(content_id):
    """Publish/unpublish content page."""
    club_id = g.club_id
    user_email = g.current_user.get("email") or g.current_user.get("username")
    body = request.get_json() or {}
    
    is_published = body.get("isPublished", True)
    
    table = get_table("ConsistencyTracker-ContentPages")
    
    # Get existing content
    existing = table.get_item(Key={"pageId": content_id})
    if "Item" not in existing:
        return flask_error_response("Content page not found", status_code=404)
    
    existing_content = existing["Item"]
    # Validate content belongs to coach's club
    if existing_content.get("clubId") != club_id:
        return flask_error_response("Content page not found or access denied", status_code=403)
    
    # Update publish status
    table.update_item(
        Key={"pageId": content_id},
        UpdateExpression="SET isPublished = :isPublished, updatedAt = :updatedAt, lastEditedBy = :lastEditedBy",
        ExpressionAttributeValues={
            ":isPublished": is_published,
            ":updatedAt": datetime.utcnow().isoformat() + "Z",
            ":lastEditedBy": user_email,
        },
        ReturnValues="ALL_NEW",
    )
    
    # Get updated content
    updated = table.get_item(Key={"pageId": content_id})
    
    return flask_success_response({
        "content": updated.get("Item"),
        "message": "Content published" if is_published else "Content unpublished",
    })


@app.route('/admin/content/reorder', methods=['PUT'])
@require_admin
@require_club
def reorder_content():
    """Update display order of content pages."""
    club_id = g.club_id
    user_email = g.current_user.get("email") or g.current_user.get("username")
    body = request.get_json() or {}
    
    # Expected format: { "reorder": [{"pageId": "...", "displayOrder": 1}, ...] }
    reorder_list = body.get("reorder", [])
    
    if not reorder_list:
        return flask_error_response("Missing 'reorder' array in request body", status_code=400)
    
    table = get_table("ConsistencyTracker-ContentPages")
    now = datetime.utcnow().isoformat() + "Z"
    
    # Validate all pages belong to coach's club before updating
    for item in reorder_list:
        page_id = item.get("pageId")
        if not page_id:
            continue
        
        existing = table.get_item(Key={"pageId": page_id})
        if "Item" not in existing:
            return flask_error_response(f"Content page {page_id} not found", status_code=404)
        
        existing_content = existing["Item"]
        if existing_content.get("clubId") != club_id:
            return flask_error_response(f"Access denied to reorder content page {page_id}", status_code=403)
    
    # Update display order for each content page
    updated_pages = []
    for item in reorder_list:
        page_id = item.get("pageId")
        display_order = item.get("displayOrder")
        
        if not page_id or display_order is None:
            continue
        
        # Update display order
        table.update_item(
            Key={"pageId": page_id},
            UpdateExpression="SET displayOrder = :displayOrder, updatedAt = :updatedAt, lastEditedBy = :lastEditedBy",
            ExpressionAttributeValues={
                ":displayOrder": display_order,
                ":updatedAt": now,
                ":lastEditedBy": user_email,
            },
            ReturnValues="ALL_NEW",
        )
        
        updated = table.get_item(Key={"pageId": page_id})
        if "Item" in updated:
            updated_pages.append(updated["Item"])
    
    return flask_success_response({
        "message": f"Updated display order for {len(updated_pages)} content pages",
        "content": updated_pages,
    })


@app.route('/admin/content/image-upload-url', methods=['POST'])
@require_admin
def image_upload():
    """Generate pre-signed S3 URL for image upload."""
    body = request.get_json() or {}
    
    file_name = body.get("fileName")
    content_type = body.get("contentType", "image/jpeg")
    
    if not file_name:
        return flask_error_response("Missing fileName in request body", status_code=400)
    
    # Validate file extension
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    file_ext = os.path.splitext(file_name)[1].lower()
    if file_ext not in allowed_extensions:
        return flask_error_response(
            f"Invalid file type. Allowed: {', '.join(allowed_extensions)}",
            status_code=400
        )
    
    # Generate unique file path (prevent overwrites)
    unique_id = str(uuid.uuid4())
    file_path = f"content/{unique_id}{file_ext}"
    
    # Generate pre-signed URL for PUT operation
    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": CONTENT_IMAGES_BUCKET,
            "Key": file_path,
            "ContentType": content_type,
        },
        ExpiresIn=300,  # 5 minutes
    )
    
    # Generate public URL (after upload, via CloudFront)
    # This will be the CloudFront URL + file_path
    public_url = f"https://content.repwarrior.net/{file_path}"
    
    return flask_success_response({
        "uploadUrl": presigned_url,
        "publicUrl": public_url,
        "filePath": file_path,
        "expiresIn": 300,
    })


# ============================================================================
# Overview Endpoint
# ============================================================================

@app.route('/admin/overview', methods=['GET'])
@require_admin
@require_club
def overview():
    """Team statistics and overview."""
    club_id = g.club_id
    current_week_id = get_current_week_id()
    
    # Get all players in club
    player_table = get_table("ConsistencyTracker-Players")
    players_response = player_table.query(
        IndexName="clubId-index",
        KeyConditionExpression="clubId = :clubId",
        ExpressionAttributeValues={":clubId": club_id},
    )
    players = players_response.get("Items", [])
    active_players = [p for p in players if p.get("isActive", True)]
    
    # Get activities (club-wide + team-specific)
    club_activities = get_activities_by_club(club_id, active_only=True)
    activities = club_activities  # Can be filtered by team if needed
    
    # Get current week tracking
    tracking_records = get_tracking_by_week(current_week_id)
    club_tracking = [t for t in tracking_records if t.get("clubId") == club_id]
    
    # Calculate statistics
    # Aggregate scores by player for current week
    player_scores = {}
    for record in club_tracking:
        player_id = record.get("playerId")
        daily_score = record.get("dailyScore", 0)
        
        if player_id not in player_scores:
            player_scores[player_id] = {
                "playerId": player_id,
                "weeklyScore": 0,
                "daysCompleted": 0,
            }
        
        player_scores[player_id]["weeklyScore"] += daily_score
        player_scores[player_id]["daysCompleted"] += 1
    
    # Calculate team averages
    total_weekly_score = sum(ps["weeklyScore"] for ps in player_scores.values())
    average_weekly_score = total_weekly_score / len(player_scores) if player_scores else 0
    
    # Get top performers
    top_performers = sorted(
        player_scores.items(),
        key=lambda x: x[1]["weeklyScore"],
        reverse=True
    )[:5]
    
    # Get player names for top performers
    player_map = {p.get("playerId"): p for p in active_players}
    top_performers_list = []
    for player_id, score_data in top_performers:
        player = player_map.get(player_id)
        if player:
            top_performers_list.append({
                "playerId": player_id,
                "name": player.get("name"),
                "weeklyScore": score_data["weeklyScore"],
                "daysCompleted": score_data["daysCompleted"],
            })
    
    # Get last 4 weeks of data for trends
    weeks_data = []
    for i in range(4):
        week_date = datetime.utcnow() - timedelta(weeks=i)
        week_id = get_week_id(week_date)
        
        week_tracking = get_tracking_by_week(week_id)
        week_club_tracking = [t for t in week_tracking if t.get("clubId") == club_id]
        
        week_player_scores = {}
        for record in week_club_tracking:
            player_id = record.get("playerId")
            daily_score = record.get("dailyScore", 0)
            
            if player_id not in week_player_scores:
                week_player_scores[player_id] = 0
            week_player_scores[player_id] += daily_score
        
        weeks_data.append({
            "weekId": week_id,
            "averageScore": sum(week_player_scores.values()) / len(week_player_scores) if week_player_scores else 0,
            "participatingPlayers": len(week_player_scores),
        })
    
    # Build response
    response_data = {
        "currentWeek": {
            "weekId": current_week_id,
            "totalPlayers": len(active_players),
            "participatingPlayers": len(player_scores),
            "averageWeeklyScore": round(average_weekly_score, 2),
            "totalWeeklyScore": total_weekly_score,
        },
        "topPerformers": top_performers_list,
        "weeksTrend": weeks_data,
        "activities": {
            "total": len(activities),
            "list": [{"activityId": a.get("activityId"), "name": a.get("name")} for a in activities],
        },
    }
    
    return flask_success_response(response_data)


# ============================================================================
# Export Endpoint
# ============================================================================

@app.route('/admin/export/<week_id>', methods=['GET'])
@require_admin
@require_club
def export_week(week_id):
    """Export week data (CSV format)."""
    club_id = g.club_id
    
    # Validate week ID format
    try:
        week_dates = get_week_dates(week_id)
    except Exception:
        return flask_error_response("Invalid weekId format (expected YYYY-WW)", status_code=400)
    
    # Get tracking records for the week
    tracking_records = get_tracking_by_week(week_id)
    club_tracking = [t for t in tracking_records if t.get("clubId") == club_id]
    
    # Get activities (club-wide + team-specific)
    club_activities = get_activities_by_club(club_id, active_only=True)
    activity_map = {a.get("activityId"): a.get("name") for a in club_activities}
    
    # Aggregate by player
    player_data = {}
    for record in club_tracking:
        player_id = record.get("playerId")
        date = record.get("date")
        completed_activities = record.get("completedActivities", [])
        daily_score = record.get("dailyScore", 0)
        
        if player_id not in player_data:
            player = get_player_by_id(player_id)
            player_data[player_id] = {
                "playerId": player_id,
                "playerName": player.get("name") if player else "Unknown",
                "dailyScores": {},
                "weeklyScore": 0,
            }
        
        player_data[player_id]["dailyScores"][date] = {
            "completedActivities": completed_activities,
            "dailyScore": daily_score,
        }
        player_data[player_id]["weeklyScore"] += daily_score
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    header = ["Player Name", "Weekly Score"] + days + ["Activities Completed"]
    writer.writerow(header)
    
    # Write data rows
    for player_id, data in sorted(player_data.items(), key=lambda x: x[1]["weeklyScore"], reverse=True):
        row = [data["playerName"], data["weeklyScore"]]
        
        # Daily scores
        for day in days:
            # Find date for this day of week
            day_scores = data["dailyScores"]
            day_score = 0
            for date, score_data in day_scores.items():
                # Simple match by day name (could be improved)
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                if date_obj.strftime("%A") == day:
                    day_score = score_data["dailyScore"]
                    break
            row.append(day_score)
        
        # Activities completed (comma-separated list)
        all_activities = set()
        for score_data in data["dailyScores"].values():
            all_activities.update(score_data["completedActivities"])
        activities_list = ", ".join(
            activity_map.get(aid, aid) for aid in sorted(all_activities)
        )
        row.append(activities_list)
        
        writer.writerow(row)
    
    csv_content = output.getvalue()
    output.close()
    
    # Return CSV as base64-encoded string (or could return as text/plain)
    csv_base64 = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
    
    return flask_success_response({
        "weekId": week_id,
        "csv": csv_base64,
        "filename": f"consistency-tracker-{week_id}.csv",
    })


# ============================================================================
# Week Advance Endpoint
# ============================================================================

@app.route('/admin/week/advance', methods=['POST'])
@require_admin
@require_club
def advance_week():
    """Advance to next week (update team configuration)."""
    club_id = g.club_id
    
    table = get_table("ConsistencyTracker-Teams")
    
    # Get current week
    current_week_id = get_current_week_id()
    
    # Calculate next week
    next_week_date = datetime.utcnow() + timedelta(weeks=1)
    next_week_id = get_week_id(next_week_date)
    
    # Get all teams in the club
    teams = get_teams_by_club(club_id)
    
    if not teams:
        return flask_error_response("No teams found for club", status_code=404)
    
    # Update current week for all teams in the club
    updated_teams = []
    for team in teams:
        team_id = team.get("teamId")
        try:
            table.update_item(
                Key={"teamId": team_id},
                UpdateExpression="SET currentWeekId = :nextWeekId, updatedAt = :updatedAt",
                ExpressionAttributeValues={
                    ":nextWeekId": next_week_id,
                    ":updatedAt": datetime.utcnow().isoformat() + "Z",
                },
                ReturnValues="ALL_NEW",
            )
            updated_teams.append(team_id)
        except Exception as e:
            print(f"Error updating team {team_id}: {e}")
    
    return flask_success_response({
        "message": "Week advanced successfully for all teams in club",
        "previousWeekId": current_week_id,
        "currentWeekId": next_week_id,
        "teamsUpdated": updated_teams,
        "totalTeams": len(teams),
    })


# ============================================================================
# Reflections Endpoint
# ============================================================================

@app.route('/admin/reflections', methods=['GET'])
@require_admin
@require_club
def list_reflections():
    """View all player reflections."""
    club_id = g.club_id
    
    # Get weekId from query parameters (optional)
    week_id = request.args.get("weekId")
    
    reflection_table = get_table("ConsistencyTracker-Reflections")
    
    if week_id:
        # Get reflections for specific week in club
        response = reflection_table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            FilterExpression="weekId = :weekId",
            ExpressionAttributeValues={
                ":clubId": club_id,
                ":weekId": week_id,
            },
        )
        reflections = response.get("Items", [])
    else:
        # Get all reflections for club
        response = reflection_table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id},
        )
        reflections = response.get("Items", [])
    
    # Get player details for each reflection
    reflections_with_players = []
    for reflection in reflections:
        player_id = reflection.get("playerId")
        player = get_player_by_id(player_id)
        
        if player and player.get("isActive", True):
            reflections_with_players.append({
                "reflectionId": reflection.get("reflectionId"),
                "playerId": player_id,
                "playerName": player.get("name"),
                "weekId": reflection.get("weekId"),
                "wentWell": reflection.get("wentWell"),
                "doBetter": reflection.get("doBetter"),
                "planForWeek": reflection.get("planForWeek"),
                "createdAt": reflection.get("createdAt"),
                "updatedAt": reflection.get("updatedAt"),
            })
    
    # Sort by weekId (most recent first) and then by player name
    reflections_with_players.sort(
        key=lambda x: (x["weekId"], x["playerName"]),
        reverse=True
    )
    
    return flask_success_response({
        "reflections": reflections_with_players,
        "total": len(reflections_with_players),
        "weekId": week_id,
    })


# ============================================================================
# Lambda Handler
# ============================================================================

def lambda_handler(event, context):
    """Lambda handler wrapper for Flask app."""
    return handle_request(app, event, context)

