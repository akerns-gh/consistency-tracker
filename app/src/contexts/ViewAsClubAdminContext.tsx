import React, { createContext, useContext, useState, ReactNode } from 'react'
import { useAuth } from './AuthContext'

interface ViewAsClubAdminContextType {
  selectedClubId: string | null
  setSelectedClubId: (clubId: string | null) => void
  isViewingAsClubAdmin: boolean
  clearViewAsClubAdmin: () => void
}

const ViewAsClubAdminContext = createContext<ViewAsClubAdminContextType | undefined>(undefined)

export const useViewAsClubAdmin = () => {
  const context = useContext(ViewAsClubAdminContext)
  if (!context) {
    throw new Error('useViewAsClubAdmin must be used within ViewAsClubAdminProvider')
  }
  return context
}

interface ViewAsClubAdminProviderProps {
  children: ReactNode
}

export const ViewAsClubAdminProvider: React.FC<ViewAsClubAdminProviderProps> = ({ children }) => {
  const { isAppAdmin } = useAuth()
  const [selectedClubId, setSelectedClubId] = useState<string | null>(() => {
    // Load from localStorage if available
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('viewAsClubAdminClubId')
      return stored || null
    }
    return null
  })

  const handleSetSelectedClubId = (clubId: string | null) => {
    setSelectedClubId(clubId)
    if (clubId) {
      localStorage.setItem('viewAsClubAdminClubId', clubId)
    } else {
      localStorage.removeItem('viewAsClubAdminClubId')
    }
  }

  const clearViewAsClubAdmin = () => {
    setSelectedClubId(null)
    localStorage.removeItem('viewAsClubAdminClubId')
  }

  const value: ViewAsClubAdminContextType = {
    selectedClubId,
    setSelectedClubId: handleSetSelectedClubId,
    isViewingAsClubAdmin: isAppAdmin && selectedClubId !== null,
    clearViewAsClubAdmin,
  }

  return <ViewAsClubAdminContext.Provider value={value}>{children}</ViewAsClubAdminContext.Provider>
}

