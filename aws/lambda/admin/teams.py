"""
Lambda function: Admin team management endpoints
- GET /admin/teams - List teams in coach's club
- POST /admin/teams - Create new team (requires clubId, validates coach has access)
- GET /admin/teams/{teamId} - Get team details
- PUT /admin/teams/{teamId} - Update team settings
"""

import json
import uuid
from datetime import datetime
from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin, get_club_id_from_user
from shared.db_utils import (
    get_table,
    get_team_by_id,
    get_teams_by_club,
)


def lambda_handler(event, context):
    """Handle admin team management requests."""
    
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
        team_id = path_params.get("teamId")
        
        table = get_table("ConsistencyTracker-Teams")
        
        if http_method == "GET":
            if team_id:
                # Get specific team
                team = get_team_by_id(team_id)
                if not team:
                    return error_response("Team not found", status_code=404)
                
                # Validate team belongs to coach's club
                if team.get("clubId") != club_id:
                    return error_response("Team not found or access denied", status_code=403)
                
                return success_response({"team": team})
            else:
                # List all teams in coach's club
                teams = get_teams_by_club(club_id)
                
                # Format response
                team_list = []
                for team in teams:
                    team_list.append({
                        "teamId": team.get("teamId"),
                        "teamName": team.get("teamName"),
                        "coachName": team.get("coachName"),
                        "clubId": team.get("clubId"),
                        "settings": team.get("settings", {}),
                        "createdAt": team.get("createdAt"),
                    })
                
                return success_response({"teams": team_list, "total": len(team_list)})
        
        elif http_method == "POST":
            # Create new team
            try:
                body = json.loads(event.get("body", "{}"))
            except json.JSONDecodeError:
                return error_response("Invalid JSON in request body", status_code=400)
            
            team_name = body.get("teamName")
            coach_name = body.get("coachName", "")
            request_club_id = body.get("clubId")
            
            if not team_name:
                return error_response("Missing required field: teamName", status_code=400)
            
            # Validate clubId matches coach's club (never trust client)
            if request_club_id and request_club_id != club_id:
                return error_response("Invalid clubId. Team must belong to your club.", status_code=403)
            
            # Create team
            new_team_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat() + "Z"
            
            team = {
                "teamId": new_team_id,
                "clubId": club_id,  # Set from coach's club (never trust client)
                "teamName": team_name,
                "coachName": coach_name,
                "settings": body.get("settings", {
                    "weekStartDay": "Monday",
                    "autoAdvanceWeek": False,
                    "scoringMethod": "points",
                }),
                "createdAt": now,
            }
            
            table.put_item(Item=team)
            
            return success_response({"team": team}, status_code=201)
        
        elif http_method == "PUT":
            # Update team settings
            if not team_id:
                return error_response("Missing teamId parameter", status_code=400)
            
            try:
                body = json.loads(event.get("body", "{}"))
            except json.JSONDecodeError:
                return error_response("Invalid JSON in request body", status_code=400)
            
            # Get existing team
            existing = get_team_by_id(team_id)
            if not existing:
                return error_response("Team not found", status_code=404)
            
            # Validate team belongs to coach's club
            if existing.get("clubId") != club_id:
                return error_response("Team not found or access denied", status_code=403)
            
            # Update allowed fields
            update_expression_parts = []
            expression_attribute_values = {}
            
            if "teamName" in body:
                update_expression_parts.append("teamName = :teamName")
                expression_attribute_values[":teamName"] = body["teamName"]
            
            if "coachName" in body:
                update_expression_parts.append("coachName = :coachName")
                expression_attribute_values[":coachName"] = body["coachName"]
            
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
                Key={"teamId": team_id},
                UpdateExpression="SET " + ", ".join(update_expression_parts),
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW",
            )
            
            # Get updated team
            updated = get_team_by_id(team_id)
            return success_response({"team": updated})
        
        else:
            return error_response(f"Method not allowed: {http_method}", status_code=405)
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/teams: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

