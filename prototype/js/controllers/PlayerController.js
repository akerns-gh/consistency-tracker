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

        // Render view
        await this.render();

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
    }

    // Handle activity toggle
    handleActivityToggle(activityId, dateStr) {
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

    // Handle week navigation
    handleWeekNavigation(direction) {
        // Save reflection before navigating
        this.saveReflection();

        // Calculate new week
        const weekDates = this.trackingModel.getWeekDates(this.currentWeekId);
        if (weekDates) {
            const newDate = new Date(weekDates.monday);
            newDate.setDate(newDate.getDate() + (direction * 7));
            const newWeekId = window.MockData && window.MockData.getWeekId ? 
                window.MockData.getWeekId(newDate) : null;
            
            if (newWeekId) {
                this.currentWeekId = newWeekId;
                Storage.setCurrentWeek(newWeekId);
                this.render();
            }
        }
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
        // Week navigation
        const prevWeekBtn = document.getElementById('prevWeek');
        const nextWeekBtn = document.getElementById('nextWeek');

        if (prevWeekBtn) {
            this.addEventListener(prevWeekBtn, 'click', () => {
                this.handleWeekNavigation(-1);
            });
        }

        if (nextWeekBtn) {
            this.addEventListener(nextWeekBtn, 'click', () => {
                this.handleWeekNavigation(1);
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

