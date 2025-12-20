import { fetchAuthSession } from 'aws-amplify/auth'
import api from './api'

/**
 * Get current JWT token from Amplify
 */
export async function getAuthToken(): Promise<string | null> {
  try {
    const session = await fetchAuthSession()
    return session.tokens?.idToken?.toString() || null
  } catch (error) {
    console.error('Error getting auth token:', error)
    return null
  }
}

/**
 * Check if user has admin role
 * This endpoint is used by the frontend to determine if admin navigation should be shown
 */
export async function checkAdminRole(): Promise<{ isAdmin: boolean; isAppAdmin?: boolean }> {
  try {
    const token = await getAuthToken()
    if (!token) {
      return { isAdmin: false, isAppAdmin: false }
    }
    
    const response = await api.get('/admin/check-role', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data.data
  } catch (error) {
    return { isAdmin: false, isAppAdmin: false }
  }
}

