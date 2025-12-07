"""
Lambda function: GET /admin/export/{weekId}
Export week data (CSV format).
"""

import csv
import io
import base64
from datetime import datetime
from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin, get_team_id_from_user
from shared.db_utils import (
    get_table,
    get_tracking_by_week,
    get_player_by_id,
    get_activities_by_team,
)
from shared.week_utils import get_week_dates


def lambda_handler(event, context):
    """Handle GET /admin/export/{weekId} request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Require admin authentication
        require_admin(event)
        team_id = get_team_id_from_user(event) or "default-team"
        
        # Extract weekId from path parameters
        week_id = event.get("pathParameters", {}).get("weekId")
        
        if not week_id:
            return error_response("Missing weekId parameter", status_code=400)
        
        # Validate week ID format
        try:
            week_dates = get_week_dates(week_id)
        except Exception:
            return error_response("Invalid weekId format (expected YYYY-WW)", status_code=400)
        
        # Get tracking records for the week
        tracking_records = get_tracking_by_week(week_id)
        team_tracking = [t for t in tracking_records if t.get("teamId") == team_id]
        
        # Get activities
        activities = get_activities_by_team(team_id, active_only=True)
        activity_map = {a.get("activityId"): a.get("name") for a in activities}
        
        # Aggregate by player
        player_data = {}
        for record in team_tracking:
            player_id = record.get("playerId")
            date = record.get("date")
            completed_activities = record.get("completedActivities", [])
            daily_score = record.get("dailyScore", 0)
            
            if player_id not in player_data:
                player = get_player_by_id(player_id)
                player_data[player_id] = {
                    "playerId": player_id,
                    "playerName": player.get("name") if player else "Unknown",
                    "dailyScores": {},
                    "weeklyScore": 0,
                }
            
            player_data[player_id]["dailyScores"][date] = {
                "completedActivities": completed_activities,
                "dailyScore": daily_score,
            }
            player_data[player_id]["weeklyScore"] += daily_score
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        header = ["Player Name", "Weekly Score"] + days + ["Activities Completed"]
        writer.writerow(header)
        
        # Write data rows
        for player_id, data in sorted(player_data.items(), key=lambda x: x[1]["weeklyScore"], reverse=True):
            row = [data["playerName"], data["weeklyScore"]]
            
            # Daily scores
            for day in days:
                # Find date for this day of week
                day_scores = data["dailyScores"]
                day_score = 0
                for date, score_data in day_scores.items():
                    # Simple match by day name (could be improved)
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    if date_obj.strftime("%A") == day:
                        day_score = score_data["dailyScore"]
                        break
                row.append(day_score)
            
            # Activities completed (comma-separated list)
            all_activities = set()
            for score_data in data["dailyScores"].values():
                all_activities.update(score_data["completedActivities"])
            activities_list = ", ".join(
                activity_map.get(aid, aid) for aid in sorted(all_activities)
            )
            row.append(activities_list)
            
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        # Return CSV as base64-encoded string (or could return as text/plain)
        csv_base64 = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
        
        return success_response({
            "weekId": week_id,
            "csv": csv_base64,
            "filename": f"consistency-tracker-{week_id}.csv",
        })
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/export: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

