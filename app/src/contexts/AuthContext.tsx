import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { signIn, signOut, getCurrentUser, confirmSignIn, fetchAuthSession, resetPassword as amplifyResetPassword, confirmResetPassword as amplifyConfirmResetPassword } from 'aws-amplify/auth'
import { checkAdminRole } from '../services/authApi'

interface User {
  email: string
  userId: string
  username?: string
}

interface AuthContextType {
  isAuthenticated: boolean
  user: User | null
  isAdmin: boolean
  isLoading: boolean
  requiresNewPassword: boolean
  login: (email: string, password: string) => Promise<void>
  changePassword: (newPassword: string) => Promise<void>
  logout: () => Promise<void>
  checkRole: () => Promise<void>
  resetPassword: (email: string) => Promise<void>
  confirmResetPassword: (email: string, confirmationCode: string, newPassword: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const [isAdmin, setIsAdmin] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [requiresNewPassword, setRequiresNewPassword] = useState(false)
  const [pendingEmail, setPendingEmail] = useState<string>('')

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const currentUser = await getCurrentUser()
      setUser({
        email: currentUser.signInDetails?.loginId || '',
        userId: currentUser.userId,
        username: currentUser.username,
      })
      setIsAuthenticated(true)
      
      // Check admin role
      await checkRole()
    } catch (error) {
      // User is not authenticated
      setIsAuthenticated(false)
      setUser(null)
      setIsAdmin(false)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const result = await signIn({ username: email, password })
      
      // Check if password change is required
      if (result.nextStep?.signInStep === 'CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED') {
        setRequiresNewPassword(true)
        setPendingEmail(email)
        // Don't throw error - let the UI handle the password change flow
        return
      }
      
      // Wait for session to be established - retry until we have a valid token
      let sessionEstablished = false
      let retries = 0
      const maxRetries = 10
      
      while (!sessionEstablished && retries < maxRetries) {
        try {
          const session = await fetchAuthSession()
          if (session.tokens?.idToken) {
            sessionEstablished = true
          } else {
            await new Promise(resolve => setTimeout(resolve, 200))
            retries++
          }
        } catch (error) {
          await new Promise(resolve => setTimeout(resolve, 200))
          retries++
        }
      }
      
      // Get user details after successful login
      const currentUser = await getCurrentUser()
      setUser({
        email: currentUser.signInDetails?.loginId || email,
        userId: currentUser.userId,
        username: currentUser.username,
      })
      setIsAuthenticated(true)
      setRequiresNewPassword(false)
      
      // Check admin role (this will fail gracefully if user is not admin)
      await checkRole()
    } catch (error: any) {
      const errorMessage = error.message || error.name || 'Login failed'
      throw new Error(errorMessage)
    }
  }

  const changePassword = async (newPassword: string) => {
    try {
      // Confirm sign-in with new password
      await confirmSignIn({ challengeResponse: newPassword })
      
      // Wait for session to be established - retry until we have a valid token
      let sessionEstablished = false
      let retries = 0
      const maxRetries = 10
      
      while (!sessionEstablished && retries < maxRetries) {
        try {
          const session = await fetchAuthSession()
          if (session.tokens?.idToken) {
            sessionEstablished = true
          } else {
            await new Promise(resolve => setTimeout(resolve, 200))
            retries++
          }
        } catch (error) {
          await new Promise(resolve => setTimeout(resolve, 200))
          retries++
        }
      }
      
      // Get user details
      const currentUser = await getCurrentUser()
      setUser({
        email: currentUser.signInDetails?.loginId || pendingEmail,
        userId: currentUser.userId,
        username: currentUser.username,
      })
      setIsAuthenticated(true)
      setRequiresNewPassword(false)
      setPendingEmail('')
      
      // Check admin role (this will fail gracefully if user is not admin)
      await checkRole()
    } catch (error: any) {
      const errorMessage = error.message || error.name || 'Failed to change password'
      throw new Error(errorMessage)
    }
  }

  const logout = async () => {
    try {
      await signOut()
      setIsAuthenticated(false)
      setUser(null)
      setIsAdmin(false)
    } catch (error) {
      console.error('Logout error:', error)
      // Clear state even if signOut fails
      setIsAuthenticated(false)
      setUser(null)
      setIsAdmin(false)
    }
  }

  const checkRole = async () => {
    try {
      const result = await checkAdminRole()
      setIsAdmin(result.isAdmin)
    } catch (error) {
      console.error('Error checking admin role:', error)
      setIsAdmin(false)
    }
  }

  const resetPassword = async (email: string) => {
    try {
      await amplifyResetPassword({ username: email })
    } catch (error: any) {
      const errorMessage = error.message || error.name || 'Failed to initiate password reset'
      throw new Error(errorMessage)
    }
  }

  const confirmResetPassword = async (email: string, confirmationCode: string, newPassword: string) => {
    try {
      await amplifyConfirmResetPassword({ username: email, confirmationCode, newPassword })
    } catch (error: any) {
      const errorMessage = error.message || error.name || 'Failed to confirm password reset'
      throw new Error(errorMessage)
    }
  }

  const value: AuthContextType = {
    isAuthenticated,
    user,
    isAdmin,
    isLoading,
    requiresNewPassword,
    login,
    changePassword,
    logout,
    checkRole,
    resetPassword,
    confirmResetPassword,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

