// Base Model class for all models
// Provides common functionality for data operations

class BaseModel {
    constructor() {
        this.storage = window.Storage || null;
        this.mockData = window.MockData || null;
    }

    // Generic get from storage
    getFromStorage(key) {
        if (!this.storage) return null;
        return this.storage.get(key);
    }

    // Generic save to storage
    saveToStorage(key, value) {
        if (!this.storage) return false;
        return this.storage.set(key, value);
    }

    // Generic remove from storage
    removeFromStorage(key) {
        if (!this.storage) return false;
        return this.storage.remove(key);
    }

    // Error handling wrapper
    handleError(error, context) {
        console.error(`Error in ${context}:`, error);
        return null;
    }

    // Validate required fields
    validateRequired(data, requiredFields) {
        const missing = requiredFields.filter(field => !data[field]);
        if (missing.length > 0) {
            throw new Error(`Missing required fields: ${missing.join(', ')}`);
        }
        return true;
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.BaseModel = BaseModel;
}

