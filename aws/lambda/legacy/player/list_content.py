"""
Lambda function: GET /content
List all published content pages.
"""

from shared.response import success_response, error_response, cors_preflight_response
from shared.db_utils import (
    get_player_by_unique_link,
    get_content_pages_by_team,
    get_content_pages_by_club,
)


def lambda_handler(event, context):
    """Handle GET /content request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
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
        
        return success_response(response_data)
        
    except Exception as e:
        print(f"Error in list_content: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

