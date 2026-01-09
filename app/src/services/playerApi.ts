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
 * Uses JWT token to identify player, or uniqueLink if provided
 */
export async function getPlayer(uniqueLink?: string): Promise<PlayerData> {
  if (uniqueLink) {
    const response = await api.get(`/player/${uniqueLink}`)
    return response.data.data
  }
  const response = await api.get('/player')
  return response.data.data
}

/**
 * Get specific week data for a player
 * Uses JWT token to identify player, or uniqueLink if provided
 */
export async function getWeek(weekId: string, uniqueLink?: string): Promise<WeekData & { clubId: string; teamId: string }> {
  if (uniqueLink) {
    const response = await api.get(`/player/${uniqueLink}/week/${weekId}`)
    return response.data.data
  }
  const response = await api.get(`/player/week/${weekId}`)
  return response.data.data
}

/**
 * Get aggregated progress statistics
 * Uses JWT token to identify player, or uniqueLink if provided
 */
export async function getProgress(uniqueLink?: string): Promise<ProgressData> {
  if (uniqueLink) {
    const response = await api.get(`/player/${uniqueLink}/progress`)
    return response.data.data
  }
  const response = await api.get('/player/progress')
  return response.data.data
}

/**
 * Mark activity complete for a day
 * Uses JWT token to identify player, or uniqueLink if provided
 * Note: checkIn is read-only when using uniqueLink (admin view-as mode)
 */
export async function checkIn(
  activityId: string,
  date: string,
  completed: boolean = true,
  uniqueLink?: string
): Promise<{ tracking: any; dailyScore: number; completedActivities: string[] }> {
  if (uniqueLink) {
    // Read-only mode - admins can't modify data when viewing as player
    throw new Error('Cannot modify player data when viewing as player')
  }
  const response = await api.post('/player/checkin', {
    activityId,
    date,
    completed,
  })
  return response.data.data
}

/**
 * Save/update weekly reflection
 * Uses JWT token to identify player, or uniqueLink if provided
 * Note: saveReflection is read-only when using uniqueLink (admin view-as mode)
 */
export async function saveReflection(
  weekId: string,
  wentWell: string,
  doBetter: string,
  planForWeek: string,
  uniqueLink?: string
): Promise<{ reflection: any }> {
  if (uniqueLink) {
    // Read-only mode - admins can't modify data when viewing as player
    throw new Error('Cannot modify player data when viewing as player')
  }
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
 * @param uniqueLink - Optional uniqueLink for admin view-as mode
 * Uses JWT token for player context, or uniqueLink if provided
 */
export async function getLeaderboard(
  weekId: string,
  scope: 'team' | 'club' = 'team',
  uniqueLink?: string
): Promise<LeaderboardData> {
  const params: any = { scope }
  if (uniqueLink) {
    params.uniqueLink = uniqueLink
  }
  const response = await api.get(`/leaderboard/${weekId}`, { params })
  return response.data.data
}

/**
 * List all published content pages
 * @param uniqueLink - Optional uniqueLink for admin view-as mode
 * Uses JWT token for player context, or uniqueLink if provided
 */
export async function listContent(uniqueLink?: string): Promise<{ content: ContentPage[]; total: number }> {
  const params = uniqueLink ? { uniqueLink } : {}
  const response = await api.get('/content', { params })
  return response.data.data
}

/**
 * Get specific content page by slug
 * @param slug - Content page slug
 * @param uniqueLink - Optional uniqueLink for admin view-as mode
 * Uses JWT token for player context, or uniqueLink if provided
 */
export async function getContent(slug: string, uniqueLink?: string): Promise<ContentPageDetail> {
  const params = uniqueLink ? { uniqueLink } : {}
  const response = await api.get(`/content/${slug}`, { params })
  return response.data.data
}

