// Base Controller class for all controllers
// Provides common functionality for event handling and coordination

class BaseController {
    constructor() {
        this.models = {};
        this.views = {};
        this.eventListeners = [];
    }

    // Initialize controller
    init() {
        // Override in subclasses
    }

    // Cleanup controller
    destroy() {
        // Remove event listeners
        this.eventListeners.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this.eventListeners = [];
    }

    // Add event listener with automatic cleanup tracking
    addEventListener(element, event, handler) {
        if (element) {
            element.addEventListener(event, handler);
            this.eventListeners.push({ element, event, handler });
        }
    }

    // Remove event listener
    removeEventListener(element, event, handler) {
        if (element) {
            element.removeEventListener(event, handler);
            this.eventListeners = this.eventListeners.filter(
                listener => !(listener.element === element && listener.event === event && listener.handler === handler)
            );
        }
    }

    // Delegate event handling
    delegateEvent(container, selector, event, handler) {
        this.addEventListener(container, event, (e) => {
            const target = e.target.closest(selector);
            if (target) {
                handler.call(target, e);
            }
        });
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.BaseController = BaseController;
}

