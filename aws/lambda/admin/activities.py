"""
Lambda function: Admin activity management endpoints
- GET /admin/activities - List all activities
- POST /admin/activities - Create activity
- PUT /admin/activities/{activityId} - Update activity
- DELETE /admin/activities/{activityId} - Delete activity
"""

import json
import uuid
from datetime import datetime
from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin, get_club_id_from_user
from shared.db_utils import (
    get_table,
    get_activities_by_team,
    get_activities_by_club,
    get_team_by_id,
)


def lambda_handler(event, context):
    """Handle admin activity management requests."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Require admin authentication
        user_info = require_admin(event)
        club_id = get_club_id_from_user(event)
        
        if not club_id:
            return error_response("User not associated with a club", status_code=403)
        
        http_method = event.get("httpMethod")
        path_params = event.get("pathParameters") or {}
        activity_id = path_params.get("activityId")
        
        table = get_table("ConsistencyTracker-Activities")
        
        if http_method == "GET":
            # List all activities in coach's club (club-wide + team-specific)
            club_activities = get_activities_by_club(club_id, active_only=False)
            # Note: For team-specific activities, we'd need to query by teamId
            # For now, return club-wide activities. Team-specific can be filtered client-side.
            activities = club_activities
            
            # Format response
            activity_list = []
            for activity in activities:
                activity_list.append({
                    "activityId": activity.get("activityId"),
                    "name": activity.get("name"),
                    "description": activity.get("description"),
                    "frequency": activity.get("frequency"),
                    "pointValue": activity.get("pointValue", 1),
                    "displayOrder": activity.get("displayOrder", 999),
                    "isActive": activity.get("isActive", True),
                })
            
            return success_response({"activities": activity_list, "total": len(activity_list)})
        
        elif http_method == "POST":
            # Create activity
            try:
                body = json.loads(event.get("body", "{}"))
            except json.JSONDecodeError:
                return error_response("Invalid JSON in request body", status_code=400)
            
            name = body.get("name")
            description = body.get("description", "")
            frequency = body.get("frequency", "daily")
            point_value = body.get("pointValue", 1)
            display_order = body.get("displayOrder", 999)
            scope = body.get("scope", "team")  # "club" or "team"
            team_id = body.get("teamId")  # Required if scope is "team"
            
            if not name:
                return error_response("Missing required field: name", status_code=400)
            
            # Validate scope and team
            if scope == "team":
                if not team_id:
                    return error_response("Missing required field: teamId for team-specific activity", status_code=400)
                # Validate team belongs to coach's club
                team = get_team_by_id(team_id)
                if not team:
                    return error_response("Team not found", status_code=404)
                if team.get("clubId") != club_id:
                    return error_response("Team not found or access denied", status_code=403)
            elif scope == "club":
                team_id = None  # Club-wide activity
            else:
                return error_response("Invalid scope (must be 'club' or 'team')", status_code=400)
            
            # Get max displayOrder to append new activity
            existing_activities = get_activities_by_club(club_id, active_only=False)
            if display_order == 999 and existing_activities:
                max_order = max(a.get("displayOrder", 0) for a in existing_activities)
                display_order = max_order + 1
            
            # Create activity
            activity_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat() + "Z"
            
            activity = {
                "activityId": activity_id,
                "name": name,
                "description": description,
                "frequency": frequency,
                "pointValue": point_value,
                "displayOrder": display_order,
                "clubId": club_id,
                "teamId": team_id,  # None for club-wide, teamId for team-specific
                "scope": scope,
                "isActive": True,
                "createdAt": now,
            }
            
            table.put_item(Item=activity)
            
            return success_response({"activity": activity}, status_code=201)
        
        elif http_method == "PUT":
            # Update activity
            if not activity_id:
                return error_response("Missing activityId parameter", status_code=400)
            
            try:
                body = json.loads(event.get("body", "{}"))
            except json.JSONDecodeError:
                return error_response("Invalid JSON in request body", status_code=400)
            
            # Get existing activity
            existing = table.get_item(Key={"activityId": activity_id})
            if "Item" not in existing:
                return error_response("Activity not found", status_code=404)
            
            existing_activity = existing["Item"]
            # Validate activity belongs to coach's club
            if existing_activity.get("clubId") != club_id:
                return error_response("Activity not found or access denied", status_code=403)
            
            # Update allowed fields
            update_expression_parts = []
            expression_attribute_values = {}
            
            if "name" in body:
                update_expression_parts.append("name = :name")
                expression_attribute_values[":name"] = body["name"]
            
            if "description" in body:
                update_expression_parts.append("description = :description")
                expression_attribute_values[":description"] = body["description"]
            
            if "frequency" in body:
                update_expression_parts.append("#freq = :frequency")
                expression_attribute_values[":frequency"] = body["frequency"]
            
            if "pointValue" in body:
                update_expression_parts.append("pointValue = :pointValue")
                expression_attribute_values[":pointValue"] = body["pointValue"]
            
            if "displayOrder" in body:
                update_expression_parts.append("displayOrder = :displayOrder")
                expression_attribute_values[":displayOrder"] = body["displayOrder"]
            
            if "isActive" in body:
                update_expression_parts.append("isActive = :isActive")
                expression_attribute_values[":isActive"] = body["isActive"]
            
            if not update_expression_parts:
                return error_response("No fields to update", status_code=400)
            
            # Add updatedAt
            update_expression_parts.append("updatedAt = :updatedAt")
            expression_attribute_values[":updatedAt"] = datetime.utcnow().isoformat() + "Z"
            
            # Build update expression with attribute name mapping for reserved words
            update_expression = "SET " + ", ".join(update_expression_parts)
            expression_attribute_names = {}
            if "#freq" in update_expression:
                expression_attribute_names["#freq"] = "frequency"
            
            # Perform update
            update_kwargs = {
                "Key": {"activityId": activity_id},
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": expression_attribute_values,
                "ReturnValues": "ALL_NEW",
            }
            if expression_attribute_names:
                update_kwargs["ExpressionAttributeNames"] = expression_attribute_names
            
            table.update_item(**update_kwargs)
            
            # Get updated activity
            updated = table.get_item(Key={"activityId": activity_id})
            return success_response({"activity": updated.get("Item")})
        
        elif http_method == "DELETE":
            # Delete activity (hard delete)
            if not activity_id:
                return error_response("Missing activityId parameter", status_code=400)
            
            # Get existing activity
            existing = table.get_item(Key={"activityId": activity_id})
            if "Item" not in existing:
                return error_response("Activity not found", status_code=404)
            
            existing_activity = existing["Item"]
            # Validate activity belongs to coach's club
            if existing_activity.get("clubId") != club_id:
                return error_response("Activity not found or access denied", status_code=403)
            
            # Delete activity
            table.delete_item(Key={"activityId": activity_id})
            
            return success_response({"message": "Activity deleted successfully"})
        
        else:
            return error_response(f"Method not allowed: {http_method}", status_code=405)
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/activities: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

