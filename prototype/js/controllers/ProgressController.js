// Progress Controller - coordinates ProgressView with TrackingModel and LeaderboardModel

class ProgressController extends BaseController {
    constructor() {
        super();
        this.trackingModel = new TrackingModel();
        this.leaderboardModel = new LeaderboardModel();
        this.activityModel = new ActivityModel();
        this.view = new ProgressView();
        this.currentPlayerId = null;
    }

    // Initialize progress view
    async init() {
        await this.activityModel.loadActivityRequirements();

        this.currentPlayerId = Storage.getCurrentPlayer() || 
            (window.PlayerModel ? new PlayerModel().getActivePlayers()[0]?.playerId : null);

        await this.render();
    }

    // Setup carousel functionality
    setupCarousel() {
        // Use setTimeout to ensure DOM is fully rendered
        setTimeout(() => {
            const carousel = document.getElementById('statsCarousel');
            const prevButton = document.querySelector('.carousel-button-prev');
            const nextButton = document.querySelector('.carousel-button-next');

            if (!carousel) {
                console.warn('Carousel container not found');
                return;
            }
            if (!prevButton || !nextButton) {
                console.warn('Carousel buttons not found');
                return;
            }

            // Calculate scroll amount based on card width + gap
            const firstCard = carousel.querySelector('.summary-card');
            if (!firstCard) return;
            
            const cardWidth = firstCard.offsetWidth;
            const gap = parseInt(getComputedStyle(carousel).gap) || 24;
            const scrollAmount = cardWidth + gap;

            const updateButtons = () => {
                const isAtStart = carousel.scrollLeft <= 5;
                const isAtEnd = carousel.scrollLeft >= carousel.scrollWidth - carousel.clientWidth - 5;
                
                prevButton.disabled = isAtStart;
                nextButton.disabled = isAtEnd;
            };

            // Remove existing listeners if any
            const newPrevButton = prevButton.cloneNode(true);
            const newNextButton = nextButton.cloneNode(true);
            prevButton.parentNode.replaceChild(newPrevButton, prevButton);
            nextButton.parentNode.replaceChild(newNextButton, nextButton);

            newPrevButton.addEventListener('click', () => {
                carousel.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
            });

            newNextButton.addEventListener('click', () => {
                carousel.scrollBy({ left: scrollAmount, behavior: 'smooth' });
            });

            carousel.addEventListener('scroll', updateButtons);
            updateButtons(); // Initial state
        }, 100);
    }

    // Render progress view
    async render() {
        // Get all tracking data for player
        const allTracking = this.trackingModel.getAllTracking();
        const playerTracking = allTracking.filter(t => t.playerId === this.currentPlayerId);

        // Get unique weeks
        const weeks = [...new Set(playerTracking.map(t => t.weekId))].sort().reverse();

        // Calculate weekly data
        const weeklyData = weeks.map(weekId => {
            const weekTracking = playerTracking.filter(t => t.weekId === weekId);
            const weeklyScore = weekTracking.reduce((sum, t) => sum + t.dailyScore, 0);
            const daysCompleted = weekTracking.filter(t => t.dailyScore > 0).length;
            const bestDay = Math.max(...weekTracking.map(t => t.dailyScore), 0);
            const totalActivities = weekTracking.reduce((sum, t) => sum + t.completedActivities.length, 0);
            const weekDates = this.trackingModel.getWeekDates(weekId);

            return {
                weekId,
                score: weeklyScore,
                daysCompleted,
                bestDay,
                totalActivities,
                dates: weekDates
            };
        });

        // Calculate summary stats
        const currentWeek = weeklyData[0] || { score: 0 };
        const previousWeek = weeklyData[1] || { score: 0 };
        const avgScore = weeklyData.length > 0 
            ? Math.round(weeklyData.reduce((sum, w) => sum + w.score, 0) / weeklyData.length)
            : 0;
        const bestWeek = weeklyData.reduce((best, week) => 
            week.score > best.score ? week : best, weeklyData[0] || { score: 0, dates: { monday: new Date() } }
        );
        const streak = this.leaderboardModel.calculateConsistencyStreak(this.currentPlayerId);

        // Render summary cards
        this.view.renderSummaryCards(currentWeek, previousWeek, avgScore, bestWeek, streak);

        // Render chart
        this.view.renderWeeklyScoresChart(weeklyData);

        // Render activity performance
        const currentWeekId = Storage.getCurrentWeek() || 
            (window.MockData ? window.MockData.currentWeekId : null);
        this.renderActivityPerformance(currentWeekId);

        // Render breakdown table
        const maxActivities = this.activityModel.getActiveActivities().length;
        this.view.renderWeeklyBreakdown(weeklyData, maxActivities);

        // Calculate and render trends
        this.calculateTrends(weeklyData);
        
        // Setup carousel after all content is rendered
        this.setupCarousel();
    }

    // Render activity performance
    renderActivityPerformance(weekId) {
        const activities = this.activityModel.getActiveActivities();
        const trackingData = this.trackingModel.getAllTrackingForWeek(this.currentPlayerId, weekId);

        const activityStats = activities.map(activity => {
            const requiredDays = this.activityModel.getRequiredDays(activity.activityId);
            const required = requiredDays.length;
            const completed = this.trackingModel.getActivityCompletionCount(
                this.currentPlayerId,
                weekId,
                activity.activityId
            );

            return {
                name: this.activityModel.getActivityDisplayName(activity.activityId),
                required,
                completed
            };
        });

        this.view.renderActivityPerformance(activityStats);
    }

    // Calculate trends
    calculateTrends(weeklyData) {
        // Score trend
        let scoreTrend = { arrow: '→', text: 'Stable' };
        if (weeklyData.length >= 2) {
            const recent = weeklyData[0].score;
            const previous = weeklyData[1].score;
            if (recent > previous) {
                scoreTrend = { arrow: '↑', text: 'Improving' };
            } else if (recent < previous) {
                scoreTrend = { arrow: '↓', text: 'Declining' };
            }
        }

        // Most improved and needs attention (simplified)
        const trends = {
            scoreTrend,
            mostImproved: '-',
            needsAttention: '-'
        };

        this.view.renderTrends(trends);
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ProgressController = ProgressController;
}

