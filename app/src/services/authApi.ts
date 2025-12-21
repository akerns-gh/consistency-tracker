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
      console.warn('No auth token available for role check')
      return { isAdmin: false, isAppAdmin: false }
    }
    
    const response = await api.get('/admin/check-role', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    console.log('Role check response:', JSON.stringify(response.data, null, 2))
    const result = response.data.data
    console.log('Role check result - isAdmin:', result.isAdmin, 'isAppAdmin:', result.isAppAdmin)
    return result
  } catch (error: any) {
    console.error('Error checking admin role:', error)
    console.error('Error details:', error.response?.data || error.message)
    return { isAdmin: false, isAppAdmin: false }
  }
}

