"""
Lambda function: GET /admin/reflections
View all player reflections.
"""

from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin, get_team_id_from_user
from shared.db_utils import (
    get_table,
    get_player_by_id,
)


def lambda_handler(event, context):
    """Handle GET /admin/reflections request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Require admin authentication
        require_admin(event)
        team_id = get_team_id_from_user(event) or "default-team"
        
        # Get weekId from query parameters (optional)
        query_params = event.get("queryStringParameters") or {}
        week_id = query_params.get("weekId")
        
        reflection_table = get_table("ConsistencyTracker-Reflections")
        
        if week_id:
            # Get reflections for specific week
            # Scan with filter (GSI would be better, but we have teamId-index)
            response = reflection_table.scan(
                FilterExpression="weekId = :weekId AND teamId = :teamId",
                ExpressionAttributeValues={
                    ":weekId": week_id,
                    ":teamId": team_id,
                },
            )
            reflections = response.get("Items", [])
        else:
            # Get all reflections for team
            response = reflection_table.query(
                IndexName="teamId-index",
                KeyConditionExpression="teamId = :teamId",
                ExpressionAttributeValues={":teamId": team_id},
            )
            reflections = response.get("Items", [])
        
        # Get player details for each reflection
        reflections_with_players = []
        for reflection in reflections:
            player_id = reflection.get("playerId")
            player = get_player_by_id(player_id)
            
            if player and player.get("isActive", True):
                reflections_with_players.append({
                    "reflectionId": reflection.get("reflectionId"),
                    "playerId": player_id,
                    "playerName": player.get("name"),
                    "weekId": reflection.get("weekId"),
                    "wentWell": reflection.get("wentWell"),
                    "doBetter": reflection.get("doBetter"),
                    "planForWeek": reflection.get("planForWeek"),
                    "createdAt": reflection.get("createdAt"),
                    "updatedAt": reflection.get("updatedAt"),
                })
        
        # Sort by weekId (most recent first) and then by player name
        reflections_with_players.sort(
            key=lambda x: (x["weekId"], x["playerName"]),
            reverse=True
        )
        
        return success_response({
            "reflections": reflections_with_players,
            "total": len(reflections_with_players),
            "weekId": week_id,
        })
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/reflections: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

