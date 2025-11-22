// Reflection Controller - coordinates ReflectionView with ReflectionModel

class ReflectionController extends BaseController {
    constructor() {
        super();
        this.reflectionModel = new ReflectionModel();
        this.view = new ReflectionView();
        this.currentPlayerId = null;
        this.currentWeekId = null;
        this.autoSaveTimer = null;
    }

    // Initialize reflection
    init() {
        this.currentPlayerId = Storage.getCurrentPlayer() || 
            (window.PlayerModel ? new PlayerModel().getActivePlayers()[0]?.playerId : null);
        this.currentWeekId = Storage.getCurrentWeek() || 
            (window.MockData ? window.MockData.currentWeekId : null);

        // Load reflection data
        const reflection = this.reflectionModel.getWeeklyReflection(
            this.currentPlayerId,
            this.currentWeekId
        );
        this.view.renderForm(reflection);

        // Render week title
        if (window.MockData && window.MockData.getWeekDates) {
            const weekDates = window.MockData.getWeekDates(this.currentWeekId);
            if (weekDates) {
                this.view.renderWeekTitle(weekDates);
            }
        }

        this.setupEventListeners();
    }

    // Save reflection
    saveReflection() {
        const formData = this.view.getFormData();
        this.reflectionModel.saveWeeklyReflection(
            this.currentPlayerId,
            this.currentWeekId,
            formData
        );
    }

    // Handle form submission
    handleSubmit(e) {
        e.preventDefault();
        this.saveReflection();
        // Show success message or redirect
    }

    // Setup event listeners
    setupEventListeners() {
        const form = document.getElementById('reflectionForm');
        if (form) {
            this.addEventListener(form, 'submit', (e) => {
                this.handleSubmit(e);
            });
        }

        // Auto-save on input
        const fields = ['wentWell', 'doBetter', 'planForWeek'];
        fields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                this.addEventListener(field, 'input', () => {
                    // Debounce auto-save
                    clearTimeout(this.autoSaveTimer);
                    this.autoSaveTimer = setTimeout(() => {
                        this.saveReflection();
                    }, 30000); // 30 seconds
                });
            }
        });
    }

    // Cleanup
    destroy() {
        super.destroy();
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ReflectionController = ReflectionController;
}

