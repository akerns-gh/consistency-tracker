// Admin View - handles rendering of admin dashboard

class AdminView extends BaseView {
    constructor() {
        super('app'); // Use the main app container
    }

    // Render player management
    renderPlayerManagement(players) {
        const container = document.getElementById('playersTableBody');
        if (!container) return;

        container.innerHTML = '';

        players.forEach(player => {
            const row = this.createElement('tr');
            row.innerHTML = `
                <td>${player.name || ''}</td>
                <td>${player.email || ''}</td>
                <td>${player.isActive ? 'Active' : 'Inactive'}</td>
                <td><code>${player.uniqueLink || ''}</code></td>
                <td>
                    <button class="btn-secondary" data-action="edit" data-id="${player.playerId}">Edit</button>
                    <button class="btn-danger" data-action="delete" data-id="${player.playerId}">Delete</button>
                </td>
            `;
            container.appendChild(row);
        });
    }

    // Render activity management
    renderActivityManagement(activities) {
        const container = document.getElementById('activitiesList');
        if (!container) return;

        container.innerHTML = '';

        activities.forEach(activity => {
            const activityCard = this.createElement('div', 'activity-card');
            activityCard.innerHTML = `
                <div class="activity-info">
                    <h3>${activity.name || ''}</h3>
                    <p>Frequency: ${activity.frequency || 'N/A'}</p>
                    <p>Point Value: ${activity.pointValue || 1}</p>
                    <p>Status: ${activity.isActive ? 'Active' : 'Inactive'}</p>
                </div>
                <div class="activity-actions">
                    <button class="btn-secondary" data-action="edit" data-id="${activity.activityId}">Edit</button>
                </div>
            `;
            container.appendChild(activityCard);
        });
    }

    // Render content management
    renderContentManagement(content, category) {
        const container = document.getElementById('contentTableBody');
        if (!container) return;

        container.innerHTML = '';

        if (!content || content.length === 0) {
            const row = this.createElement('tr');
            row.innerHTML = `
                <td colspan="5" style="text-align: center; padding: 2rem;">
                    No content pages found. Click "Add New Content" to create one.
                </td>
            `;
            container.appendChild(row);
            return;
        }

        content.forEach(item => {
            const row = this.createElement('tr');
            row.innerHTML = `
                <td>${item.title || ''}</td>
                <td>${item.category || category || 'N/A'}</td>
                <td>${item.isPublished ? 'Published' : 'Draft'}</td>
                <td>${item.updatedAt ? this.formatDate(item.updatedAt) : 'N/A'}</td>
                <td>
                    <button class="btn-secondary" data-action="edit" data-id="${item.id || item.pageId}">Edit</button>
                    <button class="btn-danger" data-action="delete" data-id="${item.id || item.pageId}">Delete</button>
                </td>
            `;
            container.appendChild(row);
        });
    }

    // Render overview stats
    renderOverviewStats(stats) {
        // Implementation for overview statistics
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.AdminView = AdminView;
}

