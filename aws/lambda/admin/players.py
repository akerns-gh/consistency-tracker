"""
Lambda function: Admin player management endpoints
- GET /admin/players - List all players
- POST /admin/players - Create new player
- PUT /admin/players/{playerId} - Update player
- DELETE /admin/players/{playerId} - Deactivate player
"""

import json
import uuid
from datetime import datetime
from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin, get_team_id_from_user
from shared.db_utils import (
    get_table,
    get_player_by_id,
    get_activities_by_team,
)
import secrets


def lambda_handler(event, context):
    """Handle admin player management requests."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Require admin authentication
        user_info = require_admin(event)
        team_id = get_team_id_from_user(event) or "default-team"
        
        http_method = event.get("httpMethod")
        path_params = event.get("pathParameters") or {}
        player_id = path_params.get("playerId")
        
        table = get_table("ConsistencyTracker-Players")
        
        if http_method == "GET":
            # List all players
            # Query by teamId using GSI
            response = table.query(
                IndexName="teamId-index",
                KeyConditionExpression="teamId = :teamId",
                ExpressionAttributeValues={":teamId": team_id},
            )
            players = response.get("Items", [])
            
            # Format response
            player_list = []
            for player in players:
                player_list.append({
                    "playerId": player.get("playerId"),
                    "name": player.get("name"),
                    "email": player.get("email"),
                    "uniqueLink": player.get("uniqueLink"),
                    "isActive": player.get("isActive", True),
                    "createdAt": player.get("createdAt"),
                })
            
            return success_response({"players": player_list, "total": len(player_list)})
        
        elif http_method == "POST":
            # Create new player
            try:
                body = json.loads(event.get("body", "{}"))
            except json.JSONDecodeError:
                return error_response("Invalid JSON in request body", status_code=400)
            
            name = body.get("name")
            email = body.get("email", "")
            
            if not name:
                return error_response("Missing required field: name", status_code=400)
            
            # Generate unique link (secure random token)
            unique_link = secrets.token_urlsafe(32)
            
            # Create player
            player_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat() + "Z"
            
            player = {
                "playerId": player_id,
                "name": name,
                "email": email,
                "uniqueLink": unique_link,
                "teamId": team_id,
                "isActive": True,
                "createdAt": now,
            }
            
            table.put_item(Item=player)
            
            return success_response({"player": player}, status_code=201)
        
        elif http_method == "PUT":
            # Update player
            if not player_id:
                return error_response("Missing playerId parameter", status_code=400)
            
            try:
                body = json.loads(event.get("body", "{}"))
            except json.JSONDecodeError:
                return error_response("Invalid JSON in request body", status_code=400)
            
            # Get existing player
            existing = get_player_by_id(player_id)
            if not existing:
                return error_response("Player not found", status_code=404)
            
            # Update allowed fields
            update_expression_parts = []
            expression_attribute_values = {}
            
            if "name" in body:
                update_expression_parts.append("name = :name")
                expression_attribute_values[":name"] = body["name"]
            
            if "email" in body:
                update_expression_parts.append("email = :email")
                expression_attribute_values[":email"] = body["email"]
            
            if not update_expression_parts:
                return error_response("No fields to update", status_code=400)
            
            # Add updatedAt
            update_expression_parts.append("updatedAt = :updatedAt")
            expression_attribute_values[":updatedAt"] = datetime.utcnow().isoformat() + "Z"
            
            # Perform update
            table.update_item(
                Key={"playerId": player_id},
                UpdateExpression="SET " + ", ".join(update_expression_parts),
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW",
            )
            
            # Get updated player
            updated = get_player_by_id(player_id)
            return success_response({"player": updated})
        
        elif http_method == "DELETE":
            # Deactivate player (soft delete)
            if not player_id:
                return error_response("Missing playerId parameter", status_code=400)
            
            # Get existing player
            existing = get_player_by_id(player_id)
            if not existing:
                return error_response("Player not found", status_code=404)
            
            # Update isActive flag
            table.update_item(
                Key={"playerId": player_id},
                UpdateExpression="SET isActive = :isActive, updatedAt = :updatedAt",
                ExpressionAttributeValues={
                    ":isActive": False,
                    ":updatedAt": datetime.utcnow().isoformat() + "Z",
                },
                ReturnValues="ALL_NEW",
            )
            
            return success_response({"message": "Player deactivated successfully"})
        
        else:
            return error_response(f"Method not allowed: {http_method}", status_code=405)
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/players: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

