import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getContent, getPlayer } from '../services/playerApi'
import NavigationMenu from '../components/navigation/NavigationMenu'
import Loading from '../components/ui/Loading'
import Card from '../components/ui/Card'
import DOMPurify from 'dompurify'

export default function ContentPageView() {
  const { uniqueLink, slug } = useParams<{ uniqueLink: string; slug: string }>()
  const [content, setContent] = useState<any>(null)
  const [player, setPlayer] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    if (!uniqueLink || !slug) return
    
    loadData()
  }, [uniqueLink, slug])

  const loadData = async () => {
    try {
      setLoading(true)
      const playerData = await getPlayer(uniqueLink!)
      setPlayer(playerData.player)
      
      const contentData = await getContent(uniqueLink!, slug!)
      setContent(contentData)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load content')
    } finally {
      setLoading(false)
    }
  }

  if (loading || !player) {
    return <Loading text="Loading content..." />
  }

  if (error || !content) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-600 mb-4">{error || 'Content not found'}</p>
          <Link
            to={`/player/${uniqueLink}/resource-list`}
            className="text-primary hover:underline"
          >
            Back to Resources
          </Link>
        </div>
      </div>
    )
  }

  // Sanitize HTML content
  const sanitizedHtml = DOMPurify.sanitize(content.htmlContent || '')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{content.title}</h1>
            {content.scope && (
              <span className={`inline-block text-xs px-2 py-1 rounded mt-2 ${
                content.scope === 'club' 
                  ? 'bg-blue-100 text-blue-800' 
                  : 'bg-green-100 text-green-800'
              }`}>
                {content.scope}
              </span>
            )}
          </div>
          <button
            onClick={() => setMenuOpen(true)}
            className="text-gray-600 hover:text-gray-800"
            aria-label="Open menu"
          >
            ☰
          </button>
        </div>
      </header>

      <NavigationMenu player={player} isOpen={menuOpen} onClose={() => setMenuOpen(false)} />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        <div className="mb-4">
          <Link
            to={`/player/${uniqueLink}/resource-list`}
            className="text-primary hover:underline"
          >
            ← Back to Resources
          </Link>
        </div>

        <Card>
          {content.category && (
            <p className="text-sm text-gray-600 mb-4">Category: {content.category}</p>
          )}
          <div
            className="prose max-w-none"
            dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
          />
          {content.lastUpdated && (
            <p className="text-xs text-gray-500 mt-6">
              Last updated: {new Date(content.lastUpdated).toLocaleDateString()}
            </p>
          )}
        </Card>
      </main>
    </div>
  )
}

