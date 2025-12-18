# Phase 2: Backend API Development

## Overview
Develop Flask applications for player and admin endpoints, configure API Gateway with proxy integration, and set up storage infrastructure (S3, CloudFront, Route 53).

**Estimated Time:** 12-16 hours

**Note:** This phase uses Flask applications deployed as Lambda functions instead of individual Lambda handlers. This provides better code organization, centralized error handling, and easier maintenance.

## 2.1 Flask Application Structure
- Create Lambda layer for shared code (boto3, Flask, serverless-wsgi, utilities, HTML sanitization with bleach)
- Set up Flask application structure with two main apps (player and admin)
- Create shared utilities module for DynamoDB operations, error handling, and authentication

**Files to create:**
- `aws/lambda/` - Lambda function code
- `aws/lambda/layer/python/` - Lambda layer with shared dependencies (Flask, serverless-wsgi, boto3, bleach, python-jose)
- `aws/lambda/shared/` - Shared utility modules
- `aws/lambda/shared/db_utils.py` - DynamoDB helper functions
- `aws/lambda/shared/html_sanitizer.py` - HTML sanitization using bleach
- `aws/lambda/shared/flask_auth.py` - Flask authentication decorators and utilities
- `aws/lambda/shared/auth_utils.py` - Helper functions to extract clubId from JWT, check Cognito group membership, verify admin role
- `aws/lambda/shared/response.py` - API response formatting
- `aws/lambda/shared/week_utils.py` - Week calculation utilities

## 2.2 Player Flask Application
Create a single Flask application (`player_app.py`) that handles all player-facing endpoints. Player endpoints are public (no authentication required).

**Endpoints to implement:**
- `GET /player/{uniqueLink}` - Get player data and current week activities (returns clubId and teamId)
- `GET /player/{uniqueLink}/week/{weekId}` - Get specific week data (returns clubId and teamId)
- `GET /player/{uniqueLink}/progress` - Get aggregated progress statistics (returns clubId and teamId)
- `POST /player/{uniqueLink}/checkin` - Mark activity complete for a day (validates activity belongs to player's club)
- `PUT /player/{uniqueLink}/reflection` - Save/update weekly reflection (stores clubId and teamId)
- `GET /leaderboard/{weekId}?scope=team|club` - Get leaderboard with scope parameter (team or club)
- `GET /content?uniqueLink={uniqueLink}` - List all published content pages (club-wide + team-specific)
- `GET /content/{slug}?uniqueLink={uniqueLink}` - Get specific content page by slug (checks both club-wide and team-specific)

**File to create:**
- `aws/lambda/player_app.py` - Flask application with all player routes

**Key features:**
- Use Flask route decorators (`@app.route()`) for each endpoint
- Use `serverless_wsgi` to handle API Gateway events
- Implement CORS headers for all responses
- Use shared utilities from `shared/` modules
- Centralized error handling with Flask error handlers

## 2.3 Admin Flask Application
Create a single Flask application (`admin_app.py`) that handles all admin endpoints. All admin endpoints require Cognito authentication and admin role verification.

**Endpoints to implement:**
- **Club management**: CRUD operations (restricted)
- **Team management**: CRUD operations (requires clubId, validates access)
- **Player management**: CRUD operations (filters by club, validates team belongs to club)
- **Activity management**: CRUD operations (supports club-wide and team-specific, validates club access)
- **Content management**: CRUD, publish/unpublish, reorder (supports club-wide and team-specific, validates club ownership on all operations)
- **Image upload**: Pre-signed S3 URL generation
- **Club overview and analytics**: Charts, reflection highlights
- **Week management**: Advance week for all teams in club
- **Coach invitation**: Cognito integration
- **Navigation menu management**: Update navigation.json structure
- **User role verification**: Check if authenticated user has admin role (via Cognito groups)

**File to create:**
- `aws/lambda/admin_app.py` - Flask application with all admin routes (14 endpoints)

**Key features:**
- Use Flask authentication decorators (`@require_admin`, `@require_club`, `@require_club_access`, `@require_resource_access`)
- Automatic user context loading (`g.current_user`, `g.club_id`) via decorators
- Use `serverless_wsgi` to handle API Gateway events
- Implement CORS headers for all responses
- Centralized error handling with Flask error handlers
- Resource-level access control via decorators

**Shared utilities:**
- `aws/lambda/shared/flask_auth.py` - Flask authentication decorators and utilities
- `aws/lambda/shared/auth_utils.py` - Helper functions to extract clubId from JWT, check Cognito group membership, verify admin role
- `aws/lambda/shared/db_utils.py` - Helper functions for club-aware queries (get_club_by_id, get_teams_by_club, get_players_by_club, etc.)

## 2.4 API Gateway Configuration
- Create REST API Gateway
- Set up Cognito authorizer for admin endpoints
- Configure proxy integration for Flask applications (routes all requests to Flask apps)
- Configure CORS for frontend domain (handled by Flask apps)
- Set up Gateway Responses with CORS headers for error responses
- Pass Cognito user groups/claims to Lambda functions for role verification

**Key implementation:**
- `aws/stacks/api_stack.py` - API Gateway with proxy integration to Flask Lambda functions
- Create 2 Lambda functions: `PlayerAppFunction` and `AdminAppFunction`
- Use proxy integration (`ANY /{proxy+}`) to route all requests to Flask apps
- Flask apps handle routing internally using Flask's routing system
- Ensure Cognito authorizer passes user groups/claims in request context to Lambda functions
- Lambda layer includes Flask 3.0+ and serverless-wsgi dependencies

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

