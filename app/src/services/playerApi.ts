import api from './api'

export interface Player {
  playerId: string
  firstName: string
  lastName: string
  email?: string
  clubId: string
  teamId: string
}

export interface Activity {
  activityId: string
  name: string
  description?: string
  frequency?: string
  pointValue: number
  displayOrder: number
  scope?: 'club' | 'team'
  activityType?: 'flyout' | 'link'
  contentSlug?: string
  flyoutContent?: string
}

export interface DailyTracking {
  completedActivities: string[]
  dailyScore: number
}

export interface WeekData {
  weekId: string
  activities: Activity[]
  dailyTracking: Record<string, DailyTracking>
  weeklyScore: number
  reflection?: {
    wentWell?: string
    doBetter?: string
    planForWeek?: string
  }
}

export interface PlayerData {
  player: Player
  currentWeek: WeekData
}

export interface ProgressData {
  player: Player
  weeks: Array<{
    weekId: string
    weeklyScore: number
    daysCompleted: number
    perfectDays: number
  }>
  statistics: {
    totalWeeks: number
    totalScore: number
    averageScore: number
    bestWeek: {
      weekId: string
      weeklyScore: number
    } | null
  }
}

export interface LeaderboardEntry {
  playerId: string
  firstName: string
  lastName: string
  weeklyScore: number
  daysCompleted: number
  rank: number
  isCurrentPlayer: boolean
}

export interface LeaderboardData {
  weekId: string
  weekDates: {
    monday: string
    sunday: string
  }
  scope: 'team' | 'club'
  leaderboard: LeaderboardEntry[]
  totalPlayers: number
}

export interface ContentPage {
  pageId: string
  slug: string
  title: string
  category: string
  scope?: 'club' | 'team'
  displayOrder: number
  lastUpdated?: string
}

export interface ContentPageDetail extends ContentPage {
  htmlContent: string
  createdAt?: string
}

/**
 * Get player data and current week activities
 * Uses JWT token to identify player
 */
export async function getPlayer(): Promise<PlayerData> {
  const response = await api.get('/player')
  return response.data.data
}

/**
 * Get specific week data for a player
 * Uses JWT token to identify player
 */
export async function getWeek(weekId: string): Promise<WeekData & { clubId: string; teamId: string }> {
  const response = await api.get(`/player/week/${weekId}`)
  return response.data.data
}

/**
 * Get aggregated progress statistics
 * Uses JWT token to identify player
 */
export async function getProgress(): Promise<ProgressData> {
  const response = await api.get('/player/progress')
  return response.data.data
}

/**
 * Mark activity complete for a day
 * Uses JWT token to identify player
 */
export async function checkIn(
  activityId: string,
  date: string,
  completed: boolean = true
): Promise<{ tracking: any; dailyScore: number; completedActivities: string[] }> {
  const response = await api.post('/player/checkin', {
    activityId,
    date,
    completed,
  })
  return response.data.data
}

/**
 * Save/update weekly reflection
 * Uses JWT token to identify player
 */
export async function saveReflection(
  weekId: string,
  wentWell: string,
  doBetter: string,
  planForWeek: string
): Promise<{ reflection: any }> {
  const response = await api.put('/player/reflection', {
    weekId,
    wentWell,
    doBetter,
    planForWeek,
  })
  return response.data.data
}

/**
 * Get leaderboard for a week
 * @param weekId - Week ID in format YYYY-WW
 * @param scope - 'team' (default) or 'club'
 * Uses JWT token for player context
 */
export async function getLeaderboard(
  weekId: string,
  scope: 'team' | 'club' = 'team'
): Promise<LeaderboardData> {
  const response = await api.get(`/leaderboard/${weekId}`, {
    params: {
      scope,
    },
  })
  return response.data.data
}

/**
 * List all published content pages
 * Uses JWT token for player context
 */
export async function listContent(): Promise<{ content: ContentPage[]; total: number }> {
  const response = await api.get('/content')
  return response.data.data
}

/**
 * Get specific content page by slug
 * Uses JWT token for player context
 */
export async function getContent(slug: string): Promise<ContentPageDetail> {
  const response = await api.get(`/content/${slug}`)
  return response.data.data
}

