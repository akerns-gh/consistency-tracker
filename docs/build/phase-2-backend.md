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
- `GET /player/{uniqueLink}` - Get player data and current week activities
- `GET /player/{uniqueLink}/week/{weekId}` - Get specific week data
- `GET /player/{uniqueLink}/progress` - Get aggregated progress statistics (for My Progress page)
- `POST /player/{uniqueLink}/checkin` - Mark activity complete for a day
- `PUT /player/{uniqueLink}/reflection` - Save/update weekly reflection
- `GET /leaderboard/{weekId}` - Get leaderboard (validates uniqueLink in query)
- `GET /content` - List all published content pages
- `GET /content/{slug}` - Get specific content page by slug

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
- Player management: CRUD operations
- Activity management: CRUD operations (including activity types: flyout/link, required days, goals)
- Content management: CRUD, publish/unpublish, reorder
- Image upload: Pre-signed S3 URL generation
- Team overview and analytics (charts, reflection highlights)
- Week management (advance week)
- Coach invitation (Cognito integration)
- Navigation menu management (update navigation.json structure)

**Lambda functions to create:**
- `cdk/lambda/admin/players.py` - List, create, update, deactivate players
- `cdk/lambda/admin/activities.py` - CRUD for activities
- `cdk/lambda/admin/content.py` - CRUD for content pages
- `cdk/lambda/admin/content_publish.py` - Publish/unpublish content
- `cdk/lambda/admin/content_reorder.py` - Update display order
- `cdk/lambda/admin/image_upload.py` - Generate pre-signed S3 URLs
- `cdk/lambda/admin/overview.py` - Team statistics
- `cdk/lambda/admin/export.py` - Export week data (CSV)
- `cdk/lambda/admin/week_advance.py` - Advance to next week
- `cdk/lambda/admin/reflections.py` - View all player reflections

## 2.4 API Gateway Configuration
- Create REST API Gateway
- Set up Cognito authorizer for admin endpoints
- Configure CORS for frontend domain
- Set up request/response models
- Configure API Gateway integrations with Lambda functions
- Set up proper error handling and response formatting

**Key implementation:**
- `cdk/stacks/api_stack.py` - API Gateway with all routes and authorizers

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

