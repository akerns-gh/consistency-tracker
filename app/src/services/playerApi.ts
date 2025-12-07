import api from './api'

export interface Player {
  playerId: string
  name: string
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
  name: string
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
 */
export async function getPlayer(uniqueLink: string): Promise<PlayerData> {
  const response = await api.get(`/player/${uniqueLink}`)
  return response.data.data
}

/**
 * Get specific week data for a player
 */
export async function getWeek(uniqueLink: string, weekId: string): Promise<WeekData & { clubId: string; teamId: string }> {
  const response = await api.get(`/player/${uniqueLink}/week/${weekId}`)
  return response.data.data
}

/**
 * Get aggregated progress statistics
 */
export async function getProgress(uniqueLink: string): Promise<ProgressData> {
  const response = await api.get(`/player/${uniqueLink}/progress`)
  return response.data.data
}

/**
 * Mark activity complete for a day
 */
export async function checkIn(
  uniqueLink: string,
  activityId: string,
  date: string,
  completed: boolean = true
): Promise<{ tracking: any; dailyScore: number; completedActivities: string[] }> {
  const response = await api.post(`/player/${uniqueLink}/checkin`, {
    activityId,
    date,
    completed,
  })
  return response.data.data
}

/**
 * Save/update weekly reflection
 */
export async function saveReflection(
  uniqueLink: string,
  weekId: string,
  wentWell: string,
  doBetter: string,
  planForWeek: string
): Promise<{ reflection: any }> {
  const response = await api.put(`/player/${uniqueLink}/reflection`, {
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
 * @param uniqueLink - Player's unique link for context
 */
export async function getLeaderboard(
  weekId: string,
  uniqueLink: string,
  scope: 'team' | 'club' = 'team'
): Promise<LeaderboardData> {
  const response = await api.get(`/leaderboard/${weekId}`, {
    params: {
      uniqueLink,
      scope,
    },
  })
  return response.data.data
}

/**
 * List all published content pages
 */
export async function listContent(uniqueLink: string): Promise<{ content: ContentPage[]; total: number }> {
  const response = await api.get('/content', {
    params: {
      uniqueLink,
    },
  })
  return response.data.data
}

/**
 * Get specific content page by slug
 */
export async function getContent(uniqueLink: string, slug: string): Promise<ContentPageDetail> {
  const response = await api.get(`/content/${slug}`, {
    params: {
      uniqueLink,
    },
  })
  return response.data.data
}

