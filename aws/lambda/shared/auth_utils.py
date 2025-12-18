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

# Admin group name
ADMIN_GROUP_NAME = "Admins"


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
    user_info = {
        "username": claims.get("cognito:username") or claims.get("sub"),
        "email": claims.get("email"),
        "user_id": claims.get("sub"),
        "groups": claims.get("cognito:groups", []),
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
        user_info = {
            "username": decoded.get("cognito:username") or decoded.get("sub"),
            "email": decoded.get("email"),
            "user_id": decoded.get("sub"),
            "groups": decoded.get("cognito:groups", []),
        }
        
        print(f"DEBUG extract_user_info_from_jwt_token: Extracted user info - email: {user_info.get('email')}, username: {user_info.get('username')}")
        return user_info
    except Exception as e:
        import traceback
        print(f"ERROR extract_user_info_from_jwt_token: Failed to decode token: {e}")
        traceback.print_exc()
        return None


def verify_admin_role(event: Dict[str, Any]) -> bool:
    """
    Verify that the authenticated user has admin role.

    Args:
        event: API Gateway Lambda event

    Returns:
        True if user is admin, False otherwise
    """
    user_info = extract_user_info_from_event(event)
    
    if not user_info:
        return False
    
    groups = user_info.get("groups", [])
    return ADMIN_GROUP_NAME in groups


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
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})
    claims = authorizer.get("claims", {})
    
    if not claims:
        return None
    
    # Try custom:clubId attribute first
    club_id = claims.get("custom:clubId")
    if club_id:
        return club_id
    
    # Try extracting from group name (e.g., "club-{clubId}-admins")
    user_info = extract_user_info_from_event(event)
    if user_info:
        groups = user_info.get("groups", [])
        for group in groups:
            if group.startswith("club-") and group.endswith("-admins"):
                # Extract clubId from group name
                club_id = group.replace("club-", "").replace("-admins", "")
                return club_id
            elif group.startswith("club-") and group.endswith("-coaches"):
                # Extract clubId from group name
                club_id = group.replace("club-", "").replace("-coaches", "")
                return club_id
    
    return None


def get_team_ids_from_user(event: Dict[str, Any]) -> List[str]:
    """
    Extract teamIds from authenticated user (from JWT token claims).

    Args:
        event: API Gateway Lambda event

    Returns:
        List of teamIds user has access to
    """
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})
    claims = authorizer.get("claims", {})
    
    if not claims:
        return []
    
    # Try custom:teamIds (comma-separated)
    team_ids_str = claims.get("custom:teamIds", "")
    if team_ids_str:
        return [tid.strip() for tid in team_ids_str.split(",") if tid.strip()]
    
    # Try extracting from group names (e.g., "team-{teamId}-coaches")
    user_info = extract_user_info_from_event(event)
    if not user_info:
        return []
    
    groups = user_info.get("groups", [])
    team_ids = []
    for group in groups:
        if group.startswith("team-") and group.endswith("-coaches"):
            team_id = group.replace("team-", "").replace("-coaches", "")
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

