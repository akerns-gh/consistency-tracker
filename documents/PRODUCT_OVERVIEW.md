# Consistency Tracker - Product Overview

**Document Version:** 1.0  
**Date:** January 2025  
**Audience:** Senior VP of Product

---

## Executive Summary

The Consistency Tracker is a multi-tenant web application designed for youth lacrosse organizations to track player consistency across key daily activities (sleep, hydration, training, etc.). The application enables players to log daily habits, view progress over time, and engage in friendly competition through leaderboards. Coaches and administrators can manage teams, track player engagement, and deliver educational content.

**Current Status:** Production-ready with core functionality complete. The application is fully deployed and operational, supporting multiple clubs with complete data isolation.

**Key Metrics:**
- **Architecture:** Serverless (AWS Lambda, DynamoDB, CloudFront)
- **Multi-Tenancy:** Full support for multiple clubs with isolated data
- **User Types:** Players, Coaches, Club Administrators, Platform Administrators
- **Deployment:** Fully automated with infrastructure-as-code (AWS CDK)

---

## Application Overview

### Purpose
The Consistency Tracker helps youth lacrosse organizations:
1. **Track Player Consistency** - Monitor daily habits that contribute to athletic performance
2. **Drive Engagement** - Gamify consistency through leaderboards and progress tracking
3. **Deliver Content** - Provide educational resources (workouts, nutrition, mental performance)
4. **Enable Reflection** - Support weekly self-reflection for player development

### Target Users

**Players (Primary Users)**
- Ages 10-18
- Track daily activities via simple check-in interface
- View personal progress and statistics
- Access team leaderboards
- Complete weekly reflections
- Browse educational content

**Coaches**
- Manage team activities and configurations
- View player progress and engagement metrics
- Create and manage educational content pages
- Review player reflections
- Export weekly reports

**Club Administrators**
- Manage multiple teams within a club
- Create teams and assign coaches
- Manage club-wide content and activities
- Access club-level analytics

**Platform Administrators**
- Create and manage clubs
- Manage club administrators
- Platform-wide configuration and oversight

---

## Current Capabilities

### 1. Player Features ✅ **COMPLETE**

#### Activity Tracking
- **Weekly Grid View**: Monday-Sunday layout showing current week
- **Daily Check-ins**: Simple checkbox interface to mark activities complete
- **Activity Types**: Support for configurable activities (sleep, hydration, training, etc.)
- **Visual Feedback**: Color-coded cells (green = complete, yellow = frequency target at risk)
- **Daily Scoring**: Automatic calculation of daily consistency scores
- **Historical Views**: Access to previous weeks' data

#### Progress & Analytics
- **My Progress Dashboard**: 
  - Aggregated statistics (total check-ins, consistency percentage)
  - Weekly breakdown charts
  - Activity-specific progress tracking
- **Progress Charts**: Visual representation of consistency over time
- **Summary Cards**: Quick view of key metrics

#### Leaderboard
- **Team Rankings**: Real-time leaderboard showing all players ranked by weekly score
- **Historical Leaderboards**: View rankings for any past week
- **Podium Visualization**: Top 3 players highlighted
- **Privacy**: Full visibility within team/club context

#### Weekly Reflections
- **Three Reflection Questions**:
  1. "What went well?"
  2. "What can I do better?"
  3. "What am I doing this week to do better?"
- **Auto-save**: Automatically saves every 30 seconds
- **Editable**: Players can update reflections throughout the week
- **Private**: Visible only to player, parents, and coaches (not on leaderboard)

#### Content Access
- **Resource Navigation**: Menu-driven access to educational content
- **Content Categories**: 
  - Training Guidance
  - Workout Plans
  - Nutrition Tips
  - Mental Performance
  - Recovery
  - General Resources
- **Rich Content**: HTML pages with embedded videos, images, and formatted text
- **Mobile Responsive**: Optimized for mobile devices

### 2. Admin/Coach Features ✅ **COMPLETE**

#### Player Management
- **Create Players**: Add new players with automatic Cognito user account creation
- **Edit Players**: Update names and team assignments
- **Activate/Deactivate**: Enable or disable player accounts
- **Email Invitations**: Automated email with temporary passwords
- **Bulk Import**: CSV upload for multiple players
- **Status Tracking**: View player verification status and activity
- **View As Player**: Admins can view the application from any player's perspective
  - See exactly what players see
  - Navigate through all player pages
  - Read-only mode (cannot modify player data)
  - Useful for troubleshooting and support

#### Activity Management
- **Create/Edit Activities**: Define custom activities for teams/clubs
- **Activity Configuration**:
  - Name and description
  - Frequency requirements (daily, 3x/week, etc.)
  - Point values for scoring
  - Display order
- **Activity Types**: Support for "flyout" (detailed HTML content) and "link" (navigation to content page)
- **Club-wide or Team-specific**: Activities can be shared across club or limited to specific teams

#### Team Management
- **Create Teams**: Add new teams within a club
- **Team Configuration**: Set team names and settings
- **Coach Assignment**: Add multiple coaches per team
- **Coach Management**: Create, edit, activate/deactivate coaches
- **Team Status**: Activate/deactivate teams

#### Club Management (App Admins Only)
- **Create Clubs**: Add new clubs to the platform
- **Club Administrators**: Assign club admins during club creation
- **Club Settings**: Manage club-wide configuration
- **View As Club Admin**: App-admins can temporarily view and manage any club as if they were a club administrator
  - Access all club-specific tabs (Players, Activities, Content, Teams)
  - All operations are scoped to the selected club
  - Useful for troubleshooting, support, and training

#### Content Management System
- **WYSIWYG Editor**: Rich text editor for creating HTML content (no HTML knowledge required)
- **Content Creation**:
  - Headings, paragraphs, lists, links
  - Image uploads (stored in S3, served via CloudFront)
  - Video embeds (YouTube, Vimeo)
  - Text formatting (bold, italic, etc.)
- **Content Organization**:
  - Categorization (Guidance, Workouts, Nutrition, etc.)
  - Drag-and-drop reordering
  - Publish/unpublish functionality
  - Preview before publishing
- **Content Scope**: Club-wide or team-specific content
- **Version Tracking**: Track creator and last editor

#### Analytics & Reporting
- **Team Overview Dashboard**:
  - Aggregate player statistics
  - Engagement metrics
  - Weekly summaries
- **Reflection Highlights**: View all player reflections for a week
- **Charts & Visualizations**: Team-wide progress charts
- **Export Functionality**: CSV export for weekly reports (API ready, UI pending)

#### Week Management
- **Manual Week Advancement**: Coaches can advance to next week
- **Historical Data**: View and analyze past weeks
- **Week-based Queries**: All data organized by week (YYYY-WW format)

### 3. Authentication & Security ✅ **COMPLETE**

#### User Authentication
- **AWS Cognito Integration**: All users authenticate via Cognito User Pool
- **Password Requirements**: Minimum 12 characters, uppercase, lowercase, number
- **First-time Login**: Temporary password with forced password change
- **Email Verification**: Required for all new users
- **Password Reset**: Automated via Cognito/SES

#### Role-Based Access Control
- **Hierarchical Admin Groups**:
  - `app-admin`: Platform-wide access
  - `club-{clubName}-admins`: Club-level access
  - `coach-{clubId}-{teamId}`: Team-level access
- **Automatic Group Creation**: Groups created automatically when clubs/teams are created
- **JWT-based Authorization**: All API calls validated with Cognito JWT tokens

#### Data Security
- **Multi-Tenant Isolation**: Complete data isolation between clubs
- **Team-level Filtering**: Optional team-specific data views
- **HTML Sanitization**: All user-generated content sanitized to prevent XSS
- **CORS Protection**: Restricted to approved domains
- **WAF Integration**: IP-based access restrictions (optional)

### 4. Infrastructure & Deployment ✅ **COMPLETE**

#### AWS Architecture
- **Frontend**: React.js static site on S3 + CloudFront CDN
- **Backend**: Flask applications on AWS Lambda
- **Database**: DynamoDB (on-demand pricing, point-in-time recovery)
- **API Gateway**: REST API with custom domain (api.repwarrior.net)
- **Email**: AWS SES with custom domain (Proton Mail integration)
- **DNS**: Route 53 for domain management
- **Infrastructure as Code**: AWS CDK (Python)

#### Deployment
- **Automated Deployment**: One-command deployment scripts
- **Data Protection**: All tables protected with RETAIN policy
- **Custom Domain**: repwarrior.net (frontend) and api.repwarrior.net (API)
- **SSL/TLS**: Automated certificate management via ACM

---

## Data Model

### Core Entities

#### Clubs
- **Primary Key**: `clubId` (UUID)
- **Attributes**: `clubName`, `createdAt`, `updatedAt`
- **Isolation**: Top-level tenant boundary

#### Teams
- **Primary Key**: `teamId` (UUID)
- **Attributes**: `teamName`, `clubId`, `isActive`, `createdAt`, `updatedAt`
- **GSI**: `clubId-index` (query teams by club)
- **Relationship**: Belongs to one club

#### Players
- **Primary Key**: `playerId` (UUID)
- **Attributes**: 
  - `firstName`, `lastName`, `email`
  - `clubId`, `teamId`
  - `isActive`, `verificationStatus`
  - `createdAt`, `updatedAt`
- **GSIs**: 
  - `teamId-index` (query players by team)
  - `clubId-index` (query players by club)
- **Authentication**: Cognito user account (email as username)

#### Coaches
- **Primary Key**: `coachId` (UUID)
- **Attributes**: 
  - `firstName`, `lastName`, `email`
  - `clubId`, `teamId`
  - `isActive`, `verificationStatus`
  - `createdAt`, `updatedAt`
- **GSIs**: 
  - `teamId-index` (query coaches by team)
  - `clubId-index` (query coaches by club)
  - `email-index` (lookup by email)
- **Authentication**: Cognito user account + group membership

#### Club Administrators
- **Primary Key**: `adminId` (UUID)
- **Attributes**: 
  - `firstName`, `lastName`, `email`
  - `clubId`
  - `isActive`, `verificationStatus`
  - `createdAt`, `updatedAt`
- **GSIs**: 
  - `clubId-index` (query admins by club)
  - `email-index` (lookup by email)
- **Authentication**: Cognito user account + group membership

#### Activities
- **Primary Key**: `activityId` (UUID)
- **Attributes**: 
  - `name`, `description`
  - `frequency` (daily, 3x/week, etc.)
  - `pointValue` (for scoring)
  - `displayOrder`
  - `activityType` (flyout, link)
  - `htmlContent` (for flyout type)
  - `linkUrl` (for link type)
  - `clubId`, `teamId` (null for club-wide)
  - `isActive`
  - `createdAt`, `updatedAt`
- **GSIs**: 
  - `teamId-index` (query activities by team)
  - `clubId-index` (query activities by club)
- **Scope**: Can be club-wide or team-specific

#### Tracking Records
- **Primary Key**: `trackingId` (composite: `playerId#weekId#date`)
- **Attributes**: 
  - `playerId`, `weekId`, `date` (YYYY-MM-DD)
  - `clubId`, `teamId`
  - `completedActivities` (array of activityIds)
  - `dailyScore` (calculated)
  - `createdAt`, `updatedAt`
- **GSIs**: 
  - `playerId-index` (query all records for a player)
  - `weekId-index` (query all records for a week - leaderboard)
  - `teamId-index` (query all records for a team)
  - `clubId-index` (query all records for a club)

#### Reflections
- **Primary Key**: `reflectionId` (composite: `playerId#weekId`)
- **Attributes**: 
  - `playerId`, `weekId`
  - `clubId`, `teamId`
  - `wentWell`, `doBetter`, `planForWeek`
  - `createdAt`, `updatedAt`
- **GSIs**: 
  - `playerId-index` (query all reflections for a player)
  - `teamId-index` (query all reflections for a team)
  - `clubId-index` (query all reflections for a club)

#### Content Pages
- **Primary Key**: `pageId` (UUID)
- **Attributes**: 
  - `title`, `slug` (URL-friendly identifier)
  - `category` (guidance, workouts, nutrition, etc.)
  - `htmlContent` (sanitized HTML)
  - `scope` ("club" or "team")
  - `clubId`, `teamId` (null for club-wide)
  - `isPublished`, `displayOrder`
  - `createdBy`, `lastEditedBy` (email)
  - `createdAt`, `updatedAt`
- **GSIs**: 
  - `teamId-index` (query pages by team)
  - `clubId-index` (query pages by club)
- **Scope**: Can be club-wide or team-specific

#### Email Verifications
- **Primary Key**: `token` (UUID)
- **Attributes**: 
  - `email`, `token`, `expiresAt`
  - `createdAt`
- **GSI**: `email-index` (query tokens by email)
- **TTL**: `expiresAt` (auto-delete expired tokens)

### Data Relationships

```
Club (1) ──< (many) Teams
Club (1) ──< (many) Club Admins
Team (1) ──< (many) Players
Team (1) ──< (many) Coaches
Team (1) ──< (many) Activities (optional - can be club-wide)
Team (1) ──< (many) Content Pages (optional - can be club-wide)
Player (1) ──< (many) Tracking Records (one per day per week)
Player (1) ──< (many) Reflections (one per week)
```

### Multi-Tenancy Architecture

**Data Isolation Strategy:**
- **Primary Isolation**: All queries filtered by `clubId` (derived from authenticated user)
- **Secondary Filtering**: Optional `teamId` filtering for team-specific views
- **Security**: Never trust client-provided `clubId` or `teamId` - always derive from JWT token
- **GSI Design**: All tables include `clubId-index` for efficient club-based queries

---

## Status: Complete vs Pending

### ✅ **COMPLETE** - Core Functionality

#### Infrastructure & Foundation
- ✅ AWS CDK infrastructure (all stacks)
- ✅ DynamoDB tables with proper schemas and GSIs
- ✅ Cognito User Pool with hierarchical admin groups
- ✅ API Gateway with custom domain
- ✅ S3 + CloudFront for frontend hosting
- ✅ AWS SES email configuration
- ✅ Route 53 DNS configuration
- ✅ Multi-tenant data isolation

#### Player Features
- ✅ Activity tracking interface (weekly grid view)
- ✅ Daily check-in functionality
- ✅ Progress dashboard with charts
- ✅ Leaderboard (current and historical weeks)
- ✅ Weekly reflections (with auto-save)
- ✅ Content browsing and viewing
- ✅ Player authentication (Cognito)
- ✅ Email verification flow

#### Admin Features
- ✅ Player management (CRUD operations)
- ✅ Activity management (CRUD operations)
- ✅ Team management (CRUD operations)
- ✅ Coach management (CRUD operations)
- ✅ Club management (App Admins only)
- ✅ Content Management System (WYSIWYG editor)
- ✅ Team overview dashboard
- ✅ Reflection viewing
- ✅ Week advancement
- ✅ CSV import for players
- ✅ Admin authentication (Cognito with role-based access)

#### Security & Operations
- ✅ Multi-tenant data isolation
- ✅ Role-based access control (hierarchical admin groups)
- ✅ HTML content sanitization
- ✅ CORS protection
- ✅ Email notifications (invitations, confirmations)
- ✅ Automated deployment scripts
- ✅ Data protection (RETAIN policies)

### ⚠️ **PARTIALLY COMPLETE** - Needs Enhancement

#### Export Functionality
- ✅ **API Endpoint**: CSV export endpoint implemented (`/admin/export/{weekId}`)
- ⚠️ **UI Integration**: Export button/functionality in admin dashboard (pending UI implementation)
- **Status**: Backend ready, frontend integration needed

#### Testing
- ✅ **Core Functionality**: Team activation/deactivation tested and verified
- ✅ **API Endpoints**: Player and coach endpoints code-verified (follow same patterns as teams)
- ⚠️ **UI Verification**: Some player/coach management UI interactions pending visual verification
- ⚠️ **Integration Tests**: Edge cases and error handling tests pending
- **Status**: Core functionality tested, comprehensive test suite in progress

### 📋 **PENDING** - Future Enhancements

#### Features Out of Scope for V1 (Per Requirements)
- Email/SMS reminders for daily check-ins
- Parent notification when player checks in
- Mobile app (native iOS/Android)
- Streak tracking (consecutive days)
- Rewards/badges for milestones
- Photo uploads for proof of completion
- Social features (comments, encouragement)
- Integration with wearables (sleep tracking, etc.)

#### Potential Enhancements (Not Yet Prioritized)
- PDF export for weekly reports (currently CSV only)
- Advanced analytics and trend analysis
- Bulk operations for player management
- Activity templates for quick setup
- Content version history
- Automated week advancement (currently manual)
- Notification system for coaches (player engagement alerts)
- Parent portal (separate from player account)

---

## Technical Architecture

### Frontend
- **Framework**: React.js with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Context API (AuthContext)
- **Build Tool**: Vite
- **Deployment**: S3 + CloudFront CDN
- **Domain**: repwarrior.net

### Backend
- **Runtime**: Python 3.9+ on AWS Lambda
- **Framework**: Flask (2 Flask apps: player_app.py, admin_app.py)
- **API Style**: RESTful
- **Authentication**: AWS Cognito JWT tokens
- **API Domain**: api.repwarrior.net

### Database
- **Primary Database**: AWS DynamoDB
- **Billing**: On-demand (pay-per-request)
- **Backup**: Point-in-time recovery enabled
- **Tables**: 12 tables with appropriate GSIs for query patterns

### Infrastructure
- **IaC**: AWS CDK (Python)
- **Stacks**: 
  - Database Stack (DynamoDB tables)
  - Auth Stack (Cognito User Pool)
  - API Stack (API Gateway + Lambda)
  - Storage Stack (S3 + CloudFront)
  - DNS Stack (Route 53)
  - SES Stack (Email configuration)

### Security
- **Authentication**: AWS Cognito
- **Authorization**: JWT-based with role groups
- **Data Isolation**: Multi-tenant with club-level isolation
- **Content Security**: HTML sanitization, XSS prevention
- **Network**: CORS restrictions, optional WAF

---

## Key Metrics & Performance

### Current Capabilities
- **Concurrent Users**: Designed for 30+ concurrent users per team
- **Response Time**: API responses < 500ms (target)
- **Page Load**: < 2 seconds on 3G connection (target)
- **Scalability**: Serverless architecture scales automatically
- **Cost Model**: Pay-per-use (DynamoDB on-demand, Lambda per request)

### Data Volume (Estimated)
- **Players per Team**: 15-30 typical
- **Teams per Club**: 1-10 typical
- **Tracking Records**: ~7 per player per week (one per day)
- **Content Pages**: 10-50 per club/team typical

---

## Deployment Status

### Production Environment
- **Status**: ✅ Fully Deployed and Operational
- **Domain**: repwarrior.net (frontend), api.repwarrior.net (API)
- **Region**: us-east-1
- **Data Protection**: All tables protected with RETAIN policy
- **Backup**: Point-in-time recovery enabled on all tables

### Deployment Process
- **Infrastructure**: Automated via `aws/deploy.sh`
- **Frontend**: Automated via `scripts/deploy-frontend.sh`
- **Rollback**: Supported via CDK stack management
- **Monitoring**: CloudWatch logs for all Lambda functions

---

## Conclusion

The Consistency Tracker application is **production-ready** with all core functionality complete and operational. The application successfully delivers on its primary objectives:

1. ✅ **Player Engagement**: Daily tracking, progress visualization, and leaderboards
2. ✅ **Coach Management**: Comprehensive admin tools for team and player management
3. ✅ **Content Delivery**: Full CMS for educational resources
4. ✅ **Multi-Tenancy**: Complete support for multiple clubs with data isolation
5. ✅ **Security**: Robust authentication and authorization with role-based access

**Next Steps:**
- Complete UI integration for export functionality
- Expand test coverage for edge cases
- Gather user feedback for prioritization of future enhancements
- Consider mobile app development based on user demand

---

**Document Prepared By:** Development Team  
**Last Updated:** January 2025  
**For Questions:** Contact development team or review technical documentation in `/documents` directory

