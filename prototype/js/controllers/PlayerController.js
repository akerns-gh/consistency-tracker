// Player Controller - coordinates PlayerView with TrackingModel and ActivityModel

class PlayerController extends BaseController {
    constructor() {
        super();
        this.playerModel = new PlayerModel();
        this.trackingModel = new TrackingModel();
        this.activityModel = new ActivityModel();
        this.view = new PlayerView();
        this.currentPlayerId = null;
        this.currentWeekId = null;
    }

    // Initialize player view
    async init() {
        // Load activity requirements
        await this.activityModel.loadActivityRequirements();

        // Set current player
        this.currentPlayerId = Storage.getCurrentPlayer() || 
            (this.playerModel.getActivePlayers()[0]?.playerId || this.playerModel.getAllPlayers()[0]?.playerId);
        Storage.setCurrentPlayer(this.currentPlayerId);

        // Set current week
        this.currentWeekId = Storage.getCurrentWeek() || 
            (window.MockData ? window.MockData.currentWeekId : null);
        Storage.setCurrentWeek(this.currentWeekId);

        // Get player data
        const player = this.playerModel.getPlayerById(this.currentPlayerId);
        if (player) {
            this.view.renderPlayerName(player.name);
        }

        // Render view first to ensure DOM is ready
        await this.render();

        // Populate week selector after render
        this.populateWeekSelector();

        // Setup event listeners
        this.setupEventListeners();
    }

    // Render the player view
    async render() {
        const activities = this.activityModel.getActiveActivities();
        const weekDates = this.trackingModel.getWeekDates(this.currentWeekId);
        const trackingData = this.trackingModel.getAllTrackingForWeek(this.currentPlayerId, this.currentWeekId);

        // Render week info
        if (weekDates) {
            this.view.renderWeekInfo(weekDates);
        }

        // Render activity grid
        this.view.renderActivityGrid(
            activities,
            weekDates,
            trackingData,
            this.activityModel,
            (activityId, dateStr) => this.handleActivityToggle(activityId, dateStr),
            (type, data, activityId) => this.handleActivityClick(type, data, activityId)
        );

        // Update scores
        this.updateScores();

        // Populate week selector
        this.populateWeekSelector();
    }

    // Handle activity toggle
    handleActivityToggle(activityId, dateStr) {
        // Check if this is the bodyweight activity (auto-tracked)
        const bodyweightActivityId = this.activityModel.getActivityIdByName('Bodyweight Training');
        
        if (bodyweightActivityId && activityId === bodyweightActivityId) {
            // Prevent manual toggle of bodyweight activity
            // Show message to user
            alert('Bodyweight Training is automatically tracked when you complete workout plans.');
            return;
        }

        const trackingId = `${this.currentPlayerId}#${this.currentWeekId}#${dateStr}`;
        const tracking = this.trackingModel.toggleActivity(
            trackingId,
            this.currentPlayerId,
            this.currentWeekId,
            activityId,
            dateStr
        );

        // Update view
        this.view.updateActivityCell(activityId, dateStr, 
            tracking.completedActivities.includes(activityId));

        // Update scores
        this.updateScores();
    }

    // Handle activity click (flyout or link)
    handleActivityClick(type, data, activityId) {
        if (type === 'flyout') {
            SharedViews.renderFlyout(data, activityId);
        } else if (type === 'link') {
            window.location.href = `content-page.html?slug=${data}`;
        }
    }

    // Update scores
    updateScores() {
        const weeklyScore = this.trackingModel.calculateWeeklyScore(this.currentPlayerId, this.currentWeekId);
        const maxScore = this.trackingModel.calculateMaxWeeklyScore();

        this.view.renderWeeklyScore(weeklyScore, maxScore);

        // Update daily scores
        const weekDates = this.trackingModel.getWeekDates(this.currentWeekId);
        const trackingData = this.trackingModel.getAllTrackingForWeek(this.currentPlayerId, this.currentWeekId);
        const activities = this.activityModel.getActiveActivities();

        if (weekDates) {
            const days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
            const scoreCells = document.querySelectorAll('.daily-score-cell');
            days.forEach((day, dayIndex) => {
                const date = new Date(weekDates.monday);
                date.setDate(date.getDate() + dayIndex);
                const dateStr = date.toISOString().split('T')[0];
                const tracking = trackingData.find(t => t.date === dateStr);
                const score = tracking ? tracking.dailyScore : 0;

                if (scoreCells[dayIndex]) {
                    scoreCells[dayIndex].textContent = `${score}/${activities.length}`;
                }
            });
        }
    }

    // Handle week change from dropdown
    handleWeekChange(weekId) {
        // Save reflection before navigating
        this.saveReflection();

        if (weekId && weekId !== this.currentWeekId) {
            this.currentWeekId = weekId;
            Storage.setCurrentWeek(weekId);
            this.render();
        }
    }

    // Populate week selector dropdown
    populateWeekSelector() {
        const weekSelector = document.getElementById('weekSelector');
        if (!weekSelector) {
            console.warn('Week selector not found');
            return;
        }

        // Get available weeks from tracking data for current player
        const allTracking = this.trackingModel.getAllTracking();
        const playerTracking = allTracking.filter(t => t.playerId === this.currentPlayerId);
        
        // Get unique weeks and sort them (newest first)
        let weeks = [...new Set(playerTracking.map(t => t.weekId))].sort().reverse();

        // Always generate weeks from mock data as fallback/backup
        if (window.MockData && window.MockData.getWeekId) {
            const currentWeekId = window.MockData.currentWeekId || this.currentWeekId;
            if (currentWeekId && !weeks.includes(currentWeekId)) {
                weeks.unshift(currentWeekId); // Add current week at the beginning
            }
            
            // Always add previous weeks to ensure we have options
            for (let i = 1; i <= 3; i++) {
                const prevDate = new Date();
                prevDate.setDate(prevDate.getDate() - (i * 7));
                const prevWeekId = window.MockData.getWeekId(prevDate);
                if (prevWeekId && !weeks.includes(prevWeekId)) {
                    weeks.push(prevWeekId);
                }
            }
        }

        // Sort weeks (newest first) and remove duplicates
        weeks = [...new Set(weeks)].sort().reverse();
        
        // Ensure we have at least the current week
        if (weeks.length === 0 && this.currentWeekId) {
            weeks.push(this.currentWeekId);
        }

        // Clear existing options
        weekSelector.innerHTML = '';

        // Add options
        weeks.forEach(weekId => {
            const option = document.createElement('option');
            option.value = weekId;
            
            // Format week label
            let weekDates = this.trackingModel.getWeekDates(weekId);
            
            // Fallback to window.MockData if trackingModel doesn't have it
            if (!weekDates && window.MockData && window.MockData.getWeekDates) {
                weekDates = window.MockData.getWeekDates(weekId);
            }
            
            if (weekDates) {
                const monday = new Date(weekDates.monday);
                const sunday = new Date(weekDates.sunday);
                const formatDate = (date) => {
                    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                };
                option.textContent = `${formatDate(monday)} - ${formatDate(sunday)}`;
            } else {
                option.textContent = weekId;
            }
            
            option.selected = weekId === this.currentWeekId;
            weekSelector.appendChild(option);
        });
    }

    // Save reflection
    saveReflection() {
        const reflectionModel = new ReflectionModel();
        const formData = {
            wentWell: document.getElementById('trackerWentWell')?.value || '',
            doBetter: document.getElementById('trackerDoBetter')?.value || '',
            planForWeek: document.getElementById('trackerPlanForWeek')?.value || ''
        };
        reflectionModel.saveWeeklyReflection(this.currentPlayerId, this.currentWeekId, formData);
    }

    // Setup event listeners
    setupEventListeners() {
        // Week selector dropdown
        const weekSelector = document.getElementById('weekSelector');
        if (weekSelector) {
            this.addEventListener(weekSelector, 'change', (e) => {
                this.handleWeekChange(e.target.value);
            });
        }

        // Reflection auto-save
        const reflectionFields = ['trackerWentWell', 'trackerDoBetter', 'trackerPlanForWeek'];
        reflectionFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                this.addEventListener(field, 'input', () => {
                    this.saveReflection();
                });
            }
        });

        // Listen for workout completion events
        if (window.EventBus) {
            window.EventBus.on('workout:completed', (data) => {
                // Refresh view if it's for current player and week
                if (data.playerId === this.currentPlayerId && data.weekId === this.currentWeekId) {
                    this.render();
                }
            });
        }

        // Flyout close handlers
        const flyoutClose = document.getElementById('flyoutClose');
        const flyoutOverlay = document.getElementById('flyoutOverlay');
        
        if (flyoutClose) {
            this.addEventListener(flyoutClose, 'click', () => {
                SharedViews.closeFlyout();
            });
        }

        if (flyoutOverlay) {
            this.addEventListener(flyoutOverlay, 'click', () => {
                SharedViews.closeFlyout();
            });
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.PlayerController = PlayerController;
}

