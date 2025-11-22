// Tracking Model - handles tracking data operations and score calculations

class TrackingModel extends BaseModel {
    constructor() {
        super();
    }

    // Get tracking for a specific date
    getTrackingForDate(playerId, weekId, dateStr) {
        try {
            const allTracking = this.getAllTracking();
            return allTracking.find(t => 
                t.playerId === playerId && 
                t.weekId === weekId && 
                t.date === dateStr
            ) || null;
        } catch (error) {
            return this.handleError(error, 'getTrackingForDate');
        }
    }

    // Get all tracking for a week
    getAllTrackingForWeek(playerId, weekId) {
        try {
            const allTracking = this.getAllTracking();
            return allTracking.filter(t => 
                t.playerId === playerId && t.weekId === weekId
            );
        } catch (error) {
            return this.handleError(error, 'getAllTrackingForWeek');
        }
    }

    // Get all tracking (merged from mock data and storage)
    getAllTracking() {
        try {
            if (!this.mockData || !this.mockData.tracking) {
                return [];
            }
            return this.storage ? this.storage.mergeTracking(this.mockData.tracking) : this.mockData.tracking;
        } catch (error) {
            return this.handleError(error, 'getAllTracking');
        }
    }

    // Toggle activity completion
    toggleActivity(trackingId, playerId, weekId, activityId, dateStr) {
        try {
            let tracking = this.getTrackingForDate(playerId, weekId, dateStr);
            
            if (!tracking) {
                // Create new tracking entry
                tracking = {
                    trackingId: trackingId,
                    playerId: playerId,
                    weekId: weekId,
                    date: dateStr,
                    completedActivities: [],
                    dailyScore: 0,
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString()
                };
            }
            
            // Toggle activity
            const index = tracking.completedActivities.indexOf(activityId);
            if (index > -1) {
                tracking.completedActivities.splice(index, 1);
            } else {
                tracking.completedActivities.push(activityId);
            }
            
            // Recalculate daily score
            tracking.dailyScore = tracking.completedActivities.length;
            tracking.updatedAt = new Date().toISOString();
            
            // Save to storage
            if (this.storage) {
                this.storage.saveTracking(trackingId, tracking);
            }
            
            return tracking;
        } catch (error) {
            return this.handleError(error, 'toggleActivity');
        }
    }

    // Calculate daily score
    calculateDailyScore(completedActivities) {
        return completedActivities ? completedActivities.length : 0;
    }

    // Calculate weekly total score
    calculateWeeklyScore(playerId, weekId) {
        try {
            const weekTracking = this.getAllTrackingForWeek(playerId, weekId);
            return weekTracking.reduce((sum, t) => sum + t.dailyScore, 0);
        } catch (error) {
            return this.handleError(error, 'calculateWeeklyScore');
        }
    }

    // Calculate max possible score for a week
    calculateMaxWeeklyScore() {
        try {
            if (!this.mockData || !this.mockData.activities) {
                return 0;
            }
            const activeActivities = this.mockData.activities.filter(a => a.isActive);
            return activeActivities.length * 7; // 7 days
        } catch (error) {
            return this.handleError(error, 'calculateMaxWeeklyScore');
        }
    }

    // Get completion count for an activity in a week
    getActivityCompletionCount(playerId, weekId, activityId) {
        try {
            const weekTracking = this.getAllTrackingForWeek(playerId, weekId);
            return weekTracking.filter(t => 
                t.completedActivities.includes(activityId)
            ).length;
        } catch (error) {
            return this.handleError(error, 'getActivityCompletionCount');
        }
    }

    // Check if activity should show warning (for frequency-based activities)
    shouldShowWarning(playerId, weekId, activityId, dayIndex, frequency) {
        try {
            if (frequency !== '3x/week') {
                return false;
            }
            
            const completionCount = this.getActivityCompletionCount(playerId, weekId, activityId);
            // Show warning if it's Friday or later (dayIndex >= 5) and not enough completions
            return completionCount < 3 && dayIndex >= 5;
        } catch (error) {
            return false;
        }
    }

    // Get week dates utility (delegates to MockData)
    getWeekDates(weekId) {
        try {
            if (this.mockData && this.mockData.getWeekDates) {
                return this.mockData.getWeekDates(weekId);
            }
            return null;
        } catch (error) {
            return this.handleError(error, 'getWeekDates');
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.TrackingModel = TrackingModel;
}

