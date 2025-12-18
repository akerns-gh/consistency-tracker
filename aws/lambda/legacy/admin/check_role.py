"""
Lambda function: GET /admin/check-role
Verify user's admin role (for frontend navigation).
"""

from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import extract_user_info_from_event, verify_admin_role


def lambda_handler(event, context):
    """Handle GET /admin/check-role request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Extract user info from event (Cognito authorizer)
        user_info = extract_user_info_from_event(event)
        
        if not user_info:
            return error_response("Authentication required", status_code=401)
        
        # Check if user is admin
        is_admin = verify_admin_role(event)
        
        # Build response
        response_data = {
            "authenticated": True,
            "isAdmin": is_admin,
            "user": {
                "username": user_info.get("username"),
                "email": user_info.get("email"),
            },
        }
        
        return success_response(response_data)
        
    except Exception as e:
        print(f"Error in check_role: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

