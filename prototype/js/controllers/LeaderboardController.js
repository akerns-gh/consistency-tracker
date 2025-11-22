// Leaderboard Controller - coordinates LeaderboardView with LeaderboardModel

class LeaderboardController extends BaseController {
    constructor() {
        super();
        this.leaderboardModel = new LeaderboardModel();
        this.trackingModel = new TrackingModel();
        this.view = new LeaderboardView();
        this.currentWeekId = null;
    }

    // Initialize leaderboard
    init() {
        this.currentWeekId = Storage.getCurrentWeek() || 
            (window.MockData ? window.MockData.currentWeekId : null);

        this.populateWeekSelector();
        this.render();

        this.setupEventListeners();
    }

    // Populate week selector dropdown
    populateWeekSelector() {
        const weekSelector = document.getElementById('weekSelector');
        if (!weekSelector) return;

        // Get available weeks from tracking data
        const allTracking = this.trackingModel.getAllTracking();
        
        // Get unique weeks and sort them (newest first)
        let weeks = [...new Set(allTracking.map(t => t.weekId))].sort().reverse();

        // If no weeks from tracking, generate weeks from mock data
        if (weeks.length === 0 && window.MockData && window.MockData.getWeekId) {
            const currentWeekId = window.MockData.currentWeekId;
            if (currentWeekId) {
                weeks.push(currentWeekId);
                // Add previous weeks
                for (let i = 1; i <= 3; i++) {
                    const prevDate = new Date();
                    prevDate.setDate(prevDate.getDate() - (i * 7));
                    const prevWeekId = window.MockData.getWeekId(prevDate);
                    if (prevWeekId && !weeks.includes(prevWeekId)) {
                        weeks.push(prevWeekId);
                    }
                }
            }
        }

        // Clear existing options
        weekSelector.innerHTML = '';

        // Add options
        weeks.forEach(weekId => {
            const option = document.createElement('option');
            option.value = weekId;
            
            // Format week label
            const weekDates = this.trackingModel.getWeekDates(weekId);
            
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

    // Render leaderboard
    render() {
        const currentPlayerId = Storage.getCurrentPlayer();
        const rankings = this.leaderboardModel.calculateRankings(this.currentWeekId);
        const stats = this.leaderboardModel.getTeamStats(this.currentWeekId);

        // Render podium
        this.view.renderPodium(
            this.leaderboardModel.getTopPlayers(this.currentWeekId, 3),
            currentPlayerId
        );

        // Render rankings
        this.view.renderRankings(rankings, currentPlayerId);

        // Render stats
        this.view.renderStats({
            averageScore: stats.averageScore,
            mostImproved: rankings[0] ? rankings[0].player.name : '-',
            perfectWeeks: stats.perfectWeeks
        });
    }

    // Handle week selector change
    handleWeekChange(weekId) {
        this.currentWeekId = weekId;
        this.render();
    }

    // Setup event listeners
    setupEventListeners() {
        const weekSelector = document.getElementById('weekSelector');
        if (weekSelector) {
            this.addEventListener(weekSelector, 'change', (e) => {
                this.handleWeekChange(e.target.value);
            });
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.LeaderboardController = LeaderboardController;
}

