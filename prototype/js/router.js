// Simple client-side routing utilities

const Router = {
    // Get current page from URL
    getCurrentPage() {
        const path = window.location.pathname;
        const filename = path.split('/').pop() || 'index.html';
        return filename.replace('.html', '');
    },

    // Navigate to a page
    navigate(page, params = {}) {
        const url = `${page}.html${this.buildQueryString(params)}`;
        window.location.href = url;
    },

    // Build query string from params
    buildQueryString(params) {
        const keys = Object.keys(params);
        if (keys.length === 0) return '';
        const pairs = keys.map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`);
        return '?' + pairs.join('&');
    },

    // Get query parameters
    getQueryParams() {
        const params = {};
        const queryString = window.location.search.substring(1);
        if (!queryString) return params;
        
        queryString.split('&').forEach(pair => {
            const [key, value] = pair.split('=');
            if (key) {
                params[decodeURIComponent(key)] = decodeURIComponent(value || '');
            }
        });
        
        return params;
    },

    // Get specific query parameter
    getQueryParam(name) {
        const params = this.getQueryParams();
        return params[name] || null;
    },

    // Check if on a specific page
    isPage(page) {
        return this.getCurrentPage() === page;
    }
};

// Make available globally
if (typeof window !== 'undefined') {
    window.Router = Router;
}

