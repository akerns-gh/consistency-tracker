"""
Lambda function: GET /admin/overview
Team statistics and overview.
"""

from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin, get_club_id_from_user
from shared.db_utils import (
    get_table,
    get_activities_by_team,
    get_activities_by_club,
    get_tracking_by_week,
)
from shared.week_utils import get_current_week_id, get_week_id
from datetime import datetime, timedelta


def lambda_handler(event, context):
    """Handle GET /admin/overview request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Require admin authentication
        require_admin(event)
        club_id = get_club_id_from_user(event)
        
        if not club_id:
            return error_response("User not associated with a club", status_code=403)
        
        current_week_id = get_current_week_id()
        
        # Get all players in club
        player_table = get_table("ConsistencyTracker-Players")
        players_response = player_table.query(
            IndexName="clubId-index",
            KeyConditionExpression="clubId = :clubId",
            ExpressionAttributeValues={":clubId": club_id},
        )
        players = players_response.get("Items", [])
        active_players = [p for p in players if p.get("isActive", True)]
        
        # Get activities (club-wide + team-specific)
        club_activities = get_activities_by_club(club_id, active_only=True)
        activities = club_activities  # Can be filtered by team if needed
        
        # Get current week tracking
        tracking_records = get_tracking_by_week(current_week_id)
        club_tracking = [t for t in tracking_records if t.get("clubId") == club_id]
        
        # Calculate statistics
        # Aggregate scores by player for current week
        player_scores = {}
        for record in club_tracking:
            player_id = record.get("playerId")
            daily_score = record.get("dailyScore", 0)
            
            if player_id not in player_scores:
                player_scores[player_id] = {
                    "playerId": player_id,
                    "weeklyScore": 0,
                    "daysCompleted": 0,
                }
            
            player_scores[player_id]["weeklyScore"] += daily_score
            player_scores[player_id]["daysCompleted"] += 1
        
        # Calculate team averages
        total_weekly_score = sum(ps["weeklyScore"] for ps in player_scores.values())
        average_weekly_score = total_weekly_score / len(player_scores) if player_scores else 0
        
        # Get top performers
        top_performers = sorted(
            player_scores.items(),
            key=lambda x: x[1]["weeklyScore"],
            reverse=True
        )[:5]
        
        # Get player names for top performers
        player_map = {p.get("playerId"): p for p in active_players}
        top_performers_list = []
        for player_id, score_data in top_performers:
            player = player_map.get(player_id)
            if player:
                top_performers_list.append({
                    "playerId": player_id,
                    "name": player.get("name"),
                    "weeklyScore": score_data["weeklyScore"],
                    "daysCompleted": score_data["daysCompleted"],
                })
        
        # Get last 4 weeks of data for trends
        weeks_data = []
        for i in range(4):
            week_date = datetime.utcnow() - timedelta(weeks=i)
            week_id = get_week_id(week_date)
            
            week_tracking = get_tracking_by_week(week_id)
            week_team_tracking = [t for t in week_tracking if t.get("teamId") == team_id]
            
            week_player_scores = {}
            for record in week_team_tracking:
                player_id = record.get("playerId")
                daily_score = record.get("dailyScore", 0)
                
                if player_id not in week_player_scores:
                    week_player_scores[player_id] = 0
                week_player_scores[player_id] += daily_score
            
            weeks_data.append({
                "weekId": week_id,
                "averageScore": sum(week_player_scores.values()) / len(week_player_scores) if week_player_scores else 0,
                "participatingPlayers": len(week_player_scores),
            })
        
        # Build response
        response_data = {
            "currentWeek": {
                "weekId": current_week_id,
                "totalPlayers": len(active_players),
                "participatingPlayers": len(player_scores),
                "averageWeeklyScore": round(average_weekly_score, 2),
                "totalWeeklyScore": total_weekly_score,
            },
            "topPerformers": top_performers_list,
            "weeksTrend": weeks_data,
            "activities": {
                "total": len(activities),
                "list": [{"activityId": a.get("activityId"), "name": a.get("name")} for a in activities],
            },
        }
        
        return success_response(response_data)
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/overview: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

