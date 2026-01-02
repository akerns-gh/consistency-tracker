import api from './api'

export interface Club {
  clubId: string
  clubName: string
  settings?: Record<string, any>
  createdAt?: string
  isDisabled?: boolean
  disabledAt?: string
  enabledAt?: string
}

export interface Team {
  teamId: string
  clubId: string
  teamName: string
  settings?: Record<string, any>
  isActive?: boolean
  createdAt?: string
}

export interface Coach {
  coachId: string
  firstName: string
  lastName: string
  email: string
  teamId: string
  clubId: string
  isActive: boolean
  verificationStatus?: "pending" | "verified"
  createdAt?: string
  updatedAt?: string
}

export interface ClubAdmin {
  adminId: string
  firstName: string
  lastName: string
  email: string
  clubId: string
  isActive: boolean
  verificationStatus?: "pending" | "verified"
  createdAt?: string
  updatedAt?: string
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
  firstName: string
  lastName: string
  adminEmail: string
}): Promise<{ club: Club }> {
  const response = await api.post('/admin/clubs', data)
  return response.data.data
}

/**
 * Get club admins for a club (app-admin only)
 */
export async function getClubAdmins(clubId: string): Promise<{ admins: ClubAdmin[]; total: number }> {
  const response = await api.get(`/admin/clubs/${clubId}/admins`)
  return response.data.data
}

/**
 * Add an additional club administrator to an existing club (app-admin only)
 */
export async function addClubAdmin(
  clubId: string,
  data: { firstName: string; lastName: string; adminEmail: string }
): Promise<{ admin: ClubAdmin; emailStatus: any; message: string }> {
  const response = await api.post(`/admin/clubs/${clubId}/admins`, data)
  return response.data.data
}

/**
 * Update a club admin's firstName and lastName
 */
export async function updateClubAdmin(
  clubId: string,
  adminId: string,
  data: { firstName: string; lastName: string }
): Promise<{ admin: ClubAdmin; message: string }> {
  const response = await api.put(`/admin/clubs/${clubId}/admins/${adminId}`, data)
  return response.data.data
}

/**
 * Delete a club admin (app-admin only)
 */
export async function deleteClubAdmin(
  clubId: string,
  adminId: string
): Promise<{ message: string }> {
  const response = await api.delete(`/admin/clubs/${clubId}/admins/${adminId}`)
  return response.data.data
}

/**
 * Update a coach's firstName and lastName
 */
export async function updateCoach(
  teamId: string,
  coachId: string,
  data: { firstName: string; lastName: string }
): Promise<{ coach: Coach; message: string }> {
  const response = await api.put(`/admin/teams/${teamId}/coaches/${coachId}`, data)
  return response.data.data
}

/**
 * Update a club
 */
export async function updateClub(
  clubId: string,
  data: Partial<Club>
): Promise<{ club: Club }> {
  const response = await api.put(`/admin/clubs/${clubId}`, data)
  return response.data.data
}

/**
 * Disable a club (removes all users from Cognito groups)
 */
export async function disableClub(clubId: string): Promise<{ club: Club; message: string }> {
  const response = await api.post(`/admin/clubs/${clubId}/disable`)
  return response.data.data
}

/**
 * Enable a club (note: users must be manually re-added to groups)
 */
export async function enableClub(clubId: string): Promise<{ club: Club; message: string }> {
  const response = await api.post(`/admin/clubs/${clubId}/enable`)
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
  settings?: Record<string, any>
}): Promise<{ team: Team }> {
  const response = await api.post('/admin/teams', data)
  return response.data.data
}

/**
 * Get coaches for a team
 */
export async function getTeamCoaches(teamId: string): Promise<{ coaches: Coach[]; total: number }> {
  const response = await api.get(`/admin/teams/${teamId}/coaches`)
  return response.data.data
}

/**
 * Add a coach to a team
 */
export async function addTeamCoach(
  teamId: string,
  data: { firstName: string; lastName: string; coachEmail: string; coachPassword: string }
): Promise<{ coach: Coach; emailStatus: any; message: string }> {
  const response = await api.post(`/admin/teams/${teamId}/coaches`, data)
  return response.data.data
}

/**
 * Remove a coach from a team
 */
export async function removeTeamCoach(teamId: string, coachEmail: string): Promise<{ message: string }> {
  const response = await api.delete(`/admin/teams/${teamId}/coaches/${encodeURIComponent(coachEmail)}`)
  return response.data.data
}

/**
 * Activate a coach
 */
export async function activateCoach(teamId: string, coachEmail: string): Promise<{ coach: Coach; message: string }> {
  const response = await api.put(`/admin/teams/${teamId}/coaches/${encodeURIComponent(coachEmail)}/activate`)
  return response.data.data
}

/**
 * Deactivate a coach
 */
export async function deactivateCoach(teamId: string, coachEmail: string): Promise<{ coach: Coach; message: string }> {
  const response = await api.put(`/admin/teams/${teamId}/coaches/${encodeURIComponent(coachEmail)}/deactivate`)
  return response.data.data
}

/**
 * Update a team
 */
export async function updateTeam(
  teamId: string,
  data: Partial<Team>
): Promise<{ team: Team }> {
  const response = await api.put(`/admin/teams/${teamId}`, data)
  return response.data.data
}

/**
 * Activate a team
 */
export async function activateTeam(teamId: string): Promise<{ team: Team; message: string }> {
  const response = await api.put(`/admin/teams/${teamId}/activate`)
  return response.data.data
}

/**
 * Deactivate a team
 */
export async function deactivateTeam(teamId: string): Promise<{ team: Team; message: string }> {
  const response = await api.put(`/admin/teams/${teamId}/deactivate`)
  return response.data.data
}

export interface Player {
  playerId: string
  firstName: string
  lastName: string
  email?: string
  clubId: string
  teamId: string
  isActive: boolean
  verificationStatus?: "pending" | "verified"
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
  firstName: string
  lastName: string
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
 * Toggle player activation status (activate if inactive, deactivate if active)
 */
export async function togglePlayerActivation(playerId: string): Promise<void> {
  await api.delete(`/admin/players/${playerId}`)
}

/**
 * Activate a player
 */
export async function activatePlayer(playerId: string): Promise<{ player: Player }> {
  const response = await api.put(`/admin/players/${playerId}`, { isActive: true })
  return response.data.data
}

/**
 * Deactivate a player
 */
export async function deactivatePlayer(playerId: string): Promise<void> {
  await api.delete(`/admin/players/${playerId}`)
}

/**
 * Resend verification email to a player
 */
export async function invitePlayer(
  playerId: string,
  email: string
): Promise<{ success: boolean }> {
  const response = await api.post(`/admin/players/${playerId}/invite`, { email })
  return response.data.data
}

/**
 * Resend verification email to a coach
 */
export async function resendCoachVerification(
  teamId: string,
  coachId: string
): Promise<{ success: boolean; message: string }> {
  const response = await api.post(`/admin/teams/${teamId}/coaches/${coachId}/resend-verification`)
  return response.data.data
}

/**
 * Resend verification email to a club admin (app-admin only)
 */
export async function resendClubAdminVerification(
  clubId: string,
  adminId: string
): Promise<{ success: boolean; message: string }> {
  const response = await api.post(`/admin/clubs/${clubId}/admins/${adminId}/resend-verification`)
  return response.data.data
}

// ========================================================================
// CSV Upload helpers
// ========================================================================

export interface CsvValidationRow {
  row: number
  errors: string[]
  warnings: string[]
  // Flexible payload – concrete fields depend on type
  [key: string]: any
}

export interface CsvValidationResponse {
  valid: boolean
  preview: CsvValidationRow[]
  summary: {
    totalRows: number
    validRows: number
    invalidRows: number
  }
}

export interface CsvUploadResults {
  created: any[]
  skipped: any[]
  errors: { row: number; error: string }[]
  summary: {
    total: number
    created: number
    skipped: number
    errors: number
  }
}

export interface TeamCsvRow {
  row: number
  teamName: string
  teamId?: string
}

export interface PlayerCsvRow {
  row: number
  name: string
  email?: string
  teamId: string
  playerId?: string
}

export async function validateTeamsCsv(file: File): Promise<CsvValidationResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/admin/teams/validate-csv', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data.data
}

export async function uploadTeamsCsv(rows: TeamCsvRow[]): Promise<CsvUploadResults> {
  const response = await api.post('/admin/teams/upload-csv', { rows })
  return response.data.data
}

export async function validatePlayersCsv(file: File): Promise<CsvValidationResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/admin/players/validate-csv', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data.data
}

export async function uploadPlayersCsv(rows: PlayerCsvRow[]): Promise<CsvUploadResults> {
  const response = await api.post('/admin/players/upload-csv', { rows })
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

