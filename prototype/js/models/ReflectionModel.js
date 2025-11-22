// Reflection Model - handles reflection data operations

class ReflectionModel extends BaseModel {
    constructor() {
        super();
    }

    // Get reflection by ID
    getReflection(reflectionId) {
        try {
            if (!this.storage) {
                return null;
            }
            return this.storage.getReflection(reflectionId);
        } catch (error) {
            return this.handleError(error, 'getReflection');
        }
    }

    // Get weekly reflection for player and week
    getWeeklyReflection(playerId, weekId) {
        try {
            const reflectionKey = `weekly-reflection-${playerId}-${weekId}`;
            const saved = localStorage.getItem(reflectionKey);
            
            if (saved) {
                return JSON.parse(saved);
            }
            return null;
        } catch (error) {
            return this.handleError(error, 'getWeeklyReflection');
        }
    }

    // Save reflection
    saveReflection(reflectionId, data) {
        try {
            if (!this.storage) {
                return false;
            }
            return this.storage.saveReflection(reflectionId, data);
        } catch (error) {
            return this.handleError(error, 'saveReflection');
        }
    }

    // Save weekly reflection
    saveWeeklyReflection(playerId, weekId, data) {
        try {
            const reflectionKey = `weekly-reflection-${playerId}-${weekId}`;
            const reflectionData = {
                ...data,
                playerId: playerId,
                weekId: weekId,
                updatedAt: new Date().toISOString()
            };
            localStorage.setItem(reflectionKey, JSON.stringify(reflectionData));
            return true;
        } catch (error) {
            return this.handleError(error, 'saveWeeklyReflection');
        }
    }

    // Get all reflections for a player
    getReflectionsByPlayer(playerId) {
        try {
            if (!this.mockData || !this.mockData.reflections) {
                return [];
            }
            const allReflections = this.storage ? 
                this.storage.mergeReflections(this.mockData.reflections) : 
                this.mockData.reflections;
            return allReflections.filter(r => r.playerId === playerId);
        } catch (error) {
            return this.handleError(error, 'getReflectionsByPlayer');
        }
    }

    // Get reflections by week
    getReflectionsByWeek(weekId) {
        try {
            if (!this.mockData || !this.mockData.reflections) {
                return [];
            }
            const allReflections = this.storage ? 
                this.storage.mergeReflections(this.mockData.reflections) : 
                this.mockData.reflections;
            return allReflections.filter(r => r.weekId === weekId);
        } catch (error) {
            return this.handleError(error, 'getReflectionsByWeek');
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ReflectionModel = ReflectionModel;
}

