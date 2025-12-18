"""
Lambda function: GET /content/{slug}
Get specific content page by slug.
"""

from shared.response import success_response, error_response, cors_preflight_response
from shared.db_utils import (
    get_player_by_unique_link,
    get_content_pages_by_club,
    get_content_pages_by_team,
)


def lambda_handler(event, context):
    """Handle GET /content/{slug} request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Extract slug from path parameters
        slug = event.get("pathParameters", {}).get("slug")
        
        if not slug:
            return error_response("Missing slug parameter", status_code=400)
        
        # Get uniqueLink from query parameters to get player's club/team context
        query_params = event.get("queryStringParameters") or {}
        unique_link = query_params.get("uniqueLink")
        
        club_id = None
        team_id = None
        
        if unique_link:
            player = get_player_by_unique_link(unique_link)
            if player:
                club_id = player.get("clubId")
                team_id = player.get("teamId")
        
        if not club_id or not team_id:
            return error_response("Missing or invalid uniqueLink parameter", status_code=400)
        
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
            return error_response("Content page not found", status_code=404)
        
        # Check if published
        if not content_page.get("isPublished", False):
            return error_response("Content page not published", status_code=403)
        
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
        
        return success_response(response_data)
        
    except Exception as e:
        print(f"Error in get_content: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

