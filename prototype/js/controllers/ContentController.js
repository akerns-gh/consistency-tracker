// Content Controller - coordinates ContentView with ContentModel

class ContentController extends BaseController {
    constructor() {
        super();
        this.contentModel = new ContentModel();
        this.view = new ContentView();
        this.workoutModel = new WorkoutModel();
        this.trackingModel = new TrackingModel();
        this.activityModel = new ActivityModel();
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
        // Load activity requirements for bodyweight lookup
        await this.activityModel.loadActivityRequirements();

        // Hide content body container
        const contentBody = document.getElementById('contentBody');
        if (contentBody) {
            contentBody.style.display = 'none';
        }

        // Set page title
        const titleEl = document.getElementById('contentTitle');
        if (titleEl) {
            titleEl.textContent = 'Weekly Workout Plan';
        }

        // Show CSV download button
        const csvButton = document.getElementById('csvButton');
        if (csvButton) {
            csvButton.style.display = 'block';
            csvButton.addEventListener('click', () => {
                this.exportWorkoutPlanToCSV();
            });
        }

        const workoutPlan = this.contentModel.getWorkoutPlan();
        const workoutId = 'workout-001'; // Default workout ID
        const currentDate = new Date().toISOString().split('T')[0];
        const workoutProgress = this.workoutModel.getWorkoutProgress(workoutId, currentDate);

        this.view.renderWorkoutTable(
            workoutPlan,
            workoutProgress,
            (activity, set, reps) => {
                // Save workout progress with current date
                this.workoutModel.saveWorkoutProgress(workoutId, activity, set, reps, currentDate);
                
                // Check if workout is complete and auto-check bodyweight
                this.checkAndUpdateBodyweightTracking(workoutId, currentDate);
            }
        );
    }

    // Export workout plan to CSV
    exportWorkoutPlanToCSV() {
        try {
            const workoutPlan = this.contentModel.getWorkoutPlan();
            if (!workoutPlan) {
                console.error('No workout plan available');
                return;
            }

            // Helper function to escape CSV values
            const escapeCSV = (value) => {
                if (value === null || value === undefined) {
                    return '';
                }
                const stringValue = String(value);
                // If value contains comma, quote, or newline, wrap in quotes and escape quotes
                if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
                    return `"${stringValue.replace(/"/g, '""')}"`;
                }
                return stringValue;
            };

            // Helper function to create CSV row
            const createCSVRow = (values) => {
                return values.map(escapeCSV).join(',');
            };

            // Build CSV rows
            const csvRows = [];
            
            // Header row
            csvRows.push(createCSVRow(['Activity', 'Duration', 'Day 1', 'Day 2', 'Day 3']));

            // Process each workout
            Object.keys(workoutPlan).forEach(workoutId => {
                const workout = workoutPlan[workoutId];
                if (workout.sections) {
                    workout.sections.forEach(section => {
                        // Add section header row
                        const sectionName = section.name || '';
                        const sectionDesc = section.description || '';
                        const sectionHeader = sectionDesc 
                            ? `${sectionName} - ${sectionDesc}` 
                            : sectionName;
                        csvRows.push(createCSVRow([sectionHeader, '', '', '', '']));

                        // Add activities
                        if (section.activities) {
                            section.activities.forEach(activity => {
                                const activityName = activity.name || '';
                                const duration = activity.duration || '';
                                // Empty cells for Day 1, Day 2, Day 3
                                csvRows.push(createCSVRow([activityName, duration, '', '', '']));
                            });
                        }
                    });
                }
            });

            // Convert to CSV string
            const csvContent = csvRows.join('\n');

            // Create download
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            
            link.setAttribute('href', url);
            link.setAttribute('download', `workout-plan-${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Error exporting workout plan to CSV:', error);
            alert('Error exporting workout plan. Please try again.');
        }
    }

    // Check workout completion and update bodyweight tracking
    checkAndUpdateBodyweightTracking(workoutId, dateStr) {
        try {
            // Get workout plan to pass to completion check
            const workoutPlan = this.contentModel.getWorkoutPlan();
            
            // Check if workout is complete
            const isComplete = this.workoutModel.isWorkoutCompleteForDate(workoutId, dateStr, workoutPlan);
            
            if (isComplete) {
                // Get bodyweight activity ID dynamically
                const bodyweightActivityId = this.activityModel.getActivityIdByName('Bodyweight Training');
                
                if (bodyweightActivityId) {
                    // Get current player and week
                    const playerId = Storage.getCurrentPlayer();
                    const weekId = Storage.getCurrentWeek();
                    
                    if (playerId && weekId) {
                        // Add bodyweight activity automatically
                        this.trackingModel.addActivityAuto(playerId, weekId, bodyweightActivityId, dateStr);
                        
                        // Emit event for view updates
                        if (window.EventBus) {
                            window.EventBus.emit('workout:completed', {
                                playerId: playerId,
                                weekId: weekId,
                                dateStr: dateStr,
                                activityId: bodyweightActivityId
                            });
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error checking workout completion:', error);
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ContentController = ContentController;
}

