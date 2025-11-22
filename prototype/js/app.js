// Main Application Logic for True Lacrosse Consistency Tracker Prototype

// Activity Requirements (loaded from JSON file, will be DynamoDB in future)
let activityRequirements = {};

// Navigation data (loaded from JSON file)
let navigationData = [];

// Content data (loaded from JSON files)
let nutritionTipsData = [];
let mentalPerformanceData = [];
let resourcesData = [];
let trainingGuidanceData = [];
let workoutsData = [];

// Load nutrition tips from JSON
async function loadNutritionTips() {
    try {
        const response = await fetch('data/nutrition-tips.json');
        if (!response.ok) {
            throw new Error(`Failed to load nutrition tips: ${response.status} ${response.statusText}`);
        }
        nutritionTipsData = await response.json();
    } catch (error) {
        console.warn('Could not load nutrition tips, using empty array:', error);
        nutritionTipsData = [];
    }
}

// Load mental performance from JSON
async function loadMentalPerformance() {
    try {
        const response = await fetch('data/mental-performance.json');
        if (!response.ok) {
            throw new Error(`Failed to load mental performance: ${response.status} ${response.statusText}`);
        }
        mentalPerformanceData = await response.json();
    } catch (error) {
        console.warn('Could not load mental performance, using empty array:', error);
        mentalPerformanceData = [];
    }
}

// Load resources from JSON
async function loadResources() {
    try {
        const response = await fetch('data/resources.json');
        if (!response.ok) {
            throw new Error(`Failed to load resources: ${response.status} ${response.statusText}`);
        }
        resourcesData = await response.json();
    } catch (error) {
        console.warn('Could not load resources, using empty array:', error);
        resourcesData = [];
    }
}

// Load training guidance from JSON
async function loadTrainingGuidance() {
    try {
        const response = await fetch('data/training-guidance.json');
        if (!response.ok) {
            throw new Error(`Failed to load training guidance: ${response.status} ${response.statusText}`);
        }
        trainingGuidanceData = await response.json();
    } catch (error) {
        console.warn('Could not load training guidance, using empty array:', error);
        trainingGuidanceData = [];
    }
}

// Load workouts from JSON
async function loadWorkouts() {
    try {
        const response = await fetch('data/workouts.json');
        if (!response.ok) {
            throw new Error(`Failed to load workouts: ${response.status} ${response.statusText}`);
        }
        workoutsData = await response.json();
    } catch (error) {
        console.warn('Could not load workouts, using empty array:', error);
        workoutsData = [];
    }
}

// Load navigation from JSON
async function loadNavigation() {
    try {
        const response = await fetch('data/navigation.json');
        if (!response.ok) {
            throw new Error(`Failed to load navigation: ${response.status} ${response.statusText}`);
        }
        navigationData = await response.json();
    } catch (error) {
        console.warn('Could not load navigation, using defaults:', error);
        // Default navigation items
        navigationData = [
            { label: 'Weekly Tracker', page: 'player-view', display: true },
            { label: 'My Progress', page: 'my-progress', display: true },
            { label: 'Leaderboard', page: 'leaderboard', display: true },
            { label: 'Weekly Reflection', page: 'reflection', display: true },
            { label: 'Training Guidance', page: 'content-list', display: true },
            { label: 'Workouts', page: 'content-list', display: true },
            { label: 'Nutrition Tips', page: 'content-list', display: true },
            { label: 'Mental Performance', page: 'content-list', display: true },
            { label: 'Resources', page: 'content-list', display: true }
        ];
    }
}

// Render navigation menu
function renderNavigation() {
    const navLinksContainer = document.getElementById('navLinks');
    if (!navLinksContainer) return;
    
    const currentPage = Router.getCurrentPage();
    navLinksContainer.innerHTML = '';
    
    // Filter items where display is true
    const visibleItems = navigationData.filter(item => item.display !== false);
    
    // List of known page names (not slugs)
    const knownPages = ['player-view', 'my-progress', 'leaderboard', 'reflection', 'content-list', 'admin-login', 'admin-dashboard', 'index'];
    
    visibleItems.forEach(item => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        
        // Determine if page value is a slug (content page) or a page name
        const isSlug = !knownPages.includes(item.page);
        
        // Check if this is the current page
        let isActive = false;
        if (isSlug) {
            // Content page with slug - check if we're on content-page with matching slug
            const params = Router.getQueryParams();
            isActive = currentPage === 'content-page' && params.slug === item.page;
        } else {
            // Regular page
            isActive = currentPage === item.page;
        }
        
        if (isActive) {
            a.classList.add('active');
        }
        
        // Set href and navigation
        if (isSlug) {
            // Content page with slug - navigate to content-page.html?slug=...
            a.href = `content-page.html?slug=${item.page}`;
            a.addEventListener('click', (e) => {
                e.preventDefault();
                Router.navigate('content-page', { slug: item.page });
            });
        } else {
            // Regular page
            a.href = `${item.page}.html`;
            a.addEventListener('click', (e) => {
                e.preventDefault();
                Router.navigate(item.page);
            });
        }
        
        a.textContent = item.label;
        li.appendChild(a);
        navLinksContainer.appendChild(li);
    });
}

// Set player name in header (used across all pages)
function setPlayerNameInHeader() {
    const playerNameEl = document.getElementById('playerName');
    if (!playerNameEl) return;
    
    const currentPlayerId = Storage.getCurrentPlayer() || 
        (MockData.players.find(p => p.isActive)?.playerId || MockData.players[0]?.playerId);
    
    if (currentPlayerId) {
        const player = MockData.players.find(p => p.playerId === currentPlayerId);
        if (player) {
            playerNameEl.textContent = player.name;
        }
    }
}

// Load activity requirements from JSON
async function loadActivityRequirements() {
    try {
        // Server runs from prototype directory, so data is in prototype/data/
        const response = await fetch('data/activity-requirements.json');
        if (!response.ok) {
            throw new Error(`Failed to load activity requirements: ${response.status} ${response.statusText}`);
        }
        activityRequirements = await response.json();
    } catch (error) {
        console.warn('Could not load activity requirements, using defaults:', error);
        // Default: all activities required daily
        MockData.activities.forEach(activity => {
            activityRequirements[activity.activityId] = {
                frequency: activity.frequency || 'daily',
                requiredDays: [0, 1, 2, 3, 4, 5, 6] // All days by default
            };
        });
    }
}

function getActivityRequirements() {
    return activityRequirements;
}

// Initialize flyout functionality
function initFlyout() {
    // Close flyout when clicking outside
    document.addEventListener('click', (e) => {
        const flyout = document.getElementById('activityFlyout');
        const flyoutOverlay = e.target.closest('.activity-flyout-overlay');
        const flyoutClose = e.target.closest('.activity-flyout-close');
        
        if (flyout && (flyoutOverlay || flyoutClose)) {
            closeFlyout();
        }
    });
    
    // Handle escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeFlyout();
        }
    });
}

function openFlyout(content, activityId) {
    const flyout = document.getElementById('activityFlyout');
    const flyoutContent = document.getElementById('activityFlyoutContent');
    
    if (flyout && flyoutContent) {
        flyoutContent.innerHTML = content;
        flyout.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeFlyout() {
    const flyout = document.getElementById('activityFlyout');
    if (flyout) {
        flyout.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    // Load navigation first
    await loadNavigation();
    renderNavigation();
    // Set player name in header (for all pages)
    setPlayerNameInHeader();
    // Load content JSON files
    await loadNutritionTips();
    await loadMentalPerformance();
    await loadResources();
    await loadTrainingGuidance();
    await loadWorkouts();
    // Load activity requirements
    await loadActivityRequirements();
    // Load workout plan data
    await loadWorkoutPlan();
    // Initialize flyout functionality
    initFlyout();
    const currentPage = Router.getCurrentPage();
    
    // Initialize based on current page
    switch (currentPage) {
        case 'player-view':
        case 'index':
            initPlayerView();
            break;
        case 'my-progress':
            initMyProgress();
            break;
        case 'leaderboard':
            initLeaderboard();
            break;
        case 'reflection':
            initReflection();
            break;
        case 'content-list':
            initContentList();
            break;
        case 'content-page':
            initContentPage();
            break;
        case 'admin-login':
            initAdminLogin();
            break;
        case 'admin-dashboard':
            initAdminDashboard();
            break;
    }
});

// ===== Player View =====
function initPlayerView() {
    // Set current player (default to first active player)
    const currentPlayerId = Storage.getCurrentPlayer() || 
        (MockData.players.find(p => p.isActive)?.playerId || MockData.players[0].playerId);
    Storage.setCurrentPlayer(currentPlayerId);
    
    const currentWeekId = Storage.getCurrentWeek() || MockData.currentWeekId;
    Storage.setCurrentWeek(currentWeekId);
    
    const player = MockData.players.find(p => p.playerId === currentPlayerId);
    const weekDates = MockData.getWeekDates(currentWeekId);
    
    // Update header
    document.getElementById('playerName').textContent = player.name;
    
    // Update week info in main content
    const weekDatesEl = document.getElementById('weekDates');
    if (weekDatesEl) {
        weekDatesEl.textContent = `Week of ${formatDate(weekDates.monday)} - ${formatDate(weekDates.sunday)}`;
    }
    
    // Setup navigation menu
    setupNavigationMenu();
    
    // Render activity grid
    renderActivityGrid(currentPlayerId, currentWeekId);
    
    // Update scores
    updateScores(currentPlayerId, currentWeekId);
    
    // Load and setup weekly reflection
    loadWeeklyReflection(currentPlayerId, currentWeekId);
    setupWeeklyReflection(currentPlayerId, currentWeekId);
    
    // Week navigation
    document.getElementById('prevWeek')?.addEventListener('click', () => {
        navigateWeek(-1);
    });
    document.getElementById('nextWeek')?.addEventListener('click', () => {
        navigateWeek(1);
    });
}

function renderActivityGrid(playerId, weekId) {
    const grid = document.getElementById('activityGrid');
    const dailyScores = document.getElementById('dailyScores');
    if (!grid || !dailyScores) return;
    
    grid.innerHTML = '';
    dailyScores.innerHTML = '';
    
    const activities = MockData.activities.filter(a => a.isActive).sort((a, b) => a.displayOrder - b.displayOrder);
    const weekDates = MockData.getWeekDates(weekId);
    const days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
    
    // Day headers
    const dayHeaders = document.createElement('div');
    dayHeaders.className = 'day-header';
    dayHeaders.textContent = 'Activities';
    grid.appendChild(dayHeaders);
    
    days.forEach(day => {
        const header = document.createElement('div');
        header.className = 'day-header';
        header.textContent = day;
        grid.appendChild(header);
    });
    
    // Activity rows
    const requirements = getActivityRequirements();
    activities.forEach(activity => {
        const rowHeader = document.createElement('div');
        rowHeader.className = 'activity-row-header';
        
        // Get name and goal from activity requirements, fallback to mock data
        const activityReq = requirements[activity.activityId];
        const displayName = activityReq?.name || activity.name;
        const goal = activityReq?.goal || activity.goal;
        const activityType = activityReq?.type || 'link';
        const slug = activityReq?.slug || '';
        const flyoutContent = activityReq?.flyoutContent || '';
        
        // Make it clickable
        rowHeader.className = 'activity-row-header activity-link';
        rowHeader.style.cursor = 'pointer';
        
        if (activityType === 'flyout' && flyoutContent) {
            rowHeader.setAttribute('data-activity-id', activity.activityId);
            rowHeader.setAttribute('data-flyout-content', flyoutContent);
            rowHeader.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                openFlyout(flyoutContent, activity.activityId);
            });
        } else {
            rowHeader.addEventListener('click', () => {
                if (slug) {
                    // Construct URL from slug
                    window.location.href = `content-page.html?slug=${slug}`;
                }
            });
        }
        
        rowHeader.textContent = displayName;
        grid.appendChild(rowHeader);
        
        days.forEach((day, dayIndex) => {
            const date = new Date(weekDates.monday);
            date.setDate(date.getDate() + dayIndex);
            const dateStr = date.toISOString().split('T')[0];
            const trackingId = `${playerId}#${weekId}#${dateStr}`;
            
            const cell = document.createElement('div');
            cell.className = 'activity-cell';
            cell.dataset.trackingId = trackingId;
            cell.dataset.activityId = activity.activityId;
            cell.dataset.date = dateStr;
            
            // Check if this day is required for this activity
            const requirements = getActivityRequirements();
            const activityReq = requirements[activity.activityId];
            if (activityReq && activityReq.requiredDays.includes(dayIndex)) {
                cell.classList.add('required');
            }
            
            // Check if completed
            const tracking = getTrackingForDate(playerId, weekId, dateStr);
            if (tracking && tracking.completedActivities.includes(activity.activityId)) {
                cell.classList.add('completed');
            }
            
            // Check for frequency warnings
            if (activity.frequency === '3x/week') {
                const weekTracking = getAllTrackingForWeek(playerId, weekId);
                const completedCount = weekTracking.filter(t => 
                    t.completedActivities.includes(activity.activityId)
                ).length;
                if (completedCount < 3 && dayIndex >= 5) {
                    cell.classList.add('warning');
                }
            }
            
            cell.addEventListener('click', () => toggleActivity(trackingId, activity.activityId, dateStr));
            grid.appendChild(cell);
        });
    });
    
    // Daily scores row
    const scoreLabel = document.createElement('div');
    scoreLabel.className = 'daily-score-label';
    scoreLabel.textContent = 'Daily Score';
    dailyScores.appendChild(scoreLabel);
    
    days.forEach((day, dayIndex) => {
        const date = new Date(weekDates.monday);
        date.setDate(date.getDate() + dayIndex);
        const dateStr = date.toISOString().split('T')[0];
        const tracking = getTrackingForDate(playerId, weekId, dateStr);
        const score = tracking ? tracking.dailyScore : 0;
        
        const scoreCell = document.createElement('div');
        scoreCell.className = 'daily-score-cell';
        scoreCell.textContent = `${score}/${activities.length}`;
        dailyScores.appendChild(scoreCell);
    });
}

function toggleActivity(trackingId, activityId, dateStr) {
    const playerId = Storage.getCurrentPlayer();
    const weekId = Storage.getCurrentWeek();
    
    let tracking = getTrackingForDate(playerId, weekId, dateStr);
    
    if (!tracking) {
        // Create new tracking entry
        tracking = {
            trackingId: trackingId,
            playerId: playerId,
            weekId: weekId,
            date: dateStr,
            completedActivities: [],
            dailyScore: 0,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };
    }
    
    // Toggle activity
    const index = tracking.completedActivities.indexOf(activityId);
    if (index > -1) {
        tracking.completedActivities.splice(index, 1);
    } else {
        tracking.completedActivities.push(activityId);
    }
    
    // Recalculate daily score
    tracking.dailyScore = tracking.completedActivities.length;
    tracking.updatedAt = new Date().toISOString();
    
    // Save to storage
    Storage.saveTracking(trackingId, tracking);
    
    // Re-render grid and update scores
    renderActivityGrid(playerId, weekId);
    updateScores(playerId, weekId);
}

function getTrackingForDate(playerId, weekId, dateStr) {
    const allTracking = Storage.mergeTracking(MockData.tracking);
    return allTracking.find(t => 
        t.playerId === playerId && 
        t.weekId === weekId && 
        t.date === dateStr
    );
}

function getAllTrackingForWeek(playerId, weekId) {
    const allTracking = Storage.mergeTracking(MockData.tracking);
    return allTracking.filter(t => 
        t.playerId === playerId && t.weekId === weekId
    );
}

function updateScores(playerId, weekId) {
    const allTracking = getAllTrackingForWeek(playerId, weekId);
    const weeklyTotal = allTracking.reduce((sum, t) => sum + t.dailyScore, 0);
    const maxScore = MockData.activities.filter(a => a.isActive).length * 7;
    
    document.getElementById('weeklyScore').textContent = `Score: ${weeklyTotal}/${maxScore}`;
    document.getElementById('totalScore').textContent = weeklyTotal;
    document.getElementById('progressFill').style.width = `${(weeklyTotal / maxScore) * 100}%`;
}

function navigateWeek(direction) {
    const currentPlayerId = Storage.getCurrentPlayer();
    const currentWeekId = Storage.getCurrentWeek();
    
    // Save current weekly reflection before navigating
    saveWeeklyReflection(currentPlayerId, currentWeekId);
    
    const weekDates = MockData.getWeekDates(currentWeekId);
    const newDate = new Date(weekDates.monday);
    newDate.setDate(newDate.getDate() + (direction * 7));
    const newWeekId = MockData.getWeekId(newDate);
    Storage.setCurrentWeek(newWeekId);
    
    // Re-render
    initPlayerView();
}

// Load weekly reflection from storage
function loadWeeklyReflection(playerId, weekId) {
    const reflectionKey = `weekly-reflection-${playerId}-${weekId}`;
    const saved = localStorage.getItem(reflectionKey);
    
    if (saved) {
        try {
            const data = JSON.parse(saved);
            const wentWellEl = document.getElementById('trackerWentWell');
            const doBetterEl = document.getElementById('trackerDoBetter');
            const planForWeekEl = document.getElementById('trackerPlanForWeek');
            
            if (wentWellEl) wentWellEl.value = data.wentWell || '';
            if (doBetterEl) doBetterEl.value = data.doBetter || '';
            if (planForWeekEl) planForWeekEl.value = data.planForWeek || '';
        } catch (e) {
            console.warn('Could not load weekly reflection:', e);
        }
    }
}

// Save weekly reflection to storage
function saveWeeklyReflection(playerId, weekId) {
    const reflectionKey = `weekly-reflection-${playerId}-${weekId}`;
    const wentWellEl = document.getElementById('trackerWentWell');
    const doBetterEl = document.getElementById('trackerDoBetter');
    const planForWeekEl = document.getElementById('trackerPlanForWeek');
    
    if (!wentWellEl || !doBetterEl || !planForWeekEl) return;
    
    const data = {
        wentWell: wentWellEl.value || '',
        doBetter: doBetterEl.value || '',
        planForWeek: planForWeekEl.value || '',
        updatedAt: new Date().toISOString()
    };
    
    localStorage.setItem(reflectionKey, JSON.stringify(data));
}

// Setup weekly reflection event listeners
function setupWeeklyReflection(playerId, weekId) {
    const wentWellEl = document.getElementById('trackerWentWell');
    const doBetterEl = document.getElementById('trackerDoBetter');
    const planForWeekEl = document.getElementById('trackerPlanForWeek');
    
    if (!wentWellEl || !doBetterEl || !planForWeekEl) return;
    
    // Auto-save on input with debounce
    let saveTimeout;
    const autoSave = () => {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
            saveWeeklyReflection(playerId, weekId);
        }, 1000);
    };
    
    wentWellEl.addEventListener('input', autoSave);
    doBetterEl.addEventListener('input', autoSave);
    planForWeekEl.addEventListener('input', autoSave);
}

function setupNavigationMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.getElementById('navMenu');
    const navClose = document.getElementById('navClose');
    
    menuToggle?.addEventListener('click', () => {
        navMenu?.classList.add('open');
    });
    
    navClose?.addEventListener('click', () => {
        navMenu?.classList.remove('open');
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (navMenu && !navMenu.contains(e.target) && !menuToggle?.contains(e.target)) {
            navMenu.classList.remove('open');
        }
    });
}

// ===== My Progress =====
function initMyProgress() {
    // Set current player
    const currentPlayerId = Storage.getCurrentPlayer() || 
        (MockData.players.find(p => p.isActive)?.playerId || MockData.players[0].playerId);
    Storage.setCurrentPlayer(currentPlayerId);
    
    const player = MockData.players.find(p => p.playerId === currentPlayerId);
    document.getElementById('playerName').textContent = player.name;
    
    // Setup navigation menu
    setupNavigationMenu();
    
    // Load and display progress data
    loadPlayerProgress(currentPlayerId);
}

function loadPlayerProgress(playerId) {
    const allTracking = Storage.mergeTracking(MockData.tracking);
    const playerTracking = allTracking.filter(t => t.playerId === playerId);
    
    // Get all unique weeks for this player
    const weeks = [...new Set(playerTracking.map(t => t.weekId))].sort().reverse();
    
    // Calculate weekly scores
    const weeklyData = weeks.map(weekId => {
        const weekTracking = playerTracking.filter(t => t.weekId === weekId);
        const weeklyScore = weekTracking.reduce((sum, t) => sum + t.dailyScore, 0);
        const daysCompleted = weekTracking.filter(t => t.dailyScore > 0).length;
        const bestDay = Math.max(...weekTracking.map(t => t.dailyScore), 0);
        const totalActivities = weekTracking.reduce((sum, t) => sum + t.completedActivities.length, 0);
        const weekDates = MockData.getWeekDates(weekId);
        
        return {
            weekId: weekId,
            score: weeklyScore,
            daysCompleted: daysCompleted,
            bestDay: bestDay,
            totalActivities: totalActivities,
            dates: weekDates
        };
    });
    
    // Update summary cards
    const currentWeek = weeklyData[0] || { score: 0 };
    const previousWeek = weeklyData[1] || { score: 0 };
    const avgScore = weeklyData.length > 0 
        ? Math.round(weeklyData.reduce((sum, w) => sum + w.score, 0) / weeklyData.length)
        : 0;
    const bestWeek = weeklyData.reduce((best, week) => 
        week.score > best.score ? week : best, weeklyData[0] || { score: 0, dates: { monday: new Date() } }
    );
    
    document.getElementById('currentWeekScore').textContent = currentWeek.score;
    const scoreChange = currentWeek.score - previousWeek.score;
    const changeEl = document.getElementById('currentWeekChange');
    if (scoreChange > 0) {
        changeEl.textContent = `↑ +${scoreChange} from last week`;
        changeEl.style.color = 'var(--success-green)';
    } else if (scoreChange < 0) {
        changeEl.textContent = `↓ ${scoreChange} from last week`;
        changeEl.style.color = 'var(--error-red)';
    } else {
        changeEl.textContent = 'Same as last week';
        changeEl.style.color = 'var(--medium-gray)';
    }
    
    document.getElementById('averageScore').textContent = avgScore;
    document.getElementById('bestWeekScore').textContent = bestWeek.score;
    if (bestWeek.dates) {
        document.getElementById('bestWeekDate').textContent = 
            `Week of ${formatDate(bestWeek.dates.monday)}`;
    }
    
    // Calculate consistency streak
    let streak = 0;
    for (let i = 0; i < weeklyData.length; i++) {
        if (weeklyData[i].score > 0) {
            streak++;
        } else {
            break;
        }
    }
    document.getElementById('consistencyStreak').textContent = streak;
    
    // Render weekly scores chart
    renderWeeklyScoresChart(weeklyData);
    
    // Render weekly activity performance
    const currentWeekId = Storage.getCurrentWeek() || MockData.currentWeekId;
    renderActivityPerformance(currentWeekId, currentPlayerId);
    
    // Render weekly breakdown table
    renderWeeklyBreakdown(weeklyData);
    
    // Calculate and display trends
    calculateTrends(weeklyData, playerTracking);
}

function renderWeeklyScoresChart(weeklyData) {
    const ctx = document.getElementById('weeklyScoresChart');
    if (!ctx || typeof Chart === 'undefined') return;
    
    const labels = weeklyData.map(w => 
        `Week of ${formatDate(w.dates.monday)}`
    ).reverse();
    const scores = weeklyData.map(w => w.score).reverse();
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Weekly Score',
                data: scores,
                borderColor: 'var(--true-green)',
                backgroundColor: 'rgba(150, 200, 85, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: 'var(--true-green)',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 35,
                    ticks: {
                        stepSize: 5
                    }
                }
            }
        }
    });
}

function renderActivityPerformance(weekId, playerId) {
    const container = document.getElementById('activityStats');
    if (!container) return;
    
    const activities = MockData.activities.filter(a => a.isActive);
    const allTracking = Storage.mergeTracking(MockData.tracking);
    
    // Get tracking data for current week only
    const weekTracking = allTracking.filter(t => 
        t.playerId === playerId && t.weekId === weekId
    );
    
    container.innerHTML = '';
    
    activities.forEach(activity => {
        // Count how many times this activity was completed in the current week
        const completions = weekTracking.filter(t => 
            t.completedActivities.includes(activity.activityId)
        ).length;
        
        // Calculate required times per week based on frequency
        let requiredPerWeek = 7; // Default to daily
        if (activity.frequency === '3x/week') {
            requiredPerWeek = 3;
        } else if (activity.frequency === 'weekly') {
            requiredPerWeek = 1;
        } else if (activity.frequency === 'daily') {
            requiredPerWeek = 7;
        }
        
        const percentage = requiredPerWeek > 0 ? Math.round((completions / requiredPerWeek) * 100) : 0;
        
        const statCard = document.createElement('div');
        statCard.className = 'activity-stat-card';
        statCard.innerHTML = `
            <div class="activity-stat-name">${activity.name}</div>
            <div class="activity-stat-bar">
                <div class="activity-stat-fill" style="width: ${percentage}%"></div>
            </div>
            <div class="activity-stat-value">${percentage}% (${completions}/${requiredPerWeek})</div>
        `;
        container.appendChild(statCard);
    });
}

function renderWeeklyBreakdown(weeklyData) {
    const tbody = document.getElementById('weeklyBreakdownBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    weeklyData.forEach(week => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatDate(week.dates.monday)} - ${formatDate(week.dates.sunday)}</td>
            <td><strong>${week.score}</strong></td>
            <td>${week.daysCompleted}/7</td>
            <td>${week.bestDay}/${MockData.activities.filter(a => a.isActive).length}</td>
            <td>${week.totalActivities}</td>
        `;
        tbody.appendChild(row);
    });
}

function calculateTrends(weeklyData, playerTracking) {
    // Score trend
    if (weeklyData.length >= 2) {
        const recent = weeklyData.slice(0, 3).reduce((sum, w) => sum + w.score, 0) / Math.min(3, weeklyData.length);
        const older = weeklyData.slice(3, 6).reduce((sum, w) => sum + w.score, 0) / Math.min(3, weeklyData.length - 3);
        
        const trendEl = document.getElementById('scoreTrend');
        const arrowEl = document.getElementById('scoreTrendArrow');
        const textEl = document.getElementById('scoreTrendText');
        
        if (recent > older * 1.1) {
            arrowEl.textContent = '↑';
            arrowEl.style.color = 'var(--success-green)';
            textEl.textContent = 'Improving';
        } else if (recent < older * 0.9) {
            arrowEl.textContent = '↓';
            arrowEl.style.color = 'var(--error-red)';
            textEl.textContent = 'Declining';
        } else {
            arrowEl.textContent = '→';
            arrowEl.style.color = 'var(--medium-gray)';
            textEl.textContent = 'Stable';
        }
    }
    
    // Most improved activity
    const activities = MockData.activities.filter(a => a.isActive);
    const currentPlayerId = Storage.getCurrentPlayer();
    const recentWeeks = weeklyData.slice(0, 2).map(w => w.weekId);
    const olderWeeks = weeklyData.slice(2, 4).map(w => w.weekId);
    
    let mostImproved = null;
    let maxImprovement = 0;
    
    activities.forEach(activity => {
        const recentCompletions = playerTracking
            .filter(t => recentWeeks.includes(t.weekId) && t.completedActivities.includes(activity.activityId))
            .length;
        const olderCompletions = playerTracking
            .filter(t => olderWeeks.includes(t.weekId) && t.completedActivities.includes(activity.activityId))
            .length;
        
        const improvement = recentCompletions - olderCompletions;
        if (improvement > maxImprovement) {
            maxImprovement = improvement;
            mostImproved = activity.name;
        }
    });
    
    document.getElementById('mostImprovedActivity').textContent = mostImproved || '-';
    
    // Needs attention (lowest completion rate)
    let needsAttention = null;
    let minPercentage = 100;
    
    activities.forEach(activity => {
        const completions = playerTracking.filter(t => 
            t.completedActivities.includes(activity.activityId)
        ).length;
        const total = playerTracking.length;
        const percentage = total > 0 ? (completions / total) * 100 : 0;
        
        if (percentage < minPercentage) {
            minPercentage = percentage;
            needsAttention = activity.name;
        }
    });
    
    document.getElementById('needsAttention').textContent = needsAttention || '-';
}

// ===== Leaderboard =====
function initLeaderboard() {
    setupNavigationMenu();
    setPlayerNameInHeader();
    const currentWeekId = Storage.getCurrentWeek() || MockData.currentWeekId;
    
    // Setup week selector
    setupWeekSelector();
    
    // Render leaderboard
    renderLeaderboard(currentWeekId);
}

function setupWeekSelector() {
    const selector = document.getElementById('weekSelector');
    if (!selector) return;
    
    // Generate week options
    const weeks = [];
    for (let i = 0; i < 4; i++) {
        const date = new Date(MockData.currentWeekId.split('-')[0], 0, 1);
        const weekNum = parseInt(MockData.currentWeekId.split('-W')[1]);
        const weekId = `${date.getFullYear()}-W${String(weekNum - i).padStart(2, '0')}`;
        const weekDates = MockData.getWeekDates(weekId);
        weeks.push({
            id: weekId,
            label: `Week of ${formatDate(weekDates.monday)} - ${formatDate(weekDates.sunday)}`
        });
    }
    
    selector.innerHTML = weeks.map(w => 
        `<option value="${w.id}">${w.label}</option>`
    ).join('');
    
    selector.value = Storage.getCurrentWeek() || MockData.currentWeekId;
    
    selector.addEventListener('change', (e) => {
        renderLeaderboard(e.target.value);
    });
}

function renderLeaderboard(weekId) {
    const currentPlayerId = Storage.getCurrentPlayer();
    const allTracking = Storage.mergeTracking(MockData.tracking);
    const activePlayers = MockData.players.filter(p => p.isActive);
    
    // Calculate weekly scores
    const playerScores = activePlayers.map(player => {
        const weekTracking = allTracking.filter(t => 
            t.playerId === player.playerId && t.weekId === weekId
        );
        const weeklyScore = weekTracking.reduce((sum, t) => sum + t.dailyScore, 0);
        return {
            player: player,
            score: weeklyScore
        };
    });
    
    // Sort by score (descending)
    playerScores.sort((a, b) => b.score - a.score);
    
    // Render top 3 podium
    renderPodium(playerScores.slice(0, 3), currentPlayerId);
    
    // Render full rankings
    renderRankings(playerScores, currentPlayerId);
    
    // Render stats
    renderStats(playerScores);
}

function renderPodium(top3, currentPlayerId) {
    const container = document.getElementById('podiumContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    const positions = ['second', 'first', 'third'];
    const medals = ['🥈', '🥇', '🥉'];
    
    top3.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = `podium-card ${positions[index]}`;
        card.innerHTML = `
            <div class="podium-rank">${medals[index]}</div>
            <div class="podium-name">${item.player.name}</div>
            <div class="podium-score">${item.score}</div>
        `;
        container.appendChild(card);
    });
}

function renderRankings(playerScores, currentPlayerId) {
    const container = document.getElementById('rankingsList');
    if (!container) return;
    
    container.innerHTML = '';
    
    playerScores.forEach((item, index) => {
        const rankingItem = document.createElement('div');
        rankingItem.className = 'ranking-item';
        if (item.player.playerId === currentPlayerId) {
            rankingItem.classList.add('current-player');
        }
        
        rankingItem.innerHTML = `
            <div class="ranking-number">${index + 1}</div>
            <div class="ranking-name">${item.player.name}</div>
            <div class="ranking-score">${item.score}</div>
        `;
        
        container.appendChild(rankingItem);
    });
}

function renderStats(playerScores) {
    const total = playerScores.reduce((sum, item) => sum + item.score, 0);
    const average = playerScores.length > 0 ? Math.round(total / playerScores.length) : 0;
    const maxScore = MockData.activities.filter(a => a.isActive).length * 7;
    const perfectWeeks = playerScores.filter(item => item.score === maxScore).length;
    
    // Find most improved (simplified - just highest score for now)
    const mostImproved = playerScores.length > 0 ? playerScores[0].player.name : '-';
    
    document.getElementById('teamAverage').textContent = average;
    document.getElementById('mostImproved').textContent = mostImproved;
    document.getElementById('perfectWeeks').textContent = perfectWeeks;
}

// ===== Reflection =====
function initReflection() {
    setupNavigationMenu();
    setPlayerNameInHeader();
    const currentPlayerId = Storage.getCurrentPlayer();
    const currentWeekId = Storage.getCurrentWeek() || MockData.currentWeekId;
    const weekDates = MockData.getWeekDates(currentWeekId);
    
    document.getElementById('reflectionWeekTitle').textContent = 
        `Week of ${formatDate(weekDates.monday)} - ${formatDate(weekDates.sunday)}`;
    
    // Setup character counters
    Forms.setupCharCounter('wentWell', 'wentWellCount');
    Forms.setupCharCounter('doBetter', 'doBetterCount');
    Forms.setupCharCounter('planForWeek', 'planForWeekCount');
    
    // Load existing reflection
    const reflectionId = `${currentPlayerId}#${currentWeekId}`;
    const reflection = Storage.getReflection(reflectionId) || 
        MockData.reflections.find(r => r.reflectionId === reflectionId);
    
    if (reflection) {
        displayReflection(reflection);
    }
    
    // Setup form
    const form = document.getElementById('reflectionForm');
    form?.addEventListener('submit', (e) => {
        e.preventDefault();
        saveReflection(currentPlayerId, currentWeekId);
    });
    
    // Auto-save
    let autoSaveTimer;
    ['wentWell', 'doBetter', 'planForWeek'].forEach(fieldId => {
        const field = document.getElementById(fieldId);
        field?.addEventListener('input', () => {
            clearTimeout(autoSaveTimer);
            updateSaveStatus('saving');
            autoSaveTimer = setTimeout(() => {
                saveReflection(currentPlayerId, currentWeekId, true);
            }, 30000); // 30 seconds
        });
    });
    
    // Edit button
    document.getElementById('editBtn')?.addEventListener('click', () => {
        showEditMode();
    });
}

function saveReflection(playerId, weekId, isAutoSave = false) {
    const reflectionId = `${playerId}#${weekId}`;
    const form = document.getElementById('reflectionForm');
    const formData = Forms.getFormData('reflectionForm');
    
    const reflection = {
        reflectionId: reflectionId,
        playerId: playerId,
        weekId: weekId,
        wentWell: formData.wentWell || '',
        doBetter: formData.doBetter || '',
        planForWeek: formData.planForWeek || '',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    };
    
    Storage.saveReflection(reflectionId, reflection);
    
    if (!isAutoSave) {
        displayReflection(reflection);
        updateSaveStatus('saved');
    } else {
        updateSaveStatus('saved');
    }
}

function displayReflection(reflection) {
    document.getElementById('displayWentWell').textContent = reflection.wentWell;
    document.getElementById('displayDoBetter').textContent = reflection.doBetter;
    document.getElementById('displayPlanForWeek').textContent = reflection.planForWeek;
    
    document.getElementById('reflectionForm').style.display = 'none';
    document.getElementById('savedReflection').style.display = 'block';
    document.getElementById('editBtn').style.display = 'inline-block';
}

function showEditMode() {
    const reflection = Storage.getReflection(`${Storage.getCurrentPlayer()}#${Storage.getCurrentWeek()}`);
    if (reflection) {
        Forms.setFormData('reflectionForm', reflection);
    }
    
    document.getElementById('reflectionForm').style.display = 'block';
    document.getElementById('savedReflection').style.display = 'none';
    document.getElementById('editBtn').style.display = 'none';
}

function updateSaveStatus(status) {
    const indicator = document.getElementById('saveStatus');
    if (!indicator) return;
    
    indicator.className = 'save-status ' + status;
    indicator.textContent = status === 'saving' ? 'Saving...' : 'Saved';
}

// ===== Content List =====
function initContentList() {
    setupNavigationMenu();
    setPlayerNameInHeader();
    const categories = ['guidance', 'workouts', 'nutrition', 'mental-health', 'resources'];
    const categoryLabels = {
        'guidance': 'Training Guidance',
        'workouts': 'Workouts',
        'nutrition': 'Nutrition Tips',
        'mental-health': 'Mental Performance',
        'resources': 'Resources'
    };
    
    const container = document.getElementById('contentList');
    if (!container) return;
    
    container.innerHTML = '';
    
    categories.forEach(category => {
        let categoryContent = [];
        
        // Load from appropriate JSON file
        if (category === 'guidance') {
            categoryContent = trainingGuidanceData.filter(c => c.isPublished !== false)
                .sort((a, b) => (a.displayOrder || 0) - (b.displayOrder || 0));
        } else if (category === 'workouts') {
            categoryContent = workoutsData.filter(c => c.isPublished !== false)
                .sort((a, b) => (a.displayOrder || 0) - (b.displayOrder || 0));
        } else if (category === 'nutrition') {
            categoryContent = nutritionTipsData.filter(c => c.isPublished !== false)
                .sort((a, b) => (a.displayOrder || 0) - (b.displayOrder || 0));
        } else if (category === 'mental-health') {
            categoryContent = mentalPerformanceData.filter(c => c.isPublished !== false)
                .sort((a, b) => (a.displayOrder || 0) - (b.displayOrder || 0));
        } else if (category === 'resources') {
            categoryContent = resourcesData.filter(c => c.isPublished !== false)
                .sort((a, b) => (a.displayOrder || 0) - (b.displayOrder || 0));
        }
        
        if (categoryContent.length === 0) return;
        
        const categorySection = document.createElement('div');
        categorySection.className = 'content-category';
        
        const title = document.createElement('h2');
        title.className = 'content-category-title';
        title.textContent = categoryLabels[category] || category;
        categorySection.appendChild(title);
        
        const items = document.createElement('div');
        items.className = 'content-items';
        
        categoryContent.forEach(content => {
            const card = document.createElement('div');
            card.className = 'content-item-card';
            
            // Determine navigation based on content type
            if (content.slug) {
                // Workout with slug (special case for weekly-workout-plan)
                card.addEventListener('click', () => {
                    Router.navigate('content-page', { slug: content.slug });
                });
            } else {
                // Regular JSON content: use category and id
                const categoryParam = category === 'mental-health' ? 'mental-performance' : 
                                     category === 'guidance' ? 'training-guidance' : category;
                card.addEventListener('click', () => {
                    Router.navigate('content-page', { category: categoryParam, id: content.id });
                });
            }
            
            card.innerHTML = `
                <div class="content-item-title">${content.title}</div>
                ${content.description ? `<div class="content-item-description">${content.description}</div>` : ''}
                <div class="content-item-meta">Last updated: ${formatDate(new Date(content.updatedAt))}</div>
            `;
            
            items.appendChild(card);
        });
        
        categorySection.appendChild(items);
        container.appendChild(categorySection);
    });
}

// ===== Content Page =====
// Load workout plan data
let workoutPlanData = null;

async function loadWorkoutPlan() {
    try {
        const response = await fetch('data/workout-plan.json');
        if (!response.ok) {
            throw new Error('Failed to load workout plan');
        }
        workoutPlanData = await response.json();
    } catch (error) {
        console.warn('Could not load workout plan, using defaults:', error);
        workoutPlanData = null;
    }
}

function renderWorkoutTable(workoutData) {
    if (!workoutData) return '';
    
    let html = `
        <p>Track your progress for each day. Enter the number of reps you achieve!</p>
        <div class="workout-tracker" data-workout-id="${workoutData.workoutId}">
            <table class="workout-table">
                <thead>
                    <tr>
                        <th>Activity</th>
                        <th>Duration/Sets</th>
                        <th>Day 1 (reps)</th>
                        <th>Day 2 (reps)</th>
                        <th>Day 3 (reps)</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    workoutData.sections.forEach(section => {
        html += `<tr class="workout-section-header">`;
        if (section.sectionNote) {
            html += `<td colspan="5"><strong>${section.sectionName}</strong> <em>(${section.sectionNote})</em></td>`;
        } else {
            html += `<td colspan="5"><strong>${section.sectionName}</strong></td>`;
        }
        html += `</tr>`;
        
        section.activities.forEach(activity => {
            const youtubeIcon = activity.link 
                ? `<a href="${activity.link}" target="_blank" class="youtube-link" title="Watch video tutorial">
                     <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                       <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                     </svg>
                   </a>`
                : '';
            
            html += `
                <tr data-activity="${activity.activityId}">
                    <td>
                        <span class="workout-activity-name">${activity.name}</span>
                        ${youtubeIcon}
                    </td>
                    <td data-duration>${activity.duration}</td>
                    <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                    <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                    <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                </tr>
            `;
        });
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    return html;
}

function initContentPage() {
    setupNavigationMenu();
    setPlayerNameInHeader();
    const params = Router.getQueryParams();
    const category = params.category;
    const id = params.id;
    const slug = params.slug;
    
    let content = null;
    let contentTitle = '';
    let contentUpdatedAt = '';
    let contentHtml = '';
    
    // Check if this is a JSON-based content (category and id provided)
    if (category && id) {
        let jsonData = [];
        if (category === 'nutrition') {
            jsonData = nutritionTipsData;
        } else if (category === 'mental-performance') {
            jsonData = mentalPerformanceData;
        } else if (category === 'resources') {
            jsonData = resourcesData;
        } else if (category === 'training-guidance') {
            jsonData = trainingGuidanceData;
        } else if (category === 'workouts') {
            jsonData = workoutsData;
        }
        
        const card = jsonData.find(c => c.id === id && c.isPublished !== false);
        if (card) {
            contentTitle = card.title;
            contentUpdatedAt = card.updatedAt;
            contentHtml = card.content;
        } else {
            Router.navigate('content-list');
            return;
        }
    } else if (slug) {
        // Check if this is a workout with slug (special case for weekly-workout-plan)
        if (slug === 'weekly-workout-plan' && workoutPlanData) {
            const workoutCard = workoutsData.find(c => c.slug === slug && c.isPublished !== false);
            if (workoutCard) {
                // Special handling for weekly-workout-plan - render from workout-plan.json
                contentTitle = workoutCard.title;
                contentUpdatedAt = workoutCard.updatedAt;
                contentHtml = null; // Signal to use workout table renderer
            } else {
                Router.navigate('content-list');
                return;
            }
        } else {
            // Try to find in JSON files by slug
            let found = false;
            const allJsonData = [
                ...trainingGuidanceData,
                ...workoutsData,
                ...nutritionTipsData,
                ...mentalPerformanceData,
                ...resourcesData
            ];
            
            const jsonCard = allJsonData.find(c => c.slug === slug && c.isPublished !== false);
            if (jsonCard && jsonCard.content) {
                contentTitle = jsonCard.title;
                contentUpdatedAt = jsonCard.updatedAt;
                contentHtml = jsonCard.content;
                found = true;
            }
            
            if (!found) {
                Router.navigate('content-list');
                return;
            }
        }
    } else {
        Router.navigate('content-list');
        return;
    }
    
    const contentTitleEl = document.getElementById('contentTitle');
    if (contentTitleEl) {
        contentTitleEl.textContent = contentTitle;
    }
    const lastUpdatedEl = document.getElementById('lastUpdated');
    if (lastUpdatedEl) {
        lastUpdatedEl.textContent = `Last Updated: ${formatDate(new Date(contentUpdatedAt))}`;
    }
    
    const contentBody = document.getElementById('contentBody');
    
    // If this is a workout plan (contentHtml is null), render from workout-plan.json
    if (!contentHtml && slug === 'weekly-workout-plan' && workoutPlanData) {
        contentBody.innerHTML = renderWorkoutTable(workoutPlanData);
    } else {
        contentBody.innerHTML = contentHtml;
    }
    
    // Show print button if this is a workout page
    const workoutTracker = document.querySelector('.workout-tracker');
    const printButton = document.getElementById('printButton');
    if (workoutTracker && printButton) {
        printButton.style.display = 'block';
        printButton.addEventListener('click', () => printWorkout(workoutTracker));
    } else if (printButton) {
        printButton.style.display = 'none';
    }
    
    // Initialize workout tracker if this is a workout page
    if (workoutTracker) {
        initWorkoutTracker(workoutTracker);
    }
}

function printWorkout(tracker) {
    // Create a print-friendly version
    const printWindow = window.open('', '_blank');
    const workoutId = tracker.dataset.workoutId || 'workout-001';
    const progress = Storage.getWorkoutProgress(workoutId);
    
    // Get current values from inputs
    const inputs = tracker.querySelectorAll('.workout-reps-input');
    const currentValues = {};
    inputs.forEach(input => {
        const activity = input.closest('tr').dataset.activity;
        const day = input.dataset.day;
        if (!currentValues[activity]) currentValues[activity] = {};
        currentValues[activity][day] = input.value || '';
    });
    
    // Build print HTML
    let printHTML = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Workout #1</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    color: #000;
                }
                h1 {
                    font-size: 24px;
                    margin-bottom: 20px;
                    text-align: center;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }
                th {
                    background-color: rgb(150, 200, 85);
                    color: #FFFFFF;
                    padding: 10px;
                    text-align: left;
                    font-weight: bold;
                    border: 1px solid rgb(150, 200, 85);
                }
                td {
                    padding: 8px 10px;
                    border: 1px solid #ddd;
                }
                .section-header {
                    background-color: #D4EDDA;
                    font-weight: bold;
                    padding: 10px;
                }
                .section-header td {
                    background-color: #D4EDDA;
                    border: 1px solid #28A745;
                }
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                .day-cell {
                    text-align: center;
                    min-width: 80px;
                }
                @media print {
                    body { padding: 10px; }
                    @page { 
                        margin: 1cm;
                        size: landscape;
                    }
                }
            </style>
        </head>
        <body>
            <h1>Workout #1</h1>
            <table>
                <thead>
                    <tr>
                        <th>Activity</th>
                        <th>Duration/Sets</th>
                        <th>Day 1</th>
                        <th>Day 2</th>
                        <th>Day 3</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add rows
    const rows = tracker.querySelectorAll('tbody tr');
    rows.forEach(row => {
        if (row.classList.contains('workout-section-header')) {
            const sectionName = row.textContent.trim();
            printHTML += `<tr class="section-header"><td colspan="5"><strong>${sectionName}</strong></td></tr>`;
        } else if (row.dataset.activity) {
            const cells = row.querySelectorAll('td');
            const activity = cells[0].textContent.trim();
            const duration = cells[1].textContent.trim();
            const day1 = currentValues[row.dataset.activity]?.['1'] || '';
            const day2 = currentValues[row.dataset.activity]?.['2'] || '';
            const day3 = currentValues[row.dataset.activity]?.['3'] || '';
            
            printHTML += `
                <tr>
                    <td>${activity}</td>
                    <td>${duration}</td>
                    <td class="day-cell">${day1}</td>
                    <td class="day-cell">${day2}</td>
                    <td class="day-cell">${day3}</td>
                </tr>
            `;
        }
    });
    
    printHTML += `
                </tbody>
            </table>
        </body>
        </html>
    `;
    
    printWindow.document.write(printHTML);
    printWindow.document.close();
    
    // Wait for content to load, then print
    setTimeout(() => {
        printWindow.print();
    }, 250);
}

function initWorkoutTracker(tracker) {
    const workoutId = tracker.dataset.workoutId || 'workout-001';
    const progress = Storage.getWorkoutProgress(workoutId);
    
    // Load saved progress
    const inputs = tracker.querySelectorAll('.workout-reps-input');
    inputs.forEach(input => {
        const activity = input.closest('tr').dataset.activity;
        const day = input.dataset.day;
        
        // Load saved value
        if (progress[activity] && progress[activity][day] !== null && progress[activity][day] !== undefined) {
            input.value = progress[activity][day];
        }
        
        // Add event listener for input changes
        input.addEventListener('input', (e) => {
            const reps = e.target.value;
            Storage.saveWorkoutProgress(workoutId, activity, day, reps);
            updateRowVisualState(input.closest('tr'));
        });
        
        // Also save on blur (when user leaves the field)
        input.addEventListener('blur', (e) => {
            const reps = e.target.value;
            Storage.saveWorkoutProgress(workoutId, activity, day, reps);
            updateRowVisualState(input.closest('tr'));
        });
        
        // Set initial visual state
        updateRowVisualState(input.closest('tr'));
    });
}

function updateRowVisualState(row) {
    const inputs = row.querySelectorAll('.workout-reps-input');
    const hasValue = Array.from(inputs).some(input => input.value && parseInt(input.value) > 0);
    
    if (hasValue) {
        row.classList.add('workout-completed');
    } else {
        row.classList.remove('workout-completed');
    }
}

// ===== Admin Login =====
function initAdminLogin() {
    // Check if already logged in
    const auth = Storage.getAdminAuth();
    if (auth && auth.isAuthenticated) {
        Router.navigate('admin-dashboard');
        return;
    }
    
    const form = document.getElementById('loginForm');
    form?.addEventListener('submit', (e) => {
        e.preventDefault();
        handleAdminLogin();
    });
}

function handleAdminLogin() {
    const formData = Forms.getFormData('loginForm');
    const errorDiv = document.getElementById('loginError');
    
    // Simple validation (in real app, this would check against Cognito)
    if (!Forms.validateEmail(formData.email)) {
        errorDiv.textContent = 'Please enter a valid email address';
        errorDiv.style.display = 'block';
        return;
    }
    
    if (!formData.password || formData.password.length < 8) {
        errorDiv.textContent = 'Password must be at least 8 characters';
        errorDiv.style.display = 'block';
        return;
    }
    
    // Simulate authentication (accept any email/password for prototype)
    Storage.setAdminAuth({
        isAuthenticated: true,
        email: formData.email,
        loginTime: new Date().toISOString()
    });
    
    Router.navigate('admin-dashboard');
}

// ===== Admin Dashboard =====
function initAdminDashboard() {
    // Check authentication
    const auth = Storage.getAdminAuth();
    if (!auth || !auth.isAuthenticated) {
        Router.navigate('admin-login');
        return;
    }
    
    // Setup tabs
    setupAdminTabs();
    
    // Initialize each tab
    initPlayersTab();
    initActivitiesTab();
    initContentTab();
    initOverviewTab();
    initSettingsTab();
    
    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', () => {
        Storage.clearAdminAuth();
        Router.navigate('admin-login');
    });
}

function setupAdminTabs() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
    
    // Show first tab by default
    switchTab('players');
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        }
    });
    
    // Show/hide tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });
    
    const activeTab = document.getElementById(`${tabName}Tab`);
    if (activeTab) {
        activeTab.style.display = 'block';
    }
}

function initPlayersTab() {
    renderPlayersTable();
    
    document.getElementById('addPlayerBtn')?.addEventListener('click', () => {
        showPlayerModal();
    });
    
    document.getElementById('playerSearch')?.addEventListener('input', (e) => {
        filterPlayers(e.target.value);
    });
}

function renderPlayersTable() {
    const tbody = document.getElementById('playersTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    MockData.players.forEach(player => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${player.name}</td>
            <td>${player.email || '-'}</td>
            <td><span class="status-badge ${player.isActive ? 'active' : 'inactive'}">${player.isActive ? 'Active' : 'Inactive'}</span></td>
            <td><code>${player.uniqueLink}</code></td>
            <td>
                <div class="table-actions">
                    <button class="table-action-btn" onclick="editPlayer('${player.playerId}')">Edit</button>
                    <button class="table-action-btn" onclick="copyPlayerLink('${player.uniqueLink}')">Copy Link</button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showPlayerModal(playerId = null) {
    const modal = document.getElementById('playerModal');
    const form = document.getElementById('playerForm');
    const title = document.getElementById('playerModalTitle');
    
    if (playerId) {
        const player = MockData.players.find(p => p.playerId === playerId);
        if (player) {
            title.textContent = 'Edit Player';
            Forms.setFormData('playerForm', player);
        }
    } else {
        title.textContent = 'Add Player';
        Forms.resetForm('playerForm');
        // Generate unique link
        const linkInput = document.getElementById('playerLinkInput');
        if (linkInput) {
            linkInput.value = generateUniqueLink();
        }
    }
    
    modal.style.display = 'flex';
    
    // Form submit
    form.onsubmit = (e) => {
        e.preventDefault();
        savePlayer(playerId);
    };
    
    // Close handlers
    document.getElementById('playerModalClose')?.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    document.getElementById('playerCancelBtn')?.addEventListener('click', () => {
        modal.style.display = 'none';
    });
}

function savePlayer(playerId) {
    const formData = Forms.getFormData('playerForm');
    
    if (playerId) {
        // Update existing
        const player = MockData.players.find(p => p.playerId === playerId);
        if (player) {
            Object.assign(player, formData);
        }
    } else {
        // Add new
        const newPlayer = {
            playerId: 'player-' + String(MockData.players.length + 1).padStart(3, '0'),
            ...formData,
            createdAt: new Date().toISOString(),
            isActive: true,
            teamId: 'team-001'
        };
        MockData.players.push(newPlayer);
    }
    
    renderPlayersTable();
    document.getElementById('playerModal').style.display = 'none';
}

function generateUniqueLink() {
    return Math.random().toString(36).substring(2, 11);
}

function copyPlayerLink(link) {
    navigator.clipboard.writeText(link).then(() => {
        alert('Link copied to clipboard!');
    });
}

function editPlayer(playerId) {
    showPlayerModal(playerId);
}

function filterPlayers(searchTerm) {
    const rows = document.querySelectorAll('#playersTableBody tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm.toLowerCase()) ? '' : 'none';
    });
}

function initActivitiesTab() {
    renderActivitiesList();
    
    document.getElementById('addActivityBtn')?.addEventListener('click', () => {
        showActivityModal();
    });
}

function renderActivitiesList() {
    const container = document.getElementById('activitiesList');
    if (!container) return;
    
    container.innerHTML = '';
    
    MockData.activities.sort((a, b) => a.displayOrder - b.displayOrder).forEach(activity => {
        const card = document.createElement('div');
        card.className = 'activity-card';
        card.innerHTML = `
            <div class="activity-drag-handle">☰</div>
            <div class="activity-info">
                <div class="activity-name">${activity.name}</div>
                <div class="activity-details">${activity.description} • ${activity.frequency} • ${activity.pointValue} point(s)</div>
            </div>
            <div class="activity-actions">
                <label class="toggle-switch">
                    <input type="checkbox" ${activity.isActive ? 'checked' : ''} onchange="toggleActivityStatus('${activity.activityId}')">
                    <span class="toggle-slider"></span>
                </label>
                <button class="table-action-btn" onclick="editActivity('${activity.activityId}')">Edit</button>
            </div>
        `;
        container.appendChild(card);
    });
}

function showActivityModal(activityId = null) {
    const modal = document.getElementById('activityModal');
    const form = document.getElementById('activityForm');
    const title = document.getElementById('activityModalTitle');
    
    if (activityId) {
        const activity = MockData.activities.find(a => a.activityId === activityId);
        if (activity) {
            title.textContent = 'Edit Activity';
            Forms.setFormData('activityForm', activity);
        }
    } else {
        title.textContent = 'Add Activity';
        Forms.resetForm('activityForm');
    }
    
    modal.style.display = 'flex';
    
    form.onsubmit = (e) => {
        e.preventDefault();
        saveActivity(activityId);
    };
    
    document.getElementById('activityModalClose')?.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    document.getElementById('activityCancelBtn')?.addEventListener('click', () => {
        modal.style.display = 'none';
    });
}

function saveActivity(activityId) {
    const formData = Forms.getFormData('activityForm');
    
    if (activityId) {
        const activity = MockData.activities.find(a => a.activityId === activityId);
        if (activity) {
            Object.assign(activity, formData);
        }
    } else {
        const newActivity = {
            activityId: 'activity-' + String(MockData.activities.length + 1).padStart(3, '0'),
            ...formData,
            displayOrder: MockData.activities.length + 1,
            isActive: true,
            teamId: 'team-001'
        };
        MockData.activities.push(newActivity);
    }
    
    renderActivitiesList();
    document.getElementById('activityModal').style.display = 'none';
}

function editActivity(activityId) {
    showActivityModal(activityId);
}

function toggleActivityStatus(activityId) {
    const activity = MockData.activities.find(a => a.activityId === activityId);
    if (activity) {
        activity.isActive = !activity.isActive;
        renderActivitiesList();
    }
}

function initContentTab() {
    renderContentTable();
    
    document.getElementById('addContentBtn')?.addEventListener('click', () => {
        showContentModal();
    });
    
    document.getElementById('contentTypeFilter')?.addEventListener('change', (e) => {
        filterContent(e.target.value);
    });
}

function renderContentTable() {
    const tbody = document.getElementById('contentTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    MockData.contentPages.forEach(content => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${content.title}</td>
            <td>${content.category}</td>
            <td><span class="status-badge ${content.isPublished ? 'published' : 'draft'}">${content.isPublished ? 'Published' : 'Draft'}</span></td>
            <td>${formatDate(new Date(content.updatedAt))}</td>
            <td>
                <div class="table-actions">
                    <button class="table-action-btn" onclick="editContent('${content.pageId}')">Edit</button>
                    <button class="table-action-btn" onclick="toggleContentPublish('${content.pageId}')">${content.isPublished ? 'Unpublish' : 'Publish'}</button>
                    <button class="table-action-btn danger" onclick="deleteContent('${content.pageId}')">Delete</button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showContentModal(contentId = null) {
    const modal = document.getElementById('contentModal');
    const form = document.getElementById('contentForm');
    const title = document.getElementById('contentModalTitle');
    const editor = document.getElementById('contentEditorInput');
    
    if (contentId) {
        const content = MockData.contentPages.find(c => c.pageId === contentId);
        if (content) {
            title.textContent = 'Edit Content';
            Forms.setFormData('contentForm', {
                title: content.title,
                type: content.category,
                slug: content.slug
            });
            if (editor) editor.innerHTML = content.htmlContent;
        }
    } else {
        title.textContent = 'Add Content';
        Forms.resetForm('contentForm');
        if (editor) editor.innerHTML = '';
    }
    
    modal.style.display = 'flex';
    
    // Editor toolbar
    document.querySelectorAll('.editor-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const command = btn.dataset.command;
            document.execCommand(command, false, null);
            editor.focus();
        });
    });
    
    form.onsubmit = (e) => {
        e.preventDefault();
        saveContent(contentId);
    };
    
    document.getElementById('contentModalClose')?.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    document.getElementById('contentCancelBtn')?.addEventListener('click', () => {
        modal.style.display = 'none';
    });
}

function saveContent(contentId) {
    const formData = Forms.getFormData('contentForm');
    const editor = document.getElementById('contentEditorInput');
    const htmlContent = editor ? editor.innerHTML : '';
    
    if (contentId) {
        const content = MockData.contentPages.find(c => c.pageId === contentId);
        if (content) {
            Object.assign(content, {
                title: formData.title,
                category: formData.type,
                slug: formData.slug,
                htmlContent: htmlContent,
                isPublished: formData.published || false,
                updatedAt: new Date().toISOString()
            });
        }
    } else {
        const newContent = {
            pageId: 'content-' + String(MockData.contentPages.length + 1).padStart(3, '0'),
            teamId: 'team-001',
            slug: formData.slug,
            title: formData.title,
            category: formData.type,
            htmlContent: htmlContent,
            isPublished: formData.published || false,
            displayOrder: MockData.contentPages.length + 1,
            createdBy: 'coach@truelacrosse.com',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            lastEditedBy: 'coach@truelacrosse.com'
        };
        MockData.contentPages.push(newContent);
    }
    
    renderContentTable();
    document.getElementById('contentModal').style.display = 'none';
}

function editContent(contentId) {
    showContentModal(contentId);
}

function toggleContentPublish(contentId) {
    const content = MockData.contentPages.find(c => c.pageId === contentId);
    if (content) {
        content.isPublished = !content.isPublished;
        renderContentTable();
    }
}

function deleteContent(contentId) {
    if (confirm('Are you sure you want to delete this content?')) {
        const index = MockData.contentPages.findIndex(c => c.pageId === contentId);
        if (index > -1) {
            MockData.contentPages.splice(index, 1);
            renderContentTable();
        }
    }
}

function filterContent(category) {
    const rows = document.querySelectorAll('#contentTableBody tr');
    rows.forEach(row => {
        if (!category) {
            row.style.display = '';
        } else {
            const categoryCell = row.cells[1];
            row.style.display = categoryCell.textContent === category ? '' : 'none';
        }
    });
}

function initOverviewTab() {
    // Summary cards
    document.getElementById('totalPlayers').textContent = MockData.players.filter(p => p.isActive).length;
    
    const allTracking = Storage.mergeTracking(MockData.tracking);
    const currentWeekScores = allTracking
        .filter(t => t.weekId === MockData.currentWeekId)
        .reduce((acc, t) => {
            if (!acc[t.playerId]) acc[t.playerId] = 0;
            acc[t.playerId] += t.dailyScore;
            return acc;
        }, {});
    const scores = Object.values(currentWeekScores);
    const avgScore = scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
    document.getElementById('avgScore').textContent = avgScore;
    
    document.getElementById('contentPages').textContent = MockData.contentPages.filter(c => c.isPublished).length;
    
    // Charts
    renderCharts();
    
    // Reflection highlights
    renderReflectionHighlights();
}

function renderCharts() {
    // Weekly scores chart
    const weeklyCtx = document.getElementById('weeklyScoresChart');
    if (weeklyCtx && typeof Chart !== 'undefined') {
        const allTracking = Storage.mergeTracking(MockData.tracking);
        const playerScores = {};
        
        MockData.players.filter(p => p.isActive).forEach(player => {
            const weekTracking = allTracking.filter(t => 
                t.playerId === player.playerId && t.weekId === MockData.currentWeekId
            );
            playerScores[player.name] = weekTracking.reduce((sum, t) => sum + t.dailyScore, 0);
        });
        
        new Chart(weeklyCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(playerScores),
                datasets: [{
                    label: 'Weekly Score',
                    data: Object.values(playerScores),
                    backgroundColor: 'rgba(0, 168, 232, 0.8)',
                    borderColor: '#00A8E8',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

function renderReflectionHighlights() {
    const container = document.getElementById('reflectionHighlights');
    if (!container) return;
    
    const reflections = Storage.mergeReflections(MockData.reflections);
    container.innerHTML = '<p>Reflection highlights will appear here as players submit their weekly reflections.</p>';
}

function initSettingsTab() {
    const settings = Storage.getSettings() || MockData.teamConfig.settings;
    const teamConfig = MockData.teamConfig;
    
    Forms.setFormData('settingsForm', {
        teamName: teamConfig.teamName,
        coachName: teamConfig.coachName,
        weekStartDay: settings.weekStartDay || 'monday',
        autoAdvanceWeek: settings.autoAdvanceWeek || false,
        scoringMethod: settings.scoringMethod || 'simple'
    });
    
    document.getElementById('settingsForm')?.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = Forms.getFormData('settingsForm');
        MockData.teamConfig.teamName = formData.teamName;
        MockData.teamConfig.coachName = formData.coachName;
        Storage.saveSettings({
            weekStartDay: formData.weekStartDay,
            autoAdvanceWeek: formData.autoAdvanceWeek,
            scoringMethod: formData.scoringMethod
        });
        alert('Settings saved!');
    });
}

// ===== Utility Functions =====
function formatDate(date) {
    if (!date) return '';
    const d = new Date(date);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[d.getMonth()]} ${d.getDate()}`;
}

// Make functions available globally for onclick handlers
window.editPlayer = editPlayer;
window.copyPlayerLink = copyPlayerLink;
window.editActivity = editActivity;
window.toggleActivityStatus = toggleActivityStatus;
window.editContent = editContent;
window.toggleContentPublish = toggleContentPublish;
window.deleteContent = deleteContent;

