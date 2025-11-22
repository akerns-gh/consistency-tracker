// Leaderboard Controller - coordinates LeaderboardView with LeaderboardModel

class LeaderboardController extends BaseController {
    constructor() {
        super();
        this.leaderboardModel = new LeaderboardModel();
        this.view = new LeaderboardView();
        this.currentWeekId = null;
    }

    // Initialize leaderboard
    init() {
        this.currentWeekId = Storage.getCurrentWeek() || 
            (window.MockData ? window.MockData.currentWeekId : null);

        this.render();

        this.setupEventListeners();
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

