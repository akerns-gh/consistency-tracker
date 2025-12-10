import React from 'react'
import { Link } from 'react-router-dom'
import { Player } from '../../services/playerApi'
import { useAuth } from '../../contexts/AuthContext'

interface NavigationMenuProps {
  player: Player
  isOpen: boolean
  onClose: () => void
}

export default function NavigationMenu({ player, isOpen, onClose }: NavigationMenuProps) {
  const { isAdmin } = useAuth()
  
  const menuItems = [
    { path: '/player', label: 'My Week', icon: '📅' },
    { path: '/player/progress', label: 'My Progress', icon: '📊' },
    { path: '/player/leaderboard', label: 'Leaderboard', icon: '🏆' },
    { path: '/player/reflection', label: 'Reflection', icon: '💭' },
    { path: '/player/resource-list', label: 'Resources', icon: '📚' },
  ]

  // Add admin link if user is admin
  if (isAdmin) {
    menuItems.push({ path: '/admin', label: 'Admin Dashboard', icon: '⚙️' })
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
      >
        <div className="p-6">
          {/* Close Button */}
          <button
            onClick={onClose}
            className="mb-6 text-gray-500 hover:text-gray-700"
            aria-label="Close menu"
          >
            ✕
          </button>
          
          {/* Player Info */}
          <div className="mb-6 pb-6 border-b">
            <h2 className="text-xl font-bold text-gray-800">{player.name}</h2>
            {player.clubId && (
              <p className="text-sm text-gray-600 mt-1">Club: {player.clubId}</p>
            )}
            {player.teamId && (
              <p className="text-sm text-gray-600">Team: {player.teamId}</p>
            )}
          </div>
          
          {/* Menu Items */}
          <nav className="space-y-2">
            {menuItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={onClose}
                className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <span className="text-xl">{item.icon}</span>
                <span className="text-gray-700">{item.label}</span>
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </>
  )
}

