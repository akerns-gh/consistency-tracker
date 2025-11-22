// Progress View - handles rendering of My Progress page

class ProgressView extends BaseView {
    constructor() {
        super('progressContainer');
    }

    // Render summary cards
    renderSummaryCards(currentWeek, previousWeek, avgScore, bestWeek, streak) {
        const currentWeekScoreEl = document.getElementById('currentWeekScore');
        const currentWeekChangeEl = document.getElementById('currentWeekChange');
        const averageScoreEl = document.getElementById('averageScore');
        const bestWeekScoreEl = document.getElementById('bestWeekScore');
        const bestWeekDateEl = document.getElementById('bestWeekDate');
        const consistencyStreakEl = document.getElementById('consistencyStreak');

        if (currentWeekScoreEl) {
            currentWeekScoreEl.textContent = currentWeek.score || 0;
        }

        if (currentWeekChangeEl) {
            const scoreChange = (currentWeek.score || 0) - (previousWeek.score || 0);
            if (scoreChange > 0) {
                currentWeekChangeEl.textContent = `↑ +${scoreChange} from last week`;
                currentWeekChangeEl.style.color = 'var(--success-green)';
            } else if (scoreChange < 0) {
                currentWeekChangeEl.textContent = `↓ ${scoreChange} from last week`;
                currentWeekChangeEl.style.color = 'var(--error-red)';
            } else {
                currentWeekChangeEl.textContent = 'Same as last week';
                currentWeekChangeEl.style.color = 'var(--medium-gray)';
            }
        }

        if (averageScoreEl) {
            averageScoreEl.textContent = avgScore || 0;
        }

        if (bestWeekScoreEl) {
            bestWeekScoreEl.textContent = bestWeek.score || 0;
        }

        if (bestWeekDateEl && bestWeek.dates) {
            bestWeekDateEl.textContent = `Week of ${this.formatDate(bestWeek.dates.monday)}`;
        }

        if (consistencyStreakEl) {
            consistencyStreakEl.textContent = streak || 0;
        }
    }

    // Render weekly scores chart
    renderWeeklyScoresChart(weeklyData) {
        const ctx = document.getElementById('weeklyScoresChart');
        if (!ctx || typeof Chart === 'undefined') return;

        const labels = weeklyData.map(w => 
            `Week of ${this.formatDate(w.dates.monday)}`
        ).reverse();
        const scores = weeklyData.map(w => w.score).reverse();

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Weekly Score',
                    data: scores,
                    borderColor: 'var(--true-green)',
                    backgroundColor: 'rgba(150, 200, 85, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'var(--true-green)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 35,
                        ticks: {
                            stepSize: 5
                        }
                    }
                }
            }
        });
    }

    // Render activity performance
    renderActivityPerformance(activityStats) {
        const container = document.getElementById('activityStats');
        if (!container) return;

        container.innerHTML = '';

        activityStats.forEach(stat => {
            const statCard = this.createElement('div', 'activity-stat-card');
            const percentage = stat.required > 0 ? (stat.completed / stat.required) * 100 : 0;

            statCard.innerHTML = `
                <div class="activity-stat-header">
                    <h4>${stat.name}</h4>
                    <span class="activity-stat-score">${stat.completed}/${stat.required}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${percentage}%"></div>
                </div>
            `;

            container.appendChild(statCard);
        });
    }

    // Render weekly breakdown table
    renderWeeklyBreakdown(weeklyData, maxActivities) {
        const tbody = document.getElementById('weeklyBreakdownBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        weeklyData.forEach(week => {
            const row = this.createElement('tr');
            row.innerHTML = `
                <td>${this.formatDate(week.dates.monday)} - ${this.formatDate(week.dates.sunday)}</td>
                <td><strong>${week.score}</strong></td>
                <td>${week.daysCompleted}/7</td>
                <td>${week.bestDay}/${maxActivities}</td>
                <td>${week.totalActivities}</td>
            `;
            tbody.appendChild(row);
        });
    }

    // Render trends
    renderTrends(trends) {
        const scoreTrendEl = document.getElementById('scoreTrend');
        const scoreTrendArrowEl = document.getElementById('scoreTrendArrow');
        const scoreTrendTextEl = document.getElementById('scoreTrendText');
        const mostImprovedEl = document.getElementById('mostImprovedActivity');
        const needsAttentionEl = document.getElementById('needsAttention');

        if (scoreTrendEl && trends.scoreTrend) {
            if (scoreTrendArrowEl) {
                scoreTrendArrowEl.textContent = trends.scoreTrend.arrow || '→';
            }
            if (scoreTrendTextEl) {
                scoreTrendTextEl.textContent = trends.scoreTrend.text || 'Stable';
            }
        }

        if (mostImprovedEl) {
            mostImprovedEl.textContent = trends.mostImproved || '-';
        }

        if (needsAttentionEl) {
            needsAttentionEl.textContent = trends.needsAttention || '-';
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ProgressView = ProgressView;
}

