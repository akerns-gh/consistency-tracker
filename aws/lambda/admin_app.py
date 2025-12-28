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
import string
import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from flask import Flask, request, g
from serverless_wsgi import handle_request
from botocore.exceptions import ClientError

from shared.flask_auth import (
    require_admin,
    require_app_admin,
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
from shared.auth_utils import extract_user_info_from_event, extract_user_info_from_jwt_token, verify_admin_role, verify_app_admin_role
from shared.flask_auth import get_api_gateway_event
from shared.html_sanitizer import sanitize_html
from shared.week_utils import get_current_week_id, get_week_id, get_week_dates
from shared.email_service import send_templated_email, validate_email_address, verify_email_identity
from shared.email_templates import (
    get_user_invitation_template,
    get_club_creation_template,
    get_team_creation_template,
    get_player_invitation_template,
    get_coach_invitation_template,
)

app = Flask(__name__)

# S3 client for image uploads
CONTENT_IMAGES_BUCKET = os.environ.get("CONTENT_IMAGES_BUCKET", "consistency-tracker-content-images")
s3_client = boto3.client("s3")

# Cognito client for group management
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")
COGNITO_REGION = os.environ.get("COGNITO_REGION", "us-east-1")
cognito_client = boto3.client("cognito-idp", region_name=COGNITO_REGION) if COGNITO_USER_POOL_ID else None


def parse_csv_from_request() -> Tuple[List[Dict[str, str]], str]:
    """
    Parse CSV file from a multipart/form-data request.

    Returns:
        (rows, error_message) tuple. If error_message is not empty, parsing failed.
    """
    if "file" not in request.files:
        return [], "No file part named 'file' in request"

    file_storage = request.files["file"]
    if file_storage.filename == "":
        return [], "No selected file"

    try:
        stream = io.StringIO(file_storage.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)
        rows: List[Dict[str, str]] = []
        for row in reader:
            rows.append({k: (v or "").strip() for k, v in row.items()})
        if not rows:
            return [], "CSV file is empty"
        return rows, ""
    except Exception as e:
        return [], f"Failed to parse CSV file: {str(e)}"


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


def validate_team_csv_row(row: Dict[str, str], row_num: int) -> Dict[str, Any]:
    """Validate a single team CSV row for preview."""
    team_name = (row.get("teamName") or "").strip()
    team_id = (row.get("teamId") or "").strip()
    errors: List[str] = []
    warnings: List[str] = []

    if not team_name:
        errors.append("Missing required column: teamName")

    return {
        "row": row_num,
        "teamName": team_name,
        "teamId": team_id or None,
        "errors": errors,
        "warnings": warnings,
    }


def validate_player_csv_row(row: Dict[str, str], row_num: int, club_id: str) -> Dict[str, Any]:
    """Validate a single player CSV row for preview."""
    name = (row.get("name") or "").strip()
    email = (row.get("email") or "").strip()
    team_id = (row.get("teamId") or "").strip()
    team_name = (row.get("teamName") or "").strip()

    errors: List[str] = []
    warnings: List[str] = []

    if not name:
        errors.append("Missing required column: name")

    if not team_id and not team_name:
        errors.append("Either teamId or teamName is required")

    resolved_team_id = team_id
    if team_id:
        team = get_team_by_id(team_id)
        if not team or team.get("clubId") != club_id:
            errors.append("teamId does not exist in your club")
        else:
            team_name = team.get("teamName", team_name)
            resolved_team_id = team.get("teamId")

    return {
        "row": row_num,
        "name": name,
        "email": email or None,
        "teamName": team_name or None,
        "teamId": resolved_team_id or None,
        "errors": errors,
        "warnings": warnings,
    }


def check_team_duplicate(team_name: str, team_id: str, club_id: str) -> Dict[str, Any]:
    """
    Check if a team with the same name (case-insensitive) or ID already exists in the club.
    """
    table = get_table("ConsistencyTracker-Teams")

    # First check by teamId if provided
    if team_id:
        existing = table.get_item(Key={"teamId": team_id}).get("Item")
        if existing and existing.get("clubId") == club_id:
            return {
                "is_duplicate": True,
                "reason": "Duplicate team ID",
                "existingTeamId": existing.get("teamId"),
            }

    # Fallback: scan by clubId + case-insensitive teamName match
    response = table.scan(
        FilterExpression="clubId = :clubId",
        ExpressionAttributeValues={":clubId": club_id},
    )
    teams = response.get("Items", [])
    lower_name = (team_name or "").strip().lower()
    for t in teams:
        if (t.get("teamName") or "").strip().lower() == lower_name:
            return {
                "is_duplicate": True,
                "reason": "Duplicate team name",
                "existingTeamId": t.get("teamId"),
            }

    return {"is_duplicate": False, "reason": "", "existingTeamId": None}


def check_player_duplicate(name: str, team_id: str, player_id: str, club_id: str) -> Dict[str, Any]:
    """
    Check if a player already exists in the club by:
      - playerId, or
      - (name, teamId) combination (case-insensitive name).
    """
    table = get_table("ConsistencyTracker-Players")

    # Check by explicit playerId if provided
    if player_id:
        existing = table.get_item(Key={"playerId": player_id}).get("Item")
        if existing and existing.get("clubId") == club_id:
            return {
                "is_duplicate": True,
                "reason": "Duplicate player ID",
                "existingPlayerId": existing.get("playerId"),
            }

    # Query by clubId index then check name+teamId combination
    response = table.query(
        IndexName="clubId-index",
        KeyConditionExpression="clubId = :clubId",
        ExpressionAttributeValues={":clubId": club_id},
    )
    players = response.get("Items", [])
    lower_name = (name or "").strip().lower()
    for p in players:
        if (
            (p.get("name") or "").strip().lower() == lower_name
            and (p.get("teamId") or "") == (team_id or "")
        ):
            return {
                "is_duplicate": True,
                "reason": "Duplicate player name for team",
                "existingPlayerId": p.get("playerId"),
            }

    return {"is_duplicate": False, "reason": "", "existingPlayerId": None}

def create_cognito_group(user_pool_id: str, group_name: str, description: str = None) -> bool:
    """
    Create a Cognito group if it doesn't exist. Returns True if created or already exists.
    
    Args:
        user_pool_id: Cognito User Pool ID
        group_name: Name of the group to create
        description: Optional description for the group
    
    Returns:
        True if group was created or already exists, False on error
    """
    if not cognito_client:
        print(f"Warning: Cognito client not initialized. Cannot create group: {group_name}")
        return False
    
    try:
        cognito_client.create_group(
            UserPoolId=user_pool_id,
            GroupName=group_name,
            Description=description
        )
        print(f"Created Cognito group: {group_name}")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceConflictException':
            # Group already exists - that's fine (idempotent)
            print(f"Cognito group already exists: {group_name}")
            return True
        else:
            print(f"Error creating Cognito group {group_name}: {e}")
            return False


def generate_temporary_password() -> str:
    """
    Generate a secure temporary password that meets Cognito password policy.
    
    Requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    
    Returns:
        A secure temporary password string
    """
    # Generate password with required characters
    uppercase = secrets.choice(string.ascii_uppercase)
    lowercase = secrets.choice(string.ascii_lowercase)
    number = secrets.choice(string.digits)
    
    # Fill remaining length with random characters (mix of upper, lower, digits)
    remaining_length = 12 - 3  # 12 total, minus the 3 required chars
    chars = string.ascii_letters + string.digits
    remaining = ''.join(secrets.choice(chars) for _ in range(remaining_length))
    
    # Combine and shuffle
    password_chars = list(uppercase + lowercase + number + remaining)
    secrets.SystemRandom().shuffle(password_chars)
    
    return ''.join(password_chars)


def create_cognito_user(user_pool_id: str, email: str, temporary_password: str, club_id: str = None) -> dict:
    """
    Create a Cognito user if it doesn't exist. Returns user info or None on error.
    
    Args:
        user_pool_id: Cognito User Pool ID
        email: User's email address (used as username)
        temporary_password: Temporary password (must meet password policy)
        club_id: Optional club ID to set as custom:clubId attribute
    
    Returns:
        Dict with user info if successful, None on error
    """
    if not cognito_client:
        print(f"Warning: Cognito client not initialized. Cannot create user: {email}")
        return None
    
    try:
        user_attributes = [
            {'Name': 'email', 'Value': email},
            {'Name': 'email_verified', 'Value': 'true'}
        ]
        
        # Add custom:clubId if provided
        if club_id:
            user_attributes.append({'Name': 'custom:clubId', 'Value': club_id})
        
        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=user_attributes,
            TemporaryPassword=temporary_password,
            MessageAction='SUPPRESS',  # Don't send welcome email (we'll send our own)
            DesiredDeliveryMediums=['EMAIL']
        )
        print(f"Created Cognito user: {email}")
        return {
            'username': response['User']['Username'],
            'status': response['User']['UserStatus']
        }
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'UsernameExistsException':
            print(f"User '{email}' already exists")
            # If user exists, try to update the clubId attribute
            if club_id:
                try:
                    cognito_client.admin_update_user_attributes(
                        UserPoolId=user_pool_id,
                        Username=email,
                        UserAttributes=[
                            {'Name': 'custom:clubId', 'Value': club_id}
                        ]
                    )
                    print(f"Updated custom:clubId for existing user {email}")
                except Exception as update_error:
                    print(f"Warning: Could not update custom:clubId for user {email}: {update_error}")
            return {'username': email, 'status': 'EXISTS'}
        else:
            print(f"Error creating Cognito user {email}: {e}")
            return None


def add_user_to_cognito_group(user_pool_id: str, username: str, group_name: str) -> bool:
    """
    Add a user to a Cognito group.
    
    Args:
        user_pool_id: Cognito User Pool ID
        username: Username (email)
        group_name: Name of the group
    
    Returns:
        True if successful, False on error
    """
    if not cognito_client:
        print(f"Warning: Cognito client not initialized. Cannot add user to group: {group_name}")
        return False
    
    try:
        cognito_client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name
        )
        print(f"Added user {username} to group: {group_name}")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'InvalidParameterException' and 'already a member' in str(e):
            print(f"User {username} is already a member of {group_name}")
            return True
        else:
            print(f"Error adding user {username} to group {group_name}: {e}")
            return False


def get_cognito_groups_for_club(club_id: str) -> List[str]:
    """
    Get all Cognito group names associated with a club.
    
    Returns:
        List of group names: [club-{name}-admins, coach-{clubId}-{teamId1}, ...]
    """
    groups = []
    
    # Get club record to get club name
    club = get_club_by_id(club_id)
    if not club:
        return groups
    
    club_name = club.get("clubName", "")
    if club_name:
        # Add club-admin group
        sanitized_name = sanitize_club_name_for_group(club_name)
        club_admin_group = f"club-{sanitized_name}-admins"
        groups.append(club_admin_group)
    
    # Get all teams for the club
    teams = get_teams_by_club(club_id)
    for team in teams:
        team_id = team.get("teamId")
        if team_id:
            coach_group = f"coach-{club_id}-{team_id}"
            groups.append(coach_group)
    
    return groups


def remove_user_from_cognito_group(user_pool_id: str, username: str, group_name: str) -> bool:
    """
    Remove a user from a Cognito group.
    
    Args:
        user_pool_id: Cognito User Pool ID
        username: Username (email)
        group_name: Name of the group
    
    Returns:
        True if successful, False on error
    """
    if not cognito_client:
        print(f"Warning: Cognito client not initialized. Cannot remove user from group: {group_name}")
        return False
    
    try:
        cognito_client.admin_remove_user_from_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name
        )
        print(f"Removed user {username} from group: {group_name}")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            # User or group doesn't exist - that's fine
            print(f"User {username} or group {group_name} does not exist")
            return True
        else:
            print(f"Error removing user {username} from group {group_name}: {e}")
            return False


def enable_cognito_user(user_pool_id: str, username: str) -> bool:
    """
    Enable a Cognito user account.
    
    Args:
        user_pool_id: Cognito User Pool ID
        username: Username (email)
    
    Returns:
        True if successful, False on error
    """
    if not cognito_client:
        print(f"Warning: Cognito client not initialized. Cannot enable user: {username}")
        return False
    
    try:
        cognito_client.admin_enable_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        print(f"Enabled Cognito user: {username}")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            print(f"User {username} does not exist")
            return False
        else:
            print(f"Error enabling user {username}: {e}")
            return False


def disable_cognito_user(user_pool_id: str, username: str) -> bool:
    """
    Disable a Cognito user account.
    
    Args:
        user_pool_id: Cognito User Pool ID
        username: Username (email)
    
    Returns:
        True if successful, False on error
    """
    if not cognito_client:
        print(f"Warning: Cognito client not initialized. Cannot disable user: {username}")
        return False
    
    try:
        cognito_client.admin_disable_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        print(f"Disabled Cognito user: {username}")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            print(f"User {username} does not exist")
            return False
        else:
            print(f"Error disabling user {username}: {e}")
            return False


def get_coaches_for_team(team_id: str) -> List[dict]:
    """
    Get all coaches (Cognito users) for a team.
    
    Args:
        team_id: Team ID
    
    Returns:
        List of coach user info dictionaries with email, username, status
    """
    if not COGNITO_USER_POOL_ID or not cognito_client:
        print(f"Warning: Cognito not configured. Cannot get coaches for team: {team_id}")
        return []
    
    # Get team to find club_id
    team = get_team_by_id(team_id)
    if not team:
        return []
    
    club_id = team.get("clubId")
    if not club_id:
        return []
    
    # Build group name
    group_name = f"coach-{club_id}-{team_id}"
    
    coaches = []
    try:
        # List all users in the group
        paginator = cognito_client.get_paginator('list_users_in_group')
        pages = paginator.paginate(
            UserPoolId=COGNITO_USER_POOL_ID,
            GroupName=group_name
        )
        
        for page in pages:
            for user in page.get('Users', []):
                username = user.get('Username')
                attributes = {attr['Name']: attr['Value'] for attr in user.get('Attributes', [])}
                email = attributes.get('email', username)
                status = user.get('UserStatus', 'UNKNOWN')
                enabled = user.get('Enabled', True)
                
                # Determine if coach is active (enabled and confirmed)
                is_active = enabled and status in ['CONFIRMED', 'FORCE_CHANGE_PASSWORD']
                
                coaches.append({
                    'email': email,
                    'username': username,
                    'status': status,
                    'enabled': enabled,
                    'isActive': is_active
                })
        
        return coaches
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            # Group doesn't exist - that's fine, return empty list
            print(f"Group {group_name} does not exist")
            return []
        else:
            print(f"Error listing coaches for team {team_id}: {e}")
            return []


def remove_all_users_from_group(user_pool_id: str, group_name: str) -> int:
    """
    Remove all users from a Cognito group.
    
    Args:
        user_pool_id: Cognito User Pool ID
        group_name: Name of the group
    
    Returns:
        Number of users removed
    """
    if not cognito_client:
        print(f"Warning: Cognito client not initialized. Cannot remove users from group: {group_name}")
        return 0
    
    removed_count = 0
    
    try:
        # List all users in the group
        paginator = cognito_client.get_paginator('list_users_in_group')
        pages = paginator.paginate(
            UserPoolId=user_pool_id,
            GroupName=group_name
        )
        
        # Collect all usernames
        usernames = []
        for page in pages:
            for user in page.get('Users', []):
                username = user.get('Username')
                if username:
                    usernames.append(username)
        
        # Remove each user from the group
        for username in usernames:
            try:
                cognito_client.admin_remove_user_from_group(
                    UserPoolId=user_pool_id,
                    Username=username,
                    GroupName=group_name
                )
                removed_count += 1
                print(f"Removed user {username} from group {group_name}")
            except ClientError as e:
                print(f"Error removing user {username} from group {group_name}: {e}")
        
        print(f"Removed {removed_count} users from group {group_name}")
        return removed_count
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            # Group doesn't exist - that's fine
            print(f"Group {group_name} does not exist")
            return 0
        else:
            print(f"Error listing users in group {group_name}: {e}")
            return 0


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
        from flask import request
        
        event = get_api_gateway_event()
        user_info = extract_user_info_from_event(event)
        
        # Fallback: if no user info from event, try to extract from Authorization header
        if not user_info:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove 'Bearer ' prefix
                user_info = extract_user_info_from_jwt_token(token)
                print(f"DEBUG check_role: Extracted user_info from Authorization header")
        
        if not user_info:
            return flask_error_response("Authentication required", status_code=401)
        
        # Debug: Log user info and groups
        groups_raw = user_info.get("groups", [])
        # Ensure groups is always a list (handle case where it's a string)
        if isinstance(groups_raw, str):
            groups = [g.strip() for g in groups_raw.split(",") if g.strip()]
        elif isinstance(groups_raw, list):
            groups = groups_raw
        else:
            groups = []
        
        print(f"DEBUG check_role: User email: {user_info.get('email')}")
        print(f"DEBUG check_role: User groups (raw): {groups_raw}, type: {type(groups_raw)}")
        print(f"DEBUG check_role: User groups (processed): {groups}, type: {type(groups)}")
        
        # Create or update event with user_info for verify_admin_role
        # verify_admin_role expects event with authorizer.claims containing cognito:groups
        if not event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("cognito:groups"):
            # If no groups in authorizer context, create one from user_info
            if not event.get("requestContext"):
                event["requestContext"] = {}
            if not event["requestContext"].get("authorizer"):
                event["requestContext"]["authorizer"] = {}
            if not event["requestContext"]["authorizer"].get("claims"):
                event["requestContext"]["authorizer"]["claims"] = {}
            
            # Update claims with user_info - ensure groups is a list
            claims = event["requestContext"]["authorizer"]["claims"]
            claims["cognito:username"] = user_info.get("username")
            claims["email"] = user_info.get("email")
            claims["sub"] = user_info.get("user_id")
            claims["cognito:groups"] = groups  # This is now guaranteed to be a list
            print(f"DEBUG check_role: Created authorizer claims from user_info, groups: {groups}")
        
        is_admin = verify_admin_role(event)
        is_app_admin = verify_app_admin_role(event)
        
        print(f"DEBUG check_role: is_admin={is_admin}, is_app_admin={is_app_admin}")
        
        response_data = {
            "authenticated": True,
            "isAdmin": is_admin,
            "isAppAdmin": is_app_admin,
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
    """List clubs. App-admins see all clubs (including disabled), club-admins see only their enabled club."""
    is_app_admin = getattr(g, 'is_app_admin', False)
    
    if is_app_admin:
        # App-admins can see all clubs (including disabled)
        table = get_table("ConsistencyTracker-Clubs")
        response = table.scan()
        clubs = response.get("Items", [])
    else:
        # Club-admins see only their club (if it's enabled)
        user_club_id = g.club_id
        if user_club_id:
            club = get_club_by_id(user_club_id)
            # Filter out disabled clubs for non-app-admins
            if club and not club.get("isDisabled", False):
                clubs = [club]
            else:
                clubs = []
        else:
            clubs = []
    
    return flask_success_response({"clubs": clubs, "total": len(clubs)})


@app.route('/admin/clubs/<club_id>', methods=['GET'])
@require_admin
def get_club(club_id):
    """Get club details. App-admins can get any club, club-admins can only get their own enabled club."""
    club = get_club_by_id(club_id)
    if not club:
        return flask_error_response("Club not found", status_code=404)
    
    # Check access: app-admins can get any club, club-admins can only get their own
    is_app_admin = getattr(g, 'is_app_admin', False)
    user_club_id = getattr(g, 'club_id', None)
    
    if not is_app_admin and club_id != user_club_id:
        return flask_error_response("Club not found or access denied", status_code=403)
    
    # Check if club is disabled (non-app-admins cannot access disabled clubs)
    if not is_app_admin and club.get("isDisabled", False):
        return flask_error_response("Club is disabled", status_code=403)
    
    return flask_success_response({"club": club})


@app.route('/admin/clubs', methods=['POST'])
@require_admin
@require_app_admin
def create_club():
    """Create new club (restricted to app-admins only)."""
    
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
    
    # Automatically create club-{sanitizedClubName}-admins group in Cognito
    admin_email = None
    if COGNITO_USER_POOL_ID:
        sanitized_name = sanitize_club_name_for_group(club_name)
        group_name = f"club-{sanitized_name}-admins"
        description = f"Administrators for club {club_name}"
        create_cognito_group(COGNITO_USER_POOL_ID, group_name, description)
        
        # If admin email and password provided, create the user and add to group
        admin_email = body.get("adminEmail")
        admin_password = body.get("adminPassword")
        verification_status = None
        if admin_email and admin_password:
            # Automatically verify the email address in SES
            # This allows sending emails to this address even in sandbox mode
            if validate_email_address(admin_email):
                verification_result = verify_email_identity(admin_email)
                verification_status = verification_result
                if verification_result.get("success"):
                    if verification_result.get("already_verified"):
                        print(f"Club admin email {admin_email} is already verified in SES")
                    else:
                        print(f"Verification email sent to club admin {admin_email}")
                else:
                    print(f"Warning: Failed to verify club admin email {admin_email}: {verification_result.get('error')}")
            
            user_info = create_cognito_user(
                COGNITO_USER_POOL_ID,
                admin_email,
                admin_password,
                club_id=new_club_id  # Set custom:clubId attribute
            )
            if user_info and group_name:
                add_user_to_cognito_group(
                    COGNITO_USER_POOL_ID,
                    user_info['username'],
                    group_name
                )
    
    # Send email notifications
    response_data = {"club": club}
    email_status = {"appAdminEmail": None, "clubAdminEmail": None, "verification": verification_status}
    
    try:
        # Get current user info for app-admin notification
        event = get_api_gateway_event()
        user_info = extract_user_info_from_event(event)
        app_admin_email = user_info.get("email") if user_info else None
        
        # Send confirmation to app-admin
        if app_admin_email and validate_email_address(app_admin_email):
            try:
                template = get_club_creation_template(club_name, new_club_id, admin_email or "Not created")
                result = send_templated_email([app_admin_email], template)
                email_status["appAdminEmail"] = {
                    "sent": True,
                    "email": app_admin_email,
                    "messageId": result.get("message_id") if result else None
                }
                print(f"App-admin confirmation email sent to {app_admin_email}")
            except Exception as e:
                email_status["appAdminEmail"] = {
                    "sent": False,
                    "email": app_admin_email,
                    "error": str(e)
                }
                print(f"Error sending app-admin confirmation email to {app_admin_email}: {e}")
        
        # Send invitation to new club-admin if created
        if admin_email and admin_password and validate_email_address(admin_email):
            try:
                login_url = os.environ.get("FRONTEND_URL", "https://repwarrior.net/admin/login")
                template = get_user_invitation_template(
                    user_name=admin_email.split("@")[0],
                    email=admin_email,
                    temporary_password=admin_password,
                    login_url=login_url,
                    role="club administrator"
                )
                # Use configured club admin from email, fallback to default
                club_admin_from_email = os.environ.get("SES_CLUB_ADMIN_FROM_EMAIL") or os.environ.get("SES_FROM_EMAIL", "noreply@repwarrior.net")
                ses_from_name = os.environ.get("SES_FROM_NAME", "Consistency Tracker")
                result = send_templated_email(
                    [admin_email], 
                    template,
                    from_email=club_admin_from_email,
                    from_name=ses_from_name
                )
                email_status["clubAdminEmail"] = {
                    "sent": True,
                    "email": admin_email,
                    "messageId": result.get("message_id") if result else None
                }
                print(f"Club-admin invitation email sent to {admin_email}")
            except Exception as e:
                email_status["clubAdminEmail"] = {
                    "sent": False,
                    "email": admin_email,
                    "error": str(e)
                }
                print(f"Error sending club-admin invitation email to {admin_email}: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
        
        response_data["adminUser"] = {
            "email": admin_email,
            "status": "created",
            "message": "Club-admin user created and added to group"
        }
    except Exception as e:
        # Don't fail the request if email sending fails, but log the error
        print(f"Warning: Failed to send club creation emails: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    # Include email status in response
    response_data["emailStatus"] = email_status
    
    return flask_success_response(response_data, status_code=201)


@app.route('/admin/clubs/<club_id>', methods=['PUT'])
@require_admin
def update_club(club_id):
    """Update club settings. App-admins can update any club, club-admins can only update their own."""
    body = request.get_json() or {}
    
    # Get existing club
    existing = get_club_by_id(club_id)
    if not existing:
        return flask_error_response("Club not found", status_code=404)
    
    # Check access: app-admins can update any club, club-admins can only update their own
    is_app_admin = getattr(g, 'is_app_admin', False)
    user_club_id = getattr(g, 'club_id', None)
    
    if not is_app_admin and club_id != user_club_id:
        return flask_error_response("Club not found or access denied", status_code=403)
    
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


@app.route('/admin/clubs/<club_id>/admins', methods=['POST'])
@require_admin
@require_app_admin
def add_club_admin(club_id):
    """
    Add an additional club administrator to an existing club.
    
    - Restricted to app-admins only
    - Ensures the user has custom:clubId set
    - Adds the user to the club-{sanitizedName}-admins Cognito group
    """
    if not COGNITO_USER_POOL_ID or not cognito_client:
        return flask_error_response("Cognito is not configured for admin management", status_code=500)
    
    # Ensure club exists
    club = get_club_by_id(club_id)
    if not club:
        return flask_error_response("Club not found", status_code=404)
    
    body = request.get_json() or {}
    admin_email = (body.get("adminEmail") or "").strip()
    admin_password = (body.get("adminPassword") or "").strip()
    
    if not admin_email or not admin_password:
        return flask_error_response("adminEmail and adminPassword are required", status_code=400)
    
    if not validate_email_address(admin_email):
        return flask_error_response("Invalid adminEmail address", status_code=400)
    
    # Build club-admin group name
    sanitized_name = sanitize_club_name_for_group(club.get("clubName", ""))
    group_name = f"club-{sanitized_name}-admins"
    
    # Ensure the group exists
    create_cognito_group(
        COGNITO_USER_POOL_ID,
        group_name,
        f"Administrators for club {club.get('clubName', club_id)}"
    )
    
    # Create or update the Cognito user and set custom:clubId
    user_info = create_cognito_user(
        COGNITO_USER_POOL_ID,
        admin_email,
        admin_password,
        club_id=club_id,  # Ensure custom:clubId is set for this club
    )
    
    if not user_info:
        return flask_error_response("Failed to create or update club admin user", status_code=500)
    
    # Add user to the club-admin group
    add_user_to_cognito_group(
        COGNITO_USER_POOL_ID,
        user_info["username"],
        group_name,
    )
    
    # Optionally send an invitation email (reuse existing template)
    email_status = None
    try:
        login_url = os.environ.get("FRONTEND_URL", "https://repwarrior.net/admin/login")
        template = get_user_invitation_template(
            user_name=admin_email.split("@")[0],
            email=admin_email,
            temporary_password=admin_password,
            login_url=login_url,
            role="club administrator",
        )
        club_admin_from_email = os.environ.get("SES_CLUB_ADMIN_FROM_EMAIL") or os.environ.get(
            "SES_FROM_EMAIL", "noreply@repwarrior.net"
        )
        ses_from_name = os.environ.get("SES_FROM_NAME", "Consistency Tracker")
        result = send_templated_email(
            [admin_email],
            template,
            from_email=club_admin_from_email,
            from_name=ses_from_name,
        )
        email_status = {
            "sent": True,
            "email": admin_email,
            "messageId": result.get("message_id") if result else None,
        }
        print(f"Additional club-admin invitation email sent to {admin_email} for club {club_id}")
    except Exception as e:
        email_status = {
            "sent": False,
            "email": admin_email,
            "error": str(e),
        }
        print(f"Error sending additional club-admin invitation email to {admin_email}: {e}")
    
    return flask_success_response(
        {
            "message": "Club administrator added successfully",
            "clubId": club_id,
            "adminEmail": admin_email,
            "emailStatus": email_status,
        },
        status_code=201,
    )


@app.route('/admin/clubs/<club_id>/disable', methods=['POST'])
@require_admin
@require_app_admin
def disable_club(club_id):
    """Disable a club (restricted to app-admins only). Removes all users from Cognito groups."""
    
    # Get existing club
    existing = get_club_by_id(club_id)
    if not existing:
        return flask_error_response("Club not found", status_code=404)
    
    # Check if already disabled
    if existing.get("isDisabled", False):
        return flask_error_response("Club is already disabled", status_code=400)
    
    # Update club to set isDisabled flag
    table = get_table("ConsistencyTracker-Clubs")
    now = datetime.utcnow().isoformat() + "Z"
    table.update_item(
        Key={"clubId": club_id},
        UpdateExpression="SET isDisabled = :disabled, disabledAt = :disabledAt",
        ExpressionAttributeValues={
            ":disabled": True,
            ":disabledAt": now
        }
    )
    
    # Remove all users from Cognito groups associated with this club
    if COGNITO_USER_POOL_ID:
        groups = get_cognito_groups_for_club(club_id)
        total_removed = 0
        for group_name in groups:
            removed = remove_all_users_from_group(COGNITO_USER_POOL_ID, group_name)
            total_removed += removed
        
        print(f"Disabled club {club_id}: removed {total_removed} users from {len(groups)} groups")
    
    # Get updated club
    updated = get_club_by_id(club_id)
    return flask_success_response({"club": updated, "message": "Club disabled successfully"})


@app.route('/admin/clubs/<club_id>/enable', methods=['POST'])
@require_admin
@require_app_admin
def enable_club(club_id):
    """Re-enable a club (restricted to app-admins only). Note: Users must be manually re-added to groups."""
    
    # Get existing club
    existing = get_club_by_id(club_id)
    if not existing:
        return flask_error_response("Club not found", status_code=404)
    
    # Check if already enabled
    if not existing.get("isDisabled", False):
        return flask_error_response("Club is already enabled", status_code=400)
    
    # Update club to clear isDisabled flag
    table = get_table("ConsistencyTracker-Clubs")
    now = datetime.utcnow().isoformat() + "Z"
    update_expression = "SET isDisabled = :disabled, enabledAt = :enabledAt REMOVE disabledAt"
    table.update_item(
        Key={"clubId": club_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues={
            ":disabled": False,
            ":enabledAt": now
        }
    )
    
    # Get updated club
    updated = get_club_by_id(club_id)
    return flask_success_response({
        "club": updated,
        "message": "Club enabled successfully. Note: Users must be manually re-added to Cognito groups."
    })


# ============================================================================
# Team Management Endpoints
# ============================================================================

@app.route('/admin/teams', methods=['GET'])
@require_admin
@require_club
def list_teams():
    """List teams in coach's club."""
    club_id = g.club_id
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    teams = get_teams_by_club(club_id, active_only=active_only)
    
    # Format response
    team_list = []
    for team in teams:
        team_list.append({
            "teamId": team.get("teamId"),
            "teamName": team.get("teamName"),
            "clubId": team.get("clubId"),
            "settings": team.get("settings", {}),
            "isActive": team.get("isActive", True),
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
        "settings": body.get("settings", {
            "weekStartDay": "Monday",
            "autoAdvanceWeek": False,
            "scoringMethod": "points",
        }),
        "isActive": body.get("isActive", True),
        "createdAt": now,
    }
    
    table = get_table("ConsistencyTracker-Teams")
    table.put_item(Item=team)
    
    # Automatically create coach-{clubId}-{teamId} group in Cognito
    if COGNITO_USER_POOL_ID and cognito_client:
        group_name = f"coach-{club_id}-{new_team_id}"
        # Get club name for description
        club = get_club_by_id(club_id)
        club_name = club.get("clubName", "Unknown Club") if club else "Unknown Club"
        description = f"Coaches for team {team_name} in club {club_name}"
        
        # Create the group
        if create_cognito_group(COGNITO_USER_POOL_ID, group_name, description):
            # Automatically add the current user (club-admin who created the team) to the group
            event = get_api_gateway_event()
            user_info = extract_user_info_from_event(event)
            if user_info and user_info.get("username"):
                username = user_info.get("username")
                try:
                    cognito_client.admin_add_user_to_group(
                        UserPoolId=COGNITO_USER_POOL_ID,
                        Username=username,
                        GroupName=group_name
                    )
                    print(f"Added user {username} to coach group: {group_name}")
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    if error_code == 'InvalidParameterException' and 'already a member' in str(e):
                        # User already in group - that's fine
                        print(f"User {username} is already a member of {group_name}")
                    else:
                        print(f"Warning: Could not add user {username} to group {group_name}: {e}")
                        # Don't fail the request if group creation succeeded
    
    # Send email notification to club-admin
    try:
        event = get_api_gateway_event()
        user_info = extract_user_info_from_event(event)
        admin_email = user_info.get("email") if user_info else None
        
        if admin_email and validate_email_address(admin_email):
            club = get_club_by_id(club_id)
            club_name = club.get("clubName", "Unknown Club") if club else "Unknown Club"
            template = get_team_creation_template(team_name, club_name, new_team_id)
            send_templated_email([admin_email], template)
    except Exception as e:
        # Don't fail the request if email sending fails
        print(f"Warning: Failed to send team creation email: {e}")
    
    return flask_success_response({"team": team}, status_code=201)


@app.route('/admin/teams/validate-csv', methods=['POST'])
@require_admin
@require_club
def validate_teams_csv():
    """Validate teams CSV upload and return preview (no writes)."""
    rows, error = parse_csv_from_request()
    if error:
        return flask_error_response(error, status_code=400)

    preview: List[Dict[str, Any]] = []
    valid_rows = 0
    invalid_rows = 0

    for idx, row in enumerate(rows, start=2):  # header is row 1
        result = validate_team_csv_row(row, idx)
        if result["errors"]:
            invalid_rows += 1
        else:
            valid_rows += 1
        preview.append(result)

    return flask_success_response({
        "valid": invalid_rows == 0 and valid_rows > 0,
        "preview": preview,
        "summary": {
            "totalRows": len(preview),
            "validRows": valid_rows,
            "invalidRows": invalid_rows,
        },
    })


@app.route('/admin/teams/upload-csv', methods=['POST'])
@require_admin
@require_club
def upload_teams_csv():
    """
    Process validated team CSV rows.

    Expects JSON body:
      { "rows": [ { "row": int, "teamName": str, "teamId": str | null } ] }
    """
    club_id = g.club_id
    body = request.get_json() or {}
    items = body.get("rows") or []

    if not isinstance(items, list) or not items:
        return flask_error_response("Request body must include non-empty 'rows' array", status_code=400)

    created: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    table = get_table("ConsistencyTracker-Teams")
    now = datetime.utcnow().isoformat() + "Z"

    for item in items:
        try:
            row_num = int(item.get("row") or 0)
        except Exception:
            row_num = 0

        team_name = (item.get("teamName") or "").strip()
        explicit_team_id = (item.get("teamId") or "").strip()

        if not team_name:
            errors.append({"row": row_num, "error": "Missing teamName"})
            continue

        dup_info = check_team_duplicate(team_name, explicit_team_id, club_id)
        if dup_info.get("is_duplicate"):
            skipped.append({
                "teamName": team_name,
                "reason": dup_info.get("reason"),
                "row": row_num,
                "existingTeamId": dup_info.get("existingTeamId"),
            })
            continue

        new_team_id = explicit_team_id or str(uuid.uuid4())
        team_item = {
            "teamId": new_team_id,
            "clubId": club_id,
            "teamName": team_name,
            "settings": {
                "weekStartDay": "Monday",
                "autoAdvanceWeek": False,
                "scoringMethod": "points",
            },
            "createdAt": now,
        }

        try:
            table.put_item(Item=team_item)
            created.append({
                "teamId": new_team_id,
                "teamName": team_name,
                "row": row_num,
            })
        except Exception as e:
            errors.append({"row": row_num, "error": f"Failed to create team: {str(e)}"})

    return flask_success_response({
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "summary": {
            "total": len(items),
            "created": len(created),
            "skipped": len(skipped),
            "errors": len(errors),
        },
    })


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
    
    if "settings" in body:
        update_expression_parts.append("settings = :settings")
        expression_attribute_values[":settings"] = body["settings"]
    
    if "isActive" in body:
        update_expression_parts.append("isActive = :isActive")
        expression_attribute_values[":isActive"] = bool(body["isActive"])
    
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


@app.route('/admin/teams/<team_id>/activate', methods=['PUT'])
@require_admin
@require_club
def activate_team(team_id):
    """Activate a team."""
    club_id = g.club_id
    
    # Get existing team
    existing = get_team_by_id(team_id)
    if not existing:
        return flask_error_response("Team not found", status_code=404)
    
    # Validate team belongs to coach's club
    if existing.get("clubId") != club_id:
        return flask_error_response("Team not found or access denied", status_code=403)
    
    # Check if already active
    if existing.get("isActive", True):
        return flask_error_response("Team is already active", status_code=400)
    
    # Update isActive flag
    table = get_table("ConsistencyTracker-Teams")
    table.update_item(
        Key={"teamId": team_id},
        UpdateExpression="SET isActive = :isActive, updatedAt = :updatedAt",
        ExpressionAttributeValues={
            ":isActive": True,
            ":updatedAt": datetime.utcnow().isoformat() + "Z",
        },
        ReturnValues="ALL_NEW",
    )
    
    # Get updated team
    updated = get_team_by_id(team_id)
    return flask_success_response({"team": updated, "message": "Team activated successfully"})


@app.route('/admin/teams/<team_id>/deactivate', methods=['PUT'])
@require_admin
@require_club
def deactivate_team(team_id):
    """Deactivate a team."""
    club_id = g.club_id
    
    # Get existing team
    existing = get_team_by_id(team_id)
    if not existing:
        return flask_error_response("Team not found", status_code=404)
    
    # Validate team belongs to coach's club
    if existing.get("clubId") != club_id:
        return flask_error_response("Team not found or access denied", status_code=403)
    
    # Check if already inactive
    if not existing.get("isActive", True):
        return flask_error_response("Team is already inactive", status_code=400)
    
    # Update isActive flag
    table = get_table("ConsistencyTracker-Teams")
    table.update_item(
        Key={"teamId": team_id},
        UpdateExpression="SET isActive = :isActive, updatedAt = :updatedAt",
        ExpressionAttributeValues={
            ":isActive": False,
            ":updatedAt": datetime.utcnow().isoformat() + "Z",
        },
        ReturnValues="ALL_NEW",
    )
    
    # Get updated team
    updated = get_team_by_id(team_id)
    return flask_success_response({"team": updated, "message": "Team deactivated successfully"})


@app.route('/admin/teams/<team_id>/coaches', methods=['GET'])
@require_admin
@require_club
def list_team_coaches(team_id):
    """List all coaches for a team."""
    club_id = g.club_id
    
    # Get team and verify it belongs to the club
    team = get_team_by_id(team_id)
    if not team:
        return flask_error_response("Team not found", status_code=404)
    
    if team.get("clubId") != club_id:
        return flask_error_response("Team not found or access denied", status_code=403)
    
    # Get coaches from Cognito group
    coaches = get_coaches_for_team(team_id)
    
    return flask_success_response({"coaches": coaches, "total": len(coaches)})


@app.route('/admin/teams/<team_id>/coaches', methods=['POST'])
@require_admin
@require_club
def add_team_coach(team_id):
    """Add a coach to a team (create Cognito user + add to group + send invitation email)."""
    if not COGNITO_USER_POOL_ID or not cognito_client:
        return flask_error_response("Cognito is not configured for coach management", status_code=500)
    
    club_id = g.club_id
    body = request.get_json() or {}
    
    coach_email = (body.get("coachEmail") or "").strip()
    coach_password = (body.get("coachPassword") or "").strip()
    
    if not coach_email or not coach_password:
        return flask_error_response("coachEmail and coachPassword are required", status_code=400)
    
    if not validate_email_address(coach_email):
        return flask_error_response("Invalid coachEmail address", status_code=400)
    
    # Get team and verify it belongs to the club
    team = get_team_by_id(team_id)
    if not team:
        return flask_error_response("Team not found", status_code=404)
    
    if team.get("clubId") != club_id:
        return flask_error_response("Team not found or access denied", status_code=403)
    
    team_name = team.get("teamName", "Unknown Team")
    club = get_club_by_id(club_id)
    club_name = club.get("clubName", "Unknown Club") if club else "Unknown Club"
    
    # Build coach group name
    group_name = f"coach-{club_id}-{team_id}"
    
    # Ensure the group exists
    description = f"Coaches for team {team_name} in club {club_name}"
    create_cognito_group(COGNITO_USER_POOL_ID, group_name, description)
    
    # Create or update the Cognito user (coaches don't need custom:clubId, they're team-scoped)
    user_info = create_cognito_user(
        COGNITO_USER_POOL_ID,
        coach_email,
        coach_password,
        club_id=None,  # Coaches are team-scoped, not club-scoped
    )
    
    if not user_info:
        return flask_error_response("Failed to create or update coach user", status_code=500)
    
    # Add user to the coach group
    add_user_to_cognito_group(
        COGNITO_USER_POOL_ID,
        user_info["username"],
        group_name,
    )
    
    # Send invitation email
    email_status = None
    try:
        # Get login URL from environment or use default
        login_url = os.environ.get("ADMIN_LOGIN_URL", "https://app.repwarrior.net/admin/login")
        
        template = get_coach_invitation_template(
            coach_email,
            coach_email,
            coach_password,
            login_url,
            team_name,
            club_name
        )
        
        # Verify email if needed (for SES sandbox)
        verification_result = verify_email_identity(coach_email)
        if verification_result.get("verified"):
            send_templated_email([coach_email], template)
            email_status = {
                "sent": True,
                "message": "Coach invitation email sent successfully"
            }
            print(f"Coach invitation email sent to {coach_email}")
        else:
            email_status = {
                "sent": False,
                "message": f"Email verification required: {verification_result.get('error', 'Unknown error')}"
            }
            print(f"Warning: Could not send coach invitation email to {coach_email}: {verification_result.get('error')}")
    except Exception as e:
        email_status = {
            "sent": False,
            "message": f"Failed to send invitation email: {str(e)}"
        }
        print(f"Error sending coach invitation email to {coach_email}: {e}")
    
    return flask_success_response({
        "coach": {
            "email": coach_email,
            "username": user_info["username"],
            "status": user_info["status"]
        },
        "emailStatus": email_status,
        "message": "Coach added successfully"
    }, status_code=201)


@app.route('/admin/teams/<team_id>/coaches/<coach_email>', methods=['DELETE'])
@require_admin
@require_club
def remove_team_coach(team_id, coach_email):
    """Remove a coach from a team (remove from Cognito group)."""
    if not COGNITO_USER_POOL_ID or not cognito_client:
        return flask_error_response("Cognito is not configured for coach management", status_code=500)
    
    club_id = g.club_id
    
    # Get team and verify it belongs to the club
    team = get_team_by_id(team_id)
    if not team:
        return flask_error_response("Team not found", status_code=404)
    
    if team.get("clubId") != club_id:
        return flask_error_response("Team not found or access denied", status_code=403)
    
    # Build coach group name
    group_name = f"coach-{club_id}-{team_id}"
    
    # Remove user from group
    success = remove_user_from_cognito_group(
        COGNITO_USER_POOL_ID,
        coach_email,
        group_name
    )
    
    if not success:
        return flask_error_response("Failed to remove coach from team", status_code=500)
    
    return flask_success_response({
        "message": "Coach removed from team successfully"
    })


@app.route('/admin/teams/<team_id>/coaches/<coach_email>/activate', methods=['PUT'])
@require_admin
@require_club
def activate_team_coach(team_id, coach_email):
    """Activate a coach (enable Cognito user account)."""
    if not COGNITO_USER_POOL_ID or not cognito_client:
        return flask_error_response("Cognito is not configured for coach management", status_code=500)
    
    club_id = g.club_id
    
    # Get team and verify it belongs to the club
    team = get_team_by_id(team_id)
    if not team:
        return flask_error_response("Team not found", status_code=404)
    
    if team.get("clubId") != club_id:
        return flask_error_response("Team not found or access denied", status_code=403)
    
    # Verify coach is in the team's coach group
    coaches = get_coaches_for_team(team_id)
    coach = next((c for c in coaches if c.get('email') == coach_email), None)
    if not coach:
        return flask_error_response("Coach not found in this team", status_code=404)
    
    # Check if already enabled
    if coach.get('enabled', True):
        return flask_error_response("Coach is already active", status_code=400)
    
    # Enable the Cognito user
    username = coach.get('username', coach_email)
    success = enable_cognito_user(COGNITO_USER_POOL_ID, username)
    
    if not success:
        return flask_error_response("Failed to activate coach", status_code=500)
    
    # Get updated coach info
    coaches = get_coaches_for_team(team_id)
    updated_coach = next((c for c in coaches if c.get('email') == coach_email), None)
    
    return flask_success_response({
        "coach": updated_coach,
        "message": "Coach activated successfully"
    })


@app.route('/admin/teams/<team_id>/coaches/<coach_email>/deactivate', methods=['PUT'])
@require_admin
@require_club
def deactivate_team_coach(team_id, coach_email):
    """Deactivate a coach (disable Cognito user account)."""
    if not COGNITO_USER_POOL_ID or not cognito_client:
        return flask_error_response("Cognito is not configured for coach management", status_code=500)
    
    club_id = g.club_id
    
    # Get team and verify it belongs to the club
    team = get_team_by_id(team_id)
    if not team:
        return flask_error_response("Team not found", status_code=404)
    
    if team.get("clubId") != club_id:
        return flask_error_response("Team not found or access denied", status_code=403)
    
    # Verify coach is in the team's coach group
    coaches = get_coaches_for_team(team_id)
    coach = next((c for c in coaches if c.get('email') == coach_email), None)
    if not coach:
        return flask_error_response("Coach not found in this team", status_code=404)
    
    # Check if already disabled
    if not coach.get('enabled', True):
        return flask_error_response("Coach is already inactive", status_code=400)
    
    # Disable the Cognito user
    username = coach.get('username', coach_email)
    success = disable_cognito_user(COGNITO_USER_POOL_ID, username)
    
    if not success:
        return flask_error_response("Failed to deactivate coach", status_code=500)
    
    # Get updated coach info
    coaches = get_coaches_for_team(team_id)
    updated_coach = next((c for c in coaches if c.get('email') == coach_email), None)
    
    return flask_success_response({
        "coach": updated_coach,
        "message": "Coach deactivated successfully"
    })


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
    
    # Email is required for player accounts (needed for Cognito authentication)
    if not email or not validate_email_address(email):
        return flask_error_response("Valid email address is required for player accounts", status_code=400)
    
    # Generate temporary password
    temporary_password = generate_temporary_password()
    
    # Create Cognito user account
    cognito_user = None
    if COGNITO_USER_POOL_ID:
        try:
            cognito_user = create_cognito_user(
                COGNITO_USER_POOL_ID,
                email,
                temporary_password,
                club_id=club_id
            )
            print(f"Created Cognito user for player: {email}")
        except Exception as e:
            # If user already exists, that's okay - we'll just send invitation
            if 'UsernameExistsException' not in str(e) and 'already exists' not in str(e).lower():
                print(f"Warning: Failed to create Cognito user for player {email}: {e}")
                # Continue anyway - player can be created without Cognito account initially
    else:
        print("Warning: COGNITO_USER_POOL_ID not configured. Cannot create Cognito user.")
    
    # Create player record
    player_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    
    player = {
        "playerId": player_id,
        "name": name,
        "email": email,
        "clubId": club_id,  # Set from coach's club
        "teamId": team_id,  # From request body (validated above)
        "isActive": True,
        "createdAt": now,
    }
    
    table = get_table("ConsistencyTracker-Players")
    table.put_item(Item=player)
    
    # Send invitation email with temporary password
    try:
        team = get_team_by_id(team_id)
        club = get_club_by_id(club_id)
        team_name = team.get("teamName", "Unknown Team") if team else "Unknown Team"
        club_name = club.get("clubName", "Unknown Club") if club else "Unknown Club"
        
        # Construct login URL
        frontend_url = os.environ.get("FRONTEND_URL", "https://repwarrior.net")
        login_url = f"{frontend_url}/login"
        
        template = get_player_invitation_template(
            player_name=name,
            email=email,
            temporary_password=temporary_password,
            login_url=login_url,
            team_name=team_name,
            club_name=club_name
        )
        send_templated_email([email], template)
        print(f"Player invitation email sent to {email}")
    except Exception as e:
        # Don't fail the request if email sending fails
        print(f"Warning: Failed to send player invitation email: {e}")
    
    return flask_success_response({"player": player}, status_code=201)


@app.route('/admin/players/validate-csv', methods=['POST'])
@require_admin
@require_club
def validate_players_csv():
    """Validate players CSV upload and return preview (no writes)."""
    club_id = g.club_id
    rows, error = parse_csv_from_request()
    if error:
        return flask_error_response(error, status_code=400)

    preview: List[Dict[str, Any]] = []
    valid_rows = 0
    invalid_rows = 0

    for idx, row in enumerate(rows, start=2):  # header is row 1
        result = validate_player_csv_row(row, idx, club_id)
        if result["errors"]:
            invalid_rows += 1
        else:
            valid_rows += 1
        preview.append(result)

    return flask_success_response({
        "valid": invalid_rows == 0 and valid_rows > 0,
        "preview": preview,
        "summary": {
            "totalRows": len(preview),
            "validRows": valid_rows,
            "invalidRows": invalid_rows,
        },
    })


@app.route('/admin/players/upload-csv', methods=['POST'])
@require_admin
@require_club
def upload_players_csv():
    """
    Process validated player CSV rows.

    Expects JSON body:
      { "rows": [ { \"row\": int, \"name\": str, \"email\": str | null, \"teamId\": str, \"playerId\": str | null } ] }
    """
    club_id = g.club_id
    body = request.get_json() or {}
    items = body.get("rows") or []

    if not isinstance(items, list) or not items:
        return flask_error_response("Request body must include non-empty 'rows' array", status_code=400)

    created: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    table = get_table("ConsistencyTracker-Players")

    for item in items:
        try:
            row_num = int(item.get("row") or 0)
        except Exception:
            row_num = 0

        name = (item.get("name") or "").strip()
        email = (item.get("email") or "").strip()
        team_id = (item.get("teamId") or "").strip()
        explicit_player_id = (item.get("playerId") or "").strip()

        if not name:
            errors.append({"row": row_num, "error": "Missing name"})
            continue
        if not team_id:
            errors.append({"row": row_num, "error": "Missing teamId"})
            continue

        # Ensure team belongs to this club
        team = get_team_by_id(team_id)
        if not team or team.get("clubId") != club_id:
            errors.append({"row": row_num, "error": "Team not found or access denied"})
            continue

        dup_info = check_player_duplicate(name, team_id, explicit_player_id, club_id)
        if dup_info.get("is_duplicate"):
            skipped.append({
                "name": name,
                "teamId": team_id,
                "reason": dup_info.get("reason"),
                "row": row_num,
                "existingPlayerId": dup_info.get("existingPlayerId"),
            })
            continue

        # Email is required for player accounts (needed for Cognito authentication)
        if not email or not validate_email_address(email):
            errors.append({"row": row_num, "error": "Valid email address is required for player accounts"})
            continue

        # Generate temporary password
        temporary_password = generate_temporary_password()
        
        # Create Cognito user account
        if COGNITO_USER_POOL_ID:
            try:
                cognito_user = create_cognito_user(
                    COGNITO_USER_POOL_ID,
                    email,
                    temporary_password,
                    club_id=club_id
                )
                if cognito_user:
                    print(f"Created Cognito user for player from CSV: {email}")
            except Exception as e:
                # If user already exists, that's okay
                if 'UsernameExistsException' not in str(e) and 'already exists' not in str(e).lower():
                    print(f"Warning: Failed to create Cognito user for player {email} from CSV: {e}")
                    # Continue anyway - player can be created without Cognito account initially

        # Create player record
        player_id = explicit_player_id or str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        player_item = {
            "playerId": player_id,
            "name": name,
            "email": email,
            "clubId": club_id,
            "teamId": team_id,
            "isActive": True,
            "createdAt": now,
        }

        try:
            table.put_item(Item=player_item)
            
            # Send invitation email if email is valid
            try:
                team = get_team_by_id(team_id) if team_id else None
                club = get_club_by_id(club_id) if club_id else None
                team_name = team.get("teamName", "Unknown Team") if team else "Unknown Team"
                club_name = club.get("clubName", "Unknown Club") if club else "Unknown Club"
                
                frontend_url = os.environ.get("FRONTEND_URL", "https://repwarrior.net")
                login_url = f"{frontend_url}/login"
                
                template = get_player_invitation_template(
                    player_name=name,
                    email=email,
                    temporary_password=temporary_password,
                    login_url=login_url,
                    team_name=team_name,
                    club_name=club_name
                )
                send_templated_email([email], template)
                print(f"Invitation email sent to {email} from CSV upload")
            except Exception as e:
                print(f"Warning: Failed to send invitation email to {email} from CSV: {e}")
            
            created.append({
                "playerId": player_id,
                "name": name,
                "teamId": team_id,
                "row": row_num,
            })
        except Exception as e:
            errors.append({"row": row_num, "error": f"Failed to create player: {str(e)}"})

    return flask_success_response({
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "summary": {
            "total": len(items),
            "created": len(created),
            "skipped": len(skipped),
            "errors": len(errors),
        },
    })


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
    
    if "isActive" in body:
        update_expression_parts.append("isActive = :isActive")
        expression_attribute_values[":isActive"] = bool(body["isActive"])
    
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
    """Toggle player activation status (soft delete/restore)."""
    # Get existing player (already validated by decorator)
    existing = g.current_resource
    
    # Determine new status based on current status
    current_status = existing.get("isActive", True)
    new_status = not current_status
    
    # Update isActive flag
    table = get_table("ConsistencyTracker-Players")
    table.update_item(
        Key={"playerId": player_id},
        UpdateExpression="SET isActive = :isActive, updatedAt = :updatedAt",
        ExpressionAttributeValues={
            ":isActive": new_status,
            ":updatedAt": datetime.utcnow().isoformat() + "Z",
        },
        ReturnValues="ALL_NEW",
    )
    
    action = "activated" if new_status else "deactivated"
    return flask_success_response({"message": f"Player {action} successfully"})


@app.route('/admin/players/<player_id>/invite', methods=['POST'])
@require_admin
@require_club
@require_resource_access('player', 'player_id', get_player_by_id)
def invite_player(player_id):
    """Send invitation email to player (create Cognito user if needed)."""
    # Get existing player (already validated by decorator)
    player = g.current_resource
    
    email = player.get("email")
    if not email:
        return flask_error_response("Player does not have an email address", status_code=400)
    
    if not validate_email_address(email):
        return flask_error_response("Player email address is invalid", status_code=400)
    
    # Get team and club info
    team_id = player.get("teamId")
    club_id = player.get("clubId")
    player_name = player.get("name", "Player")
    
    # Generate temporary password
    temporary_password = generate_temporary_password()
    
    # Create or update Cognito user account
    if COGNITO_USER_POOL_ID:
        try:
            cognito_user = create_cognito_user(
                COGNITO_USER_POOL_ID,
                email,
                temporary_password,
                club_id=club_id
            )
            if cognito_user:
                print(f"Cognito user ready for player: {email}")
            else:
                print(f"Warning: Could not create/update Cognito user for {email}")
        except Exception as e:
            print(f"Warning: Error creating Cognito user for player {email}: {e}")
            # Continue anyway - we'll still try to send email
    else:
        print("Warning: COGNITO_USER_POOL_ID not configured. Cannot create Cognito user.")
    
    try:
        team = get_team_by_id(team_id) if team_id else None
        club = get_club_by_id(club_id) if club_id else None
        team_name = team.get("teamName", "Unknown Team") if team else "Unknown Team"
        club_name = club.get("clubName", "Unknown Club") if club else "Unknown Club"
        
        # Construct login URL
        frontend_url = os.environ.get("FRONTEND_URL", "https://repwarrior.net")
        login_url = f"{frontend_url}/login"
        
        template = get_player_invitation_template(
            player_name=player_name,
            email=email,
            temporary_password=temporary_password,
            login_url=login_url,
            team_name=team_name,
            club_name=club_name
        )
        send_templated_email([email], template)
        
        return flask_success_response({"success": True, "message": "Invitation sent successfully"})
    except Exception as e:
        print(f"Error sending player invitation email: {e}")
        return flask_error_response(f"Failed to send invitation email: {str(e)}", status_code=500)


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

