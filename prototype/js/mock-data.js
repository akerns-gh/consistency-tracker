// Mock Data for True Lacrosse Consistency Tracker Prototype

// Generate week ID in format YYYY-WW
function getWeekId(date = new Date()) {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    const dayOfWeek = d.getDay();
    const diff = d.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1); // Adjust to Monday
    const monday = new Date(d.setDate(diff));
    const year = monday.getFullYear();
    const week = Math.ceil((monday - new Date(year, 0, 1)) / 86400000 / 7);
    return `${year}-W${week.toString().padStart(2, '0')}`;
}

function getWeekDates(weekId) {
    const [year, weekNum] = weekId.split('-W');
    const date = new Date(year, 0, 1);
    const days = (weekNum - 1) * 7;
    date.setDate(date.getDate() + days - date.getDay() + 1); // Monday
    const monday = new Date(date);
    const sunday = new Date(date);
    sunday.setDate(date.getDate() + 6);
    return { monday, sunday };
}

// Current week
const currentWeekId = getWeekId();
const currentWeekDates = getWeekDates(currentWeekId);
const prevWeek1 = new Date(currentWeekDates.monday);
prevWeek1.setDate(prevWeek1.getDate() - 7);
const prevWeek1Id = getWeekId(prevWeek1);
const prevWeek2 = new Date(prevWeek1);
prevWeek2.setDate(prevWeek2.getDate() - 7);
const prevWeek2Id = getWeekId(prevWeek2);
const prevWeek3 = new Date(prevWeek2);
prevWeek3.setDate(prevWeek3.getDate() - 7);
const prevWeek3Id = getWeekId(prevWeek3);

// Mock Players
const mockPlayers = [
    {
        playerId: 'player-001',
        name: 'Alex Johnson',
        email: 'alex.johnson@example.com',
        uniqueLink: 'abc123xyz',
        createdAt: '2024-01-15T10:00:00Z',
        isActive: true,
        teamId: 'team-001'
    },
    {
        playerId: 'player-002',
        name: 'Sam Martinez',
        email: 'sam.martinez@example.com',
        uniqueLink: 'def456uvw',
        createdAt: '2024-01-15T10:00:00Z',
        isActive: true,
        teamId: 'team-001'
    },
    {
        playerId: 'player-003',
        name: 'Jordan Williams',
        email: 'jordan.williams@example.com',
        uniqueLink: 'ghi789rst',
        createdAt: '2024-01-15T10:00:00Z',
        isActive: true,
        teamId: 'team-001'
    },
    {
        playerId: 'player-004',
        name: 'Casey Brown',
        email: 'casey.brown@example.com',
        uniqueLink: 'jkl012mno',
        createdAt: '2024-01-15T10:00:00Z',
        isActive: true,
        teamId: 'team-001'
    },
    {
        playerId: 'player-005',
        name: 'Taylor Davis',
        email: 'taylor.davis@example.com',
        uniqueLink: 'pqr345stu',
        createdAt: '2024-01-15T10:00:00Z',
        isActive: true,
        teamId: 'team-001'
    },
    {
        playerId: 'player-006',
        name: 'Morgan Lee',
        email: 'morgan.lee@example.com',
        uniqueLink: 'vwx678yza',
        createdAt: '2024-01-15T10:00:00Z',
        isActive: true,
        teamId: 'team-001'
    },
    {
        playerId: 'player-007',
        name: 'Riley Chen',
        email: 'riley.chen@example.com',
        uniqueLink: 'bcd901efg',
        createdAt: '2024-01-15T10:00:00Z',
        isActive: true,
        teamId: 'team-001'
    },
    {
        playerId: 'player-008',
        name: 'Avery Taylor',
        email: 'avery.taylor@example.com',
        uniqueLink: 'hij234klm',
        createdAt: '2024-01-15T10:00:00Z',
        isActive: false,
        teamId: 'team-001'
    }
];

// Mock Activities
const mockActivities = [
    {
        activityId: 'activity-001',
        name: 'Sleep',
        goal: '8+ hrs',
        description: 'Get at least 8 hours of sleep',
        frequency: 'daily',
        pointValue: 1,
        displayOrder: 1,
        isActive: true,
        teamId: 'team-001'
    },
    {
        activityId: 'activity-002',
        name: 'Hydration',
        goal: '8 glasses',
        description: 'Drink at least 8 glasses of water',
        frequency: 'daily',
        pointValue: 1,
        displayOrder: 2,
        isActive: true,
        teamId: 'team-001'
    },
    {
        activityId: 'activity-003',
        name: 'Daily Wall Ball',
        goal: '20 mins',
        description: 'Practice wall ball for 20 minutes',
        frequency: 'daily',
        pointValue: 1,
        displayOrder: 3,
        isActive: true,
        teamId: 'team-001'
    },
    {
        activityId: 'activity-004',
        name: '1-Mile Run',
        goal: null,
        description: 'Complete a 1-mile run',
        frequency: 'daily',
        pointValue: 1,
        displayOrder: 4,
        isActive: true,
        teamId: 'team-001'
    },
    {
        activityId: 'activity-005',
        name: 'Bodyweight Training',
        goal: '10 mins',
        description: 'Complete 10 minutes of bodyweight exercises',
        frequency: 'daily',
        pointValue: 1,
        displayOrder: 5,
        isActive: true,
        teamId: 'team-001'
    }
];

// Generate tracking data for a week
function generateTrackingData(playerId, weekId, activities) {
    const weekDates = getWeekDates(weekId);
    const tracking = [];
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    
    days.forEach((day, index) => {
        const date = new Date(weekDates.monday);
        date.setDate(date.getDate() + index);
        const dateStr = date.toISOString().split('T')[0];
        
        // Random completion (70% chance for each activity)
        const completedActivities = activities
            .filter(() => Math.random() > 0.3)
            .map(a => a.activityId);
        
        const dailyScore = completedActivities.length;
        
        tracking.push({
            trackingId: `${playerId}#${weekId}#${dateStr}`,
            playerId: playerId,
            weekId: weekId,
            date: dateStr,
            completedActivities: completedActivities,
            dailyScore: dailyScore,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        });
    });
    
    return tracking;
}

// Generate tracking data for all players and weeks
const mockTracking = [];
const weeks = [currentWeekId, prevWeek1Id, prevWeek2Id, prevWeek3Id];

mockPlayers.filter(p => p.isActive).forEach(player => {
    weeks.forEach(weekId => {
        mockTracking.push(...generateTrackingData(player.playerId, weekId, mockActivities));
    });
});

// Mock Reflections
const mockReflections = [
    {
        reflectionId: 'player-001#' + currentWeekId,
        playerId: 'player-001',
        weekId: currentWeekId,
        wentWell: 'I stayed consistent with my wall ball practice and improved my accuracy. My sleep schedule was much better this week.',
        doBetter: 'I need to drink more water throughout the day. Sometimes I forget until the evening.',
        planForWeek: 'I will set reminders on my phone to drink water every 2 hours. I also want to add 5 more minutes to my wall ball sessions.',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    },
    {
        reflectionId: 'player-002#' + currentWeekId,
        playerId: 'player-002',
        weekId: currentWeekId,
        wentWell: 'Great week for running! I completed all my mile runs and felt strong.',
        doBetter: 'I missed a few days of bodyweight training. Need to be more disciplined.',
        planForWeek: 'I will do bodyweight training right after my run to make it a habit.',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    }
];

// Mock Content Pages
const mockContentPages = [
    {
        pageId: 'content-001',
        teamId: 'team-001',
        slug: 'wall-ball-fundamentals',
        title: 'Wall Ball Fundamentals',
        category: 'guidance',
        htmlContent: `
            <h2>Mastering Wall Ball</h2>
            <p>Wall ball is one of the most important drills for developing stick skills and hand-eye coordination. Here are the fundamentals:</p>
            <h3>Proper Form</h3>
            <ul>
                <li>Stand 5-10 feet from the wall</li>
                <li>Keep your top hand near the head of the stick</li>
                <li>Use your bottom hand to control the stick</li>
                <li>Snap your wrists on each throw</li>
            </ul>
            <h3>Daily Routine</h3>
            <p>Start with 10 minutes and gradually increase to 20 minutes. Focus on:</p>
            <ol>
                <li>Right-handed throws (5 minutes)</li>
                <li>Left-handed throws (5 minutes)</li>
                <li>Quick stick (5 minutes)</li>
                <li>Behind the back (5 minutes)</li>
            </ol>
            <h3>Tips for Success</h3>
            <p>Consistency is key! Practice at the same time each day to build a habit. Track your progress and challenge yourself to improve each week.</p>
        `,
        isPublished: true,
        displayOrder: 1,
        createdBy: 'coach@truelacrosse.com',
        createdAt: '2024-01-10T10:00:00Z',
        updatedAt: '2024-01-15T10:00:00Z',
        lastEditedBy: 'coach@truelacrosse.com'
    },
    {
        pageId: 'content-002',
        teamId: 'team-001',
        slug: 'weekly-workout-plan',
        title: 'Workout #1',
        category: 'workouts',
        htmlContent: `
            <h2>Workout #1</h2>
            <p>Track your progress for each day. Check off activities as you complete them!</p>
            <div class="workout-tracker" data-workout-id="workout-001">
                <table class="workout-table">
                    <thead>
                        <tr>
                            <th>Activity</th>
                            <th>Duration/Sets</th>
                            <th>Day 1</th>
                            <th>Day 2</th>
                            <th>Day 3</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr class="workout-section-header">
                            <td colspan="5"><strong>Warm-up</strong></td>
                        </tr>
                        <tr data-activity="butt-kicks">
                            <td>Butt Kicks</td>
                            <td>30 seconds</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr data-activity="high-knees">
                            <td>High Knees</td>
                            <td>30 seconds</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr data-activity="arm-circles">
                            <td>Arm Circles</td>
                            <td>30 seconds</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr class="workout-section-header">
                            <td colspan="5"><strong>Exercises</strong> <em>(take 30 second break between sets | track how many you complete)</em></td>
                        </tr>
                        <tr data-activity="push-ups">
                            <td>Push ups</td>
                            <td>30 seconds x 2 sets</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr data-activity="bodyweight-squats">
                            <td>Bodyweight Squats</td>
                            <td>30 seconds x 2 sets</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr data-activity="lunges">
                            <td>Lunges</td>
                            <td>30 seconds x 2 sets</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr data-activity="planks">
                            <td>Planks</td>
                            <td>30 seconds x 2 sets</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr data-activity="burpees">
                            <td>Burpees</td>
                            <td>30 seconds x 2 sets</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr data-activity="jump-rope">
                            <td>Jump Rope or Jumping Jacks</td>
                            <td>1 minute x 2 sets</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr data-activity="speed-ladder">
                            <td>Speed Ladder or Fast Feet</td>
                            <td>30 seconds x 2 sets</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr class="workout-section-header">
                            <td colspan="5"><strong>Cool-down</strong></td>
                        </tr>
                        <tr data-activity="hip-openers">
                            <td>Hip Openers</td>
                            <td>30 seconds</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr data-activity="leg-swings-front">
                            <td>Leg Swings Front to Back</td>
                            <td>30 seconds each leg</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr data-activity="leg-swings-side">
                            <td>Leg Swings Side to Side</td>
                            <td>30 seconds each leg</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr data-activity="ankle-circles">
                            <td>Ankle Circles</td>
                            <td>30 seconds each ankle</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                        <tr data-activity="calf-stretches">
                            <td>Calf Stretches</td>
                            <td>30 seconds</td>
                            <td><input type="number" data-day="1" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="2" class="workout-reps-input" placeholder="reps" min="0"></td>
                            <td><input type="number" data-day="3" class="workout-reps-input" placeholder="reps" min="0"></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `,
        isPublished: true,
        displayOrder: 1,
        createdBy: 'coach@truelacrosse.com',
        createdAt: '2024-01-10T10:00:00Z',
        updatedAt: '2024-01-15T10:00:00Z',
        lastEditedBy: 'coach@truelacrosse.com'
    },
    {
        pageId: 'content-003',
        teamId: 'team-001',
        slug: 'nutrition-basics',
        title: 'Nutrition Basics for Athletes',
        category: 'nutrition',
        htmlContent: `
            <h2>Fuel Your Performance</h2>
            <p>Proper nutrition is essential for peak performance on and off the field.</p>
            <h3>Pre-Game Meals</h3>
            <p>Eat 2-3 hours before game time. Focus on:</p>
            <ul>
                <li>Complex carbohydrates (pasta, rice, whole grains)</li>
                <li>Lean protein (chicken, fish, beans)</li>
                <li>Limit fats and fiber to avoid digestive issues</li>
            </ul>
            <h3>Hydration</h3>
            <p>Stay hydrated throughout the day:</p>
            <ul>
                <li>Drink water consistently, not just when you're thirsty</li>
                <li>Aim for 8-10 glasses per day</li>
                <li>During practice/games: 4-8 oz every 15-20 minutes</li>
                <li>Avoid sugary drinks and excessive caffeine</li>
            </ul>
            <h3>Recovery Nutrition</h3>
            <p>Within 30 minutes after exercise, consume:</p>
            <ul>
                <li>Protein for muscle repair (chocolate milk, protein shake, Greek yogurt)</li>
                <li>Carbohydrates to replenish energy stores</li>
            </ul>
        `,
        isPublished: true,
        displayOrder: 1,
        createdBy: 'coach@truelacrosse.com',
        createdAt: '2024-01-10T10:00:00Z',
        updatedAt: '2024-01-15T10:00:00Z',
        lastEditedBy: 'coach@truelacrosse.com'
    },
    {
        pageId: 'content-004',
        teamId: 'team-001',
        slug: 'mental-performance',
        title: 'Mental Performance Tips',
        category: 'mental-health',
        htmlContent: `
            <h2>Building Mental Toughness</h2>
            <p>Physical training is only half the battle. Mental preparation is equally important.</p>
            <h3>Visualization</h3>
            <p>Before games and practices, visualize yourself performing well:</p>
            <ul>
                <li>See yourself making successful plays</li>
                <li>Imagine handling pressure situations calmly</li>
                <li>Visualize the feeling of success</li>
            </ul>
            <h3>Goal Setting</h3>
            <p>Set SMART goals:</p>
            <ul>
                <li><strong>S</strong>pecific - Clear and well-defined</li>
                <li><strong>M</strong>easurable - Can track progress</li>
                <li><strong>A</strong>chievable - Realistic and attainable</li>
                <li><strong>R</strong>elevant - Aligned with your values</li>
                <li><strong>T</strong>ime-bound - Has a deadline</li>
            </ul>
            <h3>Handling Pressure</h3>
            <p>When you feel nervous or anxious:</p>
            <ul>
                <li>Take deep breaths (4 seconds in, 4 seconds out)</li>
                <li>Focus on the process, not the outcome</li>
                <li>Remember your training and preparation</li>
                <li>Stay in the present moment</li>
            </ul>
        `,
        isPublished: true,
        displayOrder: 1,
        createdBy: 'coach@truelacrosse.com',
        createdAt: '2024-01-10T10:00:00Z',
        updatedAt: '2024-01-15T10:00:00Z',
        lastEditedBy: 'coach@truelacrosse.com'
    },
    {
        pageId: 'content-005',
        teamId: 'team-001',
        slug: 'team-resources',
        title: 'Team Resources',
        category: 'guidance',
        htmlContent: `
            <h2>Helpful Resources</h2>
            <p>Here are some valuable resources to support your development:</p>
            <h3>Online Training</h3>
            <ul>
                <li><a href="https://www.uslacrosse.org" target="_blank">US Lacrosse</a> - Official governing body</li>
                <li><a href="https://www.lacrossefilmroom.com" target="_blank">Lacrosse Film Room</a> - Game analysis and strategy</li>
            </ul>
            <h3>Equipment</h3>
            <ul>
                <li>Make sure your stick is properly strung</li>
                <li>Check your helmet fit regularly</li>
                <li>Replace worn-out cleats</li>
            </ul>
            <h3>Contact</h3>
            <p>Questions? Reach out to your coaches or team administrators.</p>
        `,
        isPublished: true,
        displayOrder: 1,
        createdBy: 'coach@truelacrosse.com',
        createdAt: '2024-01-10T10:00:00Z',
        updatedAt: '2024-01-15T10:00:00Z',
        lastEditedBy: 'coach@truelacrosse.com'
    }
];

// Mock Team Config
const mockTeamConfig = {
    teamId: 'team-001',
    teamName: 'True Lacrosse Team',
    coachName: 'Coach Smith',
    settings: {
        weekStartDay: 'monday',
        autoAdvanceWeek: true,
        scoringMethod: 'simple'
    }
};

// Export mock data
const MockData = {
    players: mockPlayers,
    activities: mockActivities,
    tracking: mockTracking,
    reflections: mockReflections,
    contentPages: mockContentPages,
    teamConfig: mockTeamConfig,
    currentWeekId: currentWeekId,
    getWeekId: getWeekId,
    getWeekDates: getWeekDates
};

// Make available globally
if (typeof window !== 'undefined') {
    window.MockData = MockData;
}

