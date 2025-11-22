// Player View - handles rendering of player dashboard

class PlayerView extends BaseView {
    constructor() {
        super('activityGridContainer'); // Main container for player view
    }

    // Render activity grid
    renderActivityGrid(activities, weekDates, trackingData, activityModel, onCellClick, onActivityClick) {
        const grid = document.getElementById('activityGrid');
        const dailyScores = document.getElementById('dailyScores');
        if (!grid || !dailyScores) return;

        grid.innerHTML = '';
        dailyScores.innerHTML = '';

        const days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];

        // Day headers
        const dayHeaders = this.createElement('div', 'day-header');
        dayHeaders.textContent = 'Activities';
        grid.appendChild(dayHeaders);

        days.forEach(day => {
            const header = this.createElement('div', 'day-header');
            header.textContent = day;
            grid.appendChild(header);
        });

        // Activity rows
        activities.forEach(activity => {
            const activityReq = activityModel.getActivityRequirement(activity.activityId);
            const displayName = activityModel.getActivityDisplayName(activity.activityId);
            const activityType = activityModel.getActivityType(activity.activityId);
            const slug = activityModel.getActivitySlug(activity.activityId);
            const flyoutContent = activityModel.getFlyoutContent(activity.activityId);
            const requiredDays = activityModel.getRequiredDays(activity.activityId);

            const rowHeader = this.createElement('div', 'activity-row-header activity-link');
            rowHeader.style.cursor = 'pointer';
            rowHeader.textContent = displayName;

            // Set up click handler
            if (activityType === 'flyout' && flyoutContent) {
                rowHeader.setAttribute('data-activity-id', activity.activityId);
                rowHeader.setAttribute('data-flyout-content', flyoutContent);
                rowHeader.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (onActivityClick) {
                        onActivityClick('flyout', flyoutContent, activity.activityId);
                    }
                });
            } else if (slug) {
                rowHeader.addEventListener('click', () => {
                    if (onActivityClick) {
                        onActivityClick('link', slug);
                    }
                });
            }

            grid.appendChild(rowHeader);

            // Activity cells for each day
            days.forEach((day, dayIndex) => {
                const date = new Date(weekDates.monday);
                date.setDate(date.getDate() + dayIndex);
                const dateStr = date.toISOString().split('T')[0];

                const cell = this.createElement('div', 'activity-cell');
                cell.dataset.activityId = activity.activityId;
                cell.dataset.date = dateStr;

                // Check if required
                if (requiredDays.includes(dayIndex)) {
                    this.addClass(cell, 'required');
                }

                // Check if completed
                const tracking = trackingData.find(t => t.date === dateStr);
                if (tracking && tracking.completedActivities.includes(activity.activityId)) {
                    this.addClass(cell, 'completed');
                }

                // Check for warnings (will be handled by controller)
                cell.addEventListener('click', () => {
                    if (onCellClick) {
                        onCellClick(activity.activityId, dateStr);
                    }
                });

                grid.appendChild(cell);
            });
        });

        // Daily scores row
        const scoreLabel = this.createElement('div', 'daily-score-label');
        scoreLabel.textContent = 'Daily Score';
        dailyScores.appendChild(scoreLabel);

        days.forEach((day, dayIndex) => {
            const date = new Date(weekDates.monday);
            date.setDate(date.getDate() + dayIndex);
            const dateStr = date.toISOString().split('T')[0];
            const tracking = trackingData.find(t => t.date === dateStr);
            const score = tracking ? tracking.dailyScore : 0;

            const scoreCell = this.createElement('div', 'daily-score-cell');
            scoreCell.textContent = `${score}/${activities.length}`;
            dailyScores.appendChild(scoreCell);
        });
    }

    // Update activity cell
    updateActivityCell(activityId, dateStr, isCompleted) {
        const cell = document.querySelector(`[data-activity-id="${activityId}"][data-date="${dateStr}"]`);
        if (cell) {
            if (isCompleted) {
                this.addClass(cell, 'completed');
            } else {
                this.removeClass(cell, 'completed');
            }
        }
    }

    // Update daily score
    updateDailyScore(dateStr, score, maxScore) {
        const cells = document.querySelectorAll('.daily-score-cell');
        const days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
        const weekDates = this.getWeekDates(); // This will need to be passed or stored
        // Implementation would need weekDates to find the right cell
        // For now, this is a placeholder
    }

    // Render weekly score card
    renderWeeklyScore(score, maxScore) {
        const totalScoreEl = document.getElementById('totalScore');
        const scoreMaxEl = document.querySelector('.score-max');
        const progressFillEl = document.getElementById('progressFill');

        if (totalScoreEl) {
            totalScoreEl.textContent = score;
        }
        if (scoreMaxEl) {
            scoreMaxEl.textContent = `/${maxScore}`;
        }
        if (progressFillEl) {
            const percentage = maxScore > 0 ? (score / maxScore) * 100 : 0;
            progressFillEl.style.width = `${percentage}%`;
        }
    }

    // Render week information
    renderWeekInfo(weekDates) {
        const weekDatesEl = document.getElementById('weekDates');
        if (weekDatesEl) {
            weekDatesEl.textContent = `Week of ${this.formatDate(weekDates.monday)} - ${this.formatDate(weekDates.sunday)}`;
        }
    }

    // Render player name in header
    renderPlayerName(playerName) {
        const playerNameEl = document.getElementById('playerName');
        if (playerNameEl) {
            playerNameEl.textContent = playerName;
        }
    }

    // Update cell warning state
    updateCellWarning(activityId, dateStr, showWarning) {
        const cell = document.querySelector(`[data-activity-id="${activityId}"][data-date="${dateStr}"]`);
        if (cell) {
            if (showWarning) {
                this.addClass(cell, 'warning');
            } else {
                this.removeClass(cell, 'warning');
            }
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.PlayerView = PlayerView;
}

