"""
Lambda function: PUT /admin/content/{contentId}/publish
Publish/unpublish content page.
"""

import json
from datetime import datetime
from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin, get_club_id_from_user
from shared.db_utils import get_table


def lambda_handler(event, context):
    """Handle PUT /admin/content/{contentId}/publish request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Require admin authentication
        user_info = require_admin(event)
        club_id = get_club_id_from_user(event)
        
        if not club_id:
            return error_response("User not associated with a club", status_code=403)
        
        user_email = user_info.get("email") or user_info.get("username")
        
        path_params = event.get("pathParameters") or {}
        content_id = path_params.get("contentId") or path_params.get("pageId")
        
        if not content_id:
            return error_response("Missing contentId parameter", status_code=400)
        
        # Parse request body
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return error_response("Invalid JSON in request body", status_code=400)
        
        is_published = body.get("isPublished", True)
        
        table = get_table("ConsistencyTracker-ContentPages")
        
        # Get existing content
        existing = table.get_item(Key={"pageId": content_id})
        if "Item" not in existing:
            return error_response("Content page not found", status_code=404)
        
        existing_content = existing["Item"]
        # Validate content belongs to coach's club
        if existing_content.get("clubId") != club_id:
            return error_response("Content page not found or access denied", status_code=403)
        
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
        
        return success_response({
            "content": updated.get("Item"),
            "message": "Content published" if is_published else "Content unpublished",
        })
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/content_publish: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

