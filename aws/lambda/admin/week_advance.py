"""
Lambda function: POST /admin/week/advance
Advance to next week (update team configuration).
"""

import json
from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin, get_team_id_from_user
from shared.db_utils import get_table
from shared.week_utils import get_current_week_id, get_week_id
from datetime import datetime, timedelta


def lambda_handler(event, context):
    """Handle POST /admin/week/advance request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Require admin authentication
        require_admin(event)
        team_id = get_team_id_from_user(event) or "default-team"
        
        table = get_table("ConsistencyTracker-Teams")
        
        # Get current week
        current_week_id = get_current_week_id()
        
        # Calculate next week
        next_week_date = datetime.utcnow() + timedelta(weeks=1)
        next_week_id = get_week_id(next_week_date)
        
        # Get or create team config
        try:
            response = table.get_item(Key={"teamId": team_id})
            if "Item" in response:
                team_config = response["Item"]
            else:
                # Create default team config
                team_config = {
                    "teamId": team_id,
                    "teamName": "Default Team",
                    "currentWeekId": current_week_id,
                    "settings": {
                        "weekStartDay": "Monday",
                        "autoAdvanceWeek": False,
                        "scoringMethod": "points",
                    },
                }
                table.put_item(Item=team_config)
        except Exception as e:
            print(f"Error getting team config: {e}")
            return error_response("Error accessing team configuration", status_code=500)
        
        # Update current week
        table.update_item(
            Key={"teamId": team_id},
            UpdateExpression="SET currentWeekId = :nextWeekId, updatedAt = :updatedAt",
            ExpressionAttributeValues={
                ":nextWeekId": next_week_id,
                ":updatedAt": datetime.utcnow().isoformat() + "Z",
            },
            ReturnValues="ALL_NEW",
        )
        
        # Get updated config
        updated = table.get_item(Key={"teamId": team_id})
        
        return success_response({
            "message": "Week advanced successfully",
            "previousWeekId": current_week_id,
            "currentWeekId": next_week_id,
            "teamConfig": updated.get("Item"),
        })
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/week_advance: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

