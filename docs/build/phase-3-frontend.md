# Phase 3: Frontend Foundation & Player Interface

## Overview
Set up React application, create shared components, build API service layer, and implement all player-facing interfaces (activity tracking, leaderboard, reflections, content viewing).

**Estimated Time:** 10-14 hours

## 3.1 React Application Setup
- Initialize React app with TypeScript (recommended) or JavaScript
- Install core dependencies: React Router, Axios, Tailwind CSS, Chart.js (for data visualization)
- Configure Tailwind with True Lacrosse color palette (green-based: `rgb(150, 200, 85)`)
- Set up project structure with components, pages, services, utils

**Files to create:**
- `frontend/package.json` - Dependencies
- `frontend/tailwind.config.js` - Custom theme with True Lacrosse colors
- `frontend/src/` - Source code directory
- `frontend/src/index.tsx` - App entry point
- `frontend/src/App.tsx` - Main app component with routing

## 3.2 Shared Components & Styling
- Create reusable UI components matching True Lacrosse branding
- Button components (primary, secondary)
- Card components
- Navigation components with conditional admin links
- Loading states and skeletons
- Error boundaries

**Files to create:**
- `frontend/src/components/ui/Button.tsx`
- `frontend/src/components/ui/Card.tsx`
- `frontend/src/components/ui/Loading.tsx`
- `frontend/src/components/ui/ErrorBoundary.tsx`
- `frontend/src/components/navigation/NavigationMenu.tsx` - Navigation menu that conditionally shows admin links based on user role
- `frontend/src/styles/globals.css` - Global styles with True Lacrosse theme

## 3.3 API Service Layer
- Create API client with base configuration
- Set up interceptors for error handling
- Create service functions for all API endpoints
- Handle authentication token management
- Add user role checking service (check if user is admin)

**Files to create:**
- `frontend/src/services/api.ts` - Axios instance and base config
- `frontend/src/services/playerApi.ts` - Player endpoint functions
- `frontend/src/services/adminApi.ts` - Admin endpoint functions
- `frontend/src/services/contentApi.ts` - Content endpoint functions
- `frontend/src/services/authApi.ts` - Authentication and role checking functions

## 3.4 My Progress View
- Aggregated week-over-week statistics for individual players
- Summary cards carousel with:
  - Current Week Score
  - Average Weekly Score
  - Best Week Score
  - Total Weeks Tracked
  - Current Streak
- Weekly scores over time chart (using Chart.js or similar)
- Weekly breakdown table showing daily scores
- Week navigation (previous/next week buttons)
- Activity-specific progress indicators

**Files to create:**
- `frontend/src/pages/MyProgressView.tsx` - My Progress page
- `frontend/src/components/progress/SummaryCards.tsx` - Summary cards carousel
- `frontend/src/components/progress/ProgressChart.tsx` - Weekly scores chart
- `frontend/src/components/progress/WeeklyBreakdown.tsx` - Weekly breakdown table

## 3.5 Player View - Activity Tracking
- Main player dashboard with weekly grid view
- Activity grid component (7 days × N activities)
- Daily check-in functionality (toggle activities)
- Daily score calculation and display (bottom row of grid)
- Weekly total score display with progress bar
- Navigation menu (hamburger menu with slide-out animation)
- Activity flyout panels (click activity name to view details)
- Activity types: flyout (shows HTML content) or link (navigates to content page)
- Week navigation (previous/next week buttons)
- Visual feedback: green for completed, yellow for frequency warnings

**Files to create:**
- `frontend/src/pages/PlayerView.tsx` - Main player dashboard
- `frontend/src/components/player/ActivityGrid.tsx` - Weekly activity grid
- `frontend/src/components/player/ActivityCell.tsx` - Individual activity cell
- `frontend/src/components/player/WeeklyScore.tsx` - Score display
- `frontend/src/components/player/NavigationMenu.tsx` - Side navigation

## 3.6 Leaderboard View
- Team leaderboard display
- Top 3 podium visualization (special styling for 1st, 2nd, 3rd place)
- Full rankings list below podium
- Week selector dropdown
- Current player highlighting (bright border/background)
- Stats summary (team average, most improved, perfect weeks)

**Files to create:**
- `frontend/src/pages/LeaderboardView.tsx` - Leaderboard page
- `frontend/src/components/leaderboard/Podium.tsx` - Top 3 display
- `frontend/src/components/leaderboard/RankingsList.tsx` - Full rankings

## 3.7 Weekly Reflection
- Reflection form with three questions
- Auto-save functionality
- Display saved reflections

**Files to create:**
- `frontend/src/components/player/ReflectionForm.tsx` - Reflection input form with auto-save
- `frontend/src/pages/ReflectionView.tsx` - Reflection page (standalone view)

## 3.8 Content Pages (Player View)
- Content list view (`/resource-list`) by category
- Individual content page display (`/content-page/:slug`)
- Mobile-responsive HTML content rendering
- Client-side HTML sanitization with DOMPurify
- Category filtering via navigation menu
- Back navigation to return to previous page

**Files to create:**
- `frontend/src/pages/ContentListView.tsx` - List of content by category
- `frontend/src/pages/ContentPageView.tsx` - Individual content page
- `frontend/src/components/content/ContentDisplay.tsx` - HTML content renderer

