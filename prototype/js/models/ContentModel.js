// Content Model - handles content data operations (nutrition, mental performance, training guidance, etc.)

class ContentModel extends BaseModel {
    constructor() {
        super();
        this.nutritionTips = [];
        this.mentalPerformance = [];
        this.trainingGuidance = [];
        this.navigation = [];
        this.workoutPlan = null;
    }

    // Load nutrition tips
    async loadNutritionTips() {
        try {
            const response = await fetch('data/nutrition-tips.json');
            if (!response.ok) {
                throw new Error(`Failed to load nutrition tips: ${response.status}`);
            }
            this.nutritionTips = await response.json();
            return this.nutritionTips;
        } catch (error) {
            console.warn('Could not load nutrition tips:', error);
            this.nutritionTips = [];
            return [];
        }
    }

    // Load mental performance
    async loadMentalPerformance() {
        try {
            const response = await fetch('data/mental-performance.json');
            if (!response.ok) {
                throw new Error(`Failed to load mental performance: ${response.status}`);
            }
            this.mentalPerformance = await response.json();
            return this.mentalPerformance;
        } catch (error) {
            console.warn('Could not load mental performance:', error);
            this.mentalPerformance = [];
            return [];
        }
    }

    // Load training guidance
    async loadTrainingGuidance() {
        try {
            const response = await fetch('data/training-guidance.json');
            if (!response.ok) {
                throw new Error(`Failed to load training guidance: ${response.status}`);
            }
            this.trainingGuidance = await response.json();
            return this.trainingGuidance;
        } catch (error) {
            console.warn('Could not load training guidance:', error);
            this.trainingGuidance = [];
            return [];
        }
    }

    // Load navigation
    async loadNavigation() {
        try {
            const response = await fetch('data/navigation.json');
            if (!response.ok) {
                throw new Error(`Failed to load navigation: ${response.status}`);
            }
            this.navigation = await response.json();
            return this.navigation;
        } catch (error) {
            console.warn('Could not load navigation:', error);
            this.navigation = [];
            return [];
        }
    }

    // Load workout plan
    async loadWorkoutPlan() {
        try {
            const response = await fetch('data/workout-plan.json');
            if (!response.ok) {
                throw new Error(`Failed to load workout plan: ${response.status}`);
            }
            this.workoutPlan = await response.json();
            return this.workoutPlan;
        } catch (error) {
            console.warn('Could not load workout plan:', error);
            this.workoutPlan = null;
            return null;
        }
    }

    // Get content by category
    getContentByCategory(category) {
        switch (category) {
            case 'nutrition':
                return this.nutritionTips;
            case 'mental-health':
                return this.mentalPerformance;
            case 'guidance':
                return this.trainingGuidance;
            default:
                return [];
        }
    }

    // Get content by ID and category
    getContentById(category, id) {
        const content = this.getContentByCategory(category);
        return content.find(item => item.id === id) || null;
    }

    // Get content by slug
    getContentBySlug(slug) {
        // Check all categories
        const categories = [
            { name: 'guidance', data: this.trainingGuidance },
            { name: 'nutrition', data: this.nutritionTips },
            { name: 'mental-health', data: this.mentalPerformance }
        ];

        for (const category of categories) {
            const item = category.data.find(c => c.slug === slug);
            if (item) {
                return { ...item, category: category.name };
            }
        }

        return null;
    }

    // Get navigation items
    getNavigation() {
        return this.navigation.filter(item => item.display !== false);
    }

    // Get workout plan
    getWorkoutPlan() {
        if (!this.workoutPlan) return null;
        
        // Transform the JSON structure to match what the view expects
        // JSON has: { workoutId, title, sections: [{ sectionName, sectionNote, activities }] }
        // View expects: { [workoutId]: { sections: [{ name, description, activities }] } }
        if (this.workoutPlan.workoutId) {
            const transformed = {
                [this.workoutPlan.workoutId]: {
                    sections: this.workoutPlan.sections.map(section => ({
                        name: section.sectionName || section.name,
                        description: section.sectionNote || section.description || '',
                        activities: section.activities || []
                    }))
                }
            };
            return transformed;
        }
        
        // If already in the expected format, return as-is
        return this.workoutPlan;
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ContentModel = ContentModel;
}

