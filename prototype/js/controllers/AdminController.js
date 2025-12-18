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
        // Hamburger menu toggle
        const hamburgerMenu = document.getElementById('hamburgerMenu');
        const menuOverlay = document.getElementById('menuOverlay');
        const menuDrawer = document.getElementById('menuDrawer');
        const menuClose = document.getElementById('menuClose');

        const toggleMenu = () => {
            hamburgerMenu?.classList.toggle('active');
            menuOverlay?.classList.toggle('active');
            menuDrawer?.classList.toggle('active');
        };

        const closeMenu = () => {
            hamburgerMenu?.classList.remove('active');
            menuOverlay?.classList.remove('active');
            menuDrawer?.classList.remove('active');
        };

        hamburgerMenu?.addEventListener('click', toggleMenu);
        menuClose?.addEventListener('click', closeMenu);
        menuOverlay?.addEventListener('click', closeMenu);

        // Tab navigation (from tab navigation bar)
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // Tab navigation (from menu drawer)
        const menuTabs = document.querySelectorAll('.menu-tab');
        menuTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
                closeMenu();
            });
        });

        // Set initial active tab
        this.switchTab('overview'); // Default to overview tab like the app

        // Delegate player actions
        const playersList = document.getElementById('playersTableBody');
        if (playersList) {
            this.delegateEvent(playersList, 'button[data-action]', 'click', (e) => {
                const action = e.target.dataset.action;
                const id = e.target.dataset.id;
                this.handlePlayerAction(action, id);
            });
        }

        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                // Navigate to login page
                window.location.href = 'admin-login.html';
            });
        }
    }

    // Switch between tabs
    switchTab(tabName) {
        // Hide all tabs
        const allTabs = document.querySelectorAll('.tab-content');
        allTabs.forEach(tab => {
            tab.style.display = 'none';
        });

        // Remove active class from all tab navigation buttons
        const allTabButtons = document.querySelectorAll('.tab-button');
        allTabButtons.forEach(btn => {
            btn.classList.remove('active');
        });

        // Remove active class from all menu tab buttons
        const allMenuTabs = document.querySelectorAll('.menu-tab');
        allMenuTabs.forEach(btn => {
            btn.classList.remove('active');
        });

        // Show selected tab
        const selectedTab = document.getElementById(`${tabName}Tab`);
        if (selectedTab) {
            selectedTab.style.display = 'block';
        }

        // Add active class to selected tab navigation button
        const selectedTabButton = document.querySelector(`.tab-button[data-tab="${tabName}"]`);
        if (selectedTabButton) {
            selectedTabButton.classList.add('active');
        }

        // Add active class to selected menu tab button
        const selectedMenuTab = document.querySelector(`.menu-tab[data-tab="${tabName}"]`);
        if (selectedMenuTab) {
            selectedMenuTab.classList.add('active');
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.AdminController = AdminController;
}

