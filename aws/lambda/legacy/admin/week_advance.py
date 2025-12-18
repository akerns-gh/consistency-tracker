"""
Lambda function: POST /admin/week/advance
Advance to next week (update team configuration).
"""

import json
from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin, get_club_id_from_user
from shared.db_utils import get_table, get_teams_by_club
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
        club_id = get_club_id_from_user(event)
        
        if not club_id:
            return error_response("User not associated with a club", status_code=403)
        
        table = get_table("ConsistencyTracker-Teams")
        
        # Get current week
        current_week_id = get_current_week_id()
        
        # Calculate next week
        next_week_date = datetime.utcnow() + timedelta(weeks=1)
        next_week_id = get_week_id(next_week_date)
        
        # Get all teams in the club
        teams = get_teams_by_club(club_id)
        
        if not teams:
            return error_response("No teams found for club", status_code=404)
        
        # Update current week for all teams in the club
        updated_teams = []
        for team in teams:
            team_id = team.get("teamId")
            try:
                table.update_item(
                    Key={"teamId": team_id},
                    UpdateExpression="SET currentWeekId = :nextWeekId, updatedAt = :updatedAt",
                    ExpressionAttributeValues={
                        ":nextWeekId": next_week_id,
                        ":updatedAt": datetime.utcnow().isoformat() + "Z",
                    },
                    ReturnValues="ALL_NEW",
                )
                updated_teams.append(team_id)
            except Exception as e:
                print(f"Error updating team {team_id}: {e}")
        
        return success_response({
            "message": "Week advanced successfully for all teams in club",
            "previousWeekId": current_week_id,
            "currentWeekId": next_week_id,
            "teamsUpdated": updated_teams,
            "totalTeams": len(teams),
        })
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/week_advance: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

