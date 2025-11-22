// Shared Views - reusable UI components

class SharedViews {
    // Render header with player name
    static renderHeader(playerName) {
        const playerNameEl = document.getElementById('playerName');
        if (playerNameEl) {
            playerNameEl.textContent = playerName;
        }
    }

    // Render navigation menu
    static renderNavigation(navigationData, currentPage) {
        const navLinks = document.getElementById('navLinks');
        if (!navLinks) return;

        navLinks.innerHTML = '';

        navigationData.forEach(item => {
            if (item.display === false) return;

            const li = document.createElement('li');
            const a = document.createElement('a');
            a.className = 'nav-link';
            a.href = this.buildNavUrl(item);
            a.textContent = item.label;

            // Set active state
            if (this.isActivePage(item, currentPage)) {
                a.classList.add('active');
            }

            li.appendChild(a);
            navLinks.appendChild(li);
        });
    }

    // Build navigation URL
    static buildNavUrl(item) {
        if (item.page === 'content-page' && item.slug) {
            return `content-page.html?slug=${item.slug}`;
        } else if (item.page === 'content-list' && item.category) {
            return `content-list.html?category=${item.category}`;
        } else {
            return `${item.page}.html`;
        }
    }

    // Check if page is active
    static isActivePage(item, currentPage) {
        if (item.page === currentPage) {
            return true;
        }
        if (item.page === 'content-page' && currentPage === 'content-page') {
            // Could check slug here if needed
            return false;
        }
        return false;
    }

    // Render modal
    static renderModal(title, content, onClose) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const closeBtn = modal.querySelector('.modal-close');
        closeBtn.addEventListener('click', () => {
            document.body.removeChild(modal);
            if (onClose) onClose();
        });

        return modal;
    }

    // Render flyout
    static renderFlyout(content, activityId) {
        const flyout = document.getElementById('activityFlyout');
        const flyoutPanel = document.getElementById('activityFlyoutPanel');
        const flyoutContent = document.getElementById('activityFlyoutContent');

        if (!flyout || !flyoutPanel || !flyoutContent) return;

        flyoutContent.innerHTML = content;
        flyout.classList.add('active');
        document.body.style.overflow = 'hidden';

        // Close on overlay click
        flyout.addEventListener('click', (e) => {
            if (e.target === flyout) {
                this.closeFlyout();
            }
        });

        // Close button
        const closeBtn = flyoutPanel.querySelector('.activity-flyout-close') || 
                        document.getElementById('flyoutClose');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeFlyout();
            });
        }

        // Close on overlay click (specific overlay element)
        const overlay = document.getElementById('flyoutOverlay');
        if (overlay) {
            overlay.addEventListener('click', () => {
                this.closeFlyout();
            });
        }
    }

    // Close flyout
    static closeFlyout() {
        const flyout = document.getElementById('activityFlyout');
        if (flyout) {
            flyout.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    // Render page title
    static renderPageTitle(title) {
        const titleEl = document.querySelector('.page-content-title');
        if (titleEl) {
            titleEl.textContent = title;
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.SharedViews = SharedViews;
}

