# Phase 2: Backend API Development

## Overview
Develop all Lambda functions for player and admin endpoints, configure API Gateway, and set up storage infrastructure (S3, CloudFront, Route 53).

**Estimated Time:** 12-16 hours

## 2.1 Lambda Function Structure
- Create Lambda layer for shared code (boto3, utilities, HTML sanitization with bleach)
- Set up Lambda function directory structure
- Create shared utilities module for DynamoDB operations, error handling

**Files to create:**
- `cdk/lambda/` - Lambda function code
- `cdk/lambda/layer/` - Lambda layer with shared dependencies
- `cdk/lambda/shared/` - Shared utility modules
- `cdk/lambda/shared/db_utils.py` - DynamoDB helper functions
- `cdk/lambda/shared/html_sanitizer.py` - HTML sanitization using bleach
- `cdk/lambda/shared/response.py` - API response formatting

## 2.2 Player Endpoints (No Auth Required)
- `GET /player/{uniqueLink}` - Get player data and current week activities (returns clubId and teamId)
- `GET /player/{uniqueLink}/week/{weekId}` - Get specific week data (returns clubId and teamId)
- `GET /player/{uniqueLink}/progress` - Get aggregated progress statistics (returns clubId and teamId)
- `POST /player/{uniqueLink}/checkin` - Mark activity complete for a day (validates activity belongs to player's club)
- `PUT /player/{uniqueLink}/reflection` - Save/update weekly reflection (stores clubId and teamId)
- `GET /leaderboard/{weekId}?scope=team|club` - Get leaderboard with scope parameter (team or club)
- `GET /content?uniqueLink={uniqueLink}` - List all published content pages (club-wide + team-specific)
- `GET /content/{slug}?uniqueLink={uniqueLink}` - Get specific content page by slug (checks both club-wide and team-specific)

**Lambda functions to create:**
- `cdk/lambda/get_player.py` - Get player data and current week
- `cdk/lambda/get_week.py` - Get specific week data
- `cdk/lambda/get_progress.py` - Get aggregated progress statistics (My Progress page)
- `cdk/lambda/checkin.py` - Mark activity complete for a day
- `cdk/lambda/save_reflection.py` - Save/update weekly reflection
- `cdk/lambda/get_leaderboard.py` - Get leaderboard for a week
- `cdk/lambda/list_content.py` - List all published content pages
- `cdk/lambda/get_content.py` - Get specific content page by slug

## 2.3 Admin Endpoints (Cognito Auth Required)
- **Club management**: CRUD operations (restricted)
- **Team management**: CRUD operations (requires clubId, validates access)
- Player management: CRUD operations (filters by club, validates team belongs to club)
- Activity management: CRUD operations (supports club-wide and team-specific, validates club access)
- Content management: CRUD, publish/unpublish, reorder (supports club-wide and team-specific)
- Image upload: Pre-signed S3 URL generation
- Club overview and analytics (charts, reflection highlights)
- Week management (advance week for all teams in club)
- Coach invitation (Cognito integration)
- Navigation menu management (update navigation.json structure)
- **User role verification**: Check if authenticated user has admin role (via Cognito groups)
- **Authorization middleware**: Validate admin role and club access before processing admin endpoint requests

**Lambda functions to create:**
- `cdk/lambda/admin/clubs.py` - Club CRUD operations (NEW)
- `cdk/lambda/admin/teams.py` - Team CRUD operations (NEW)
- `cdk/lambda/admin/players.py` - List, create, update, deactivate players (filters by club)
- `cdk/lambda/admin/activities.py` - CRUD for activities (supports club-wide and team-specific)
- `cdk/lambda/admin/content.py` - CRUD for content pages (supports club-wide and team-specific)
- `cdk/lambda/admin/content_publish.py` - Publish/unpublish content
- `cdk/lambda/admin/content_reorder.py` - Update display order
- `cdk/lambda/admin/image_upload.py` - Generate pre-signed S3 URLs
- `cdk/lambda/admin/overview.py` - Club statistics (filters by club)
- `cdk/lambda/admin/export.py` - Export week data (CSV, filters by club)
- `cdk/lambda/admin/week_advance.py` - Advance to next week (for all teams in club)
- `cdk/lambda/admin/reflections.py` - View all player reflections (filters by club)
- `cdk/lambda/admin/check_role.py` - Verify user's admin role (for frontend navigation)

**Shared utilities:**
- `cdk/lambda/shared/auth_utils.py` - Helper functions to extract clubId from JWT, check Cognito group membership, verify admin role
- `cdk/lambda/shared/db_utils.py` - Helper functions for club-aware queries (get_club_by_id, get_teams_by_club, get_players_by_club, etc.)

## 2.4 API Gateway Configuration
- Create REST API Gateway
- Set up Cognito authorizer for admin endpoints
- Configure CORS for frontend domain
- Set up request/response models
- Configure API Gateway integrations with Lambda functions
- Set up proper error handling and response formatting
- Pass Cognito user groups/claims to Lambda functions for role verification

**Key implementation:**
- `cdk/stacks/api_stack.py` - API Gateway with all routes and authorizers
- Ensure Cognito authorizer passes user groups/claims in request context to Lambda functions

## 2.5 Storage Stack (S3 & CloudFront)
- Create S3 bucket for React frontend hosting (private)
- Create S3 bucket for content images (private)
- Create CloudFront distribution for frontend with S3 origin
- Create CloudFront distribution for content images
- Configure Origin Access Identity (OAI) for both
- Set up SSL certificates via ACM
- Configure CloudFront error pages (404 -> index.html for React routing)
- Set up cache behaviors for optimal performance

**Key implementation:**
- `cdk/stacks/storage_stack.py` - S3 buckets, CloudFront distributions, ACM certificates

## 2.6 DNS Stack (Route 53)
- Create hosted zone for domain
- Configure A record pointing to CloudFront distribution
- Set up certificate validation records
- Configure subdomain for content images (optional)

**Key implementation:**
- `cdk/stacks/dns_stack.py` - Route 53 configuration

