"""
Lambda function: PUT /player/{uniqueLink}/reflection
Save/update weekly reflection.
"""

import json
from shared.response import success_response, error_response, cors_preflight_response
from shared.db_utils import (
    get_player_by_unique_link,
    create_or_update_reflection,
)
from shared.week_utils import get_current_week_id


def lambda_handler(event, context):
    """Handle PUT /player/{uniqueLink}/reflection request."""
    
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
        
        went_well = body.get("wentWell", "")
        do_better = body.get("doBetter", "")
        plan_for_week = body.get("planForWeek", "")
        week_id = body.get("weekId")  # Optional, defaults to current week
        
        # Get player by unique link
        player = get_player_by_unique_link(unique_link)
        
        if not player:
            return error_response("Player not found", status_code=404)
        
        if not player.get("isActive", True):
            return error_response("Player is inactive", status_code=403)
        
        team_id = player.get("teamId")
        player_id = player.get("playerId")
        
        # Use current week if not specified
        if not week_id:
            week_id = get_current_week_id()
        
        # Create or update reflection
        reflection = create_or_update_reflection(
            player_id=player_id,
            week_id=week_id,
            went_well=went_well,
            do_better=do_better,
            plan_for_week=plan_for_week,
            team_id=team_id,
        )
        
        # Build response
        response_data = {
            "reflection": reflection,
        }
        
        return success_response(response_data, status_code=200)
        
    except Exception as e:
        print(f"Error in save_reflection: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

