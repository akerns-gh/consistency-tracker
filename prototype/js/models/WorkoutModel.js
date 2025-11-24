// Workout Model - handles workout plan data operations

class WorkoutModel extends BaseModel {
    constructor() {
        super();
    }

    // Get workout plan (delegates to ContentModel)
    getWorkoutPlan() {
        try {
            // Try to get from ContentModel if available
            if (window.ContentModel) {
                const contentModel = new ContentModel();
                return contentModel.getWorkoutPlan();
            }
            // Fallback: try to access global contentModel instance
            if (window.contentModel) {
                return window.contentModel.getWorkoutPlan();
            }
            return null;
        } catch (error) {
            return this.handleError(error, 'getWorkoutPlan');
        }
    }

    // Save workout progress
    saveWorkoutProgress(workoutId, activity, day, reps, dateStr = null) {
        try {
            if (!this.storage) {
                return false;
            }
            return this.storage.saveWorkoutProgress(workoutId, activity, day, reps, dateStr);
        } catch (error) {
            return this.handleError(error, 'saveWorkoutProgress');
        }
    }

    // Get workout progress
    getWorkoutProgress(workoutId, dateStr = null) {
        try {
            if (!this.storage) {
                return {};
            }
            return this.storage.getWorkoutProgress(workoutId, dateStr);
        } catch (error) {
            return this.handleError(error, 'getWorkoutProgress');
        }
    }

    // Get workout progress for a specific date
    getWorkoutProgressForDate(workoutId, dateStr) {
        try {
            return this.getWorkoutProgress(workoutId, dateStr);
        } catch (error) {
            return this.handleError(error, 'getWorkoutProgressForDate');
        }
    }

    // Parse required sets from duration string
    parseRequiredSets(durationString) {
        try {
            if (!durationString || typeof durationString !== 'string') {
                return null;
            }

            // Look for pattern like "x 2 sets" or "x 3 sets"
            const setsMatch = durationString.match(/x\s*(\d+)\s*sets?/i);
            if (setsMatch && setsMatch[1]) {
                return parseInt(setsMatch[1], 10);
            }

            // Look for pattern like "2 sets" (without x)
            const setsMatch2 = durationString.match(/(\d+)\s*sets?/i);
            if (setsMatch2 && setsMatch2[1]) {
                return parseInt(setsMatch2[1], 10);
            }

            // No sets mentioned - time-based activity
            return null;
        } catch (error) {
            return null;
        }
    }

    // Check if workout is complete for a specific date
    isWorkoutCompleteForDate(workoutId, dateStr, workoutPlan = null) {
        try {
            // Get workout plan structure (use provided or try to get it)
            if (!workoutPlan) {
                workoutPlan = this.getWorkoutPlan();
            }
            if (!workoutPlan) {
                return false;
            }

            // Get progress for this date
            const progress = this.getWorkoutProgressForDate(workoutId, dateStr);
            if (!progress || Object.keys(progress).length === 0) {
                return false;
            }

            // Find the workout in the plan
            const workout = workoutPlan[workoutId];
            if (!workout || !workout.sections) {
                return false;
            }

            // Check if at least one activity has completed its required sets
            let hasCompletedActivity = false;

            workout.sections.forEach(section => {
                if (!section.activities) return;

                section.activities.forEach(activity => {
                    const activityId = activity.activityId;
                    const duration = activity.duration || '';
                    const requiredSets = this.parseRequiredSets(duration);

                    // Get progress for this activity
                    const activityProgress = progress[activityId];
                    if (!activityProgress) {
                        return;
                    }

                    // Count how many sets have reps > 0
                    const completedSets = Object.values(activityProgress).filter(
                        reps => reps !== null && reps !== undefined && reps > 0
                    ).length;

                    // Check completion
                    if (requiredSets === null) {
                        // Time-based: any rep entry counts
                        if (completedSets > 0) {
                            hasCompletedActivity = true;
                        }
                    } else {
                        // Set-based: need all required sets
                        if (completedSets >= requiredSets) {
                            hasCompletedActivity = true;
                        }
                    }
                });
            });

            return hasCompletedActivity;
        } catch (error) {
            return this.handleError(error, 'isWorkoutCompleteForDate');
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.WorkoutModel = WorkoutModel;
}

