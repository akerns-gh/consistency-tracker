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
            this.contentModel.loadResources(),
            this.contentModel.loadTrainingGuidance(),
            this.contentModel.loadWorkouts(),
            this.contentModel.loadNavigation(),
            this.contentModel.loadWorkoutPlan()
        ]);

        // Determine what to render based on page type
        const params = Router.getQueryParams();
        const category = params.category;
        const id = params.id;
        const slug = params.slug;

        if (category) {
            // Content list page
            this.renderContentList(category);
        } else if (slug) {
            // Individual content page
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

    // Render individual content page
    renderContentPage(slug) {
        const content = this.contentModel.getContentBySlug(slug);
        if (content) {
            this.view.renderContentPage(content);
        }
    }

    // Render workout plan
    async renderWorkoutPlan() {
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

