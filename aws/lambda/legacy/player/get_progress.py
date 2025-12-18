"""
Lambda function: GET /player/{uniqueLink}/progress
Get aggregated progress statistics (for My Progress page).
"""

from shared.response import success_response, error_response, cors_preflight_response
from shared.db_utils import (
    get_player_by_unique_link,
    get_tracking_by_player_week,
)
from shared.week_utils import get_current_week_id, get_week_id, get_week_dates
from datetime import datetime, timedelta


def lambda_handler(event, context):
    """Handle GET /player/{uniqueLink}/progress request."""
    
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
        
        club_id = player.get("clubId")
        team_id = player.get("teamId")
        player_id = player.get("playerId")
        current_week_id = get_current_week_id()
        
        if not club_id or not team_id:
            return error_response("Player missing clubId or teamId", status_code=500)
        
        # Get last 4 weeks of data
        weeks_data = []
        current_date = datetime.utcnow()
        
        for i in range(4):
            week_date = current_date - timedelta(weeks=i)
            week_id = get_week_id(week_date)
            
            tracking_records = get_tracking_by_player_week(player_id, week_id)
            
            # Calculate stats for this week
            weekly_score = sum(record.get("dailyScore", 0) for record in tracking_records)
            days_completed = len(tracking_records)
            perfect_days = sum(1 for record in tracking_records if record.get("dailyScore", 0) > 0)
            
            weeks_data.append({
                "weekId": week_id,
                "weeklyScore": weekly_score,
                "daysCompleted": days_completed,
                "perfectDays": perfect_days,
            })
        
        # Calculate overall statistics
        total_weeks = len(weeks_data)
        total_score = sum(w.get("weeklyScore", 0) for w in weeks_data)
        average_score = total_score / total_weeks if total_weeks > 0 else 0
        best_week = max(weeks_data, key=lambda w: w.get("weeklyScore", 0)) if weeks_data else None
        
        # Build response
        response_data = {
            "player": {
                "playerId": player_id,
                "name": player.get("name"),
                "clubId": club_id,
                "teamId": team_id,
            },
            "weeks": weeks_data,
            "statistics": {
                "totalWeeks": total_weeks,
                "totalScore": total_score,
                "averageScore": round(average_score, 2),
                "bestWeek": best_week,
            },
        }
        
        return success_response(response_data)
        
    except Exception as e:
        print(f"Error in get_progress: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

