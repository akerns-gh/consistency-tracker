import api from './api'

// Admin API functions will be implemented in Phase 4
// Placeholder for now

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
  const token = localStorage.getItem('authToken')
  const response = await api.get('/admin/clubs', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  return response.data.data
}

/**
 * Get teams in coach's club
 */
export async function getTeams(): Promise<{ teams: Team[]; total: number }> {
  const token = localStorage.getItem('authToken')
  const response = await api.get('/admin/teams', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  return response.data.data
}

