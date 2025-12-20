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
    verify_admin_role,
    verify_app_admin_role,
    get_club_id_from_user,
    get_team_ids_from_user,
)


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
        event = get_api_gateway_event()
        user_info = extract_user_info_from_event(event)
        
        if not user_info:
            abort(401, description="Authentication required")
        
        if not verify_admin_role(event):
            abort(403, description="Admin access required")
        
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
    is associated with a club.
    
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
        return f(*args, **kwargs)
    return decorated_function


def require_club_access(club_id_param: str = 'club_id'):
    """
    Decorator factory to verify user can access a specific club.
    
    Validates that the requested club_id matches the user's club_id.
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

