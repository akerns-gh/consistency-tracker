"""
Flask application for player endpoints.

Consolidates all player Lambda functions into a single Flask app.
Player endpoints are public (no authentication required).
"""

from datetime import datetime, timedelta
from flask import Flask, request
from serverless_wsgi import handle_request

from shared.flask_auth import flask_success_response, flask_error_response, get_api_gateway_event
from shared.auth_utils import extract_user_info_from_event, extract_user_info_from_jwt_token
from shared.db_utils import (
    get_player_by_unique_link,
    get_player_by_email,
    get_activities_by_team,
    get_activities_by_club,
    get_tracking_by_player_week,
    get_tracking_by_week,
    get_reflection_by_player_week,
    create_tracking_record,
    create_or_update_reflection,
    get_content_pages_by_team,
    get_content_pages_by_club,
    get_player_by_id,
    get_team_by_id,
)
from shared.week_utils import get_current_week_id, get_week_id, get_week_dates

app = Flask(__name__)


@app.before_request
def before_request():
    """Log all incoming requests for debugging."""
    print(f"=" * 80)
    print(f"DEBUG: Incoming request")
    print(f"  Path: {request.path}")
    print(f"  URL: {request.url}")
    print(f"  Method: {request.method}")
    print(f"  Endpoint: {request.endpoint}")
    print(f"  View args: {request.view_args}")
    print(f"  Headers: {dict(request.headers)}")
    print(f"  Args: {dict(request.args)}")
    # Log the API Gateway event if available
    event = get_api_gateway_event()
    if event:
        print(f"  API Gateway path: {event.get('path', 'N/A')}")
        print(f"  API Gateway rawPath: {event.get('rawPath', 'N/A')}")
    print(f"=" * 80)


@app.after_request
def after_request(response):
    """Add CORS headers to all responses."""
    # Get origin from request
    origin = request.headers.get('Origin')
    
    # Only allow specific origins
    allowed_origins = ['https://repwarrior.net', 'https://www.repwarrior.net']
    if origin and origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        # Default to first allowed origin if no origin or invalid origin
        response.headers['Access-Control-Allow-Origin'] = 'https://repwarrior.net'
    
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS,PATCH'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


# Error handlers (specific errors first)
@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(error):
    """Handle HTTP errors with consistent format."""
    # Get error description or default message
    if hasattr(error, 'description') and error.description:
        message = error.description
    elif hasattr(error, 'code'):
        message = f"HTTP {error.code} error occurred"
    else:
        message = "An error occurred"
    
    # Get status code
    status_code = error.code if hasattr(error, 'code') else 500
    
    return flask_error_response(
        message,
        status_code=status_code
    )

# Global exception handler to catch all unhandled exceptions (must be last)
@app.errorhandler(Exception)
def handle_unhandled_exception(error):
    """Handle all unhandled exceptions with CORS headers."""
    import traceback
    print(f"Unhandled exception: {error}")
    traceback.print_exc()
    
    # Check if this is an HTTPException (already handled by specific handlers)
    from werkzeug.exceptions import HTTPException
    if isinstance(error, HTTPException):
        return handle_error(error)
    
    return flask_error_response(
        "An internal server error occurred",
        status_code=500
    )


# ============================================================================
# Player Endpoints
# ============================================================================

def get_player_from_jwt():
    """Helper function to get player from JWT token. Returns (player_dict, error_response) tuple."""
    try:
        print(f"DEBUG get_player_from_jwt: Starting authentication")
        
        # Try to get player from JWT token
        # First try to get from API Gateway event (if authorizer was used)
        event = get_api_gateway_event()
        print(f"DEBUG get_player_from_jwt: Event keys: {list(event.keys()) if event else 'None'}")
        
        user_info = extract_user_info_from_event(event)
        print(f"DEBUG get_player_from_jwt: User info from event: {user_info is not None}")
        
        # If no user info from event, try to extract from Authorization header manually
        if not user_info:
            auth_header = request.headers.get('Authorization', '')
            print(f"DEBUG get_player_from_jwt: Authorization header present: {bool(auth_header)}")
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove 'Bearer ' prefix
                print(f"DEBUG get_player_from_jwt: Token length: {len(token)}")
                # Try to decode JWT token (without verification - API Gateway would verify if authorizer was used)
                user_info = extract_user_info_from_jwt_token(token)
                print(f"DEBUG get_player_from_jwt: User info from token: {user_info is not None}")
        
        if not user_info:
            print(f"DEBUG get_player_from_jwt: No user info found, returning 401")
            return None, flask_error_response("Authentication required", status_code=401)
        
        email = user_info.get("email")
        print(f"DEBUG get_player_from_jwt: Email from user_info: {email}")
        if not email:
            return None, flask_error_response("Email not found in token", status_code=400)
        
        # Get player by email
        print(f"DEBUG get_player_from_jwt: Looking up player by email: {email}")
        player = get_player_by_email(email)
        print(f"DEBUG get_player_from_jwt: Player found: {player is not None}")
        
        if not player:
            return None, flask_error_response("Player not found for this user", status_code=404)
        
        if not player.get("isActive", True):
            return None, flask_error_response("Player is inactive", status_code=403)
        
        club_id = player.get("clubId")
        team_id = player.get("teamId")
        
        if not club_id or not team_id:
            return None, flask_error_response("Player missing clubId or teamId", status_code=500)
        
        # Validate team is active
        team = get_team_by_id(team_id)
        if not team:
            return None, flask_error_response("Team not found", status_code=404)
        
        if not team.get("isActive", True):
            return None, flask_error_response("Team is inactive", status_code=403)
        
        print(f"DEBUG get_player_from_jwt: Successfully authenticated player: {player.get('playerId')}")
        return player, None
    except Exception as e:
        import traceback
        print(f"ERROR in get_player_from_jwt: {e}")
        traceback.print_exc()
        return None, flask_error_response(
            "An error occurred while authenticating",
            status_code=500
        )


@app.route('/player', methods=['GET', 'OPTIONS'])
@app.route('/player/', methods=['GET', 'OPTIONS'])  # Handle trailing slash
def get_player_by_jwt():
    """Get player data and current week activities using JWT token."""
    try:
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            return flask_success_response({}, 200)
        
        # Debug: Log the request path
        print(f"DEBUG: Request path: {request.path}")
        print(f"DEBUG: Request URL: {request.url}")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Flask route matched: {request.endpoint}")
        
        player, error = get_player_from_jwt()
        if error:
            return error
        
        club_id = player.get("clubId")
        team_id = player.get("teamId")
        player_id = player.get("playerId")
        current_week_id = get_current_week_id()
        
        # Get club-wide activities
        club_activities = get_activities_by_club(club_id, active_only=True)
        
        # Get team-specific activities
        team_activities = get_activities_by_team(team_id, active_only=True)
        
        # Combine activities and deduplicate by activityId
        activity_map = {}
        for activity in club_activities + team_activities:
            activity_id = activity.get("activityId")
            if activity_id and activity_id not in activity_map:
                activity_map[activity_id] = activity
        
        activities = list(activity_map.values())
        # Sort by displayOrder
        activities.sort(key=lambda x: x.get("displayOrder", 999))
        
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
                "clubId": club_id,
                "teamId": team_id,
            },
            "currentWeek": {
                "weekId": current_week_id,
                "activities": activities,
                "dailyTracking": daily_tracking,
                "weeklyScore": weekly_score,
            },
        }
        
        return flask_success_response(response_data)
    except Exception as e:
        import traceback
        print(f"Error in get_player_by_jwt: {e}")
        traceback.print_exc()
        return flask_error_response(
            "An error occurred while fetching player data",
            status_code=500
        )


@app.route('/player/week/<week_id>', methods=['GET'])
def get_week_by_jwt(week_id):
    """Get specific week data for a player using JWT token."""
    try:
        if not week_id:
            return flask_error_response("Missing weekId parameter", status_code=400)
        
        # Validate week ID format
        try:
            week_dates = get_week_dates(week_id)
        except Exception:
            return flask_error_response("Invalid weekId format (expected YYYY-WW)", status_code=400)
        
        player, error = get_player_from_jwt()
        if error:
            return error
        
        club_id = player.get("clubId")
        team_id = player.get("teamId")
        player_id = player.get("playerId")
        
        # Get club-wide activities
        club_activities = get_activities_by_club(club_id, active_only=True)
        
        # Get team-specific activities
        team_activities = get_activities_by_team(team_id, active_only=True)
        
        # Combine activities and deduplicate by activityId
        activity_map = {}
        for activity in club_activities + team_activities:
            activity_id = activity.get("activityId")
            if activity_id and activity_id not in activity_map:
                activity_map[activity_id] = activity
        
        activities = list(activity_map.values())
        # Sort by displayOrder
        activities.sort(key=lambda x: x.get("displayOrder", 999))
        
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
            "clubId": club_id,
            "teamId": team_id,
            "activities": activities,
            "dailyTracking": daily_tracking,
            "weeklyScore": weekly_score,
            "reflection": reflection if reflection else None,
        }
        
        return flask_success_response(response_data)
    except Exception as e:
        import traceback
        print(f"Error in get_week_by_jwt: {e}")
        traceback.print_exc()
        return flask_error_response(
            "An error occurred while fetching week data",
            status_code=500
        )


@app.route('/player/progress', methods=['GET'])
def get_progress_by_jwt():
    """Get aggregated progress statistics using JWT token."""
    try:
        player, error = get_player_from_jwt()
        if error:
            return error
        
        club_id = player.get("clubId")
        team_id = player.get("teamId")
        player_id = player.get("playerId")
        current_week_id = get_current_week_id()
        
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
        
        return flask_success_response(response_data)
    except Exception as e:
        import traceback
        print(f"Error in get_progress_by_jwt: {e}")
        traceback.print_exc()
        return flask_error_response(
            "An error occurred while fetching progress data",
            status_code=500
        )


@app.route('/player/checkin', methods=['POST'])
def checkin_by_jwt():
    """Mark activity complete for a day using JWT token."""
    try:
        body = request.get_json() or {}
        
        activity_id = body.get("activityId")
        date = body.get("date")  # YYYY-MM-DD format
        completed = body.get("completed", True)  # True to mark complete, False to unmark
        
        if not activity_id:
            return flask_error_response("Missing activityId in request body", status_code=400)
        
        if not date:
            return flask_error_response("Missing date in request body", status_code=400)
        
        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return flask_error_response("Invalid date format (expected YYYY-MM-DD)", status_code=400)
        
        player, error = get_player_from_jwt()
        if error:
            return error
        
        club_id = player.get("clubId")
        team_id = player.get("teamId")
        player_id = player.get("playerId")
        current_week_id = get_current_week_id()
        
        # Get club-wide activities
        club_activities = get_activities_by_club(club_id, active_only=True)
        
        # Get team-specific activities
        activities = get_activities_by_team(team_id, active_only=True)
        
        # Combine activities for validation
        all_activities = club_activities + activities
        activity_map = {a.get("activityId"): a for a in all_activities}
        
        if activity_id not in activity_map:
            return flask_error_response("Activity not found", status_code=404)
        
        activity = activity_map[activity_id]
        point_value = activity.get("pointValue", 1)
        
        # Validate activity belongs to player's club (club-wide or team-specific)
        activity_club_id = activity.get("clubId")
        activity_team_id = activity.get("teamId")
        if activity_club_id != club_id:
            return flask_error_response("Activity does not belong to player's club", status_code=403)
        if activity_team_id and activity_team_id != team_id:
            return flask_error_response("Activity does not belong to player's team", status_code=403)
        
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
            club_id=club_id,
        )
        
        # Build response
        response_data = {
            "tracking": tracking_record,
            "dailyScore": daily_score,
            "completedActivities": completed_activities,
        }
        
        return flask_success_response(response_data, status_code=200)
    except Exception as e:
        import traceback
        print(f"Error in checkin_by_jwt: {e}")
        traceback.print_exc()
        return flask_error_response(
            "An error occurred while updating check-in",
            status_code=500
        )


@app.route('/player/reflection', methods=['PUT'])
def save_reflection_by_jwt():
    """Save/update weekly reflection using JWT token."""
    try:
        body = request.get_json() or {}
        
        went_well = body.get("wentWell", "")
        do_better = body.get("doBetter", "")
        plan_for_week = body.get("planForWeek", "")
        week_id = body.get("weekId")  # Optional, defaults to current week
        
        player, error = get_player_from_jwt()
        if error:
            return error
        
        club_id = player.get("clubId")
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
            club_id=club_id,
        )
        
        # Build response
        response_data = {
            "reflection": reflection,
        }
        
        return flask_success_response(response_data, status_code=200)
    except Exception as e:
        import traceback
        print(f"Error in save_reflection_by_jwt: {e}")
        traceback.print_exc()
        return flask_error_response(
            "An error occurred while saving reflection",
            status_code=500
        )


@app.route('/player/<unique_link>', methods=['GET'])
def get_player(unique_link):
    """Get player data and current week activities."""
    if not unique_link:
        return flask_error_response("Missing uniqueLink parameter", status_code=400)
    
    # Get player by unique link
    player = get_player_by_unique_link(unique_link)
    
    if not player:
        return flask_error_response("Player not found", status_code=404)
    
    if not player.get("isActive", True):
        return flask_error_response("Player is inactive", status_code=403)
    
    club_id = player.get("clubId")
    team_id = player.get("teamId")
    player_id = player.get("playerId")
    current_week_id = get_current_week_id()
    
    if not club_id or not team_id:
        return flask_error_response("Player missing clubId or teamId", status_code=500)
    
    # Validate team is active
    team = get_team_by_id(team_id)
    if not team:
        return flask_error_response("Team not found", status_code=404)
    
    if not team.get("isActive", True):
        return flask_error_response("Team is inactive", status_code=403)
    
    # Get club-wide activities
    club_activities = get_activities_by_club(club_id, active_only=True)
    
    # Get team-specific activities
    team_activities = get_activities_by_team(team_id, active_only=True)
    
    # Combine activities and deduplicate by activityId
    activity_map = {}
    for activity in club_activities + team_activities:
        activity_id = activity.get("activityId")
        if activity_id and activity_id not in activity_map:
            activity_map[activity_id] = activity
    
    activities = list(activity_map.values())
    # Sort by displayOrder
    activities.sort(key=lambda x: x.get("displayOrder", 999))
    
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
            "clubId": club_id,
            "teamId": team_id,
        },
        "currentWeek": {
            "weekId": current_week_id,
            "activities": activities,
            "dailyTracking": daily_tracking,
            "weeklyScore": weekly_score,
        },
    }
    
    return flask_success_response(response_data)


@app.route('/player/<unique_link>/week/<week_id>', methods=['GET'])
def get_week(unique_link, week_id):
    """Get specific week data for a player."""
    if not unique_link:
        return flask_error_response("Missing uniqueLink parameter", status_code=400)
    
    if not week_id:
        return flask_error_response("Missing weekId parameter", status_code=400)
    
    # Validate week ID format
    try:
        week_dates = get_week_dates(week_id)
    except Exception:
        return flask_error_response("Invalid weekId format (expected YYYY-WW)", status_code=400)
    
    # Get player by unique link
    player = get_player_by_unique_link(unique_link)
    
    if not player:
        return flask_error_response("Player not found", status_code=404)
    
    if not player.get("isActive", True):
        return flask_error_response("Player is inactive", status_code=403)
    
    club_id = player.get("clubId")
    team_id = player.get("teamId")
    player_id = player.get("playerId")
    
    if not club_id or not team_id:
        return flask_error_response("Player missing clubId or teamId", status_code=500)
    
    # Validate team is active
    team = get_team_by_id(team_id)
    if not team:
        return flask_error_response("Team not found", status_code=404)
    
    if not team.get("isActive", True):
        return flask_error_response("Team is inactive", status_code=403)
    
    # Get club-wide activities
    club_activities = get_activities_by_club(club_id, active_only=True)
    
    # Get team-specific activities
    team_activities = get_activities_by_team(team_id, active_only=True)
    
    # Combine activities and deduplicate by activityId
    activity_map = {}
    for activity in club_activities + team_activities:
        activity_id = activity.get("activityId")
        if activity_id and activity_id not in activity_map:
            activity_map[activity_id] = activity
    
    activities = list(activity_map.values())
    # Sort by displayOrder
    activities.sort(key=lambda x: x.get("displayOrder", 999))
    
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
        "clubId": club_id,
        "teamId": team_id,
        "activities": activities,
        "dailyTracking": daily_tracking,
        "weeklyScore": weekly_score,
        "reflection": reflection if reflection else None,
    }
    
    return flask_success_response(response_data)


@app.route('/player/<unique_link>/progress', methods=['GET'])
def get_progress(unique_link):
    """Get aggregated progress statistics (for My Progress page)."""
    if not unique_link:
        return flask_error_response("Missing uniqueLink parameter", status_code=400)
    
    # Get player by unique link
    player = get_player_by_unique_link(unique_link)
    
    if not player:
        return flask_error_response("Player not found", status_code=404)
    
    if not player.get("isActive", True):
        return flask_error_response("Player is inactive", status_code=403)
    
    club_id = player.get("clubId")
    team_id = player.get("teamId")
    player_id = player.get("playerId")
    current_week_id = get_current_week_id()
    
    if not club_id or not team_id:
        return flask_error_response("Player missing clubId or teamId", status_code=500)
    
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
    
    return flask_success_response(response_data)


@app.route('/player/<unique_link>/checkin', methods=['POST'])
def checkin(unique_link):
    """Mark activity complete for a day."""
    if not unique_link:
        return flask_error_response("Missing uniqueLink parameter", status_code=400)
    
    body = request.get_json() or {}
    
    activity_id = body.get("activityId")
    date = body.get("date")  # YYYY-MM-DD format
    completed = body.get("completed", True)  # True to mark complete, False to unmark
    
    if not activity_id:
        return flask_error_response("Missing activityId in request body", status_code=400)
    
    if not date:
        return flask_error_response("Missing date in request body", status_code=400)
    
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return flask_error_response("Invalid date format (expected YYYY-MM-DD)", status_code=400)
    
    # Get player by unique link
    player = get_player_by_unique_link(unique_link)
    
    if not player:
        return flask_error_response("Player not found", status_code=404)
    
    if not player.get("isActive", True):
        return flask_error_response("Player is inactive", status_code=403)
    
    club_id = player.get("clubId")
    team_id = player.get("teamId")
    player_id = player.get("playerId")
    current_week_id = get_current_week_id()
    
    if not club_id or not team_id:
        return flask_error_response("Player missing clubId or teamId", status_code=500)
    
    # Validate team is active
    team = get_team_by_id(team_id)
    if not team:
        return flask_error_response("Team not found", status_code=404)
    
    if not team.get("isActive", True):
        return flask_error_response("Team is inactive", status_code=403)
    
    # Get club-wide activities
    club_activities = get_activities_by_club(club_id, active_only=True)
    
    # Get team-specific activities
    activities = get_activities_by_team(team_id, active_only=True)
    
    # Combine activities for validation
    all_activities = club_activities + activities
    activity_map = {a.get("activityId"): a for a in all_activities}
    
    if activity_id not in activity_map:
        return flask_error_response("Activity not found", status_code=404)
    
    activity = activity_map[activity_id]
    point_value = activity.get("pointValue", 1)
    
    # Validate activity belongs to player's club (club-wide or team-specific)
    activity_club_id = activity.get("clubId")
    activity_team_id = activity.get("teamId")
    if activity_club_id != club_id:
        return flask_error_response("Activity does not belong to player's club", status_code=403)
    if activity_team_id and activity_team_id != team_id:
        return flask_error_response("Activity does not belong to player's team", status_code=403)
    
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
        club_id=club_id,
    )
    
    # Build response
    response_data = {
        "tracking": tracking_record,
        "dailyScore": daily_score,
        "completedActivities": completed_activities,
    }
    
    return flask_success_response(response_data, status_code=200)


@app.route('/player/<unique_link>/reflection', methods=['PUT'])
def save_reflection(unique_link):
    """Save/update weekly reflection."""
    if not unique_link:
        return flask_error_response("Missing uniqueLink parameter", status_code=400)
    
    body = request.get_json() or {}
    
    went_well = body.get("wentWell", "")
    do_better = body.get("doBetter", "")
    plan_for_week = body.get("planForWeek", "")
    week_id = body.get("weekId")  # Optional, defaults to current week
    
    # Get player by unique link
    player = get_player_by_unique_link(unique_link)
    
    if not player:
        return flask_error_response("Player not found", status_code=404)
    
    if not player.get("isActive", True):
        return flask_error_response("Player is inactive", status_code=403)
    
    club_id = player.get("clubId")
    team_id = player.get("teamId")
    player_id = player.get("playerId")
    
    if not club_id or not team_id:
        return flask_error_response("Player missing clubId or teamId", status_code=500)
    
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
        club_id=club_id,
    )
    
    # Build response
    response_data = {
        "reflection": reflection,
    }
    
    return flask_success_response(response_data, status_code=200)


# ============================================================================
# Leaderboard Endpoint
# ============================================================================

@app.route('/leaderboard/<week_id>', methods=['GET'])
def get_leaderboard(week_id):
    """Get leaderboard for a week (validates uniqueLink in query for context)."""
    if not week_id:
        return flask_error_response("Missing weekId parameter", status_code=400)
    
    # Validate week ID format
    try:
        week_dates = get_week_dates(week_id)
    except Exception:
        return flask_error_response("Invalid weekId format (expected YYYY-WW)", status_code=400)
    
    # Get uniqueLink and scope from query parameters
    unique_link = request.args.get("uniqueLink")
    scope = request.args.get("scope", "team")  # Default to "team", can be "club"
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
    
    return flask_success_response(response_data)


# ============================================================================
# Content Endpoints
# ============================================================================

@app.route('/content', methods=['GET'])
def list_content():
    """List all published content pages."""
    # Get uniqueLink from query parameters to get player's club/team context
    unique_link = request.args.get("uniqueLink")
    
    club_id = None
    team_id = None
    
    if unique_link:
        player = get_player_by_unique_link(unique_link)
        if player:
            club_id = player.get("clubId")
            team_id = player.get("teamId")
    
    if not club_id or not team_id:
        return flask_error_response("Missing or invalid uniqueLink parameter", status_code=400)
    
    # Get club-wide content pages
    club_content = get_content_pages_by_club(club_id, published_only=True)
    
    # Get team-specific content pages
    team_content = get_content_pages_by_team(team_id, published_only=True)
    
    # Combine content and deduplicate by pageId
    content_map = {}
    for page in club_content + team_content:
        page_id = page.get("pageId")
        if page_id and page_id not in content_map:
            content_map[page_id] = page
    
    content_pages = list(content_map.values())
    # Sort by displayOrder
    content_pages.sort(key=lambda x: x.get("displayOrder", 999))
    
    # Format response (exclude full HTML content from list view)
    content_list = []
    for page in content_pages:
        # Determine scope
        page_team_id = page.get("teamId")
        scope = "team" if page_team_id else "club"
        
        content_list.append({
            "pageId": page.get("pageId"),
            "slug": page.get("slug"),
            "title": page.get("title"),
            "category": page.get("category"),
            "scope": scope,
            "displayOrder": page.get("displayOrder"),
            "lastUpdated": page.get("updatedAt"),
        })
    
    # Build response
    response_data = {
        "content": content_list,
        "total": len(content_list),
    }
    
    return flask_success_response(response_data)


@app.route('/content/<slug>', methods=['GET'])
def get_content(slug):
    """Get specific content page by slug."""
    if not slug:
        return flask_error_response("Missing slug parameter", status_code=400)
    
    # Get uniqueLink from query parameters to get player's club/team context
    unique_link = request.args.get("uniqueLink")
    
    club_id = None
    team_id = None
    
    if unique_link:
        player = get_player_by_unique_link(unique_link)
        if player:
            club_id = player.get("clubId")
            team_id = player.get("teamId")
    
    if not club_id or not team_id:
        return flask_error_response("Missing or invalid uniqueLink parameter", status_code=400)
    
    # Get club-wide content pages
    club_content = get_content_pages_by_club(club_id, published_only=False)
    
    # Get team-specific content pages
    team_content = get_content_pages_by_team(team_id, published_only=False)
    
    # Search for content page by slug in both club and team content
    content_page = None
    for page in club_content + team_content:
        if page.get("slug") == slug:
            # Validate content belongs to player's club
            page_club_id = page.get("clubId")
            if page_club_id != club_id:
                continue
            # If team-specific, validate it belongs to player's team
            page_team_id = page.get("teamId")
            if page_team_id and page_team_id != team_id:
                continue
            content_page = page
            break
    
    if not content_page:
        return flask_error_response("Content page not found", status_code=404)
    
    # Check if published
    if not content_page.get("isPublished", False):
        return flask_error_response("Content page not published", status_code=403)
    
    # Determine scope
    page_team_id = content_page.get("teamId")
    scope = "team" if page_team_id else "club"
    
    # Build response (include full HTML content)
    response_data = {
        "pageId": content_page.get("pageId"),
        "slug": content_page.get("slug"),
        "title": content_page.get("title"),
        "category": content_page.get("category"),
        "scope": scope,
        "htmlContent": content_page.get("htmlContent"),
        "lastUpdated": content_page.get("updatedAt"),
        "createdAt": content_page.get("createdAt"),
    }
    
    return flask_success_response(response_data)


# ============================================================================
# Catch-all route for debugging (must be last)
# ============================================================================

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def catch_all(path):
    """Catch-all route to debug unmatched routes."""
    print(f"DEBUG CATCH-ALL: Unmatched route!")
    print(f"  Full path parameter: {path}")
    print(f"  Request path: {request.path}")
    print(f"  Request URL: {request.url}")
    print(f"  Method: {request.method}")
    print(f"  All registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"    {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")
    return flask_error_response(
        f"Route not found: {request.path}",
        status_code=404
    )


# ============================================================================
# Lambda Handler
# ============================================================================

def lambda_handler(event, context):
    """Lambda handler wrapper for Flask app."""
    print(f"DEBUG lambda_handler: Event keys: {list(event.keys())}")
    print(f"DEBUG lambda_handler: Request path from event: {event.get('path', 'N/A')}")
    print(f"DEBUG lambda_handler: HTTP method: {event.get('httpMethod', 'N/A')}")
    return handle_request(app, event, context)

