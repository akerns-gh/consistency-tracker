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


def get_team_id_from_user(event: Dict[str, Any]) -> Optional[str]:
    """
    Extract teamId from authenticated user (future: from user attributes or groups).

    For now, returns None (single team mode).
    In multi-tenant mode, this would extract teamId from user attributes.

    Args:
        event: API Gateway Lambda event

    Returns:
        teamId or None
    """
    # TODO: In Phase 7 (multi-tenancy), extract teamId from:
    # - User attributes (custom:teamId)
    # - User groups (team-specific groups)
    # - Default team for now
    return None  # Single team mode for now

