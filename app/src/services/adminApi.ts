import api from './api'

export interface Club {
  clubId: string
  clubName: string
  settings?: Record<string, any>
  createdAt?: string
}

export interface Team {
  teamId: string
  clubId: string
  teamName: string
  coachName?: string
  settings?: Record<string, any>
  createdAt?: string
}

/**
 * Get clubs (for admin)
 */
export async function getClubs(): Promise<{ clubs: Club[]; total: number }> {
  const response = await api.get('/admin/clubs')
  return response.data.data
}

/**
 * Create a new club (bootstrap)
 */
export async function createClub(data: {
  clubName: string
  settings?: Record<string, any>
}): Promise<{ club: Club }> {
  const response = await api.post('/admin/clubs', data)
  return response.data.data
}

/**
 * Get teams in coach's club
 */
export async function getTeams(): Promise<{ teams: Team[]; total: number }> {
  const response = await api.get('/admin/teams')
  return response.data.data
}

/**
 * Create a new team (in coach's club)
 */
export async function createTeam(data: {
  teamName: string
  coachName?: string
  settings?: Record<string, any>
}): Promise<{ team: Team }> {
  const response = await api.post('/admin/teams', data)
  return response.data.data
}

export interface Player {
  playerId: string
  name: string
  email?: string
  clubId: string
  teamId: string
  isActive: boolean
  uniqueLink?: string
  createdAt?: string
}

/**
 * Get all players
 */
export async function getPlayers(): Promise<{ players: Player[]; total: number }> {
  const response = await api.get('/admin/players')
  return response.data.data
}

/**
 * Create a new player
 */
export async function createPlayer(data: {
  name: string
  email: string
  teamId: string
}): Promise<{ player: Player }> {
  const response = await api.post('/admin/players', data)
  return response.data.data
}

/**
 * Update a player
 */
export async function updatePlayer(
  playerId: string,
  data: Partial<Player>
): Promise<{ player: Player }> {
  const response = await api.put(`/admin/players/${playerId}`, data)
  return response.data.data
}

/**
 * Deactivate a player
 */
export async function deactivatePlayer(playerId: string): Promise<void> {
  await api.delete(`/admin/players/${playerId}`)
}

/**
 * Invite a player (create Cognito user and send email)
 */
export async function invitePlayer(
  playerId: string,
  email: string
): Promise<{ success: boolean }> {
  const response = await api.post(`/admin/players/${playerId}/invite`, { email })
  return response.data.data
}

export interface Activity {
  activityId: string
  name: string
  description?: string
  frequency?: string
  pointValue: number
  displayOrder: number
  isActive: boolean
  scope?: 'club' | 'team'
  activityType?: 'flyout' | 'link'
  contentSlug?: string
  flyoutContent?: string
  requiredDaysPerWeek?: number[]
  activityGoal?: string
}

/**
 * Get all activities
 */
export async function getActivities(): Promise<{ activities: Activity[]; total: number }> {
  const response = await api.get('/admin/activities')
  return response.data.data
}

/**
 * Create a new activity
 */
export async function createActivity(data: Partial<Activity>): Promise<{ activity: Activity }> {
  const response = await api.post('/admin/activities', data)
  return response.data.data
}

/**
 * Update an activity
 */
export async function updateActivity(
  activityId: string,
  data: Partial<Activity>
): Promise<{ activity: Activity }> {
  const response = await api.put(`/admin/activities/${activityId}`, data)
  return response.data.data
}

/**
 * Delete an activity
 */
export async function deleteActivity(activityId: string): Promise<void> {
  await api.delete(`/admin/activities/${activityId}`)
}

/**
 * Get overview statistics
 */
export async function getOverview(): Promise<{
  totalPlayers: number
  averageScore: number
  totalWeeks: number
  contentPages: number
  trends?: any
}> {
  const response = await api.get('/admin/overview')
  return response.data.data
}

/**
 * Get reflections for overview
 */
export async function getReflections(): Promise<{
  reflections: Array<{
    playerName: string
    weekId: string
    wentWell: string
    doBetter: string
    planForWeek: string
  }>
}> {
  const response = await api.get('/admin/reflections')
  return response.data.data
}

/**
 * Advance to next week
 */
export async function advanceWeek(): Promise<{ success: boolean; newWeekId: string }> {
  const response = await api.post('/admin/week/advance')
  return response.data.data
}

