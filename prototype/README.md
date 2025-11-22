# True Lacrosse Consistency Tracker - HTML Prototype

A standalone HTML prototype for the True Lacrosse Consistency Tracker application. This prototype validates requirements and functionality before building the full stack application.

## Overview

This prototype is built with vanilla HTML, CSS, and JavaScript - no build process required. It runs entirely in the browser and uses LocalStorage for data persistence.

## Features

### Player Interface
- **Activity Grid**: 7-day × 5-activity grid for tracking daily habits
- **Real-time Scoring**: Daily and weekly scores update automatically
- **Week Navigation**: View current and previous weeks
- **Navigation Menu**: Slide-out menu for easy access to all features
- **Visual Feedback**: Green highlighting for completed activities, yellow for frequency warnings

### Leaderboard
- **Top 3 Podium**: Special visualization for top performers
- **Full Rankings**: Complete team rankings with current player highlighting
- **Week Selector**: View leaderboards for any week
- **Team Stats**: Average scores, most improved, perfect weeks

### Weekly Reflection
- **Three Questions**: What went well? What can I do better? What am I doing this week?
- **Auto-save**: Automatically saves every 30 seconds
- **Edit Mode**: View and edit saved reflections
- **Character Counters**: Track input length for each field

### Content Pages
- **Category Organization**: Content organized by Guidance, Workouts, Nutrition, Mental Performance, Resources
- **Rich HTML Content**: Full HTML rendering with proper styling
- **Navigation**: Easy navigation between content pages

### Admin Dashboard
- **Player Management**: Add, edit, and manage players with unique links
- **Activity Management**: Configure activities, frequencies, and point values
- **Content Management**: Create and edit HTML content pages with WYSIWYG editor
- **Overview**: Team statistics, charts, and reflection highlights
- **Settings**: Team configuration and preferences

## Getting Started

### Running Locally

1. **Open the prototype**: Simply open `index.html` in a web browser
   - You can double-click the file, or
   - Use a local server (recommended for better experience)

2. **Using a local server** (optional but recommended):
   ```bash
   # Python 3
   python -m http.server 8000
   
   # Node.js (with http-server)
   npx http-server
   
   # PHP
   php -S localhost:8000
   ```
   Then navigate to `http://localhost:8000/prototype/` in your browser

### Default Access

- **My Progress**: Opens automatically when you load `index.html` (redirects to my-progress.html)
- **Admin Dashboard**: Navigate to `admin-login.html`
  - For the prototype, any email/password combination works (password must be 8+ characters)

## File Structure

```
prototype/
├── index.html              # Landing page (redirects to my-progress)
├── player-view.html        # Weekly Tracker (activity grid)
├── my-progress.html         # My Progress (aggregated stats)
├── leaderboard.html        # Team leaderboard
├── reflection.html         # Weekly reflection form
├── content-list.html       # Content pages list
├── content-page.html       # Individual content page
├── admin-login.html        # Admin login page
├── admin-dashboard.html    # Admin dashboard
├── css/
│   └── styles.css          # All styling
├── data/                   # JSON data files
│   ├── activity-requirements.json
│   ├── navigation.json
│   ├── nutrition-tips.json
│   ├── mental-performance.json
│   ├── resources.json
│   ├── training-guidance.json
│   ├── workout-plan.json
│   └── workouts.json
├── js/
│   ├── mock-data.js        # Mock data
│   ├── models/             # MVC Models
│   │   ├── BaseModel.js
│   │   ├── PlayerModel.js
│   │   ├── ActivityModel.js
│   │   ├── TrackingModel.js
│   │   ├── ReflectionModel.js
│   │   ├── ContentModel.js
│   │   ├── LeaderboardModel.js
│   │   └── WorkoutModel.js
│   ├── views/              # MVC Views
│   │   ├── BaseView.js
│   │   ├── SharedViews.js
│   │   ├── PlayerView.js
│   │   ├── ProgressView.js
│   │   ├── LeaderboardView.js
│   │   ├── ReflectionView.js
│   │   ├── ContentView.js
│   │   └── AdminView.js
│   ├── controllers/        # MVC Controllers
│   │   ├── BaseController.js
│   │   ├── PlayerController.js
│   │   ├── ProgressController.js
│   │   ├── LeaderboardController.js
│   │   ├── ReflectionController.js
│   │   ├── ContentController.js
│   │   └── AdminController.js
│   ├── core/               # Core application logic
│   │   ├── App.js          # Main entry point
│   │   ├── EventBus.js
│   │   └── StateManager.js
│   └── utils/              # Utility functions
│       ├── router.js       # Routing utilities
│       ├── storage.js      # LocalStorage wrapper
│       └── forms.js        # Form validation
└── README.md               # This file
```

## Mock Data

The prototype includes comprehensive mock data:

- **8 Players**: Sample players with unique links
- **5 Activities**: Default activities (Sleep, Hydration, Wall Ball, Run, Bodyweight Training)
- **Tracking Data**: 4 weeks of tracking data for all active players
- **Reflections**: Sample weekly reflections
- **Content Pages**: 5 sample content pages across different categories

### Modifying Mock Data

Edit `js/mock-data.js` to change:
- Player names and information
- Activity definitions
- Content pages
- Default week settings

## Data Persistence

The prototype uses browser LocalStorage to persist:
- Activity completions
- Weekly reflections
- Admin authentication state
- Settings changes

### Clearing Data

To reset all data:
1. Open browser developer tools (F12)
2. Go to Application/Storage tab
3. Clear LocalStorage for the site
4. Refresh the page

Or use the browser console:
```javascript
localStorage.clear();
location.reload();
```

## Browser Compatibility

- **Chrome/Edge**: Full support
- **Firefox**: Full support
- **Safari**: Full support
- **Mobile browsers**: Responsive design works on iOS and Android

## True Lacrosse Branding

The prototype uses the official True Lacrosse color scheme:
- **Primary Green**: `rgb(150, 200, 85)` - Main brand color
- **Dark Green**: `rgb(100, 150, 50)` - Text and accents
- **Header Background**: Black (`#000000`)
- **Table Headers**: Dark gray (`#2a2a2a`) with green text
- **Warning Yellow**: `#FCD34D`
- **Error Red**: `#EF4444`

Typography uses Inter, Montserrat, or Poppins font families with a modern, athletic aesthetic.

## Architecture

This prototype uses a **Model-View-Controller (MVC)** architecture:

- **Models** (`js/models/`): Data management and business logic
- **Views** (`js/views/`): UI rendering and presentation
- **Controllers** (`js/controllers/`): Coordination between models and views
- **Core** (`js/core/`): Application initialization and shared utilities

This structure makes the codebase maintainable and prepares it for migration to a React-based frontend.

## Features Demonstrated

### Player Features
- ✅ Weekly activity grid with interactive checkboxes
- ✅ Daily and weekly score calculation
- ✅ Week navigation (previous/next)
- ✅ Navigation menu
- ✅ Visual feedback (green/yellow highlighting)
- ✅ Real-time score updates

### Leaderboard Features
- ✅ Top 3 podium visualization
- ✅ Full rankings list
- ✅ Week selector
- ✅ Current player highlighting
- ✅ Team stats summary

### Reflection Features
- ✅ Three-question form
- ✅ Auto-save functionality
- ✅ Edit mode
- ✅ Character counters
- ✅ Display saved reflections

### Content Features
- ✅ Category organization
- ✅ HTML content rendering
- ✅ Navigation between pages
- ✅ Responsive layout

### Admin Features
- ✅ Login page with validation
- ✅ Tab navigation
- ✅ Player management (add/edit/copy links)
- ✅ Activity management (add/edit/reorder)
- ✅ Content management (WYSIWYG editor, publish/unpublish)
- ✅ Overview dashboard with charts
- ✅ Settings configuration

## Testing the Prototype

### Player Flow
1. Open `index.html` (redirects to `my-progress.html`)
2. View aggregated progress statistics
3. Navigate to Weekly Tracker (`player-view.html`)
4. Click on activity cells to toggle completion
5. Observe score updates in real-time
6. Navigate to leaderboard
7. Complete a weekly reflection
8. Browse content pages

### Admin Flow
1. Navigate to `admin-login.html`
2. Login with any email/password (8+ chars)
3. Explore all tabs:
   - Add/edit players
   - Manage activities
   - Create/edit content
   - View overview
   - Update settings

## Known Limitations

- **No Backend**: All data is stored in LocalStorage (browser-specific)
- **No Real Authentication**: Admin login is simulated
- **No Image Upload**: Content editor doesn't support image uploads
- **No Real Charts**: Charts use Chart.js but with limited data
- **Single Browser**: Data doesn't sync across devices/browsers

## Next Steps

After validating the prototype:
1. Build the full React frontend
2. Set up AWS infrastructure (CDK)
3. Implement DynamoDB data models
4. Create Lambda API functions
5. Set up Cognito authentication
6. Deploy to AWS S3 + CloudFront

## Support

For questions or issues with the prototype, refer to the main requirements document:
`docs/requirements/consistency-tracker-requirements.md`

## License

This is a prototype for internal use and requirements validation.

