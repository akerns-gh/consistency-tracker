// Admin View - handles rendering of admin dashboard

class AdminView extends BaseView {
    constructor() {
        super('adminContainer');
    }

    // Render player management
    renderPlayerManagement(players) {
        const container = document.getElementById('playersList');
        if (!container) return;

        container.innerHTML = '';

        players.forEach(player => {
            const row = this.createElement('tr');
            row.innerHTML = `
                <td>${player.name}</td>
                <td>${player.email}</td>
                <td><code>${player.uniqueLink}</code></td>
                <td>${player.isActive ? 'Active' : 'Inactive'}</td>
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
            const row = this.createElement('tr');
            row.innerHTML = `
                <td>${activity.name}</td>
                <td>${activity.frequency}</td>
                <td>${activity.pointValue}</td>
                <td>${activity.isActive ? 'Active' : 'Inactive'}</td>
                <td>
                    <button class="btn-secondary" data-action="edit" data-id="${activity.activityId}">Edit</button>
                </td>
            `;
            container.appendChild(row);
        });
    }

    // Render content management
    renderContentManagement(content, category) {
        const container = document.getElementById('contentList');
        if (!container) return;

        container.innerHTML = '';

        content.forEach(item => {
            const card = this.createElement('div', 'content-card');
            card.innerHTML = `
                <h3>${item.title}</h3>
                <p>${item.description || ''}</p>
                <button class="btn-primary" data-action="edit" data-id="${item.id}">Edit</button>
            `;
            container.appendChild(card);
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

