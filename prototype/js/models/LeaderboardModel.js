// Leaderboard Model - handles leaderboard calculations and statistics

class LeaderboardModel extends BaseModel {
    constructor() {
        super();
    }

    // Calculate rankings for a week
    calculateRankings(weekId) {
        try {
            const players = this.mockData ? this.mockData.players.filter(p => p.isActive) : [];
            const allTracking = this.storage && this.mockData ? 
                this.storage.mergeTracking(this.mockData.tracking) : 
                (this.mockData ? this.mockData.tracking : []);

            const playerScores = players.map(player => {
                const weekTracking = allTracking.filter(t => 
                    t.playerId === player.playerId && t.weekId === weekId
                );
                const weeklyScore = weekTracking.reduce((sum, t) => sum + t.dailyScore, 0);
                return {
                    player: player,
                    score: weeklyScore
                };
            });

            // Sort by score (descending)
            playerScores.sort((a, b) => b.score - a.score);

            return playerScores;
        } catch (error) {
            return this.handleError(error, 'calculateRankings');
        }
    }

    // Get top N players
    getTopPlayers(weekId, count = 3) {
        try {
            const rankings = this.calculateRankings(weekId);
            return rankings.slice(0, count);
        } catch (error) {
            return this.handleError(error, 'getTopPlayers');
        }
    }

    // Calculate team statistics
    getTeamStats(weekId) {
        try {
            const rankings = this.calculateRankings(weekId);
            if (rankings.length === 0) {
                return {
                    totalPlayers: 0,
                    averageScore: 0,
                    highestScore: 0,
                    perfectWeeks: 0
                };
            }

            const totalPlayers = rankings.length;
            const totalScore = rankings.reduce((sum, item) => sum + item.score, 0);
            const averageScore = Math.round(totalScore / totalPlayers);
            const highestScore = rankings[0] ? rankings[0].score : 0;
            
            // Calculate max possible score
            const maxScore = this.mockData && this.mockData.activities ? 
                this.mockData.activities.filter(a => a.isActive).length * 7 : 0;
            const perfectWeeks = rankings.filter(item => item.score === maxScore).length;

            return {
                totalPlayers,
                averageScore,
                highestScore,
                perfectWeeks
            };
        } catch (error) {
            return this.handleError(error, 'getTeamStats');
        }
    }

    // Calculate player progress over multiple weeks
    calculatePlayerProgress(playerId, weeks) {
        try {
            const allTracking = this.storage && this.mockData ? 
                this.storage.mergeTracking(this.mockData.tracking) : 
                (this.mockData ? this.mockData.tracking : []);

            return weeks.map(weekId => {
                const weekTracking = allTracking.filter(t => 
                    t.playerId === playerId && t.weekId === weekId
                );
                const weeklyScore = weekTracking.reduce((sum, t) => sum + t.dailyScore, 0);
                const weekDates = this.mockData && this.mockData.getWeekDates ? 
                    this.mockData.getWeekDates(weekId) : null;
                
                return {
                    weekId,
                    score: weeklyScore,
                    dates: weekDates
                };
            });
        } catch (error) {
            return this.handleError(error, 'calculatePlayerProgress');
        }
    }

    // Calculate consistency streak
    calculateConsistencyStreak(playerId) {
        try {
            if (!this.mockData || !this.mockData.currentWeekId) {
                return 0;
            }

            const weeks = [];
            let currentWeekId = this.mockData.currentWeekId;
            
            // Get last 10 weeks
            for (let i = 0; i < 10; i++) {
                weeks.push(currentWeekId);
                const weekDates = this.mockData.getWeekDates ? 
                    this.mockData.getWeekDates(currentWeekId) : null;
                if (weekDates) {
                    const prevDate = new Date(weekDates.monday);
                    prevDate.setDate(prevDate.getDate() - 7);
                    currentWeekId = this.mockData.getWeekId ? 
                        this.mockData.getWeekId(prevDate) : null;
                    if (!currentWeekId) break;
                } else {
                    break;
                }
            }

            const progress = this.calculatePlayerProgress(playerId, weeks);
            let streak = 0;
            
            for (const week of progress) {
                if (week.score > 0) {
                    streak++;
                } else {
                    break;
                }
            }

            return streak;
        } catch (error) {
            return this.handleError(error, 'calculateConsistencyStreak');
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.LeaderboardModel = LeaderboardModel;
}

