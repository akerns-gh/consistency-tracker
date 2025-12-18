# Phase 6: Testing, Polish & Deployment

## Overview
Comprehensive testing, performance optimization, security validation, deployment to production, and post-deployment setup.

**Estimated Time:** 6-8 hours

## 6.1 Backend Testing
- Test all Flask application endpoints with sample data
- Test DynamoDB operations (CRUD)
- Test HTML sanitization with malicious inputs
- Test image upload flow
- Test Cognito authentication flow
- Test Flask authentication decorators (`@require_admin`, `@require_club`, etc.)
- Load testing with multiple concurrent users

**Testing approach:**
- Manual testing with Postman/curl
- Test both Flask applications: `player_app.py` and `admin_app.py`
- Unit tests for Flask routes (optional)
- Integration tests for API endpoints
- Verify proxy integration works correctly with API Gateway

## 6.2 Frontend Testing
- Test player flow: unique link access, check-in, reflections
- Test My Progress page: aggregated statistics, charts, week navigation
- Test Weekly Tracker: activity grid, flyouts, scoring, week navigation
- Test Leaderboard: top 3 podium, rankings, week selector
- Test activity flyouts: click activity names to view details
- Test content pages: resource-list, content-page navigation
- Test admin flow: login, CRUD operations
- Test content management: create, edit, publish, WYSIWYG editor
- Test on multiple devices (iOS, Android, desktop browsers)
- Test responsive design at all breakpoints
- Test HTML content rendering and sanitization
- Test navigation menu (slide-out, dynamic rendering)
- Test auto-save functionality for reflections

## 6.3 Security Testing
- Test unique link security (non-guessable)
- Test XSS prevention (HTML sanitization)
- Test authentication and authorization
- Test CORS configuration
- Test API rate limiting
- Test image upload security (file type, size limits)
- Test geographic restrictions (non-US IPs should be blocked with custom error page)

## 6.4 Performance Optimization
- Optimize Lambda cold starts (provisioned concurrency if needed)
- Optimize CloudFront caching strategies
- Optimize React bundle size (code splitting)
- Optimize image sizes and formats
- Test page load times (< 2 seconds target)

## 6.5 Deployment
- Deploy CDK stacks: `cdk deploy --all`
- Create initial admin account in Cognito User Pool (via AWS Console)
- Build React app: `cd app && npm run build`
- Deploy frontend to S3:
  ```bash
  aws s3 sync app/dist/ s3://consistency-tracker-frontend-us-east-1/ --delete
  ```
- Invalidate CloudFront cache:
  ```bash
  aws cloudfront create-invalidation --distribution-id E11CYNQ91MDSZR --paths "/*"
  ```
- Verify CloudFront origin configuration (should use S3 endpoint with OAI, not website endpoint)
- Configure custom domain in Route 53 (if not already done)
- Verify SSL certificate is active
- Test production deployment end-to-end

## 6.6 Post-Deployment Setup
- Set up CloudWatch monitoring and alarms
- Configure DynamoDB automated backups
- Configure IP allowlisting (optional, for restricted access):
  - Run the IP allowlist script: `./scripts/update-waf-ip-allowlist.sh`
  - This script automatically detects your current IPv4 and IPv6 addresses
  - Updates AWS WAF to only allow traffic from your IP addresses
  - Sets default action to "Block" to enforce IP restriction
  - **Note**: Run this script again if your IP address changes
  - See `scripts/README.md` for detailed documentation
- Create initial team data:
  - Default activities (Sleep, Hydration, Daily Wall Ball, 1-Mile Run, Bodyweight Training)
  - Activity configurations (types: flyout/link, required days, goals)
  - Content categories (Guidance, Workouts, Nutrition, Mental Performance, Resources)
  - Navigation menu structure
- Create initial test players (with unique links)
- Set up sample content pages (optional)
- Document admin procedures
- Create user guides (players, parents, coaches)

## 6.7 Monitoring & Maintenance
- Set up CloudWatch dashboard for key metrics
- Configure SNS alerts for errors
- Set up AWS Budget alerts
- Document troubleshooting procedures
- Create runbook for common issues

