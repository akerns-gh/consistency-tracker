import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listContent, getPlayer } from '../services/playerApi'
import NavigationMenu from '../components/navigation/NavigationMenu'
import Loading from '../components/ui/Loading'
import Card from '../components/ui/Card'

export default function ContentListView() {
  const [content, setContent] = useState<any[]>([])
  const [player, setPlayer] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const playerData = await getPlayer()
      setPlayer(playerData.player)
      
      const contentData = await listContent()
      setContent(contentData.content || [])
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load content')
    } finally {
      setLoading(false)
    }
  }

  const categories = ['all', ...new Set(content.map((c: any) => c.category).filter(Boolean))]

  const filteredContent = selectedCategory === 'all'
    ? content
    : content.filter((c: any) => c.category === selectedCategory)

  if (loading || !player) {
    return <Loading text="Loading resources..." />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Resources</h1>
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
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Category Filter */}
        <div className="mb-6 flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                selectedCategory === category
                  ? 'bg-primary text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>

        {error ? (
          <div className="text-center text-red-600">{error}</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredContent.map((page: any) => (
              <Link
                key={page.pageId}
                to={`/player/content-page/${page.slug}`}
                className="block"
              >
                <Card className="h-full hover:shadow-lg transition-shadow">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">
                    {page.title}
                  </h3>
                  {page.category && (
                    <p className="text-sm text-gray-600 mb-2">Category: {page.category}</p>
                  )}
                  {page.scope && (
                    <span className={`inline-block text-xs px-2 py-1 rounded mb-2 ${
                      page.scope === 'club' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {page.scope}
                    </span>
                  )}
                  {page.lastUpdated && (
                    <p className="text-xs text-gray-500">
                      Updated: {new Date(page.lastUpdated).toLocaleDateString()}
                    </p>
                  )}
                </Card>
              </Link>
            ))}
          </div>
        )}

        {filteredContent.length === 0 && !loading && (
          <div className="text-center text-gray-600 py-12">
            <p>No content available in this category.</p>
          </div>
        )}
      </main>
    </div>
  )
}

