// Base View class for all views
// Provides common rendering utilities and DOM helpers

class BaseView {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.warn(`Container not found: ${containerId}`);
        }
    }

    // Query selector helper
    $(selector) {
        return this.container ? this.container.querySelector(selector) : null;
    }

    // Query selector all helper
    $$(selector) {
        return this.container ? this.container.querySelectorAll(selector) : [];
    }

    // Create element helper
    createElement(tag, className = '', attributes = {}) {
        const element = document.createElement(tag);
        if (className) {
            element.className = className;
        }
        Object.keys(attributes).forEach(key => {
            element.setAttribute(key, attributes[key]);
        });
        return element;
    }

    // Clear container
    clear() {
        if (this.container) {
            this.container.innerHTML = '';
        }
    }

    // Format date helper
    formatDate(date) {
        if (!date) return '';
        const d = new Date(date);
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return `${months[d.getMonth()]} ${d.getDate()}`;
    }

    // Format date range
    formatDateRange(startDate, endDate) {
        const start = this.formatDate(startDate);
        const end = this.formatDate(endDate);
        return `${start} - ${end}`;
    }

    // Show element
    show(element) {
        if (element) {
            element.style.display = '';
        }
    }

    // Hide element
    hide(element) {
        if (element) {
            element.style.display = 'none';
        }
    }

    // Add class
    addClass(element, className) {
        if (element) {
            element.classList.add(className);
        }
    }

    // Remove class
    removeClass(element, className) {
        if (element) {
            element.classList.remove(className);
        }
    }

    // Toggle class
    toggleClass(element, className) {
        if (element) {
            element.classList.toggle(className);
        }
    }

    // Set text content
    setText(element, text) {
        if (element) {
            element.textContent = text;
        }
    }

    // Set HTML content
    setHTML(element, html) {
        if (element) {
            element.innerHTML = html;
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.BaseView = BaseView;
}

