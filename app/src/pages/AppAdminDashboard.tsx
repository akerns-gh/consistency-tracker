import { useState } from 'react'
import NavBar from '../components/admin/NavBar'
import ClubManagement from '../components/admin/clubs/ClubManagement'

export default function AppAdminDashboard() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar onMenuClick={() => setMenuOpen(true)} />
      
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Platform Administration</h1>
          <p className="text-gray-600 mt-2">Manage all clubs and platform settings</p>
        </div>
        
        <ClubManagement />
      </main>
    </div>
  )
}

