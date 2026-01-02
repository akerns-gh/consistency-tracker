import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { verifyEmail, setPasswordAfterVerification } from '../services/api'
import { signIn } from 'aws-amplify/auth'
import { useAuth } from '../contexts/AuthContext'

export default function EmailVerificationView() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { login } = useAuth()
  const [status, setStatus] = useState<'loading' | 'success' | 'password-setup' | 'error'>('loading')
  const [message, setMessage] = useState<string>('')
  const [email, setEmail] = useState<string>('')
  const [token, setToken] = useState<string>('')
  const [password, setPassword] = useState<string>('')
  const [confirmPassword, setConfirmPassword] = useState<string>('')
  const [passwordError, setPasswordError] = useState<string>('')
  const [isSettingPassword, setIsSettingPassword] = useState(false)

  useEffect(() => {
    const tokenParam = searchParams.get('token')
    
    if (!tokenParam) {
      setStatus('error')
      setMessage('Invalid verification link. No token provided.')
      return
    }

    setToken(tokenParam)

    // Verify email with token
    verifyEmail(tokenParam)
      .then((response) => {
        if (response.success && response.data) {
          const needsPasswordSetup = response.data.needsPasswordSetup || false
          setEmail(response.data.email || '')
          
          if (needsPasswordSetup) {
            setStatus('password-setup')
            setMessage('Your email has been verified! Please set your password to continue.')
          } else {
            setStatus('success')
            setMessage(response.data.message || 'Your email has been verified successfully!')
          }
        } else {
          setStatus('error')
          setMessage(response.error || 'Verification failed. Please try again.')
        }
      })
      .catch((error) => {
        setStatus('error')
        const errorData = error.response?.data
        const errorMessage = errorData?.error?.message || errorData?.error || errorData?.message || error.message || 'An error occurred during verification'
        setMessage(errorMessage)
      })
  }, [searchParams])

  const validatePassword = (pwd: string): string => {
    if (pwd.length < 12) {
      return 'Password must be at least 12 characters long'
    }
    if (!/[A-Z]/.test(pwd)) {
      return 'Password must contain at least one uppercase letter'
    }
    if (!/[a-z]/.test(pwd)) {
      return 'Password must contain at least one lowercase letter'
    }
    if (!/[0-9]/.test(pwd)) {
      return 'Password must contain at least one number'
    }
    return ''
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError('')

    // Validate password
    const validationError = validatePassword(password)
    if (validationError) {
      setPasswordError(validationError)
      return
    }

    // Check passwords match
    if (password !== confirmPassword) {
      setPasswordError('Passwords do not match')
      return
    }

    setIsSettingPassword(true)

    try {
      // Set password via API
      const result = await setPasswordAfterVerification(token, password)
      
      if (result.success) {
        // Automatically log in with the new password
        try {
          const roleResult = await login(email, password)
          
          // Navigate based on role
          if (roleResult?.isAdmin) {
            navigate('/admin')
          } else {
            navigate('/player')
          }
        } catch (loginError: any) {
          console.error('Auto-login error:', loginError)
          // Password was set successfully, but auto-login failed
          // Redirect to login page with success message
          navigate('/login?passwordSet=true')
        }
      } else {
        setPasswordError(result.error?.message || result.error || 'Failed to set password. Please try again.')
        setIsSettingPassword(false)
      }
    } catch (error: any) {
      console.error('Error setting password:', error)
      setPasswordError(error.response?.data?.error?.message || error.message || 'An error occurred while setting your password.')
      setIsSettingPassword(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        {status === 'loading' && (
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Verifying Your Email</h1>
            <p className="text-gray-600">Please wait while we verify your email address...</p>
          </div>
        )}

        {status === 'password-setup' && (
          <div>
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
                <svg
                  className="w-8 h-8 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Email Verified!</h1>
              <p className="text-gray-600">{message}</p>
              {email && (
                <p className="text-sm text-gray-500 mt-2">Verified email: {email}</p>
              )}
            </div>

            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter your password"
                  required
                  disabled={isSettingPassword}
                />
                <p className="mt-1 text-xs text-gray-500">
                  Must be at least 12 characters with uppercase, lowercase, and a number
                </p>
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                  Confirm Password
                </label>
                <input
                  type="password"
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Confirm your password"
                  required
                  disabled={isSettingPassword}
                />
              </div>

              {passwordError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-600">{passwordError}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={isSettingPassword}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSettingPassword ? 'Setting Password...' : 'Set Password & Continue'}
              </button>
            </form>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
              <svg
                className="w-8 h-8 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Email Verified!</h1>
            <p className="text-gray-600 mb-6">{message}</p>
            {email && (
              <p className="text-sm text-gray-500 mb-6">Verified email: {email}</p>
            )}
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors font-medium"
            >
              Continue to Login
            </button>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
              <svg
                className="w-8 h-8 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Verification Failed</h1>
            <p className="text-gray-600 mb-4">{message}</p>
            {(message.includes('expired') || message.includes('Token expired')) && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
                <p className="text-sm text-yellow-800">
                  <strong>This verification link has expired.</strong> Please contact your administrator to request a new verification email.
                </p>
              </div>
            )}
            <div className="space-y-3">
              <button
                onClick={() => navigate('/login')}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors font-medium"
              >
                Go to Login
              </button>
              <p className="text-sm text-gray-500">
                If you need a new verification link, please contact your administrator.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

