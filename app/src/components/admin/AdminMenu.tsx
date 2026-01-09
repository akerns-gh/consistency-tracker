import { Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { useViewAsPlayer } from '../../contexts/ViewAsPlayerContext'

interface AdminMenuProps {
  isOpen: boolean
  onClose: () => void
}

export default function AdminMenu({ isOpen, onClose }: AdminMenuProps) {
  const { isAdmin } = useAuth()
  const { selectedUniqueLink, isViewingAsPlayer } = useViewAsPlayer()

  const getAppPagePath = (basePath: string) => {
    if (isViewingAsPlayer && selectedUniqueLink) {
      // For player pages, use uniqueLink format
      if (basePath.startsWith('/player')) {
        const subPath = basePath.replace('/player', '')
        return `/player/${selectedUniqueLink}${subPath || ''}`
      }
      return basePath
    }
    return basePath
  }

  const appPages = [
    { path: '/player', label: 'My Week', icon: '📅' },
    { path: '/player/progress', label: 'My Progress', icon: '📊' },
    { path: '/player/leaderboard', label: 'Leaderboard', icon: '🏆' },
    { path: '/player/reflection', label: 'Reflection', icon: '💭' },
    { path: '/player/resource-list', label: 'Resources', icon: '📚' },
    { path: '/help', label: 'Help & Support', icon: '❓' },
  ]

  const handleLinkClick = () => {
    onClose()
  }

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={onClose}
        />
      )}

      {/* Side Menu */}
      <div
        className={`fixed top-0 left-0 h-full w-64 bg-white shadow-lg z-50 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 h-full overflow-y-auto">
          {/* Close Button */}
          <button
            onClick={onClose}
            className="mb-6 text-gray-500 hover:text-gray-700"
            aria-label="Close menu"
          >
            ✕
          </button>

          {/* App Pages Section */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">App Pages</h3>
            <nav className="space-y-1">
              {appPages.map((page) => {
                const path = getAppPagePath(page.path)
                // Disable all player pages except Help for admins until they select a player
                const isDisabled = isAdmin && !isViewingAsPlayer && page.path !== '/help' && page.path.startsWith('/player')
                
                if (isDisabled) {
                  return (
                    <div
                      key={page.path}
                      className="flex items-center space-x-3 px-4 py-2 rounded-lg text-gray-400 cursor-not-allowed"
                      title="Use 'View As' button on Players page to view this page"
                    >
                      <span className="text-lg">{page.icon}</span>
                      <span className="text-gray-400">{page.label}</span>
                    </div>
                  )
                }
                
                return (
                  <Link
                    key={page.path}
                    to={path}
                    onClick={handleLinkClick}
                    className="flex items-center space-x-3 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <span className="text-lg">{page.icon}</span>
                    <span className="text-gray-700">{page.label}</span>
                  </Link>
                )
              })}
            </nav>
          </div>
        </div>
      </div>
    </>
  )
}

