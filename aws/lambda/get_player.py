"""
Lambda function: GET /player/{uniqueLink}
Get player data and current week activities.
"""

import json
from shared.response import success_response, error_response, cors_preflight_response
from shared.db_utils import (
    get_player_by_unique_link,
    get_activities_by_team,
    get_tracking_by_player_week,
)
from shared.week_utils import get_current_week_id


def lambda_handler(event, context):
    """Handle GET /player/{uniqueLink} request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Extract uniqueLink from path parameters
        unique_link = event.get("pathParameters", {}).get("uniqueLink")
        
        if not unique_link:
            return error_response("Missing uniqueLink parameter", status_code=400)
        
        # Get player by unique link
        player = get_player_by_unique_link(unique_link)
        
        if not player:
            return error_response("Player not found", status_code=404)
        
        if not player.get("isActive", True):
            return error_response("Player is inactive", status_code=403)
        
        team_id = player.get("teamId")
        player_id = player.get("playerId")
        current_week_id = get_current_week_id()
        
        # Get activities for the team
        activities = get_activities_by_team(team_id, active_only=True)
        
        # Get tracking data for current week
        tracking_records = get_tracking_by_player_week(player_id, current_week_id)
        
        # Build daily tracking map
        daily_tracking = {}
        for record in tracking_records:
            date = record.get("date")
            daily_tracking[date] = {
                "completedActivities": record.get("completedActivities", []),
                "dailyScore": record.get("dailyScore", 0),
            }
        
        # Calculate weekly score
        weekly_score = sum(record.get("dailyScore", 0) for record in tracking_records)
        
        # Build response
        response_data = {
            "player": {
                "playerId": player_id,
                "name": player.get("name"),
                "email": player.get("email"),
                "teamId": team_id,
            },
            "currentWeek": {
                "weekId": current_week_id,
                "activities": activities,
                "dailyTracking": daily_tracking,
                "weeklyScore": weekly_score,
            },
        }
        
        return success_response(response_data)
        
    except Exception as e:
        print(f"Error in get_player: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

