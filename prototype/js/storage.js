// LocalStorage wrapper for mock data persistence

const Storage = {
    // Keys
    KEYS: {
        TRACKING: 'consistency_tracker_tracking',
        REFLECTIONS: 'consistency_tracker_reflections',
        PLAYERS: 'consistency_tracker_players',
        ACTIVITIES: 'consistency_tracker_activities',
        CONTENT: 'consistency_tracker_content',
        ADMIN_AUTH: 'consistency_tracker_admin_auth',
        CURRENT_PLAYER: 'consistency_tracker_current_player',
        CURRENT_WEEK: 'consistency_tracker_current_week',
        SETTINGS: 'consistency_tracker_settings',
        WORKOUTS: 'consistency_tracker_workouts'
    },

    // Get item from localStorage
    get(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (e) {
            console.error('Error reading from localStorage:', e);
            return null;
        }
    },

    // Set item in localStorage
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Error writing to localStorage:', e);
            return false;
        }
    },

    // Remove item from localStorage
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Error removing from localStorage:', e);
            return false;
        }
    },

    // Clear all app data
    clear() {
        try {
            Object.values(this.KEYS).forEach(key => {
                localStorage.removeItem(key);
            });
            return true;
        } catch (e) {
            console.error('Error clearing localStorage:', e);
            return false;
        }
    },

    // Merge mock data with localStorage data
    mergeTracking(mockTracking) {
        const stored = this.get(this.KEYS.TRACKING) || {};
        const merged = [...mockTracking];
        
        // Override with stored data
        Object.keys(stored).forEach(key => {
            const index = merged.findIndex(t => t.trackingId === key);
            if (index !== -1) {
                merged[index] = { ...merged[index], ...stored[key] };
            } else {
                merged.push(stored[key]);
            }
        });
        
        return merged;
    },

    // Save tracking data
    saveTracking(trackingId, data) {
        const stored = this.get(this.KEYS.TRACKING) || {};
        stored[trackingId] = data;
        return this.set(this.KEYS.TRACKING, stored);
    },

    // Get tracking for player and week
    getTracking(playerId, weekId) {
        const stored = this.get(this.KEYS.TRACKING) || {};
        return Object.values(stored).filter(t => 
            t.playerId === playerId && t.weekId === weekId
        );
    },

    // Save reflection
    saveReflection(reflectionId, data) {
        const stored = this.get(this.KEYS.REFLECTIONS) || {};
        stored[reflectionId] = data;
        return this.set(this.KEYS.REFLECTIONS, stored);
    },

    // Get reflection
    getReflection(reflectionId) {
        const stored = this.get(this.KEYS.REFLECTIONS) || {};
        return stored[reflectionId] || null;
    },

    // Merge reflections with mock data
    mergeReflections(mockReflections) {
        const stored = this.get(this.KEYS.REFLECTIONS) || {};
        const merged = [...mockReflections];
        
        Object.keys(stored).forEach(key => {
            const index = merged.findIndex(r => r.reflectionId === key);
            if (index !== -1) {
                merged[index] = { ...merged[index], ...stored[key] };
            } else {
                merged.push(stored[key]);
            }
        });
        
        return merged;
    },

    // Save current player
    setCurrentPlayer(playerId) {
        return this.set(this.KEYS.CURRENT_PLAYER, playerId);
    },

    // Get current player
    getCurrentPlayer() {
        return this.get(this.KEYS.CURRENT_PLAYER);
    },

    // Save current week
    setCurrentWeek(weekId) {
        return this.set(this.KEYS.CURRENT_WEEK, weekId);
    },

    // Get current week
    getCurrentWeek() {
        return this.get(this.KEYS.CURRENT_WEEK) || (window.MockData ? window.MockData.currentWeekId : null);
    },

    // Admin authentication
    setAdminAuth(authData) {
        return this.set(this.KEYS.ADMIN_AUTH, authData);
    },

    getAdminAuth() {
        return this.get(this.KEYS.ADMIN_AUTH);
    },

    clearAdminAuth() {
        return this.remove(this.KEYS.ADMIN_AUTH);
    },

    // Settings
    saveSettings(settings) {
        return this.set(this.KEYS.SETTINGS, settings);
    },

    getSettings() {
        return this.get(this.KEYS.SETTINGS);
    },

    // Workout Tracking
    saveWorkoutProgress(workoutId, activity, day, reps) {
        const key = `${this.KEYS.WORKOUTS}_${workoutId}`;
        const stored = this.get(key) || {};
        if (!stored[activity]) {
            stored[activity] = {};
        }
        stored[activity][day] = reps !== '' && reps !== null ? parseInt(reps) || 0 : null;
        return this.set(key, stored);
    },

    getWorkoutProgress(workoutId) {
        const key = `${this.KEYS.WORKOUTS}_${workoutId}`;
        return this.get(key) || {};
    }
};

// Make available globally
if (typeof window !== 'undefined') {
    window.Storage = Storage;
}

