"""
Authentication and authorization utilities for Lambda functions.
"""

import os
import json
import base64
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError

try:
    import boto3
    from jose import jwt, jwk
    from jose.utils import base64url_decode
except ImportError:
    # Fallback if jose is not available
    jwt = None
    jwk = None
    boto3 = None

# Cognito configuration (will be set via environment variables)
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")
COGNITO_REGION = os.environ.get("COGNITO_REGION", "us-east-2")

# Admin group names
APP_ADMIN_GROUP_NAME = "app-admin"  # Platform-wide admins (can create clubs)
# Note: Dynamic groups are created automatically:
# - club-{clubName}-admins: Created when app-admin creates a club (uses sanitized club name)
# - coach-{clubId}-{teamId}: Created when club-admin creates a team


def get_cognito_public_keys(user_pool_id: str, region: str) -> Dict[str, Any]:
    """
    Get Cognito public keys for JWT verification.

    Args:
        user_pool_id: Cognito User Pool ID
        region: AWS region

    Returns:
        Dictionary of public keys
    """
    if not boto3:
        return {}

    try:
        cognito_client = boto3.client("cognito-idp", region_name=region)
        response = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
        issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        
        # Get JWKS from well-known endpoint
        import urllib.request
        jwks_url = f"{issuer}/.well-known/jwks.json"
        with urllib.request.urlopen(jwks_url) as response:
            jwks = json.loads(response.read())
        
        return jwks
    except Exception as e:
        print(f"Error getting Cognito public keys: {e}")
        return {}


def extract_user_info_from_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract user information from API Gateway event (Cognito authorizer context).

    Args:
        event: API Gateway Lambda event

    Returns:
        Dictionary with user info (username, email, groups) or None if not authenticated
    """
    # Check for Cognito authorizer context
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})
    
    # Cognito authorizer puts claims in the authorizer context
    claims = authorizer.get("claims", {})
    
    if not claims:
        return None
    
    # Extract user information from JWT claims
    # Handle groups - can be a list or a string (comma-separated)
    groups_raw = claims.get("cognito:groups", [])
    if isinstance(groups_raw, str):
        # If groups is a string, split by comma and strip whitespace
        groups = [g.strip() for g in groups_raw.split(",") if g.strip()]
    elif isinstance(groups_raw, list):
        groups = groups_raw
    else:
        groups = []
    
    user_info = {
        "username": claims.get("cognito:username") or claims.get("sub"),
        "email": claims.get("email"),
        "user_id": claims.get("sub"),
        "groups": groups,
    }
    
    return user_info


def extract_user_info_from_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract user information from a JWT token by decoding it (without verification).
    
    WARNING: This does NOT verify the token signature. Use only when token has been
    validated by API Gateway authorizer or another trusted source.
    
    Args:
        token: JWT token string (without 'Bearer ' prefix)
    
    Returns:
        Dictionary with user info (username, email, groups) or None if token is invalid
    """
    if not token:
        print(f"DEBUG extract_user_info_from_jwt_token: No token provided")
        return None
    
    if not jwt:
        print(f"DEBUG extract_user_info_from_jwt_token: JWT library not available")
        return None
    
    try:
        print(f"DEBUG extract_user_info_from_jwt_token: Attempting to decode token (length: {len(token)})")
        # Decode without verification (since API Gateway would have verified it if authorizer was used)
        # In production, you should verify the signature using Cognito public keys
        decoded = jwt.get_unverified_claims(token)
        print(f"DEBUG extract_user_info_from_jwt_token: Successfully decoded token. Keys: {list(decoded.keys())[:10]}")
        
        # Extract user information from JWT claims
        # Handle groups - can be a list or a string (comma-separated)
        groups_raw = decoded.get("cognito:groups", [])
        if isinstance(groups_raw, str):
            # If groups is a string, split by comma and strip whitespace
            groups = [g.strip() for g in groups_raw.split(",") if g.strip()]
        elif isinstance(groups_raw, list):
            groups = groups_raw
        else:
            groups = []
        
        user_info = {
            "username": decoded.get("cognito:username") or decoded.get("sub"),
            "email": decoded.get("email"),
            "user_id": decoded.get("sub"),
            "groups": groups,
        }
        
        print(f"DEBUG extract_user_info_from_jwt_token: Extracted user info - email: {user_info.get('email')}, username: {user_info.get('username')}, groups: {groups}")
        return user_info
    except Exception as e:
        import traceback
        print(f"ERROR extract_user_info_from_jwt_token: Failed to decode token: {e}")
        traceback.print_exc()
        return None


def verify_app_admin_role(event: Dict[str, Any]) -> bool:
    """
    Verify that the authenticated user has app-admin role (platform-wide admin).

    Args:
        event: API Gateway Lambda event

    Returns:
        True if user is app-admin, False otherwise
    """
    user_info = extract_user_info_from_event(event)
    
    if not user_info:
        return False
    
    groups = user_info.get("groups", [])
    # Check for exact app-admin group match
    return APP_ADMIN_GROUP_NAME in groups


def verify_admin_role(event: Dict[str, Any]) -> bool:
    """
    Verify that the authenticated user has admin role (app-admin, club-admin, or coach).

    Args:
        event: API Gateway Lambda event

    Returns:
        True if user is app-admin, club-{clubName}-admins, or coach-{clubId}-{teamId}, False otherwise
    """
    import re
    
    user_info = extract_user_info_from_event(event)
    
    if not user_info:
        print("DEBUG verify_admin_role: No user_info from event")
        return False
    
    groups = user_info.get("groups", [])
    print(f"DEBUG verify_admin_role: Checking groups: {groups}")
    
    # Check for app-admin (exact match)
    if APP_ADMIN_GROUP_NAME in groups:
        print(f"DEBUG verify_admin_role: Found app-admin group")
        return True
    
    # Check for club-{clubName}-admins pattern (new format with sanitized club name)
    # Matches: club-{alphanumeric, underscores, hyphens}-admins
    club_admin_pattern = re.compile(r'^club-([a-z0-9_-]+)-admins$')
    for group in groups:
        print(f"DEBUG verify_admin_role: Checking group '{group}' against club-admin pattern")
        if club_admin_pattern.match(group):
            print(f"DEBUG verify_admin_role: Group '{group}' matches club-admin pattern")
            return True
    
    # Check for coach-{clubId}-{teamId} pattern
    coach_pattern = re.compile(r'^coach-([a-f0-9-]+)-([a-f0-9-]+)$')
    for group in groups:
        print(f"DEBUG verify_admin_role: Checking group '{group}' against coach pattern")
        if coach_pattern.match(group):
            print(f"DEBUG verify_admin_role: Group '{group}' matches coach pattern")
            return True
    
    print(f"DEBUG verify_admin_role: No matching admin groups found")
    return False


def require_admin(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Require admin role, raise error if not admin.

    Args:
        event: API Gateway Lambda event

    Returns:
        User info dictionary if admin

    Raises:
        Exception: If user is not authenticated or not admin
    """
    user_info = extract_user_info_from_event(event)
    
    if not user_info:
        raise Exception("Authentication required")
    
    if not verify_admin_role(event):
        raise Exception("Admin access required")
    
    return user_info


def get_club_id_from_user(event: Dict[str, Any]) -> Optional[str]:
    """
    Extract clubId from authenticated user (from JWT token claims).

    Args:
        event: API Gateway Lambda event

    Returns:
        clubId or None
    """
    import re
    
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})
    claims = authorizer.get("claims", {})
    
    if not claims:
        return None
    
    # Try custom:clubId attribute first (preferred)
    club_id = claims.get("custom:clubId")
    if club_id:
        return club_id
    
    # Try extracting from group names using pattern matching
    # Note: With new format (club-{name}-admins), we can't extract club ID from group name
    # So we rely on custom:clubId claim (checked above) or coach groups
    user_info = extract_user_info_from_event(event)
    if user_info:
        groups = user_info.get("groups", [])
        
        # Pattern for coach-{clubId}-{teamId} (extract clubId)
        coach_pattern = re.compile(r'^coach-([a-f0-9-]+)-([a-f0-9-]+)$')
        for group in groups:
            match = coach_pattern.match(group)
            if match:
                return match.group(1)  # Return clubId from coach group
    
    return None


def get_team_ids_from_user(event: Dict[str, Any]) -> List[str]:
    """
    Extract teamIds from authenticated user (from JWT token claims).

    Args:
        event: API Gateway Lambda event

    Returns:
        List of teamIds user has access to
    """
    import re
    
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})
    claims = authorizer.get("claims", {})
    
    if not claims:
        return []
    
    # Try custom:teamIds (comma-separated) - preferred
    team_ids_str = claims.get("custom:teamIds", "")
    if team_ids_str:
        return [tid.strip() for tid in team_ids_str.split(",") if tid.strip()]
    
    # Try extracting from group names using pattern matching
    # Pattern: coach-{clubId}-{teamId}
    user_info = extract_user_info_from_event(event)
    if not user_info:
        return []
    
    groups = user_info.get("groups", [])
    team_ids = []
    coach_pattern = re.compile(r'^coach-([a-f0-9-]+)-([a-f0-9-]+)$')
    for group in groups:
        match = coach_pattern.match(group)
        if match:
            team_id = match.group(2)  # Extract teamId from coach group
            if team_id not in team_ids:
                team_ids.append(team_id)
    
    return team_ids


def get_team_id_from_user(event: Dict[str, Any]) -> Optional[str]:
    """
    Extract teamId from authenticated user (deprecated - use get_club_id_from_user).

    For backward compatibility, returns None.
    In club-based multi-tenancy, use get_club_id_from_user() instead.

    Args:
        event: API Gateway Lambda event

    Returns:
        teamId or None
    """
    # Deprecated: Use get_club_id_from_user() for club-based multi-tenancy
    return None

