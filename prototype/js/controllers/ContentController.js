// Content Controller - coordinates ContentView with ContentModel

class ContentController extends BaseController {
    constructor() {
        super();
        this.contentModel = new ContentModel();
        this.view = new ContentView();
        this.workoutModel = new WorkoutModel();
    }

    // Initialize content
    async init() {
        // Load all content
        await Promise.all([
            this.contentModel.loadNutritionTips(),
            this.contentModel.loadMentalPerformance(),
            this.contentModel.loadTrainingGuidance(),
            this.contentModel.loadNavigation(),
            this.contentModel.loadWorkoutPlan()
        ]);

        // Determine what to render based on page type
        const params = Router.getQueryParams();
        const category = params.category;
        const id = params.id;
        const slug = params.slug;

        if (category && id) {
            // Individual content page by category and id
            this.renderContentPageById(category, id);
        } else if (category) {
            // Content list page
            this.renderContentList(category);
        } else if (slug) {
            // Individual content page by slug
            if (slug === 'weekly-workout-plan') {
                await this.renderWorkoutPlan();
            } else {
                this.renderContentPage(slug);
            }
        }
    }

    // Render content list
    renderContentList(category) {
        const content = this.contentModel.getContentByCategory(category);
        this.view.renderContentList(content, category);
    }

    // Render individual content page by slug
    renderContentPage(slug) {
        const content = this.contentModel.getContentBySlug(slug);
        if (content) {
            this.view.renderContentPage(content);
        }
    }

    // Render individual content page by category and id
    renderContentPageById(category, id) {
        const content = this.contentModel.getContentById(category, id);
        if (content) {
            this.view.renderContentPage(content);
        }
    }

    // Render workout plan
    async renderWorkoutPlan() {
        // Set page title
        const titleEl = document.getElementById('contentTitle');
        if (titleEl) {
            titleEl.textContent = 'Weekly Workout Plan';
        }

        // Show print button
        const printButton = document.getElementById('printButton');
        if (printButton) {
            printButton.style.display = 'block';
            printButton.addEventListener('click', () => {
                window.print();
            });
        }

        const workoutPlan = this.contentModel.getWorkoutPlan();
        const workoutId = 'workout-001'; // Default workout ID
        const workoutProgress = this.workoutModel.getWorkoutProgress(workoutId);

        this.view.renderWorkoutTable(
            workoutPlan,
            workoutProgress,
            (activity, set, reps) => {
                this.workoutModel.saveWorkoutProgress(workoutId, activity, set, reps);
            }
        );
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ContentController = ContentController;
}

