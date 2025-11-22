// Main Application - initializes controllers based on route

class App {
    constructor() {
        this.currentController = null;
        this.contentModel = null;
    }

    // Initialize application
    async init() {
        // Initialize state manager
        if (window.StateManager) {
            window.StateManager.init();
        }

        // Load content model for navigation
        this.contentModel = new ContentModel();
        await this.contentModel.loadNavigation();

        // Render navigation
        this.renderNavigation();

        // Set player name in header
        this.setPlayerNameInHeader();

        // Setup navigation menu toggle
        this.setupNavigationMenu();

        // Initialize controller based on current page
        await this.initController();
    }

    // Initialize controller for current page
    async initController() {
        const currentPage = Router.getCurrentPage();

        // Cleanup previous controller
        if (this.currentController && this.currentController.destroy) {
            this.currentController.destroy();
        }

        // Initialize appropriate controller
        switch (currentPage) {
            case 'player-view':
                this.currentController = new PlayerController();
                await this.currentController.init();
                break;
            case 'my-progress':
            case 'index':
                this.currentController = new ProgressController();
                await this.currentController.init();
                break;
            case 'leaderboard':
                this.currentController = new LeaderboardController();
                this.currentController.init();
                break;
            case 'reflection':
                this.currentController = new ReflectionController();
                this.currentController.init();
                break;
            case 'resource-list':
            case 'content-page':
                this.currentController = new ContentController();
                await this.currentController.init();
                break;
            case 'admin-login':
                // Admin login doesn't need a controller yet
                this.setupAdminLogin();
                break;
            case 'admin-dashboard':
                this.currentController = new AdminController();
                await this.currentController.init();
                break;
        }
    }

    // Render navigation menu
    renderNavigation() {
        if (this.contentModel) {
            const navigation = this.contentModel.getNavigation();
            const currentPage = Router.getCurrentPage();
            SharedViews.renderNavigation(navigation, currentPage);
        }
    }

    // Set player name in header
    setPlayerNameInHeader() {
        const playerModel = new PlayerModel();
        const currentPlayerId = Storage.getCurrentPlayer() || 
            playerModel.getActivePlayers()[0]?.playerId;
        
        if (currentPlayerId) {
            const player = playerModel.getPlayerById(currentPlayerId);
            if (player) {
                SharedViews.renderHeader(player.name);
            }
        }
    }

    // Setup navigation menu toggle
    setupNavigationMenu() {
        const menuToggle = document.getElementById('menuToggle');
        const navMenu = document.getElementById('navMenu');
        const navClose = document.getElementById('navClose');

        // Open menu
        menuToggle?.addEventListener('click', () => {
            navMenu?.classList.add('open');
        });

        // Close menu
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

    // Setup admin login
    setupAdminLogin() {
        const form = document.getElementById('adminLoginForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const email = document.getElementById('adminEmail').value;
                const password = document.getElementById('adminPassword').value;
                
                // Simple validation for prototype
                if (password.length >= 8) {
                    Storage.setAdminAuth({ email, loggedIn: true });
                    window.location.href = 'admin-dashboard.html';
                } else {
                    alert('Password must be at least 8 characters');
                }
            });
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    const app = new App();
    await app.init();
    
    // Make app available globally for debugging
    window.App = app;
});

