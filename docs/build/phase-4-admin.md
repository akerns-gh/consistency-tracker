# Phase 4: Admin Dashboard & Authentication

## Overview
Implement AWS Amplify authentication, admin login, and all admin dashboard features (player management, activity management, overview, settings).

**Estimated Time:** 8-12 hours

## 4.1 AWS Amplify Auth Integration
- Configure AWS Amplify for Cognito authentication
- Set up login/logout flows
- Implement JWT token management
- Create protected route wrapper component
- **Extract user role from JWT token** (Cognito groups/claims)
- **Determine admin status** from user's Cognito group membership
- Store admin status in auth context for navigation rendering

**Files to create:**
- `frontend/src/config/aws-config.ts` - Amplify configuration
- `frontend/src/services/auth.ts` - Auth service functions with role checking
- `frontend/src/components/auth/ProtectedRoute.tsx` - Route protection
- `frontend/src/contexts/AuthContext.tsx` - Auth state management with user role (isAdmin flag)

## 4.2 Admin Login Page
- Login form with email/password
- Error handling and display
- "Forgot Password" functionality
- Remember me option
- True Lacrosse branded styling

**Files to create:**
- `frontend/src/pages/AdminLogin.tsx` - Login page

## 4.3 Admin Dashboard Layout
- Top navigation bar with tabs
- Tab navigation: Players, Activities, Content, Overview, Settings
- Logout functionality
- Responsive layout
- **Hamburger menu with app navigation links** (for navigating to player-facing pages)
- **Conditional admin links in main navigation** (only visible to admin users)

**Files to create:**
- `frontend/src/pages/AdminDashboard.tsx` - Main dashboard layout
- `frontend/src/components/admin/NavBar.tsx` - Top navigation with hamburger menu
- `frontend/src/components/admin/TabNavigation.tsx` - Tab component
- `frontend/src/components/admin/AdminMenu.tsx` - Hamburger menu with app navigation and admin tabs

## 4.4 Players Management Tab
- List all players in table/card view
- Add new player (generates unique link)
- Edit player information
- Copy unique link to clipboard
- Deactivate player (archive)
- Search/filter functionality

**Files to create:**
- `frontend/src/components/admin/players/PlayerList.tsx` - Player list view
- `frontend/src/components/admin/players/PlayerForm.tsx` - Add/edit form
- `frontend/src/components/admin/players/PlayerCard.tsx` - Individual player card

## 4.5 Activities Management Tab
- List all activities
- Add/edit/delete activities
- Drag-and-drop reordering
- Set frequency requirements (daily, 3x/week, etc.)
- Set point values for scoring
- Toggle active/inactive
- Configure activity types: "flyout" (shows HTML content) or "link" (navigates to content page)
- Set required days per week (array of day indices: 0=Sunday, 1=Monday, etc.)
- Configure activity goals (e.g., "8+ hrs", "20 mins")

**Files to create:**
- `frontend/src/components/admin/activities/ActivityList.tsx` - Activity list
- `frontend/src/components/admin/activities/ActivityForm.tsx` - Add/edit form
- `frontend/src/components/admin/activities/ActivityCard.tsx` - Activity card

## 4.6 Overview Tab
- Summary cards (total players, average score, trends, content pages published)
- Charts and graphs (weekly trends using Chart.js or similar)
- Reflection highlights (common themes from player reflections)
- Export functionality (CSV/PDF)
- Team statistics dashboard

**Files to create:**
- `frontend/src/components/admin/overview/SummaryCards.tsx` - Stats cards
- `frontend/src/components/admin/overview/Charts.tsx` - Data visualization
- `frontend/src/components/admin/overview/ReflectionHighlights.tsx` - Reflection summary

## 4.7 Settings Tab
- Team information management
- Coach account management (view only, add via Cognito console)
- Default activities configuration
- Content categories management
- Week management (advance week manually)

**Files to create:**
- `frontend/src/components/admin/settings/SettingsForm.tsx` - Settings form
- `frontend/src/components/admin/settings/TeamInfo.tsx` - Team info section

## 4.8 Navigation & Role-Based UI
- **User role detection**: Extract admin status from Cognito JWT token (groups/claims)
- **Conditional navigation rendering**: Show admin navigation links only to authenticated admin users
- **Main navigation component**: Update to check `isAdmin` flag from AuthContext
- **Admin menu integration**: Hamburger menu in admin dashboard includes both app navigation and admin-specific tabs
- **Role verification**: Frontend checks user role on app initialization and after login

**Implementation notes:**
- Admin status determined by checking if user belongs to "Admins" Cognito group
- JWT token contains group membership information
- AuthContext provides `isAdmin` boolean flag to all components
- Navigation components conditionally render admin links based on `isAdmin` flag
- Admin dashboard always shows admin navigation (protected route ensures admin access)

