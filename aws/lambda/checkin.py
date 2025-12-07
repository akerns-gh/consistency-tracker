"""
Lambda function: POST /player/{uniqueLink}/checkin
Mark activity complete for a day.
"""

import json
from shared.response import success_response, error_response, cors_preflight_response
from shared.db_utils import (
    get_player_by_unique_link,
    get_activities_by_team,
    get_tracking_by_player_week,
    create_tracking_record,
)
from shared.week_utils import get_current_week_id
from datetime import datetime


def lambda_handler(event, context):
    """Handle POST /player/{uniqueLink}/checkin request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Extract uniqueLink from path parameters
        unique_link = event.get("pathParameters", {}).get("uniqueLink")
        
        if not unique_link:
            return error_response("Missing uniqueLink parameter", status_code=400)
        
        # Parse request body
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return error_response("Invalid JSON in request body", status_code=400)
        
        activity_id = body.get("activityId")
        date = body.get("date")  # YYYY-MM-DD format
        completed = body.get("completed", True)  # True to mark complete, False to unmark
        
        if not activity_id:
            return error_response("Missing activityId in request body", status_code=400)
        
        if not date:
            return error_response("Missing date in request body", status_code=400)
        
        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return error_response("Invalid date format (expected YYYY-MM-DD)", status_code=400)
        
        # Get player by unique link
        player = get_player_by_unique_link(unique_link)
        
        if not player:
            return error_response("Player not found", status_code=404)
        
        if not player.get("isActive", True):
            return error_response("Player is inactive", status_code=403)
        
        team_id = player.get("teamId")
        player_id = player.get("playerId")
        current_week_id = get_current_week_id()
        
        # Get activities to validate activityId and calculate scores
        activities = get_activities_by_team(team_id, active_only=True)
        activity_map = {a.get("activityId"): a for a in activities}
        
        if activity_id not in activity_map:
            return error_response("Activity not found", status_code=404)
        
        activity = activity_map[activity_id]
        point_value = activity.get("pointValue", 1)
        
        # Get existing tracking record for this day
        tracking_records = get_tracking_by_player_week(player_id, current_week_id)
        existing_record = next(
            (r for r in tracking_records if r.get("date") == date),
            None
        )
        
        # Get or initialize completed activities list
        if existing_record:
            completed_activities = list(existing_record.get("completedActivities", []))
        else:
            completed_activities = []
        
        # Update completed activities list
        if completed:
            if activity_id not in completed_activities:
                completed_activities.append(activity_id)
        else:
            if activity_id in completed_activities:
                completed_activities.remove(activity_id)
        
        # Calculate daily score (sum of point values for completed activities)
        daily_score = sum(
            activity_map.get(aid, {}).get("pointValue", 1)
            for aid in completed_activities
            if aid in activity_map
        )
        
        # Create or update tracking record
        tracking_record = create_tracking_record(
            player_id=player_id,
            week_id=current_week_id,
            date=date,
            completed_activities=completed_activities,
            daily_score=daily_score,
            team_id=team_id,
        )
        
        # Build response
        response_data = {
            "tracking": tracking_record,
            "dailyScore": daily_score,
            "completedActivities": completed_activities,
        }
        
        return success_response(response_data, status_code=200)
        
    except Exception as e:
        print(f"Error in checkin: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

