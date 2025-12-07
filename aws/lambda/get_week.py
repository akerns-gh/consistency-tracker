"""
Lambda function: GET /player/{uniqueLink}/week/{weekId}
Get specific week data for a player.
"""

from shared.response import success_response, error_response, cors_preflight_response
from shared.db_utils import (
    get_player_by_unique_link,
    get_activities_by_team,
    get_tracking_by_player_week,
    get_reflection_by_player_week,
)
from shared.week_utils import get_week_dates


def lambda_handler(event, context):
    """Handle GET /player/{uniqueLink}/week/{weekId} request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Extract parameters from path
        path_params = event.get("pathParameters", {})
        unique_link = path_params.get("uniqueLink")
        week_id = path_params.get("weekId")
        
        if not unique_link:
            return error_response("Missing uniqueLink parameter", status_code=400)
        
        if not week_id:
            return error_response("Missing weekId parameter", status_code=400)
        
        # Validate week ID format
        try:
            week_dates = get_week_dates(week_id)
        except Exception:
            return error_response("Invalid weekId format (expected YYYY-WW)", status_code=400)
        
        # Get player by unique link
        player = get_player_by_unique_link(unique_link)
        
        if not player:
            return error_response("Player not found", status_code=404)
        
        if not player.get("isActive", True):
            return error_response("Player is inactive", status_code=403)
        
        team_id = player.get("teamId")
        player_id = player.get("playerId")
        
        # Get activities for the team (as they were in that week)
        activities = get_activities_by_team(team_id, active_only=True)
        
        # Get tracking data for the week
        tracking_records = get_tracking_by_player_week(player_id, week_id)
        
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
        
        # Get reflection for the week
        reflection = get_reflection_by_player_week(player_id, week_id)
        
        # Build response
        response_data = {
            "weekId": week_id,
            "weekDates": {
                "monday": week_dates[0].isoformat(),
                "sunday": week_dates[1].isoformat(),
            },
            "activities": activities,
            "dailyTracking": daily_tracking,
            "weeklyScore": weekly_score,
            "reflection": reflection if reflection else None,
        }
        
        return success_response(response_data)
        
    except Exception as e:
        print(f"Error in get_week: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

