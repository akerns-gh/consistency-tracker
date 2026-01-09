import React, { createContext, useContext, useState, ReactNode } from 'react'
import { useAuth } from './AuthContext'

interface ViewAsPlayerContextType {
  selectedUniqueLink: string | null
  setSelectedUniqueLink: (uniqueLink: string | null) => void
  isViewingAsPlayer: boolean
  clearViewAsPlayer: () => void
}

const ViewAsPlayerContext = createContext<ViewAsPlayerContextType | undefined>(undefined)

export const useViewAsPlayer = () => {
  const context = useContext(ViewAsPlayerContext)
  if (!context) {
    throw new Error('useViewAsPlayer must be used within ViewAsPlayerProvider')
  }
  return context
}

interface ViewAsPlayerProviderProps {
  children: ReactNode
}

export const ViewAsPlayerProvider: React.FC<ViewAsPlayerProviderProps> = ({ children }) => {
  const { isAdmin } = useAuth()
  const [selectedUniqueLink, setSelectedUniqueLink] = useState<string | null>(() => {
    // Load from localStorage if available
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('viewAsPlayerUniqueLink')
      return stored || null
    }
    return null
  })

  const handleSetSelectedUniqueLink = (uniqueLink: string | null) => {
    setSelectedUniqueLink(uniqueLink)
    if (uniqueLink) {
      localStorage.setItem('viewAsPlayerUniqueLink', uniqueLink)
    } else {
      localStorage.removeItem('viewAsPlayerUniqueLink')
    }
  }

  const clearViewAsPlayer = () => {
    setSelectedUniqueLink(null)
    localStorage.removeItem('viewAsPlayerUniqueLink')
  }

  const value: ViewAsPlayerContextType = {
    selectedUniqueLink,
    setSelectedUniqueLink: handleSetSelectedUniqueLink,
    isViewingAsPlayer: isAdmin && selectedUniqueLink !== null,
    clearViewAsPlayer,
  }

  return <ViewAsPlayerContext.Provider value={value}>{children}</ViewAsPlayerContext.Provider>
}

