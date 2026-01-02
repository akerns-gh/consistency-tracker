"""
Flask-specific authentication and authorization utilities.

Provides decorators and helpers for Flask applications that integrate with
existing auth_utils functions and API Gateway Cognito authorizer.
"""

from functools import wraps
from flask import request, g, abort, jsonify
from typing import Optional, Dict, Any
from shared.auth_utils import (
    extract_user_info_from_event,
    extract_user_info_from_jwt_token,
    verify_admin_role,
    verify_app_admin_role,
    get_club_id_from_user,
    get_team_ids_from_user,
)
# Import get_club_by_id lazily to avoid import issues at module load time


def get_api_gateway_event() -> Dict[str, Any]:
    """
    Extract the original API Gateway event from Flask request.
    
    serverless-wsgi stores the original event in request.environ.
    
    Returns:
        API Gateway event dictionary
    """
    return request.environ.get('serverless.event', {})


def require_admin(f):
    """
    Decorator to require admin authentication.
    
    Validates that the user is authenticated and has admin role.
    Stores user info in Flask's g object for use in route handlers.
    
    Usage:
        @app.route('/admin/endpoint')
        @require_admin
        def my_endpoint():
            # g.current_user is available
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if event exists in request.environ before retrieving
        event_exists = 'serverless.event' in request.environ
        event = get_api_gateway_event()
        user_info = extract_user_info_from_event(event)
        
        # Fallback: if no user info from event, try to extract from Authorization header
        if not user_info:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove 'Bearer ' prefix
                user_info = extract_user_info_from_jwt_token(token)
                print(f"DEBUG require_admin: Extracted user_info from Authorization header")
        
        if not user_info:
            abort(401, description="Authentication required")
        
        # Ensure event has authorizer context for verify_admin_role
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
            groups_raw = user_info.get("groups", [])
            if isinstance(groups_raw, str):
                groups = [g.strip() for g in groups_raw.split(",") if g.strip()]
            elif isinstance(groups_raw, list):
                groups = groups_raw
            else:
                groups = []
            
            claims["cognito:username"] = user_info.get("username")
            claims["email"] = user_info.get("email")
            claims["sub"] = user_info.get("user_id")
            claims["cognito:groups"] = groups
            # Include custom attributes if present
            if user_info.get("custom:clubId"):
                claims["custom:clubId"] = user_info.get("custom:clubId")
            if user_info.get("custom:teamIds"):
                claims["custom:teamIds"] = user_info.get("custom:teamIds")
            print(f"DEBUG require_admin: Created authorizer claims from user_info, groups: {groups}, clubId: {claims.get('custom:clubId')}")
            
            # Store modified event back to request.environ if it wasn't there originally
            if not event_exists:
                request.environ['serverless.event'] = event
        
        if not verify_admin_role(event):
            abort(403, description="Admin access required")
        
        # Check verification status for coaches and club-admins
        email = user_info.get("email")
        if email:
            # Lazy import to avoid circular dependencies
            from shared.db_utils import get_coach_by_email, get_club_admin_by_email
            
            # Check if user is a coach
            coach = get_coach_by_email(email)
            if coach:
                verification_status = coach.get("verificationStatus")
                if verification_status == "pending":
                    abort(403, description="Account verification pending. Please complete email verification and password setup.")
            
            # Check if user is a club-admin (only if not a coach)
            if not coach:
                admin = get_club_admin_by_email(email)
                if admin:
                    verification_status = admin.get("verificationStatus")
                    if verification_status == "pending":
                        abort(403, description="Account verification pending. Please complete email verification and password setup.")
        
        # Store user info in Flask's g object
        g.current_user = user_info
        g.club_id = get_club_id_from_user(event)
        g.team_ids = get_team_ids_from_user(event)
        g.is_app_admin = verify_app_admin_role(event)  # Set app-admin flag
        
        return f(*args, **kwargs)
    return decorated_function


def require_app_admin(f):
    """
    Decorator to require app-admin authentication (platform-wide admin).
    
    Validates that the user is authenticated and has app-admin role.
    Must be used after @require_admin.
    
    Usage:
        @app.route('/admin/clubs', methods=['POST'])
        @require_admin
        @require_app_admin
        def create_club():
            # Only app-admins can access this
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        event = get_api_gateway_event()
        
        if not verify_app_admin_role(event):
            abort(403, description="App-admin access required")
        
        # Ensure is_app_admin is set
        g.is_app_admin = True
        
        return f(*args, **kwargs)
    return decorated_function


def require_club(f):
    """
    Decorator to require club association.
    
    Must be used after @require_admin. Validates that the user
    is associated with a club and the club is not disabled.
    
    Usage:
        @app.route('/admin/endpoint')
        @require_admin
        @require_club
        def my_endpoint():
            # g.club_id is available
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'club_id') or not g.club_id:
            abort(403, description="User not associated with a club")
        
        # Check if club is disabled (app-admins can still access disabled clubs)
        is_app_admin = getattr(g, 'is_app_admin', False)
        if not is_app_admin:
            try:
                # Lazy import to avoid import issues at module load time
                from shared.db_utils import get_club_by_id
                club = get_club_by_id(g.club_id)
                if club and club.get("isDisabled", False):
                    abort(403, description="Club is disabled")
            except Exception as e:
                # If we can't check club status, allow access (fail open)
                # This prevents blocking access due to transient DB issues
                print(f"Warning: Could not check club disabled status: {e}")
        
        return f(*args, **kwargs)
    return decorated_function


def require_club_access(club_id_param: str = 'club_id'):
    """
    Decorator factory to verify user can access a specific club.
    
    Validates that the requested club_id matches the user's club_id
    and the club is not disabled (unless user is app-admin).
    Must be used after @require_admin and @require_club.
    
    Args:
        club_id_param: Name of the route parameter containing club_id
    
    Usage:
        @app.route('/admin/clubs/<club_id>')
        @require_admin
        @require_club
        @require_club_access('club_id')
        def get_club(club_id):
            # club_id has been validated
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            requested_club_id = kwargs.get(club_id_param)
            user_club_id = g.club_id
            
            if requested_club_id and requested_club_id != user_club_id:
                abort(403, description="Club not found or access denied")
            
            # Check if club is disabled (app-admins can still access disabled clubs)
            is_app_admin = getattr(g, 'is_app_admin', False)
            if not is_app_admin and requested_club_id:
                try:
                    # Lazy import to avoid import issues at module load time
                    from shared.db_utils import get_club_by_id
                    club = get_club_by_id(requested_club_id)
                    if club and club.get("isDisabled", False):
                        abort(403, description="Club is disabled")
                except Exception as e:
                    # If we can't check club status, allow access (fail open)
                    # This prevents blocking access due to transient DB issues
                    print(f"Warning: Could not check club disabled status: {e}")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_resource_access(resource_type: str, id_param: str, resource_getter):
    """
    Decorator factory to verify user owns a resource.
    
    Fetches the resource and validates that it belongs to the user's club.
    Stores the validated resource in g.current_resource for reuse.
    
    Args:
        resource_type: Type of resource (for error messages)
        id_param: Name of the route parameter containing resource ID
        resource_getter: Function that takes resource_id and returns resource dict
    
    Usage:
        @app.route('/admin/players/<player_id>')
        @require_admin
        @require_club
        @require_resource_access('player', 'player_id', get_player_by_id)
        def update_player(player_id):
            # g.current_resource is available and validated
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            resource_id = kwargs.get(id_param)
            club_id = g.club_id
            
            if not resource_id:
                abort(400, description=f"Missing {id_param} parameter")
            
            # Fetch resource
            resource = resource_getter(resource_id)
            if not resource:
                abort(404, description=f"{resource_type.capitalize()} not found")
            
            # Validate ownership
            resource_club_id = resource.get("clubId")
            if resource_club_id != club_id:
                abort(403, description=f"{resource_type.capitalize()} not found or access denied")
            
            # Store validated resource
            g.current_resource = resource
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def flask_success_response(data: Any = None, status_code: int = 200):
    """
    Create a successful Flask response matching existing API format.
    
    Args:
        data: Response data (will be JSON serialized)
        status_code: HTTP status code (default: 200)
    
    Returns:
        Flask JSON response
    """
    response_body = {"success": True}
    if data is not None:
        response_body["data"] = data
    
    return jsonify(response_body), status_code


def flask_error_response(message: str, status_code: int = 400, error_code: Optional[str] = None):
    """
    Create an error Flask response matching existing API format.
    
    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        error_code: Optional error code for client handling
    
    Returns:
        Flask JSON response
    """
    response_body = {
        "success": False,
        "error": {
            "message": message,
        },
    }
    
    if error_code:
        response_body["error"]["code"] = error_code
    
    return jsonify(response_body), status_code

