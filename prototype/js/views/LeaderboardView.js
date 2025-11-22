// Leaderboard View - handles rendering of leaderboard

class LeaderboardView extends BaseView {
    constructor() {
        // LeaderboardView doesn't use a single container, it renders to specific elements
        // Pass null to avoid the warning about missing container
        super(null);
    }

    // Render podium (top 3)
    renderPodium(top3, currentPlayerId) {
        const container = document.getElementById('podiumContainer');
        if (!container) return;

        container.innerHTML = '';

        const positions = ['second', 'first', 'third'];
        const medals = ['🥈', '🥇', '🥉'];

        top3.forEach((item, index) => {
            const card = this.createElement('div', `podium-card ${positions[index]}`);
            card.innerHTML = `
                <div class="podium-rank">${medals[index]}</div>
                <div class="podium-name">${item.player.name}</div>
                <div class="podium-score">${item.score}</div>
            `;
            container.appendChild(card);
        });
    }

    // Render full rankings list
    renderRankings(playerScores, currentPlayerId) {
        const container = document.getElementById('rankingsList');
        if (!container) return;

        container.innerHTML = '';

        playerScores.forEach((item, index) => {
            const rankingItem = this.createElement('div', 'ranking-item');
            if (item.player.playerId === currentPlayerId) {
                this.addClass(rankingItem, 'current-player');
            }

            rankingItem.innerHTML = `
                <div class="ranking-number">${index + 1}</div>
                <div class="ranking-name">${item.player.name}</div>
                <div class="ranking-score">${item.score}</div>
            `;

            container.appendChild(rankingItem);
        });
    }

    // Render team statistics
    renderStats(stats) {
        const teamAverageEl = document.getElementById('teamAverage');
        const mostImprovedEl = document.getElementById('mostImproved');
        const perfectWeeksEl = document.getElementById('perfectWeeks');

        if (teamAverageEl) {
            teamAverageEl.textContent = stats.averageScore || 0;
        }
        if (mostImprovedEl) {
            mostImprovedEl.textContent = stats.mostImproved || '-';
        }
        if (perfectWeeksEl) {
            perfectWeeksEl.textContent = stats.perfectWeeks || 0;
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.LeaderboardView = LeaderboardView;
}

