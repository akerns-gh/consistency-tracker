"""
Lambda function: Admin club management endpoints
- GET /admin/clubs - List clubs (for super-admin or multi-club coaches)
- POST /admin/clubs - Create new club (restricted)
- GET /admin/clubs/{clubId} - Get club details
- PUT /admin/clubs/{clubId} - Update club settings
"""

import json
import uuid
from datetime import datetime
from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin, get_club_id_from_user
from shared.db_utils import (
    get_table,
    get_club_by_id,
)


def lambda_handler(event, context):
    """Handle admin club management requests."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Require admin authentication
        user_info = require_admin(event)
        user_club_id = get_club_id_from_user(event)
        
        http_method = event.get("httpMethod")
        path_params = event.get("pathParameters") or {}
        club_id = path_params.get("clubId")
        
        table = get_table("ConsistencyTracker-Clubs")
        
        if http_method == "GET":
            if club_id:
                # Get specific club
                club = get_club_by_id(club_id)
                if not club:
                    return error_response("Club not found", status_code=404)
                
                # Validate user has access to this club
                if user_club_id and club_id != user_club_id:
                    return error_response("Club not found or access denied", status_code=403)
                
                return success_response({"club": club})
            else:
                # List clubs (for now, only return user's club)
                # In future, could support multi-club coaches
                if user_club_id:
                    club = get_club_by_id(user_club_id)
                    clubs = [club] if club else []
                else:
                    clubs = []
                
                return success_response({"clubs": clubs, "total": len(clubs)})
        
        elif http_method == "POST":
            # Create new club (restricted - for now, allow if user doesn't have a club)
            if user_club_id:
                return error_response("User already associated with a club. Club creation restricted.", status_code=403)
            
            try:
                body = json.loads(event.get("body", "{}"))
            except json.JSONDecodeError:
                return error_response("Invalid JSON in request body", status_code=400)
            
            club_name = body.get("clubName")
            
            if not club_name:
                return error_response("Missing required field: clubName", status_code=400)
            
            # Create club
            new_club_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat() + "Z"
            
            club = {
                "clubId": new_club_id,
                "clubName": club_name,
                "createdAt": now,
                "settings": body.get("settings", {}),
            }
            
            table.put_item(Item=club)
            
            return success_response({"club": club}, status_code=201)
        
        elif http_method == "PUT":
            # Update club settings
            if not club_id:
                return error_response("Missing clubId parameter", status_code=400)
            
            # Validate user has access to this club
            if user_club_id and club_id != user_club_id:
                return error_response("Club not found or access denied", status_code=403)
            
            try:
                body = json.loads(event.get("body", "{}"))
            except json.JSONDecodeError:
                return error_response("Invalid JSON in request body", status_code=400)
            
            # Get existing club
            existing = get_club_by_id(club_id)
            if not existing:
                return error_response("Club not found", status_code=404)
            
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
                return error_response("No fields to update", status_code=400)
            
            # Add updatedAt
            update_expression_parts.append("updatedAt = :updatedAt")
            expression_attribute_values[":updatedAt"] = datetime.utcnow().isoformat() + "Z"
            
            # Perform update
            table.update_item(
                Key={"clubId": club_id},
                UpdateExpression="SET " + ", ".join(update_expression_parts),
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW",
            )
            
            # Get updated club
            updated = get_club_by_id(club_id)
            return success_response({"club": updated})
        
        else:
            return error_response(f"Method not allowed: {http_method}", status_code=405)
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/clubs: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

