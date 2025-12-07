"""
Lambda function: GET /content
List all published content pages.
"""

from shared.response import success_response, error_response, cors_preflight_response
from shared.db_utils import get_content_pages_by_team


def lambda_handler(event, context):
    """Handle GET /content request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Get teamId from query parameters (for multi-tenant, default to None for now)
        query_params = event.get("queryStringParameters") or {}
        team_id = query_params.get("teamId")
        
        # For now, single team mode - in Phase 7, this will be required
        if not team_id:
            # Default team for single-tenant mode
            team_id = "default-team"
        
        # Get published content pages
        content_pages = get_content_pages_by_team(team_id, published_only=True)
        
        # Format response (exclude full HTML content from list view)
        content_list = []
        for page in content_pages:
            content_list.append({
                "pageId": page.get("pageId"),
                "slug": page.get("slug"),
                "title": page.get("title"),
                "category": page.get("category"),
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

