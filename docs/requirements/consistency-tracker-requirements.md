# Youth Lacrosse Consistency Tracker - Application Requirements

## Project Overview
Build a web-based consistency tracking application for a youth lacrosse team that allows players to track daily habits, view their progress, and compare performance with teammates through a leaderboard.

## Technical Stack
- **Frontend**: React.js (static site)
- **Hosting**: AWS S3 + CloudFront CDN
- **Infrastructure as Code**: AWS CDK (Python)
- **Database**: AWS DynamoDB (serverless, on-demand pricing)
- **API**: AWS API Gateway + Lambda functions (Python)
- **Authentication**: 
  - Players/Parents: Passwordless via unique links (magic links)
  - Coaches/Admin: AWS Cognito User Pool with email/password
- **Domain**: To be provided by user (will be configured in AWS Route 53)
- **SSL/TLS**: AWS Certificate Manager (ACM)

## Target Users
- **Players**: Youth lacrosse team members (ages 10-18 estimated)
- **Parents**: View their child's progress (same unique link as player)
- **Coaches/Admin**: Manage activities, view all players, generate player links, view analytics
  - Requires authenticated login via AWS Cognito
  - Multiple coaches can have access (email/password based)
  - Coach accounts created and managed by primary admin

## Core Features

### 1. User Access & Authentication

**Player/Parent Passwordless Access via Unique Links**
- Each player receives a unique URL (e.g., `app.domain.com/player/abc123xyz`)
- No username/password required - bookmark the link to access
- Link provides access to both player view and parent view (same permissions)
- Links should be non-guessable (UUID or similar)

**Coach/Admin Authentication via AWS Cognito**
- Coaches access admin dashboard at `app.domain.com/admin`
- Login with email and password through AWS Cognito User Pool
- Support for multiple coach accounts with same permissions
- Password requirements: minimum 8 characters, including uppercase, lowercase, number
- Password reset functionality via email
- Session management with JWT tokens
- Optional: MFA (Multi-Factor Authentication) for enhanced security

**Coach Account Management**
- Primary admin (you) creates initial Cognito User Pool via AWS Console
- Ability to invite additional coaches via email
- Coaches receive invitation email with temporary password
- Must change password on first login
- Coaches can be added/removed from Cognito User Pool
- All coaches have full admin dashboard access (no role hierarchy in V1)

### 2. Activity Tracking Interface
**Week-by-Week Grid View**
- Display current week by default (Monday-Sunday)
- Show previous weeks in archive/history section
- Track the following default activities:
  - Sleep (8+ hrs)
  - Hydration (8 glasses of water)
  - Daily Wall Ball (20 mins)
  - 1-Mile Run
  - Bodyweight Training (10 mins)
- Activities should be configurable by admin (add/remove/edit)

**Daily Check-in**
- Simple checkbox or tap interface to mark activity complete
- Visual feedback: Green/yellow highlighting based on completion
- Yellow denotes frequency targets (configurable per activity)
- Calculate daily consistency score (0-5 based on activities completed)
- Show running weekly total (sum of daily scores)

**Frequency Tracking**
- Some activities may have frequency requirements (e.g., 3x per week minimum)
- Highlight cells in yellow when frequency target is at risk
- Mark completion with checkmark or 'X' notation

### 3. Leaderboard
**Team Comparison View**
- Display all players ranked by weekly consistency score
- Show player name/nickname and weekly total
- Update in real-time as players check in
- Option to view historical week leaderboards
- Keep it positive and motivational (no shaming for low scores)

**Privacy Considerations**
- Players see full leaderboard with all names
- Optional: Allow players to opt for anonymous display on leaderboard
- Parents see full leaderboard (same as players)

### 4. Weekly Reflection Questions
**End-of-Week Reflection**
- Display three reflection questions at bottom of weekly view:
  1. "What went well?"
  2. "What can I do better?"
  3. "What am I doing this week to do better?"
- Text input fields for free-form responses
- Responses saved per player per week
- Players can edit their reflections throughout the week
- Reflections visible to player, parents, and coach only (not on leaderboard)

### 5. Admin/Coach Dashboard
**Player Management**
- Add new players (generate unique link automatically)
- Edit player information (name, email for parent notifications if implemented later)
- Deactivate players (archive, don't delete data)
- View/copy unique links for distribution

**Activity Management**
- Create/edit/delete tracked activities
- Set frequency requirements per activity (daily, 3x/week, etc.)
- Reorder activities in display
- Set point values per activity for consistency scoring

**Content Pages Management**
- Create/edit/delete custom HTML content pages
- WYSIWYG editor for easy content creation (no HTML knowledge required)
- Categories: Guidance, Workouts, Nutrition, Mental Health, Resources
- Drag-and-drop to reorder pages in navigation
- Preview before publishing
- Publish/unpublish pages
- Track who created and last edited each page
- Embed videos, images, and links

**Team Overview**
- View all players' data in aggregate
- Export weekly reports (CSV or PDF)
- View all reflection responses
- Historical trends and analytics

**Week Management**
- Manually advance to new week (or auto-advance on Monday)
- Archive old weeks
- View historical data by week

**Content/Resources Management (NEW)**
- Create and edit HTML content pages (guidance, workouts, nutrition tips)
- Rich text editor with formatting options (bold, italic, lists, links, images)
- Organize content by type/category
- Publish/unpublish content
- Reorder content for display
- Preview content before publishing
- Content accessible to players via navigation menu

### 6. Content/Resources Pages
**Player-Accessible Content**
- Navigation menu showing available content categories:
  - Training Guidance
  - Workout Plans
  - Nutrition Tips
  - Mental Performance
  - General Resources
- Each page displays full HTML content created by coaches
- Clean, readable layout matching True Lacrosse aesthetic
- Mobile-responsive content display
- "Last Updated" timestamp visible
- Back to dashboard navigation

## Data Model

### Coach/Admin Table (AWS Cognito User Pool)
```
Managed by AWS Cognito - no DynamoDB table needed
Cognito stores:
- email (username)
- password (hashed)
- name
- email_verified
- custom:role (future use for permissions)
- created_at
- updated_at
```

### Player Table (DynamoDB)
```
{
  playerId: string (UUID, primary key),
  name: string,
  email: string (optional, for future parent notifications),
  uniqueLink: string (secure token),
  createdAt: timestamp,
  isActive: boolean,
  teamId: string (for future multi-team support)
}
```

### Activity Table (DynamoDB)
```
{
  activityId: string (UUID, primary key),
  name: string,
  description: string,
  frequency: string (daily, 3x/week, etc.),
  pointValue: number (for consistency score),
  displayOrder: number,
  isActive: boolean,
  teamId: string
}
```

### Tracking Table (DynamoDB)
```
{
  trackingId: string (composite: playerId#weekId#date, primary key),
  playerId: string (GSI),
  weekId: string (YYYY-WW format, GSI),
  date: string (YYYY-MM-DD),
  completedActivities: array of activityIds,
  dailyScore: number,
  createdAt: timestamp,
  updatedAt: timestamp
}
```

### Reflection Table (DynamoDB)
```
{
  reflectionId: string (composite: playerId#weekId, primary key),
  playerId: string,
  weekId: string (YYYY-WW format),
  wentWell: string,
  doBetter: string,
  planForWeek: string,
  createdAt: timestamp,
  updatedAt: timestamp
}
```

### Team/Config Table (DynamoDB)
```
{
  teamId: string (primary key),
  teamName: string,
  coachName: string,
  adminAccessCode: string (for coach login),
  settings: {
    weekStartDay: string (default: Monday),
    autoAdvanceWeek: boolean,
    scoringMethod: string
  }
}
```

### Content Pages Table (DynamoDB)
```
{
  pageId: string (UUID, primary key),
  clubId: string (GSI for querying all club pages - primary isolation),
  teamId: string (GSI for querying team pages, can be null for club-wide content),
  scope: string ("club" or "team" - indicates if content is club-wide or team-specific),
  slug: string (URL-friendly identifier, e.g., "nutrition-guide"),
  title: string,
  category: string (guidance, workouts, nutrition, mental-health, etc.),
  htmlContent: string (full HTML content, sanitized),
  isPublished: boolean,
  displayOrder: number (for sorting in navigation),
  createdBy: string (coach email),
  createdAt: timestamp,
  updatedAt: timestamp,
  lastEditedBy: string (coach email)
}
```

### Content/Resources Table (DynamoDB)
```
{
  contentId: string (UUID, primary key),
  teamId: string (GSI),
  title: string,
  slug: string (URL-friendly, e.g., "wall-ball-drills"),
  contentType: string (guidance, workout, nutrition, mental, general),
  htmlContent: string (full HTML content),
  isPublished: boolean,
  displayOrder: number,
  createdBy: string (coach email),
  createdAt: timestamp,
  updatedAt: timestamp,
  lastEditedBy: string (coach email)
}
```

## API Endpoints

### Player Endpoints (No Authentication Required - Validated by Unique Link)
- `GET /player/{uniqueLink}` - Get player data and activities
- `GET /player/{uniqueLink}/week/{weekId}` - Get specific week data
- `POST /player/{uniqueLink}/checkin` - Mark activity complete
- `PUT /player/{uniqueLink}/reflection` - Save weekly reflection
- `GET /leaderboard/{weekId}` - Get leaderboard for week (requires valid uniqueLink as query param for context)
- `GET /content` - List all published content/resources
- `GET /content/{slug}` - Get specific content page by slug

### Admin Endpoints (Require Cognito JWT Token in Authorization Header)
- `POST /admin/auth` - Exchange Cognito credentials for JWT (handled by Cognito, not custom endpoint)
- `GET /admin/players` - List all players
- `POST /admin/players` - Create new player (returns unique link)
- `PUT /admin/players/{playerId}` - Update player info
- `DELETE /admin/players/{playerId}` - Deactivate player
- `GET /admin/activities` - List all activities
- `POST /admin/activities` - Create activity
- `PUT /admin/activities/{activityId}` - Update activity
- `DELETE /admin/activities/{activityId}` - Delete activity
- `GET /admin/overview` - Team statistics and overview
- `GET /admin/export/{weekId}` - Export week data
- `POST /admin/week/advance` - Move to next week
- `GET /admin/reflections` - View all player reflections
- `POST /admin/coaches/invite` - Invite new coach (sends Cognito invitation)
- `GET /admin/content` - List all content pages (published and unpublished)
- `GET /admin/content/{contentId}` - Get specific content for editing
- `POST /admin/content` - Create new content page
- `PUT /admin/content/{contentId}` - Update content page
- `DELETE /admin/content/{contentId}` - Delete content page
- `PUT /admin/content/{contentId}/publish` - Publish/unpublish content
- `PUT /admin/content/reorder` - Update display order of content pages
- `POST /admin/content/image-upload-url` - Generate pre-signed S3 URL for image upload

### Authentication Flow
**Coach Login:**
1. Frontend sends email/password to Cognito via AWS SDK
2. Cognito returns JWT access token, ID token, and refresh token
3. Frontend stores tokens in secure storage (httpOnly cookies or localStorage)
4. All subsequent admin API calls include: `Authorization: Bearer {accessToken}`
5. API Gateway validates JWT against Cognito User Pool
6. Lambda functions receive authenticated user info in event context

## Design & Branding

### Visual Identity
The app should match the True Lacrosse brand aesthetic from https://truelacrosse.com/

**Color Palette:**
- **Primary Colors:**
  - Navy Blue: `#0A1F44` (dark navy, primary brand color)
  - Bright Blue/Cyan: `#00A8E8` (accent color for CTAs and highlights)
  - White: `#FFFFFF` (backgrounds, text on dark)
  
- **Secondary Colors:**
  - Light Gray: `#F5F5F5` (backgrounds, cards)
  - Medium Gray: `#6B7280` (secondary text, borders)
  - Dark Gray: `#1F2937` (primary text)
  
- **Status Colors:**
  - Success Green: `#10B981` (completed activities)
  - Warning Yellow: `#FCD34D` (frequency warnings)
  - Red/Orange: `#EF4444` (alerts, incomplete)

**Typography:**
- **Headings**: Sans-serif, bold, modern (similar to True Lacrosse)
  - Consider: Inter, Montserrat, or Poppins
  - Font weights: 600-800 for headings
  - All caps for section headers to match True Lacrosse style
  
- **Body Text**: Clean, readable sans-serif
  - Font weight: 400-500 for body
  - Line height: 1.6 for readability
  
- **Size Scale:**
  - H1: 2.5rem (40px) - Page titles
  - H2: 2rem (32px) - Section headers
  - H3: 1.5rem (24px) - Card headers
  - Body: 1rem (16px) - Standard text
  - Small: 0.875rem (14px) - Labels, captions

**Design Elements:**
- **Modern & Athletic**: Clean lines, bold typography, high contrast
- **Professional yet approachable**: Inspire confidence while being youth-friendly
- **Action-oriented**: Strong CTAs with bright blue accent color
- **Card-based layouts**: Elevated cards with subtle shadows (like True Lacrosse sections)
- **Hero sections**: Large, bold headers with supporting text
- **Icons**: Simple, line-based icons for activities and navigation

**Button Styles:**
- Primary buttons: Bright blue background, white text, rounded corners
- Secondary buttons: Navy outline, navy text, rounded corners
- Hover states: Slightly darker/brighter with smooth transitions
- Large, tappable areas for mobile (min 44px height)

**Imagery & Graphics:**
- Use lacrosse-related imagery sparingly (stick patterns, field lines as subtle backgrounds)
- Player photos should be action-oriented and inspirational
- Maintain lots of white space for clean, modern feel

## User Interface Requirements

### Design Principles
- **Mobile-first**: Must work well on phones (players will primarily use mobile)
- **Simple and clean**: Minimal clicks to check in
- **Visual feedback**: Clear indication of completion status
- **Motivational**: Positive reinforcement, celebration of consistency
- **Fast loading**: Optimize for quick access
- **Brand alignment**: Match True Lacrosse's premium, professional aesthetic

### Player View - Main Screen
- **Header**: 
  - Navy blue background with white text
  - Player name in bold, large font
  - Current week dates (e.g., "Week of Nov 18-24")
  - Weekly score displayed prominently with bright blue highlight
  - Navigation menu icon (hamburger) on right side
  
- **Navigation Menu** (Slide-out or dropdown):
  - My Progress (default view)
  - Leaderboard
  - Training Guidance (links to content pages)
  - Workouts
  - Nutrition Tips
  - Mental Performance
  - Resources
  - Weekly Reflection
  
- **Activity Grid**:
  - Clean white card with subtle shadow
  - 7 columns (Mon-Sun) with day abbreviations in navy
  - N rows for activities with activity names on left
  - Each cell: Large checkbox or tap-to-toggle circle
  - Visual states:
    - Complete: Bright green checkmark on light green background
    - Incomplete: Empty circle with light gray border
    - Frequency warning: Yellow border/background
  
- **Daily Score Row**:
  - Bottom of grid in navy blue background
  - White text showing "X/5" for each day
  - Bold, easy to read
  
- **Weekly Total**:
  - Large card below grid with bright blue background
  - White text: "Weekly Score: XX/35"
  - Progress bar visualization
  
- **Action Buttons**:
  - "View Leaderboard" - Bright blue, full width
  - "Weekly Reflection" - Navy outline button
  - Positioned at bottom, easy thumb reach
  
- **Reflection Section**:
  - Collapsible card or separate view
  - Three text areas with labels in navy
  - White background, subtle borders
  - Auto-save indicator

### Content Page View
- **Header**:
  - Navy blue with back button
  - Page title in white text
  - "Last Updated: [date]" in small text
  
- **Content Area**:
  - White background with generous padding
  - HTML content rendered with proper styling
  - Headings in navy (True Lacrosse style)
  - Links in bright blue
  - Images responsive and centered
  - Lists with proper formatting
  - Embedded videos (YouTube/Vimeo) responsive
  
- **Typography in Content**:
  - Matches True Lacrosse aesthetic
  - Readable font sizes (minimum 16px body)
  - Good line height (1.6-1.8)
  - Proper heading hierarchy
  
- **Mobile Optimization**:
  - Content scrolls smoothly
  - Images scale to screen width
  - Text doesn't require horizontal scrolling
  - Touch-friendly link spacing

### Leaderboard View
- **Hero Header**:
  - Navy blue background with gradient
  - Large white text: "TEAM LEADERBOARD"
  - Week selector dropdown in bright blue
  
- **Podium Top 3**:
  - Special cards for 1st, 2nd, 3rd place
  - Gold/silver/bronze accent colors
  - Larger player names, prominent scores
  - Trophy/medal icons
  
- **Rankings List**:
  - Clean white cards with subtle shadows
  - Each row shows: rank number (in circle), player name, weekly score
  - Current player highlighted with bright blue border
  - Alternating light gray backgrounds for readability
  
- **Stats Summary**:
  - Small card at bottom showing:
    - Team average score
    - Most improved player
    - Perfect week count
  
- **Navigation**:
  - Back button (navy) to return to player view
  - Week history toggle in bright blue

### Admin Dashboard

**Login Page (New)**
- Clean, centered login form on navy blue background
- White card container with True Lacrosse branding
- Email and password input fields
- "Sign In" button (bright blue)
- "Forgot Password?" link below (navy text)
- Error messages displayed in red above form
- "Remember me" checkbox option
- Responsive design (works on mobile and desktop)

**Post-Login Navigation:**
- Top Navigation Bar:
  - Navy blue background
  - White text navigation: Players | Activities | Content | Overview | Settings
  - Active tab highlighted with bright blue underline
  - True Lacrosse style all-caps labels
  - Logout button on far right
  
**Players Tab:**
  - Clean table layout with white cards
  - Column headers in navy
  - Action buttons in bright blue (Add Player, View, Edit, Copy Link)
  - Search/filter bar at top
  - Player status indicators (active/inactive) with color coding
  
**Activities Tab:**
  - Card-based layout for each activity
  - Drag handles for reordering (navy icons)
  - Inline editing with bright blue save buttons
  - Add Activity button prominent at top (bright blue)
  - Toggle switches for active/inactive (blue when on)

**Content Tab (NEW):**
  - **Content List View**:
    - Table/card view of all content pages
    - Columns: Title, Type, Status (Published/Draft), Last Updated, Actions
    - Filter by content type dropdown
    - Search bar for finding content
    - "Add New Content" button (bright blue) prominent at top
    - Drag handles for reordering within each category
    - Actions: Edit, Preview, Publish/Unpublish, Delete
    
  - **Content Editor View**:
    - Two-panel layout (desktop) or stacked (mobile)
    - Left panel: Editor controls
      - Title input field
      - Content type selector (dropdown)
      - Slug field (auto-generated from title, editable)
      - Display order number
      - Published toggle switch (blue when on)
    - Main panel: Rich text editor
      - WYSIWYG HTML editor (TinyMCE or similar)
      - Formatting toolbar:
        - Text styles: Bold, Italic, Underline
        - Headings: H1, H2, H3, H4
        - Lists: Bullets, Numbered
        - Alignment: Left, Center, Right
        - Links: Insert/edit hyperlinks
        - Images: Upload or URL
        - Embedded videos: YouTube/Vimeo URLs
        - Tables: Insert/edit tables
        - HTML source view for advanced editing
      - Live preview mode toggle
      - Character count display
    - Bottom actions:
      - Save Draft (navy outline button)
      - Preview (navy outline button)
      - Publish (bright blue button)
      - Cancel (gray text link)
    
  - **Content Preview**:
    - Shows exactly how content appears to players
    - Matches player view styling
    - "Edit" and "Close" buttons at top
  
**Overview Tab:**
  - Summary cards at top (white with colored accents):
    - Total players (blue accent)
    - Average team score (green accent)
    - Week-over-week trend (arrow indicators)
    - Content pages published (purple accent)
  - Charts and graphs with navy/blue color scheme
  - Reflection highlights section with most common themes
  - Export button (bright blue) prominent at top right
  
**Settings Tab:**
  - Form-based layout with labeled sections
  - Coach management section (add/remove coach accounts)
  - Team information (name, description)
  - Default activities configuration
  - Content categories management
  - Toggle switches and dropdowns
  - Navy labels, blue interactive elements
  - Save changes button (bright blue, sticky bottom)

**Overall Admin Aesthetic:**
- Professional data dashboard feel
- Generous white space between sections
- Clear visual hierarchy with navy headers
- Bright blue for all CTAs and interactive elements
- Responsive grid layout (1 column mobile, 2-3 columns desktop)

### Responsive Breakpoints
- Mobile: < 768px (single column, stacked layout)
- Tablet: 768px - 1024px (optimized grid)
- Desktop: > 1024px (full dashboard view for admin)

### CSS Framework & Implementation
- **Tailwind CSS** recommended for styling (matches modern approach)
- **Custom theme configuration** to match True Lacrosse colors:
  ```javascript
  // tailwind.config.js
  theme: {
    extend: {
      colors: {
        'true-navy': '#0A1F44',
        'true-blue': '#00A8E8',
        'true-success': '#10B981',
        'true-warning': '#FCD34D',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      }
    }
  }
  ```
- **Component library considerations**:
  - Headless UI or Radix UI for accessible components
  - Custom styled to match True Lacrosse aesthetic
  - Avoid pre-built themes that conflict with branding

### Animation & Interaction
- Smooth transitions (200-300ms) for hover states
- Celebration animation when activities are checked (subtle confetti or checkmark scale)
- Loading states with branded colors
- Skeleton screens while data loads (maintain navy/blue theme)

## Scoring Logic

### Daily Consistency Score
- Base: 1 point per activity completed
- Maximum daily score = number of active activities (typically 5)
- Display: "3/5" or "3 of 5 activities completed"

### Weekly Consistency Score
- Sum of all daily scores for the week
- Maximum weekly score = daily max × 7 (typically 35)
- Leaderboard ranks by weekly score

### Frequency Tracking (Future Enhancement)
- Activities with frequency requirements (e.g., 3x/week) calculate compliance
- Warning indicators if player is behind pace
- Bonus points for hitting frequency targets

## Security & Privacy

### Data Protection
- Unique links should be cryptographically secure (UUID v4 or similar)
- No personally identifiable information exposed in URLs
- HTTPS only (enforced by CloudFront)
- DynamoDB data encrypted at rest (AWS default)
- API rate limiting to prevent abuse (via API Gateway throttling)

### Access Control
- **Players/Parents**: Can only view/edit their own data via unique link validation
- **Coaches**: 
  - Authenticated via AWS Cognito User Pool
  - JWT tokens validated by API Gateway Cognito Authorizer
  - Can view all player data and manage team settings
  - Session timeout after 1 hour (configurable via Cognito)
  - Refresh tokens valid for 30 days
- **API Protection**:
  - All admin endpoints protected by Cognito JWT authorizer
  - Player endpoints validate unique link exists in database
  - CORS configured to only allow requests from approved domains

### Content Security
- **HTML Sanitization**:
  - All user-submitted HTML must be sanitized server-side
  - Use library like bleach (Python) or DOMPurify (JavaScript)
  - Allow safe tags: p, h1-h6, strong, em, ul, ol, li, a, img, br, table, thead, tbody, tr, td, th, iframe (for videos)
  - Strip dangerous tags: script, style, object, embed
  - Sanitize attributes (only allow href, src, alt, title, etc.)
  
- **Image Uploads**:
  - Store images in separate S3 bucket (not main hosting bucket)
  - Validate file types (only allow: jpg, jpeg, png, gif, webp)
  - Limit file size (max 5MB per image)
  - Generate unique filenames to prevent overwrites
  - CloudFront distribution for image delivery
  - Images served from dedicated subdomain (e.g., content.yourdomain.com)
  
- **Video Embeds**:
  - Only allow YouTube and Vimeo iframe embeds
  - Validate URLs match YouTube/Vimeo patterns
  - Strip any JavaScript from iframe attributes
  - Use sandbox attribute on iframes

### Cognito Security Configuration
- Password policy: Minimum 8 characters, require uppercase, lowercase, number
- Account lockout after 5 failed login attempts (15 minute lockout)
- Email verification required for new coach accounts
- Optional MFA (TOTP or SMS) for enhanced security
- Secure password reset flow via email
- JWT token expiration: 1 hour access tokens, 30 day refresh tokens

### Content Management Security
**HTML Sanitization:**
- CRITICAL: All user-submitted HTML content MUST be sanitized before storage
- Use server-side HTML sanitization library (e.g., bleach for Python, DOMPurify for JavaScript)
- Whitelist safe HTML tags: `<p>, <h1-h6>, <strong>, <em>, <ul>, <ol>, <li>, <a>, <img>, <iframe>, <table>, <tr>, <td>, <th>, <br>, <div>, <span>`
- Whitelist safe attributes: `href, src, alt, title, width, height, class, style` (limited)
- Strip all JavaScript: No `<script>` tags or `onclick`/`onerror` attributes
- Allow only HTTPS URLs for links and embedded content
- Validate iframe sources (YouTube, Vimeo domains only)
- Prevent CSS injection through style attributes

**Storage Best Practices:**
- Store sanitized HTML in DynamoDB (max 400KB per item)
- For larger content, store HTML in S3 and reference URL in DynamoDB
- Track content version history (optional for v2)
- Log all content modifications (who, when, what changed)

**XSS Prevention:**
- Server-side sanitization on save (Python Lambda)
- Client-side sanitization on render (React)
- Content Security Policy headers in CloudFront
- Escape user-generated content in reflections and player names

## Performance Requirements
- Page load time: < 2 seconds on 3G connection
- API response time: < 500ms for check-in operations
- Support concurrent usage by entire team (30 users)
- Offline capability: Nice to have (cache last loaded data)

## Future Enhancements (Out of Scope for V1)
- Email/SMS reminders for daily check-ins
- Parent notification when player checks in
- Multi-team support for organization-wide deployment
- Mobile app (native iOS/Android)
- Streak tracking (consecutive days)
- Rewards/badges for milestones
- Custom activity categories (nutrition, academic, etc.)
- Photo uploads for proof of completion
- Social features (comments, encouragement)
- Integration with wearables (sleep tracking, etc.)

## Development Phases

### Phase 1: MVP (Minimum Viable Product)
- Player tracking interface with unique links
- Basic leaderboard
- Admin player management
- Fixed set of 5 activities
- Current week view only
- Coach authentication via Cognito

### Phase 2: Core Features
- Weekly reflection questions
- Historical week views
- Activity management (admin)
- Enhanced leaderboard with history
- Content/Resources management (admin can create HTML pages)
- Content viewing for players (guidance, workouts, etc.)

### Phase 3: Polish & Enhancement
- Improved mobile UX
- Export functionality
- Team analytics
- Custom branding

## Testing Requirements
- Test with 5-10 players initially
- Verify concurrent check-ins don't cause data loss
- Test on multiple devices (iOS, Android, various browsers)
- Validate unique link security
- Load test with 50+ simulated users
- Test HTML sanitization with malicious input attempts
- Verify content page rendering on all device sizes
- Test WYSIWYG editor across browsers

## Technical Implementation Notes

### WYSIWYG Editor Selection
**Recommended Editors:**
1. **TinyMCE** (Recommended)
   - Pros: Feature-rich, excellent mobile support, good customization
   - Free tier available
   - Built-in sanitization options
   - Easy image upload integration with S3
   
2. **Quill**
   - Pros: Lightweight, modern, open source
   - Good for simpler use cases
   - Easy to customize toolbar
   
3. **React Draft Wysiwyg**
   - Pros: Built for React, lightweight
   - Good community support
   - Simpler than TinyMCE

**Editor Configuration:**
- Toolbar buttons: Headings, Bold, Italic, Lists, Links, Images, Video embed
- Image upload: Direct to S3 with pre-signed URLs
- Max content size: 400KB (DynamoDB item limit)
- Auto-save every 30 seconds
- Paste from Word cleanup enabled
- Spell check enabled

### Image Upload Strategy
**S3 Storage for Content Images:**
```
content-images/
  ├── [teamId]/
  │   ├── [pageId]/
  │   │   ├── image1.jpg
  │   │   ├── image2.png
```

**Upload Flow:**
1. User selects image in WYSIWYG editor
2. Frontend requests pre-signed S3 URL from Lambda
3. Image uploads directly to S3 (client-side)
4. S3 URL inserted into HTML content
5. CloudFront serves images with CDN caching

**Image Optimization:**
- Max upload size: 5MB
- Auto-resize large images (Lambda or client-side)
- Convert to WebP for better performance (optional)
- Generate thumbnails for image library view

### Content Categories (Predefined)
- **Guidance**: General advice, best practices, team philosophy
- **Workouts**: Exercise routines, training plans, drills
- **Nutrition**: Meal plans, hydration tips, supplements
- **Mental Performance**: Mindset, goal setting, focus techniques
- **Recovery**: Sleep, rest days, injury prevention
- **Resources**: Links, documents, external content

**Category Customization:**
- Coaches can add custom categories via Settings tab
- Categories appear in player navigation menu
- Empty categories hidden from players

## Development Prerequisites

### Required Tools & Accounts
- **AWS Account**: Active AWS account with administrative access
- **Domain Name**: Registered domain (via Route 53, Namecheap, or other registrar)
- **Development Environment**:
  - Python 3.9+ installed
  - Node.js 18+ and npm (for CDK CLI and React)
  - AWS CLI configured with credentials (`aws configure`)
  - Git for version control
  - Code editor (VS Code recommended)

### AWS CLI Configuration
```bash
# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1 recommended), Output format (json)

# Verify configuration
aws sts get-caller-identity
```

### CDK Prerequisites
```bash
# Install AWS CDK CLI globally
npm install -g aws-cdk

# Verify installation
cdk --version

# Install Python CDK libraries
pip install aws-cdk-lib constructs
```

### AWS Account Setup
1. **Enable required services** in your AWS region:
   - S3, CloudFront, Route 53, DynamoDB
   - Lambda, API Gateway, Cognito
   - ACM, CloudWatch, IAM

2. **Bootstrap CDK** (one-time setup per region):
   ```bash
   cdk bootstrap aws://ACCOUNT-ID/REGION
   ```

3. **Domain preparation**:
   - If using Route 53: Domain already in AWS
   - If external registrar: Prepare to update nameservers to Route 53

## Deployment & Maintenance

### AWS CDK Infrastructure (Python)

**CDK Stack Structure:**
```
aws/
├── app.py                          # CDK app entry point
├── requirements.txt                # Python dependencies
├── cdk.json                        # CDK configuration
└── stacks/
    ├── __init__.py
    ├── storage_stack.py            # S3, CloudFront, Certificate
    ├── database_stack.py           # DynamoDB tables
    ├── auth_stack.py               # Cognito User Pool
    ├── api_stack.py                # API Gateway, Lambda functions
    └── dns_stack.py                # Route 53 configuration
```

**Key CDK Resources to Define:**

1. **S3 & CloudFront (storage_stack.py)**
   - S3 bucket for frontend hosting (private, not public)
   - S3 bucket for content images/media (private, accessed via CloudFront)
   - CloudFront distribution for frontend with S3 origin
   - CloudFront distribution for content media with S3 origin
   - CloudFront Origin Access Identity (OAI) for both distributions
   - SSL certificates from ACM for custom domain and content subdomain
   - Cache behaviors for optimal performance
   - Custom error pages (404 -> index.html for React routing)

2. **DynamoDB Tables (database_stack.py)**
   - Player table with playerId as partition key
   - Activity table with activityId as partition key
   - Tracking table with composite key (playerId#weekId#date)
   - Reflection table with composite key (playerId#weekId)
   - Team/Config table with teamId as partition key
   - Global Secondary Indexes (GSI) as needed for queries
   - On-demand billing mode
   - Point-in-time recovery enabled

3. **Cognito User Pool (auth_stack.py)**
   - User pool for coach authentication
   - Password policy configuration
   - Email verification settings
   - MFA configuration (optional)
   - App client for web application
   - Custom attributes if needed (role, teamId)

4. **API Gateway & Lambda (api_stack.py)**
   - REST API Gateway
   - Cognito authorizer for admin endpoints
   - Lambda functions (Python 3.11+):
     - Player endpoints (5-6 functions)
     - Admin endpoints (15-18 functions):
       - Player management (CRUD)
       - Activity management (CRUD)
       - Content management (CRUD, publish/unpublish, reorder)
       - Image upload pre-signed URL generation
       - Overview and analytics
       - Data export
       - Coach invitation
   - Lambda layers for shared code (boto3, utilities, HTML sanitization)
   - Environment variables for DynamoDB table names and S3 bucket names
   - IAM roles with least privilege access
   - API Gateway request/response models
   - CORS configuration

5. **Route 53 (dns_stack.py)**
   - Hosted zone for domain
   - A record pointing to CloudFront distribution
   - Certificate validation records

**CDK Deployment Commands:**
```bash
# Install CDK
npm install -g aws-cdk

# Install Python dependencies
cd aws
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap aws://ACCOUNT-ID/REGION

# Synthesize CloudFormation template
cdk synth

# Deploy all stacks
cdk deploy --all

# Deploy specific stack
cdk deploy StorageStack

# Destroy all resources (careful!)
cdk destroy --all
```

**Environment Configuration:**
```python
# aws/app.py
import aws_cdk as cdk
from stacks.storage_stack import StorageStack
from stacks.database_stack import DatabaseStack
from stacks.auth_stack import AuthStack
from stacks.api_stack import ApiStack
from stacks.dns_stack import DnsStack

app = cdk.App()

# Environment variables
env = cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
    region=os.environ["CDK_DEFAULT_REGION"]
)

# Configuration
config = {
    "domain_name": "yourdomain.com",  # Update with actual domain
    "team_name": "True Lacrosse Team",
    "admin_email": "coach@example.com"  # First admin account
}

# Deploy stacks with dependencies
database_stack = DatabaseStack(app, "DatabaseStack", env=env)
auth_stack = AuthStack(app, "AuthStack", env=env, config=config)
api_stack = ApiStack(
    app, "ApiStack", 
    env=env,
    database_stack=database_stack,
    auth_stack=auth_stack
)
storage_stack = StorageStack(
    app, "StorageStack",
    env=env,
    api_stack=api_stack,
    config=config
)
dns_stack = DnsStack(
    app, "DnsStack",
    env=env,
    storage_stack=storage_stack,
    config=config
)

app.synth()
```

**Frontend Build & Deploy:**
```bash
# Build React app
cd app
npm run build

# Deploy to S3 (CDK can automate this with BucketDeployment construct)
aws s3 sync build/ s3://YOUR-BUCKET-NAME --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR-DIST-ID \
  --paths "/*"
```

**Automated Deployment (Recommended):**
- Use CDK BucketDeployment construct to auto-deploy React build
- Trigger on `cdk deploy` command
- Automatically invalidates CloudFront cache

### Ongoing Maintenance
- Weekly DynamoDB backups (automated via AWS Backup or CDK)
- Monthly cost review (target: $10-20/month)
- Monitor CloudWatch logs for Lambda errors
- Review Cognito user activity
- Update Lambda runtime versions as needed

### Monitoring & Alerts
- CloudWatch dashboard for key metrics:
  - API Gateway request count and latency
  - Lambda invocations and errors
  - DynamoDB read/write capacity
  - CloudFront cache hit rate
- SNS alerts for:
  - Lambda function errors (threshold: 5 errors in 5 minutes)
  - API Gateway 5xx errors
  - DynamoDB throttling events
  - High AWS costs (> $20/month)

## Estimated AWS Costs

### Monthly Cost Breakdown (for 20-30 users with light daily usage)

**Serverless Architecture with CDK:**
- **S3 hosting**: $0.50-1/month (storage + requests)
- **CloudFront CDN**: $1-2/month (data transfer)
- **Route 53**: $0.50/month (hosted zone)
- **API Gateway**: $1-3/month (API calls, ~5,000 requests/month)
- **Lambda**: $0-1/month (likely free tier, ~10,000 invocations/month)
- **DynamoDB**: $1-2/month (on-demand pricing, light usage)
- **Cognito**: $0/month (free tier up to 50,000 MAUs)
- **ACM (SSL Certificate)**: $0/month (free)
- **CloudWatch Logs**: $0.50-1/month (log storage)

**Total Estimated Cost: $5-12/month**

**First Year Advantage:** 
Most services will stay within AWS Free Tier limits, potentially keeping costs under $5/month for the first 12 months.

**Scaling Considerations:**
- Single team (20-30 users): $5-12/month
- Multiple teams (50-80 users): $15-20/month
- Large organization (100+ users): $25-35/month

**Cost Optimization Tips:**
- DynamoDB on-demand pricing is best for unpredictable traffic
- CloudFront caching reduces origin requests and costs
- Lambda free tier covers 1M requests/month
- Set up AWS Budget alerts to monitor spending

## Success Metrics
- Player engagement: 70%+ of players check in 5+ days per week
- Load time: < 2 seconds average
- Uptime: 99%+ availability
- Cost: Stay within $15/month budget
- Coach satisfaction: Easy to manage, valuable insights

## Documentation Needed
- Player quick-start guide (how to use unique link, check in)
- Parent guide (how to view progress)
- Admin manual (managing players, activities, and content pages)
- Content creation guide (using WYSIWYG editor, image uploads, video embeds)
- Technical documentation (architecture, deployment, troubleshooting)
- Content Management Implementation Guide (see separate document for detailed HTML sanitization, WYSIWYG editor integration, and security best practices)

---

## Getting Started Prompt for AI Development Tool

To build this application with AWS CDK (Python), follow these steps:

### Phase 1: Infrastructure Setup
1. **Initialize CDK project structure** (Python)
   - Create app.py and stack files
   - Configure cdk.json with proper settings
   
2. **Create DatabaseStack** 
   - Define all 5 DynamoDB tables with proper schemas
   - Add GSIs where needed
   - Enable point-in-time recovery

3. **Create AuthStack**
   - Set up Cognito User Pool with password policies
   - Configure email verification
   - Create app client for web application

4. **Create ApiStack**
   - Define API Gateway REST API
   - Create Cognito authorizer for admin endpoints
   - Build Lambda functions (Python 3.11+):
     - Player CRUD operations
     - Activity management
     - Tracking and leaderboard
     - Reflection management
     - Admin operations
   - Set up proper IAM roles and permissions
   - Configure CORS

5. **Create StorageStack**
   - S3 bucket for React frontend
   - CloudFront distribution with OAI
   - ACM certificate for custom domain
   - BucketDeployment construct for automated frontend deployment

6. **Create DnsStack**
   - Route 53 hosted zone
   - A record for CloudFront distribution
   - Certificate validation records

### Phase 2: Frontend Development
1. **Set up React application** with TypeScript (recommended)
2. **Install dependencies**:
   - AWS Amplify JS library (for Cognito auth)
   - Tailwind CSS for styling
   - React Router for navigation
   - Axios or Fetch for API calls
   - Rich text editor: TinyMCE or React Quill for content editing
   - HTML sanitization: DOMPurify for client-side sanitization

3. **Build core components**:
   - PlayerView (main tracking grid)
   - Leaderboard
   - ReflectionForm
   - AdminLogin
   - AdminDashboard with tabs
   - Shared UI components (buttons, cards, etc.)

4. **Implement routing**:
   - `/player/:uniqueLink` - Player view
   - `/leaderboard` - Team leaderboard
   - `/admin` - Admin login
   - `/admin/dashboard` - Admin dashboard (protected route)

5. **Configure AWS Amplify Auth**:
   - Connect to Cognito User Pool
   - Implement login/logout flows
   - Handle JWT token management
   - Protected route logic for admin

### Phase 3: Integration & Testing
1. **Connect frontend to API Gateway endpoints**
2. **Test player flows**: Unique link access, activity tracking, reflections
3. **Test admin flows**: Login, player management, activity management
4. **Test authentication**: Cognito login, token refresh, logout
5. **Test on multiple devices**: Mobile, tablet, desktop

### Phase 4: Deployment
1. **Deploy CDK stacks**: `cdk deploy --all`
2. **Create initial admin account** in Cognito User Pool
3. **Build React app**: `npm run build`
4. **Deploy frontend** (automated via CDK BucketDeployment)
5. **Configure custom domain** in Route 53
6. **Verify SSL certificate** is active
7. **Test production deployment**

### Phase 5: Post-Deployment
1. **Set up CloudWatch monitoring and alarms**
2. **Configure DynamoDB backups**
3. **Create initial team data** (activities, test players)
4. **Document admin procedures**
5. **Train coaches on admin dashboard usage**

### Recommended Development Order:
1. Backend first (CDK stacks, Lambda functions, DynamoDB)
2. Test APIs with Postman or similar tool
3. Frontend development against deployed backend
4. Integration testing
5. Production deployment

Use this requirements document as the complete specification for all features and functionality.
