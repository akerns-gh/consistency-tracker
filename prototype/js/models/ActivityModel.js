// Activity Model - handles activity data operations

class ActivityModel extends BaseModel {
    constructor() {
        super();
        this.activityRequirements = {};
        this._bodyweightActivityIdCache = null;
    }

    // Load activity requirements from JSON
    async loadActivityRequirements() {
        try {
            const response = await fetch('data/activity-requirements.json');
            if (!response.ok) {
                throw new Error(`Failed to load activity requirements: ${response.status}`);
            }
            this.activityRequirements = await response.json();
            return this.activityRequirements;
        } catch (error) {
            console.warn('Could not load activity requirements, using defaults:', error);
            this.activityRequirements = {};
            return {};
        }
    }

    // Get all activities
    getAllActivities() {
        try {
            if (!this.mockData || !this.mockData.activities) {
                return [];
            }
            return this.mockData.activities;
        } catch (error) {
            return this.handleError(error, 'getAllActivities');
        }
    }

    // Get active activities
    getActiveActivities() {
        try {
            const activities = this.getAllActivities();
            return activities.filter(a => a.isActive)
                .sort((a, b) => a.displayOrder - b.displayOrder);
        } catch (error) {
            return this.handleError(error, 'getActiveActivities');
        }
    }

    // Get activity by ID
    getActivityById(activityId) {
        try {
            const activities = this.getAllActivities();
            return activities.find(a => a.activityId === activityId) || null;
        } catch (error) {
            return this.handleError(error, 'getActivityById');
        }
    }

    // Get activity requirements
    getActivityRequirements() {
        return this.activityRequirements;
    }

    // Get requirement for specific activity
    getActivityRequirement(activityId) {
        return this.activityRequirements[activityId] || null;
    }

    // Get display name for activity (from requirements or activity data)
    getActivityDisplayName(activityId) {
        const requirement = this.getActivityRequirement(activityId);
        const activity = this.getActivityById(activityId);
        
        if (requirement && requirement.name) {
            return requirement.name;
        }
        return activity ? activity.name : activityId;
    }

    // Get goal for activity
    getActivityGoal(activityId) {
        const requirement = this.getActivityRequirement(activityId);
        const activity = this.getActivityById(activityId);
        
        if (requirement && requirement.goal) {
            return requirement.goal;
        }
        return activity ? activity.goal : null;
    }

    // Get activity type (flyout or link)
    getActivityType(activityId) {
        const requirement = this.getActivityRequirement(activityId);
        return requirement ? (requirement.type || 'link') : 'link';
    }

    // Get activity slug for navigation
    getActivitySlug(activityId) {
        const requirement = this.getActivityRequirement(activityId);
        return requirement ? (requirement.slug || '') : '';
    }

    // Get flyout content
    getFlyoutContent(activityId) {
        const requirement = this.getActivityRequirement(activityId);
        return requirement ? (requirement.flyoutContent || '') : '';
    }

    // Get required days for activity
    getRequiredDays(activityId) {
        const requirement = this.getActivityRequirement(activityId);
        if (requirement && requirement.requiredDays) {
            return requirement.requiredDays;
        }
        // Default: all days required
        return [0, 1, 2, 3, 4, 5, 6];
    }

    // Get activity ID by name (for resilience to ID changes)
    getActivityIdByName(activityName) {
        try {
            // Check cache first
            if (this._bodyweightActivityIdCache && activityName === 'Bodyweight Training') {
                return this._bodyweightActivityIdCache;
            }

            // Search activity requirements by name
            for (const [activityId, requirement] of Object.entries(this.activityRequirements)) {
                if (requirement.name === activityName) {
                    // Cache if it's Bodyweight Training
                    if (activityName === 'Bodyweight Training') {
                        this._bodyweightActivityIdCache = activityId;
                    }
                    return activityId;
                }
            }

            // Fallback: search in mock data activities
            if (this.mockData && this.mockData.activities) {
                const activity = this.mockData.activities.find(a => a.name === activityName);
                if (activity) {
                    if (activityName === 'Bodyweight Training') {
                        this._bodyweightActivityIdCache = activity.activityId;
                    }
                    return activity.activityId;
                }
            }

            return null;
        } catch (error) {
            return this.handleError(error, 'getActivityIdByName');
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ActivityModel = ActivityModel;
}

