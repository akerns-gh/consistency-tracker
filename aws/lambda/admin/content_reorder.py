"""
Lambda function: PUT /admin/content/reorder
Update display order of content pages.
"""

import json
from datetime import datetime
from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin, get_club_id_from_user
from shared.db_utils import get_table


def lambda_handler(event, context):
    """Handle PUT /admin/content/reorder request."""
    
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
        
        # Parse request body
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return error_response("Invalid JSON in request body", status_code=400)
        
        # Expected format: { "reorder": [{"pageId": "...", "displayOrder": 1}, ...] }
        reorder_list = body.get("reorder", [])
        
        if not reorder_list:
            return error_response("Missing 'reorder' array in request body", status_code=400)
        
        table = get_table("ConsistencyTracker-ContentPages")
        now = datetime.utcnow().isoformat() + "Z"
        
        # Validate all pages belong to coach's club before updating
        for item in reorder_list:
            page_id = item.get("pageId")
            if not page_id:
                continue
            
            existing = table.get_item(Key={"pageId": page_id})
            if "Item" not in existing:
                return error_response(f"Content page {page_id} not found", status_code=404)
            
            existing_content = existing["Item"]
            if existing_content.get("clubId") != club_id:
                return error_response(f"Access denied to reorder content page {page_id}", status_code=403)
        
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
        
        return success_response({
            "message": f"Updated display order for {len(updated_pages)} content pages",
            "content": updated_pages,
        })
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/content_reorder: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

