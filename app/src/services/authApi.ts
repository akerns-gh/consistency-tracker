import api from './api'

/**
 * Check if user has admin role
 * This endpoint is used by the frontend to determine if admin navigation should be shown
 */
export async function checkAdminRole(): Promise<{ isAdmin: boolean }> {
  try {
    const token = localStorage.getItem('authToken')
    if (!token) {
      return { isAdmin: false }
    }
    
    const response = await api.get('/admin/check-role', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data.data
  } catch (error) {
    return { isAdmin: false }
  }
}

