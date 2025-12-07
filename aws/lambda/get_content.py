"""
Lambda function: GET /content/{slug}
Get specific content page by slug.
"""

from shared.response import success_response, error_response, cors_preflight_response
from shared.db_utils import get_content_page_by_slug


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
        
        # Get teamId from query parameters (for multi-tenant, default to None for now)
        query_params = event.get("queryStringParameters") or {}
        team_id = query_params.get("teamId")
        
        # For now, single team mode - in Phase 7, this will be required
        if not team_id:
            # Default team for single-tenant mode
            team_id = "default-team"
        
        # Get content page by slug
        content_page = get_content_page_by_slug(team_id, slug)
        
        if not content_page:
            return error_response("Content page not found", status_code=404)
        
        # Check if published
        if not content_page.get("isPublished", False):
            return error_response("Content page not published", status_code=403)
        
        # Build response (include full HTML content)
        response_data = {
            "pageId": content_page.get("pageId"),
            "slug": content_page.get("slug"),
            "title": content_page.get("title"),
            "category": content_page.get("category"),
            "htmlContent": content_page.get("htmlContent"),
            "lastUpdated": content_page.get("updatedAt"),
            "createdAt": content_page.get("createdAt"),
        }
        
        return success_response(response_data)
        
    except Exception as e:
        print(f"Error in get_content: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

