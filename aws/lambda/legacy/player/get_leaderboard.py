"""
Lambda function: GET /leaderboard/{weekId}
Get leaderboard for a week (validates uniqueLink in query for context).
"""

from shared.response import success_response, error_response, cors_preflight_response
from shared.db_utils import (
    get_player_by_unique_link,
    get_tracking_by_week,
    get_player_by_id,
)
from shared.week_utils import get_week_dates


def lambda_handler(event, context):
    """Handle GET /leaderboard/{weekId} request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Extract weekId from path parameters
        week_id = event.get("pathParameters", {}).get("weekId")
        
        if not week_id:
            return error_response("Missing weekId parameter", status_code=400)
        
        # Validate week ID format
        try:
            week_dates = get_week_dates(week_id)
        except Exception:
            return error_response("Invalid weekId format (expected YYYY-WW)", status_code=400)
        
        # Get uniqueLink and scope from query parameters
        query_params = event.get("queryStringParameters") or {}
        unique_link = query_params.get("uniqueLink")
        scope = query_params.get("scope", "team")  # Default to "team", can be "club"
        current_player_id = None
        club_id = None
        team_id = None
        
        if unique_link:
            player = get_player_by_unique_link(unique_link)
            if player:
                current_player_id = player.get("playerId")
                club_id = player.get("clubId")
                team_id = player.get("teamId")
        
        # Get all tracking records for the week
        tracking_records = get_tracking_by_week(week_id)
        
        # Filter by scope if player context is available
        if scope == "club" and club_id:
            # Filter to players in same club
            filtered_records = [
                r for r in tracking_records 
                if r.get("clubId") == club_id
            ]
        elif scope == "team" and team_id:
            # Filter to players in same team
            filtered_records = [
                r for r in tracking_records 
                if r.get("teamId") == team_id
            ]
        else:
            # No filtering (show all) if no context or invalid scope
            filtered_records = tracking_records
        
        tracking_records = filtered_records
        
        # Aggregate scores by player
        player_scores = {}
        for record in tracking_records:
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
        
        # Get player details and build leaderboard
        leaderboard = []
        for player_id, score_data in player_scores.items():
            player = get_player_by_id(player_id)
            if player and player.get("isActive", True):
                leaderboard.append({
                    "playerId": player_id,
                    "name": player.get("name"),
                    "weeklyScore": score_data["weeklyScore"],
                    "daysCompleted": score_data["daysCompleted"],
                    "isCurrentPlayer": player_id == current_player_id,
                })
        
        # Sort by weekly score (descending)
        leaderboard.sort(key=lambda x: x["weeklyScore"], reverse=True)
        
        # Add rank
        for i, entry in enumerate(leaderboard, start=1):
            entry["rank"] = i
        
        # Build response
        response_data = {
            "weekId": week_id,
            "weekDates": {
                "monday": week_dates[0].isoformat(),
                "sunday": week_dates[1].isoformat(),
            },
            "scope": scope,
            "leaderboard": leaderboard,
            "totalPlayers": len(leaderboard),
        }
        
        return success_response(response_data)
        
    except Exception as e:
        print(f"Error in get_leaderboard: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

