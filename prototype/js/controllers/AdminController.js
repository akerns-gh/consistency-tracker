// Admin Controller - coordinates AdminView with all models

class AdminController extends BaseController {
    constructor() {
        super();
        this.playerModel = new PlayerModel();
        this.activityModel = new ActivityModel();
        this.contentModel = new ContentModel();
        this.view = new AdminView();
    }

    // Initialize admin dashboard
    async init() {
        await this.activityModel.loadActivityRequirements();
        await Promise.all([
            this.contentModel.loadNutritionTips(),
            this.contentModel.loadMentalPerformance(),
            this.contentModel.loadResources(),
            this.contentModel.loadTrainingGuidance()
        ]);

        this.render();
        this.setupEventListeners();
    }

    // Render admin dashboard
    render() {
        // Render players
        const players = this.playerModel.getAllPlayers();
        this.view.renderPlayerManagement(players);

        // Render activities
        const activities = this.activityModel.getAllActivities();
        this.view.renderActivityManagement(activities);

        // Render content (example for one category)
        const nutrition = this.contentModel.getContentByCategory('nutrition');
        this.view.renderContentManagement(nutrition, 'nutrition');
    }

    // Handle player actions
    handlePlayerAction(action, playerId) {
        if (action === 'edit') {
            // Open edit modal
        } else if (action === 'delete') {
            this.playerModel.deletePlayer(playerId);
            this.render();
        }
    }

    // Setup event listeners
    setupEventListeners() {
        // Delegate player actions
        const playersList = document.getElementById('playersList');
        if (playersList) {
            this.delegateEvent(playersList, 'button[data-action]', 'click', (e) => {
                const action = e.target.dataset.action;
                const id = e.target.dataset.id;
                this.handlePlayerAction(action, id);
            });
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.AdminController = AdminController;
}

