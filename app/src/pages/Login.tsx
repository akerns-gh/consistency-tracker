import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import Button from '../components/ui/Button'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showResetPassword, setShowResetPassword] = useState(false)
  const [resetCode, setResetCode] = useState<string | null>(null)
  const [resetEmail, setResetEmail] = useState('')
  const [codeSent, setCodeSent] = useState(false)
  const { login, changePassword, requiresNewPassword, isAdmin, resetPassword, confirmResetPassword } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Client-side validation
    if (!email.trim()) {
      setError('Please enter your email address')
      return
    }

    // Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email.trim())) {
      setError('Please enter a valid email address')
      return
    }

    if (!password) {
      setError('Please enter your password')
      return
    }

    setIsLoading(true)

    try {
      await login(email.trim(), password)
      // If requiresNewPassword is true, don't navigate - show password change form
      if (!requiresNewPassword) {
        // Wait a moment for role check to complete, then navigate based on role
        setTimeout(() => {
          if (isAdmin) {
            navigate('/admin')
          } else {
            navigate('/player')
          }
        }, 300)
      }
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your email and password.')
      setIsLoading(false)
    }
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validate passwords match
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    // Validate password requirements (12+ chars, uppercase, lowercase, number)
    if (newPassword.length < 12) {
      setError('Password must be at least 12 characters long')
      return
    }

    if (!/[a-z]/.test(newPassword)) {
      setError('Password must contain at least one lowercase letter')
      return
    }

    if (!/[A-Z]/.test(newPassword)) {
      setError('Password must contain at least one uppercase letter')
      return
    }

    if (!/[0-9]/.test(newPassword)) {
      setError('Password must contain at least one number')
      return
    }

    setIsLoading(true)

    try {
      await changePassword(newPassword)
      // After password change, navigate based on role
      setTimeout(() => {
        if (isAdmin) {
          navigate('/admin')
        } else {
          navigate('/player')
        }
      }, 300)
    } catch (err: any) {
      setError(err.message || 'Failed to change password. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    if (!resetEmail.trim()) {
      setError('Please enter your email address')
      return
    }

    // Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(resetEmail.trim())) {
      setError('Please enter a valid email address')
      return
    }

    setIsLoading(true)
    try {
      await resetPassword(resetEmail)
      setError('')
      // After successfully sending code, show code entry form
      setCodeSent(true)
      setResetCode('')
    } catch (err: any) {
      setError(err.message || 'Failed to send password reset code. Please check your email address.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleConfirmResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validate passwords match
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    // Validate password requirements
    if (newPassword.length < 12) {
      setError('Password must be at least 12 characters long')
      return
    }

    if (!/[a-z]/.test(newPassword)) {
      setError('Password must contain at least one lowercase letter')
      return
    }

    if (!/[A-Z]/.test(newPassword)) {
      setError('Password must contain at least one uppercase letter')
      return
    }

    if (!/[0-9]/.test(newPassword)) {
      setError('Password must contain at least one number')
      return
    }

    if (!resetCode || resetCode.trim() === '') {
      setError('Please enter the verification code from your email')
      return
    }

    setIsLoading(true)

    try {
      await confirmResetPassword(resetEmail, resetCode, newPassword)
      // Success - return to login form
      alert('Password reset successful! Please log in with your new password.')
      setShowResetPassword(false)
      setResetEmail('')
      setResetCode(null)
      setNewPassword('')
      setConfirmPassword('')
      setCodeSent(false)
    } catch (err: any) {
      setError(err.message || 'Failed to reset password. Please check your code and try again.')
    } finally {
      setIsLoading(false)
    }
  }

  // Show password change form if required
  if (requiresNewPassword) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div>
            <div className="text-center">
              <h1 className="text-4xl font-bold" style={{ color: 'rgb(150, 200, 85)' }}>
                TRUE
              </h1>
              <h2 className="text-2xl font-semibold text-gray-800">LACROSSE</h2>
            </div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              Change Password
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              Please set a new password for your account
            </p>
          </div>
          <form className="mt-8 space-y-6" onSubmit={handlePasswordChange}>
            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-800">{error}</div>
              </div>
            )}
            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <label htmlFor="newPassword" className="sr-only">
                  New Password
                </label>
                <input
                  id="newPassword"
                  name="newPassword"
                  type="password"
                  autoComplete="new-password"
                  required
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                  placeholder="New Password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="confirmPassword" className="sr-only">
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  required
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                  placeholder="Confirm Password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
            </div>

            <div className="text-sm text-gray-600">
              <p>Password requirements:</p>
              <ul className="list-disc list-inside mt-1 space-y-1">
                <li>At least 12 characters</li>
                <li>At least one uppercase letter</li>
                <li>At least one lowercase letter</li>
                <li>At least one number</li>
              </ul>
            </div>

            <div>
              <Button
                type="submit"
                disabled={isLoading}
                className="w-full"
                style={{ backgroundColor: 'rgb(150, 200, 85)' }}
              >
                {isLoading ? 'Changing password...' : 'Change Password'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    )
  }

  // Show password reset form
  if (showResetPassword) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div>
            <div className="text-center">
              <h1 className="text-4xl font-bold" style={{ color: 'rgb(150, 200, 85)' }}>
                TRUE
              </h1>
              <h2 className="text-2xl font-semibold text-gray-800">LACROSSE</h2>
            </div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              Reset Password
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              {codeSent ? 'Enter the verification code and your new password' : 'Enter your email to receive a reset code'}
            </p>
          </div>
          
          {!codeSent ? (
            <form className="mt-8 space-y-6" onSubmit={handleForgotPassword}>
              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <div className="text-sm text-red-800">{error}</div>
                </div>
              )}
              {!error && (
                <div className="rounded-md bg-blue-50 p-4">
                  <div className="text-sm text-blue-800">
                    Password reset code will be sent to your email address.
                  </div>
                </div>
              )}
              <div className="rounded-md shadow-sm">
                <div>
                  <label htmlFor="resetEmail" className="sr-only">
                    Email address
                  </label>
                  <input
                    id="resetEmail"
                    name="resetEmail"
                    type="email"
                    autoComplete="email"
                    required
                    className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                    placeholder="Email address"
                    value={resetEmail}
                    onChange={(e) => setResetEmail(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full"
                  style={{ backgroundColor: 'rgb(150, 200, 85)' }}
                >
                  {isLoading ? 'Sending code...' : 'Send Reset Code'}
                </Button>
              </div>
              
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setShowResetPassword(false)
                    setError('')
                    setResetEmail('')
                    setCodeSent(false)
                    setResetCode(null)
                  }}
                  className="text-sm font-medium"
                  style={{ color: 'rgb(150, 200, 85)' }}
                >
                  Back to login
                </button>
              </div>
            </form>
          ) : (
            <form className="mt-8 space-y-6" onSubmit={handleConfirmResetPassword}>
              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <div className="text-sm text-red-800">{error}</div>
                </div>
              )}
              <div className="rounded-md shadow-sm -space-y-px">
                <div>
                  <label htmlFor="resetCode" className="sr-only">
                    Verification Code
                  </label>
                  <input
                    id="resetCode"
                    name="resetCode"
                    type="text"
                    required
                    className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                    placeholder="Verification Code"
                    value={resetCode || ''}
                    onChange={(e) => setResetCode(e.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="newPassword" className="sr-only">
                    New Password
                  </label>
                  <input
                    id="newPassword"
                    name="newPassword"
                    type="password"
                    autoComplete="new-password"
                    required
                    className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                    placeholder="New Password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="confirmPassword" className="sr-only">
                    Confirm Password
                  </label>
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    autoComplete="new-password"
                    required
                    className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                    placeholder="Confirm Password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />
                </div>
              </div>

              <div className="text-sm text-gray-600">
                <p>Password requirements:</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>At least 12 characters</li>
                  <li>At least one uppercase letter</li>
                  <li>At least one lowercase letter</li>
                  <li>At least one number</li>
                </ul>
              </div>

              <div>
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full"
                  style={{ backgroundColor: 'rgb(150, 200, 85)' }}
                >
                  {isLoading ? 'Resetting password...' : 'Reset Password'}
                </Button>
              </div>
              
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setResetCode(null)
                    setNewPassword('')
                    setConfirmPassword('')
                    setError('')
                    setCodeSent(false)
                  }}
                  className="text-sm font-medium"
                  style={{ color: 'rgb(150, 200, 85)' }}
                >
                  Resend code
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    )
  }

  // Main login form
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="text-center">
            <h1 className="text-4xl font-bold" style={{ color: 'rgb(150, 200, 85)' }}>
              TRUE
            </h1>
            <h2 className="text-2xl font-semibold text-gray-800">LACROSSE</h2>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign In
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sign in to access your account
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-sm">
              <a
                href="#"
                className="font-medium"
                style={{ color: 'rgb(150, 200, 85)' }}
                onClick={(e) => {
                  e.preventDefault()
                  setShowResetPassword(true)
                }}
              >
                Forgot your password?
              </a>
            </div>
          </div>

          <div>
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full"
              style={{ backgroundColor: 'rgb(150, 200, 85)' }}
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </Button>
          </div>

          <div className="text-sm text-center text-gray-600">
            <p>
              First time logging in? Check your email for your temporary password.
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}

