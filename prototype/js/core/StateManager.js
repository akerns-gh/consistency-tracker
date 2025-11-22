// State Manager - centralized application state management

class StateManager {
    constructor() {
        this.state = {
            currentPlayer: null,
            currentWeek: null,
            isAdmin: false
        };
        this.listeners = [];
    }

    // Get state value
    get(key) {
        return this.state[key];
    }

    // Set state value
    set(key, value) {
        const oldValue = this.state[key];
        this.state[key] = value;
        
        // Notify listeners
        this.notify(key, value, oldValue);
        
        // Persist to storage if needed
        if (key === 'currentPlayer' && window.Storage) {
            window.Storage.setCurrentPlayer(value);
        }
        if (key === 'currentWeek' && window.Storage) {
            window.Storage.setCurrentWeek(value);
        }
    }

    // Subscribe to state changes
    subscribe(callback) {
        this.listeners.push(callback);
        
        // Return unsubscribe function
        return () => {
            this.listeners = this.listeners.filter(cb => cb !== callback);
        };
    }

    // Notify listeners of state change
    notify(key, newValue, oldValue) {
        this.listeners.forEach(callback => {
            callback(key, newValue, oldValue);
        });
        
        // Also emit event bus event
        if (window.EventBus) {
            window.EventBus.emit(`state:${key}`, { newValue, oldValue });
        }
    }

    // Initialize state from storage
    init() {
        if (window.Storage) {
            const currentPlayer = window.Storage.getCurrentPlayer();
            const currentWeek = window.Storage.getCurrentWeek();
            
            if (currentPlayer) {
                this.state.currentPlayer = currentPlayer;
            }
            if (currentWeek) {
                this.state.currentWeek = currentWeek;
            }
        }
    }
}

// Create singleton instance
const stateManager = new StateManager();

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.StateManager = stateManager;
}

