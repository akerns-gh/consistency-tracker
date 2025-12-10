import { useAuth } from '../../contexts/AuthContext'
import Button from '../ui/Button'

interface NavBarProps {
  onMenuClick: () => void
}

export default function NavBar({ onMenuClick }: NavBarProps) {
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
    window.location.href = '/admin/login'
  }

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={onMenuClick}
            className="text-gray-600 hover:text-gray-800"
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div>
            <h1 className="text-xl font-bold" style={{ color: 'rgb(150, 200, 85)' }}>
              TRUE LACROSSE
            </h1>
            <p className="text-xs text-gray-600">Admin Dashboard</p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          {user && (
            <span className="text-sm text-gray-600">{user.email}</span>
          )}
          <Button onClick={handleLogout} variant="outline" size="sm">
            Logout
          </Button>
        </div>
      </div>
    </nav>
  )
}

