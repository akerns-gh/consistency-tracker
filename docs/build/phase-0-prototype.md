# Phase 0: HTML Prototype & Requirements Validation

## Overview
Create a standalone HTML prototype that runs locally (no build process) to validate requirements and functionality before building the full stack. This prototype uses vanilla HTML, CSS, and JavaScript with mock data.

**Estimated Time:** 8-12 hours

## 0.1 Static HTML Prototype Setup
- Create standalone HTML prototype that runs locally (no build process)
- Use vanilla HTML, CSS, and JavaScript with MVC architecture
- Structure with separate HTML files for each major view
- Include mock data embedded in JavaScript files and JSON files for dynamic content
- True Lacrosse branding and color scheme (green-based palette)

**Files to create:**
- `prototype/` - Prototype directory
- `prototype/index.html` - Landing page (redirects to my-progress.html)
- `prototype/my-progress.html` - My Progress page (aggregated player statistics)
- `prototype/player-view.html` - Weekly Tracker (main player dashboard with activity grid)
- `prototype/leaderboard.html` - Team leaderboard view
- `prototype/reflection.html` - Weekly reflection form
- `prototype/resource-list.html` - Content pages list by category
- `prototype/content-page.html` - Individual content page view
- `prototype/admin-login.html` - Admin login page
- `prototype/admin-dashboard.html` - Admin dashboard with all tabs
- `prototype/css/styles.css` - All styling with True Lacrosse theme
- `prototype/data/` - JSON data files directory
  - `activity-requirements.json` - Activity configuration (required days, types, content, flyout info)
  - `navigation.json` - Navigation menu configuration (menu items, display flags, categories)
  - `nutrition-tips.json` - Nutrition content pages
  - `mental-performance.json` - Mental performance content pages
  - `training-guidance.json` - Training guidance content pages
  - `workout-plan.json` - Workout plan content page
- `prototype/js/mock-data.js` - Mock data for players, activities, tracking, content
- `prototype/js/models/` - MVC Models (data management and business logic)
  - `BaseModel.js` - Base model class
  - `PlayerModel.js` - Player data management
  - `ActivityModel.js` - Activity requirements and configuration
  - `TrackingModel.js` - Activity tracking and scoring
  - `ReflectionModel.js` - Weekly reflection data
  - `ContentModel.js` - Content and navigation management
  - `LeaderboardModel.js` - Leaderboard calculations
  - `WorkoutModel.js` - Workout plan data
- `prototype/js/views/` - MVC Views (UI rendering)
  - `BaseView.js` - Base view class
  - `SharedViews.js` - Shared UI components (header, navigation, flyouts)
  - `PlayerView.js` - Weekly Tracker view
  - `ProgressView.js` - My Progress view
  - `LeaderboardView.js` - Leaderboard view
  - `ReflectionView.js` - Reflection form view
  - `ContentView.js` - Content pages view
  - `AdminView.js` - Admin dashboard view
- `prototype/js/controllers/` - MVC Controllers (coordination)
  - `BaseController.js` - Base controller class
  - `PlayerController.js` - Weekly Tracker controller
  - `ProgressController.js` - My Progress controller
  - `LeaderboardController.js` - Leaderboard controller
  - `ReflectionController.js` - Reflection controller
  - `ContentController.js` - Content pages controller
  - `AdminController.js` - Admin dashboard controller
- `prototype/js/core/` - Core application logic
  - `App.js` - Main application entry point and initialization
  - `EventBus.js` - Event system for component communication
  - `StateManager.js` - Application state management
- `prototype/js/utils/` - Utility functions
  - `router.js` - Simple client-side routing
  - `storage.js` - LocalStorage wrapper for mock data persistence
  - `forms.js` - Form handling and validation
- `prototype/README.md` - Instructions for running locally

## 0.2 Player Interface Prototype

### My Progress Page
- Aggregated week-over-week statistics for individual players
- Summary cards carousel with:
  - Current Week Score
  - Average Weekly Score
  - Best Week Score
  - Total Weeks Tracked
  - Current Streak
- Weekly scores over time chart (using Chart.js)
- Weekly breakdown table showing daily scores
- Week navigation (previous/next week)
- Activity-specific progress indicators

### Weekly Tracker Page
- Weekly activity grid (7 days × 5 activities) with interactive checkboxes
- Daily score calculation and display (bottom row of grid)
- Weekly total score card with progress bar
- Navigation menu (hamburger menu with slide-out animation)
- Visual feedback for completed activities (green highlighting)
- Frequency warnings (yellow highlighting for activities at risk)
- Activity flyouts for detailed information (click activity name to view)
- Clickable activity names that open flyout panels or link to content pages
- Activity types: "flyout" (shows HTML content) or "link" (navigates to content page)
- Weekly reflection form integrated below activity grid
- Week navigation (previous/next week buttons)
- Mock data for current week and previous weeks

**Key features to prototype:**
- Click/tap to toggle activity completion
- Real-time score updates
- Week navigation (view previous weeks)
- Activity flyout panels for detailed information
- Responsive mobile layout

## 0.3 Leaderboard Prototype
- Top 3 podium visualization with special styling
- Full rankings list
- Week selector dropdown
- Current player highlighting
- Team stats summary
- Mock data for multiple players and weeks

**Key features to prototype:**
- Sorting by weekly score
- Week selection functionality
- Visual hierarchy (top 3 vs. rest)

## 0.4 Reflection Prototype
- Three-question form (What went well? What can I do better? What am I doing this week?)
- Integrated into Weekly Tracker page (below activity grid)
- Auto-save functionality (saves on input)
- Display saved reflections
- Edit functionality
- Reflection data persists per week

**Key features to prototype:**
- Form validation
- Save/load from localStorage
- Auto-save on input
- Week-specific reflection storage

## 0.5 Content Pages Prototype
- Content list view (`resource-list.html`) organized by categories
- Individual content page (`content-page.html`) with HTML rendering
- Sample content pages loaded from JSON files:
  - `data/nutrition-tips.json`
  - `data/mental-performance.json`
  - `data/training-guidance.json`
  - `data/workout-plan.json`
- Navigation between content pages via navigation menu
- Mobile-responsive content display
- Category-based filtering (via URL query parameters)

**Key features to prototype:**
- Category filtering via navigation menu
- HTML content rendering (sample rich content from JSON)
- Navigation flow with back buttons
- Responsive typography and layout
- Content pages accessible via slug-based routing

## 0.6 Admin Dashboard Prototype
- Login page with form validation
- Dashboard layout with tab navigation
- Players tab: list view, add/edit forms, unique link display
- Activities tab: list view, add/edit forms, reordering simulation
- Content tab: list view, WYSIWYG editor simulation, publish toggle
- Overview tab: summary cards, charts (using Chart.js or similar)
- Settings tab: team info form, configuration options

**Key features to prototype:**
- Tab navigation
- Form interactions (add/edit/delete)
- Modal dialogs for forms
- Data table/list views
- Simulated drag-and-drop for reordering
- Basic chart visualization

## 0.7 Interactive Functionality & Architecture

### MVC Architecture
The prototype uses a Model-View-Controller (MVC) architecture pattern:
- **Models** (`js/models/`): Data management, business logic, and data persistence
- **Views** (`js/views/`): UI rendering, DOM manipulation, and presentation logic
- **Controllers** (`js/controllers/`): Coordinate between models and views, handle user interactions
- **Core** (`js/core/`): Application initialization, event system, state management

This architecture provides:
- Separation of concerns
- Maintainable codebase
- Easy migration path to React frontend
- Reusable components

### JSON-Based Data Management
- Activity requirements loaded from `data/activity-requirements.json`
- Navigation menu loaded from `data/navigation.json`
- Content pages loaded from category-specific JSON files
- Dynamic content rendering based on JSON structure

### Interactive Features
- Client-side routing between pages (using simple page navigation with query parameters)
- LocalStorage for persisting mock data changes (tracking, reflections, admin auth)
- Form validation and error messages
- Loading states and transitions
- Responsive breakpoints (mobile, tablet, desktop)
- Activity flyout panels for detailed information (slide-in from side)
- Dynamic navigation menu rendering based on `navigation.json`
- Navigation menu slide-out animation
- Chart.js integration for data visualization (My Progress page)
- Auto-save functionality for reflections (saves every 30 seconds)

**Key implementation:**
- `prototype/js/core/App.js` - Main application entry point and initialization
- `prototype/js/utils/router.js` - Simple client-side routing
- `prototype/js/utils/storage.js` - LocalStorage wrapper for mock data persistence
- `prototype/js/utils/forms.js` - Form handling and validation
- `prototype/js/views/SharedViews.js` - Shared UI components (navigation, flyouts, modals)

## 0.8 Requirements Validation Checklist
- ✅ Verify all UI requirements from documentation
- ✅ Test user flows: 
  - My Progress page (aggregated statistics with charts)
  - Weekly Tracker (activity grid, scoring, reflections, flyouts)
  - Viewing leaderboard (top 3 podium, full rankings)
  - Content pages navigation (resource-list, content-page)
- ✅ Test admin flows: managing players, activities, content
- ✅ Validate True Lacrosse branding and color scheme (green-based palette: `rgb(150, 200, 85)`)
- ✅ Test responsive design at all breakpoints
- ✅ Test activity flyout functionality (click activity names)
- ✅ Test JSON-based data loading (navigation, content, activities)
- ✅ Test LocalStorage persistence (tracking, reflections, admin auth)
- ✅ Test auto-save functionality for reflections
- ✅ Test week navigation (previous/next)
- ✅ Test navigation menu (slide-out, dynamic rendering)
- Gather feedback on UX and make adjustments
- Document any requirement clarifications or changes

**Deliverables:**
- ✅ Fully functional HTML prototype running locally
- ✅ All major views and interactions implemented:
  - My Progress (aggregated stats with charts)
  - Weekly Tracker (activity grid with flyouts)
  - Leaderboard (top 3 podium, rankings)
  - Weekly Reflection (auto-save)
  - Content Pages (resource-list, content-page)
  - Admin Dashboard (all tabs functional)
- ✅ MVC architecture implemented
- ✅ JSON-based data management (navigation, content, activities)
- ✅ Mock data representing realistic scenarios (8 players, 4 weeks of data)
- ✅ LocalStorage persistence for user data
- ✅ Chart.js integration for data visualization
- ✅ Responsive design for mobile, tablet, desktop
- Documentation of any requirement changes or clarifications

## 0.9 Architecture Notes

### MVC Pattern Benefits
- **Maintainability**: Clear separation of concerns makes code easier to understand and modify
- **Scalability**: Easy to add new features without affecting existing code
- **Testability**: Models, views, and controllers can be tested independently
- **Migration Path**: MVC structure aligns well with React component architecture

### Data Management
- **JSON Files**: Content and configuration stored in JSON files for easy editing
- **LocalStorage**: User data (tracking, reflections) persisted in browser LocalStorage
- **Mock Data**: Initial data provided in `mock-data.js` for development

### Color Scheme
The prototype uses the True Lacrosse green-based color palette:
- **Primary Green**: `rgb(150, 200, 85)` - Main brand color
- **Dark Green**: `rgb(115, 165, 65)` - Text and accents
- **Header Background**: Black (`#000000`)
- **Table Headers**: Dark gray (`#2a2a2a`) with green text
- **Warning Yellow**: `#FCD34D`
- **Error Red**: `#EF4444`
- **Background Colors**: Light gray (`#F5F5F5`), Section background (`#E8E8E8`)
- **Typography Colors**: Dark gray (`#1F2937`) for body text, medium gray (`#6B7280`) for secondary text

