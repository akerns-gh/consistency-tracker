"""
Lambda function: Admin content management endpoints
- GET /admin/content - List all content pages
- GET /admin/content/{contentId} - Get specific content for editing
- POST /admin/content - Create new content page
- PUT /admin/content/{contentId} - Update content page
- DELETE /admin/content/{contentId} - Delete content page
"""

import json
import uuid
import re
from datetime import datetime
from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin, get_club_id_from_user
from shared.db_utils import (
    get_table,
    get_content_pages_by_team,
    get_content_pages_by_club,
    get_all_content_pages_by_club,
    get_team_by_id,
)
from shared.html_sanitizer import sanitize_html


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    if not text:
        return ""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


def lambda_handler(event, context):
    """Handle admin content management requests."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Require admin authentication
        user_info = require_admin(event)
        club_id = get_club_id_from_user(event)
        
        if not club_id:
            return error_response("User not associated with a club", status_code=403)
        
        user_email = user_info.get("email") or user_info.get("username")
        
        http_method = event.get("httpMethod")
        path_params = event.get("pathParameters") or {}
        content_id = path_params.get("contentId") or path_params.get("pageId")
        
        table = get_table("ConsistencyTracker-ContentPages")
        
        if http_method == "GET":
            if content_id:
                # Get specific content page
                response = table.get_item(Key={"pageId": content_id})
                if "Item" not in response:
                    return error_response("Content page not found", status_code=404)
                
                content = response["Item"]
                # Validate content belongs to coach's club
                if content.get("clubId") != club_id:
                    return error_response("Content page not found or access denied", status_code=403)
                
                return success_response({"content": content})
            else:
                # List all content pages in club (club-wide + team-specific)
                content_pages = get_all_content_pages_by_club(club_id, published_only=False)
                
                # Format response (exclude full HTML content from list view)
                content_list = []
                for page in content_pages:
                    content_list.append({
                        "pageId": page.get("pageId"),
                        "slug": page.get("slug"),
                        "title": page.get("title"),
                        "category": page.get("category"),
                        "isPublished": page.get("isPublished", False),
                        "displayOrder": page.get("displayOrder"),
                        "createdAt": page.get("createdAt"),
                        "updatedAt": page.get("updatedAt"),
                        "createdBy": page.get("createdBy"),
                        "lastEditedBy": page.get("lastEditedBy"),
                        "clubId": page.get("clubId"),
                        "teamId": page.get("teamId"),
                        "scope": page.get("scope"),
                    })
                
                return success_response({"content": content_list, "total": len(content_list)})
        
        elif http_method == "POST":
            # Create new content page
            try:
                body = json.loads(event.get("body", "{}"))
            except json.JSONDecodeError:
                return error_response("Invalid JSON in request body", status_code=400)
            
            title = body.get("title")
            category = body.get("category", "general")
            html_content = body.get("htmlContent", "")
            slug = body.get("slug") or slugify(title)
            display_order = body.get("displayOrder", 999)
            is_published = body.get("isPublished", False)
            scope = body.get("scope", "team")  # "club" or "team"
            team_id = body.get("teamId")  # Required if scope is "team"
            
            if not title:
                return error_response("Missing required field: title", status_code=400)
            
            # Validate scope and team
            if scope == "team":
                if not team_id:
                    return error_response("Missing required field: teamId for team-specific content", status_code=400)
                # Validate team belongs to coach's club
                team = get_team_by_id(team_id)
                if not team:
                    return error_response("Team not found", status_code=404)
                if team.get("clubId") != club_id:
                    return error_response("Team not found or access denied", status_code=403)
            elif scope == "club":
                team_id = None  # Club-wide content
            else:
                return error_response("Invalid scope (must be 'club' or 'team')", status_code=400)
            
            # Sanitize HTML content
            sanitized_html = sanitize_html(html_content)
            
            # Get max displayOrder to append new content (check against all club content)
            existing_content = get_all_content_pages_by_club(club_id, published_only=False)
            if display_order == 999 and existing_content:
                max_order = max(c.get("displayOrder", 0) for c in existing_content)
                display_order = max_order + 1
            
            # Check if slug already exists (check against all club content)
            for content in existing_content:
                if content.get("slug") == slug:
                    return error_response(f"Slug '{slug}' already exists", status_code=400)
            
            # Create content page
            page_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat() + "Z"
            
            content = {
                "pageId": page_id,
                "clubId": club_id,
                "teamId": team_id,  # None for club-wide, teamId for team-specific
                "scope": scope,
                "slug": slug,
                "title": title,
                "category": category,
                "htmlContent": sanitized_html,
                "isPublished": is_published,
                "displayOrder": display_order,
                "createdBy": user_email,
                "createdAt": now,
                "updatedAt": now,
                "lastEditedBy": user_email,
            }
            
            table.put_item(Item=content)
            
            return success_response({"content": content}, status_code=201)
        
        elif http_method == "PUT":
            # Update content page
            if not content_id:
                return error_response("Missing contentId parameter", status_code=400)
            
            try:
                body = json.loads(event.get("body", "{}"))
            except json.JSONDecodeError:
                return error_response("Invalid JSON in request body", status_code=400)
            
            # Get existing content
            existing = table.get_item(Key={"pageId": content_id})
            if "Item" not in existing:
                return error_response("Content page not found", status_code=404)
            
            existing_content = existing["Item"]
            
            # Validate content belongs to coach's club
            if existing_content.get("clubId") != club_id:
                return error_response("Content page not found or access denied", status_code=403)
            
            # Update allowed fields
            update_expression_parts = []
            expression_attribute_values = {}
            
            if "title" in body:
                update_expression_parts.append("title = :title")
                expression_attribute_values[":title"] = body["title"]
            
            if "category" in body:
                update_expression_parts.append("category = :category")
                expression_attribute_values[":category"] = body["category"]
            
            if "htmlContent" in body:
                # Sanitize HTML content
                sanitized_html = sanitize_html(body["htmlContent"])
                update_expression_parts.append("htmlContent = :htmlContent")
                expression_attribute_values[":htmlContent"] = sanitized_html
            
            if "slug" in body:
                # Check if new slug already exists (check against all club content)
                new_slug = body["slug"]
                existing_content_list = get_all_content_pages_by_club(club_id, published_only=False)
                for content in existing_content_list:
                    if content.get("pageId") != content_id and content.get("slug") == new_slug:
                        return error_response(f"Slug '{new_slug}' already exists", status_code=400)
                
                update_expression_parts.append("slug = :slug")
                expression_attribute_values[":slug"] = new_slug
            
            if "scope" in body:
                # Allow changing scope, but validate
                new_scope = body["scope"]
                new_team_id = body.get("teamId")  # Can be null for club scope
                
                if new_scope == "team":
                    if not new_team_id:
                        return error_response("Missing teamId for team-scoped content update", status_code=400)
                    new_team = get_team_by_id(new_team_id)
                    if not new_team or new_team.get("clubId") != club_id:
                        return error_response("New target team not found or access denied", status_code=403)
                    update_expression_parts.append("teamId = :teamId")
                    expression_attribute_values[":teamId"] = new_team_id
                else:  # new_scope == "club"
                    update_expression_parts.append("teamId = :teamId")
                    expression_attribute_values[":teamId"] = None  # Set teamId to null for club-wide
                
                update_expression_parts.append("scope = :scope")
                expression_attribute_values[":scope"] = new_scope
            
            if "displayOrder" in body:
                update_expression_parts.append("displayOrder = :displayOrder")
                expression_attribute_values[":displayOrder"] = body["displayOrder"]
            
            if "isPublished" in body:
                update_expression_parts.append("isPublished = :isPublished")
                expression_attribute_values[":isPublished"] = body["isPublished"]
            
            if not update_expression_parts:
                return error_response("No fields to update", status_code=400)
            
            # Add updatedAt and lastEditedBy
            update_expression_parts.append("updatedAt = :updatedAt")
            update_expression_parts.append("lastEditedBy = :lastEditedBy")
            expression_attribute_values[":updatedAt"] = datetime.utcnow().isoformat() + "Z"
            expression_attribute_values[":lastEditedBy"] = user_email
            
            # Perform update
            table.update_item(
                Key={"pageId": content_id},
                UpdateExpression="SET " + ", ".join(update_expression_parts),
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW",
            )
            
            # Get updated content
            updated = table.get_item(Key={"pageId": content_id})
            return success_response({"content": updated.get("Item")})
        
        elif http_method == "DELETE":
            # Delete content page
            if not content_id:
                return error_response("Missing contentId parameter", status_code=400)
            
            # Get existing content
            existing = table.get_item(Key={"pageId": content_id})
            if "Item" not in existing:
                return error_response("Content page not found", status_code=404)
            
            existing_content = existing["Item"]
            # Validate content belongs to coach's club
            if existing_content.get("clubId") != club_id:
                return error_response("Content page not found or access denied", status_code=403)
            
            # Delete content
            table.delete_item(Key={"pageId": content_id})
            
            return success_response({"message": "Content page deleted successfully"})
        
        else:
            return error_response(f"Method not allowed: {http_method}", status_code=405)
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/content: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)
