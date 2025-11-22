// Content View - handles rendering of content pages

class ContentView extends BaseView {
    constructor() {
        super('contentContainer');
    }

    // Render content list
    renderContentList(content, category) {
        const container = document.getElementById('contentList');
        if (!container) return;

        container.innerHTML = '';

        content.forEach(item => {
            const card = this.createElement('div', 'content-card');
            card.innerHTML = `
                <h3>${item.title}</h3>
                <p>${item.description || ''}</p>
                <a href="content-page.html?category=${category}&id=${item.id}" class="btn-primary">Read More</a>
            `;
            container.appendChild(card);
        });
    }

    // Render individual content page
    renderContentPage(content) {
        const titleEl = document.getElementById('contentTitle');
        const contentEl = document.getElementById('contentBody');

        if (titleEl && content) {
            titleEl.textContent = content.title;
        }
        if (contentEl && content) {
            contentEl.innerHTML = content.content || '';
        }
    }

    // Render workout plan table
    renderWorkoutTable(workoutPlan, workoutProgress, onRepChange) {
        const container = document.getElementById('workoutTableContainer');
        if (!container || !workoutPlan) return;

        container.innerHTML = '';

        const table = this.createElement('table', 'workout-table');
        const thead = this.createElement('thead');
        const tbody = this.createElement('tbody');

        // Header
        const headerRow = this.createElement('tr');
        headerRow.innerHTML = `
            <th>Activity</th>
            <th>Duration</th>
            <th>Set 1</th>
            <th>Set 2</th>
            <th>Link</th>
        `;
        thead.appendChild(headerRow);

        // Sections
        Object.keys(workoutPlan).forEach(workoutId => {
            const workout = workoutPlan[workoutId];
            if (workout.sections) {
                workout.sections.forEach(section => {
                    // Section header
                    const sectionRow = this.createElement('tr', 'workout-section-header');
                    sectionRow.innerHTML = `
                        <td colspan="5">${section.name}${section.description ? ` ${section.description}` : ''}</td>
                    `;
                    tbody.appendChild(sectionRow);

                    // Activities
                    if (section.activities) {
                        section.activities.forEach(activity => {
                            const activityRow = this.createElement('tr');
                            const progress = workoutProgress[activity.activityId] || {};
                            const linkIcon = activity.link ? '🔗' : '';

                            activityRow.innerHTML = `
                                <td class="workout-activity-name">${activity.name}</td>
                                <td>${activity.duration || ''}</td>
                                <td>
                                    <input type="number" 
                                           class="workout-rep-input" 
                                           data-activity="${activity.activityId}" 
                                           data-set="1"
                                           value="${progress[1] || ''}" 
                                           placeholder="0">
                                </td>
                                <td>
                                    <input type="number" 
                                           class="workout-rep-input" 
                                           data-activity="${activity.activityId}" 
                                           data-set="2"
                                           value="${progress[2] || ''}" 
                                           placeholder="0">
                                </td>
                                <td>
                                    ${activity.link ? `<a href="${activity.link}" target="_blank">${linkIcon}</a>` : ''}
                                </td>
                            `;
                            tbody.appendChild(activityRow);
                        });
                    }
                });
            }
        });

        table.appendChild(thead);
        table.appendChild(tbody);
        container.appendChild(table);

        // Add event listeners for rep inputs
        if (onRepChange) {
            const inputs = container.querySelectorAll('.workout-rep-input');
            inputs.forEach(input => {
                input.addEventListener('change', (e) => {
                    const activity = e.target.dataset.activity;
                    const set = parseInt(e.target.dataset.set);
                    const reps = e.target.value;
                    onRepChange(activity, set, reps);
                });
            });
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ContentView = ContentView;
}

