import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { getPlayer } from '../services/playerApi'
import NavBar from '../components/admin/NavBar'
import AdminMenu from '../components/admin/AdminMenu'
import { AdminTab } from '../components/admin/TabNavigation'
import NavigationMenu from '../components/navigation/NavigationMenu'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Loading from '../components/ui/Loading'

type HelpSection = 
  | 'overview'
  | 'csv-teams'
  | 'csv-players'
  | 'teams'
  | 'players'
  | 'activities'
  | 'content'

export default function HelpView() {
  const { isAdmin } = useAuth()
  const navigate = useNavigate()
  const [activeSection, setActiveSection] = useState<HelpSection>('overview')
  const [menuOpen, setMenuOpen] = useState(false)
  const [player, setPlayer] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Only load player data if user is not admin (for player navigation)
    if (!isAdmin) {
      loadPlayerData()
    } else {
      setLoading(false)
    }
  }, [isAdmin])

  const loadPlayerData = async () => {
    try {
      const playerData = await getPlayer()
      setPlayer(playerData.player)
    } catch (err) {
      console.error('Failed to load player data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAdminTabChange = (tab: AdminTab) => {
    // Navigate to admin dashboard with the selected tab
    navigate('/admin')
    // Note: The AdminDashboard component will handle setting the active tab
    // This is a limitation - we can't directly set the tab from here
    // but at least we navigate them back to the admin dashboard
  }

  const sections: { id: HelpSection; label: string; icon: string }[] = [
    { id: 'overview', label: 'Overview', icon: '📖' },
    { id: 'csv-teams', label: 'CSV Upload: Teams', icon: '📤' },
    { id: 'csv-players', label: 'CSV Upload: Players', icon: '📤' },
    { id: 'teams', label: 'Team Management', icon: '🏆' },
    { id: 'players', label: 'Player Management', icon: '👥' },
    { id: 'activities', label: 'Activities', icon: '🏃' },
    { id: 'content', label: 'Content Management', icon: '📄' },
  ]

  const renderContent = () => {
    switch (activeSection) {
      case 'overview':
        return <OverviewSection onNavigate={setActiveSection} />
      case 'csv-teams':
        return <CsvTeamsSection />
      case 'csv-players':
        return <CsvPlayersSection />
      case 'teams':
        return <TeamsSection />
      case 'players':
        return <PlayersSection />
      case 'activities':
        return <ActivitiesSection />
      case 'content':
        return <ContentSection />
      default:
        return <OverviewSection onNavigate={setActiveSection} />
    }
  }

  if (loading) {
    return <Loading text="Loading..." />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with Navigation */}
      {isAdmin ? (
        <>
          <NavBar onMenuClick={() => setMenuOpen(true)} />
          <AdminMenu
            isOpen={menuOpen}
            onClose={() => setMenuOpen(false)}
            activeTab="overview"
            onTabChange={handleAdminTabChange}
          />
        </>
      ) : (
        <>
          <header className="bg-white shadow-sm">
            <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-800">Help & Support</h1>
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
          {player && (
            <NavigationMenu player={player} isOpen={menuOpen} onClose={() => setMenuOpen(false)} />
          )}
        </>
      )}

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Help & Support</h1>
          <p className="text-gray-600">Find answers to common questions and learn how to use the system</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-1">
            <Card>
              <nav className="space-y-1">
                {sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors text-left ${
                      activeSection === section.id
                        ? 'bg-primary bg-opacity-10 text-primary font-medium'
                        : 'hover:bg-gray-100 text-gray-700'
                    }`}
                  >
                    <span className="text-lg">{section.icon}</span>
                    <span>{section.label}</span>
                  </button>
                ))}
              </nav>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <Card>{renderContent()}</Card>
          </div>
        </div>
      </div>
    </div>
  )
}

interface OverviewSectionProps {
  onNavigate: (section: HelpSection) => void
}

function OverviewSection({ onNavigate }: OverviewSectionProps) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Welcome to Help & Support</h2>
      <p className="text-gray-600">
        This help center provides documentation and guides for using the Consistency Tracker application.
        Use the navigation menu on the left to find information about specific features.
      </p>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Quick Links</h3>
        <ul className="space-y-2 text-gray-600">
          <li>
            <button
              onClick={() => onNavigate('csv-teams')}
              className="text-primary hover:text-primary-dark hover:underline font-semibold text-left"
            >
              CSV Upload:
            </button>
            <span className="ml-1">Learn how to bulk import teams and players using CSV files</span>
          </li>
          <li>
            <button
              onClick={() => onNavigate('teams')}
              className="text-primary hover:text-primary-dark hover:underline font-semibold text-left"
            >
              Team Management:
            </button>
            <span className="ml-1">Create and manage teams, assign coaches</span>
          </li>
          <li>
            <button
              onClick={() => onNavigate('players')}
              className="text-primary hover:text-primary-dark hover:underline font-semibold text-left"
            >
              Player Management:
            </button>
            <span className="ml-1">Add players, send invitations, track progress</span>
          </li>
          <li>
            <button
              onClick={() => onNavigate('activities')}
              className="text-primary hover:text-primary-dark hover:underline font-semibold text-left"
            >
              Activities:
            </button>
            <span className="ml-1">Configure activities for tracking consistency</span>
          </li>
          <li>
            <button
              onClick={() => onNavigate('content')}
              className="text-primary hover:text-primary-dark hover:underline font-semibold text-left"
            >
              Content Management:
            </button>
            <span className="ml-1">Create and manage content pages for players</span>
          </li>
        </ul>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-800 mb-2">Need Additional Help?</h4>
        <p className="text-blue-700 text-sm">
          If you can't find the answer you're looking for, please contact your system administrator
          or refer to the system documentation.
        </p>
      </div>
    </div>
  )
}

function CsvTeamsSection() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">CSV Upload: Teams</h2>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Prerequisites</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>Must be logged in as a club-admin (your club is automatically assigned)</li>
          <li>No other prerequisites required</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">File Requirements</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>File format: CSV (.csv)</li>
          <li>Maximum file size: 5MB</li>
          <li>Maximum rows: 1000 per upload</li>
          <li>Encoding: UTF-8</li>
          <li>First row must be a header row with column names</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">CSV Format</h3>
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <h4 className="font-semibold text-gray-800 mb-2">Required Columns:</h4>
          <ul className="list-disc list-inside space-y-1 text-gray-600 mb-4">
            <li><code className="bg-white px-2 py-1 rounded">teamName</code> - Team name (required)</li>
          </ul>
          <h4 className="font-semibold text-gray-800 mb-2">Optional Columns:</h4>
          <ul className="list-disc list-inside space-y-1 text-gray-600">
            <li><code className="bg-white px-2 py-1 rounded">teamId</code> - If provided, used for duplicate detection</li>
          </ul>
        </div>

        <h4 className="font-semibold text-gray-800 mb-2">Example CSV:</h4>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
{`teamName,teamId
2028 Boys,
2029 Girls,
Varsity,
JV,`}
        </pre>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Validations</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>File must be valid CSV format with UTF-8 encoding</li>
          <li><code>teamName</code> column must be present and non-empty for each row</li>
          <li>Duplicate detection checks for existing teams by name (case-insensitive) or ID</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Duplicate Detection</h3>
        <p className="text-gray-600 mb-2">
          During upload, the system checks for duplicates:
        </p>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>If <code className="bg-gray-100 px-1 rounded">teamId</code> is provided: Checks if a team with that ID already exists in your club</li>
          <li>Always checks if a team with the same name (case-insensitive) already exists in your club</li>
          <li>Duplicate rows are skipped (not created) and reported in the upload results</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">What Gets Created</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>New team record with auto-generated <code className="bg-gray-100 px-1 rounded">teamId</code> (if not provided)</li>
          <li>Default settings: weekStartDay: "Monday", autoAdvanceWeek: false, scoringMethod: "points"</li>
          <li>Automatically creates Cognito group <code className="bg-gray-100 px-1 rounded">coach-{'{clubId}'}-{'{teamId}'}</code></li>
          <li>Current user automatically added to the coach group</li>
        </ul>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h4 className="font-semibold text-yellow-800 mb-2">Important Notes</h4>
        <ul className="list-disc list-inside space-y-1 text-yellow-700 text-sm">
          <li>Upload teams before players if you plan to reference teams by name in your players CSV</li>
          <li>Review skipped rows in upload results to understand what wasn't created</li>
          <li>To update existing teams, use the individual edit forms instead of CSV upload</li>
        </ul>
      </div>
    </div>
  )
}

function CsvPlayersSection() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">CSV Upload: Players</h2>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Prerequisites</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>Must be logged in as a club-admin</li>
          <li>
            <strong>Teams must exist before uploading players</strong>
            <ul className="list-disc list-inside ml-6 mt-1">
              <li>Players reference teams by <code className="bg-gray-100 px-1 rounded">teamId</code> or <code className="bg-gray-100 px-1 rounded">teamName</code></li>
              <li>If using <code className="bg-gray-100 px-1 rounded">teamName</code>, the team must already exist in your club</li>
              <li>If using <code className="bg-gray-100 px-1 rounded">teamId</code>, it must be a valid team ID that belongs to your club</li>
            </ul>
          </li>
          <li><strong>Recommended workflow:</strong> Upload teams CSV first, then upload players CSV</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">File Requirements</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>File format: CSV (.csv)</li>
          <li>Maximum file size: 5MB</li>
          <li>Maximum rows: 1000 per upload</li>
          <li>Encoding: UTF-8</li>
          <li>First row must be a header row with column names</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">CSV Format</h3>
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <h4 className="font-semibold text-gray-800 mb-2">Required Columns:</h4>
          <ul className="list-disc list-inside space-y-1 text-gray-600 mb-4">
            <li><code className="bg-white px-2 py-1 rounded">name</code> - Player's full name (required)</li>
            <li><code className="bg-white px-2 py-1 rounded">teamName</code> OR <code className="bg-white px-2 py-1 rounded">teamId</code> - One is required</li>
          </ul>
          <h4 className="font-semibold text-gray-800 mb-2">Optional Columns:</h4>
          <ul className="list-disc list-inside space-y-1 text-gray-600">
            <li><code className="bg-white px-2 py-1 rounded">email</code> - Player's email address (for invitation emails)</li>
            <li><code className="bg-white px-2 py-1 rounded">playerId</code> - If provided, used for duplicate detection</li>
          </ul>
        </div>

        <h4 className="font-semibold text-gray-800 mb-2">Example CSV (using teamName):</h4>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto mb-4">
{`name,email,teamName
John Doe,john.doe@example.com,2028 Boys
Jane Smith,jane.smith@example.com,2028 Boys
Bob Johnson,,2029 Girls`}
        </pre>

        <h4 className="font-semibold text-gray-800 mb-2">Example CSV (using teamId):</h4>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
{`name,email,teamId
John Doe,john.doe@example.com,abc-123-def-456
Jane Smith,jane.smith@example.com,abc-123-def-456`}
        </pre>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Validations</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>File must be valid CSV format with UTF-8 encoding</li>
          <li><code>name</code> column must be present and non-empty for each row</li>
          <li>Either <code className="bg-gray-100 px-1 rounded">teamId</code> or <code className="bg-gray-100 px-1 rounded">teamName</code> must be provided</li>
          <li>If <code className="bg-gray-100 px-1 rounded">teamId</code> provided: Verifies team exists and belongs to your club</li>
          <li>If <code className="bg-gray-100 px-1 rounded">teamName</code> provided: Looks up team by name (must exist in your club)</li>
          <li>If team not found or doesn't belong to your club: Validation error</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Duplicate Detection</h3>
        <p className="text-gray-600 mb-2">
          During upload, the system checks for duplicates:
        </p>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>If <code className="bg-gray-100 px-1 rounded">playerId</code> is provided: Checks if a player with that ID already exists in your club</li>
          <li>Always checks if a player with the same <code className="bg-gray-100 px-1 rounded">name</code> (case-insensitive) + <code className="bg-gray-100 px-1 rounded">teamId</code> combination already exists</li>
          <li>Duplicate rows are skipped (not created) and reported with reason in upload results</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">What Gets Created</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>New player record with auto-generated <code className="bg-gray-100 px-1 rounded">playerId</code> (if not provided)</li>
          <li>Auto-generated secure <code className="bg-gray-100 px-1 rounded">uniqueLink</code> (32-character URL-safe token)</li>
          <li>Player set to <code className="bg-gray-100 px-1 rounded">isActive: true</code></li>
          <li><code className="bg-gray-100 px-1 rounded">clubId</code> automatically set from your logged-in club</li>
          <li>If email is provided and valid: Invitation email is sent automatically</li>
        </ul>
      </div>

      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h4 className="font-semibold text-red-800 mb-2">Common Issues</h4>
        <div className="space-y-3 text-sm">
          <div>
            <strong className="text-red-800">"Team not found or access denied"</strong>
            <p className="text-red-700 mt-1">
              Solution: Ensure the team exists in your club before uploading players. Upload teams CSV first, or manually create teams.
              Verify <code className="bg-red-100 px-1 rounded">teamName</code> matches exactly (case-sensitive) or use <code className="bg-red-100 px-1 rounded">teamId</code> from the Teams list.
            </p>
          </div>
          <div>
            <strong className="text-red-800">"Either teamId or teamName is required"</strong>
            <p className="text-red-700 mt-1">
              Solution: Include either <code className="bg-red-100 px-1 rounded">teamId</code> or <code className="bg-red-100 px-1 rounded">teamName</code> column in your CSV. At least one must be present for each player row.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-800 mb-2">Best Practices</h4>
        <ul className="list-disc list-inside space-y-1 text-blue-700 text-sm">
          <li>Upload teams first, then players</li>
          <li>Use <code className="bg-blue-100 px-1 rounded">teamId</code> in players CSV for reliability (copy from Teams list after creation)</li>
          <li>Always validate before uploading to catch errors early</li>
          <li>Keep CSV files under 1000 rows per upload</li>
          <li>Review skipped rows in results to understand what wasn't created</li>
        </ul>
      </div>
    </div>
  )
}

function TeamsSection() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Team Management</h2>
      <p className="text-gray-600">
        Teams are organizational units within your club. Each team can have multiple coaches and players.
      </p>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Creating Teams</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>Use the "Create New Team" button to add teams individually</li>
          <li>Or use CSV upload to bulk import multiple teams at once</li>
          <li>Each team requires a unique name within your club</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Managing Coaches</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>Click "Manage Coaches" on any team to add or remove coaches</li>
          <li>Coaches need an email address and temporary password (minimum 12 characters)</li>
          <li>Coaches receive invitation emails with login credentials</li>
          <li>Each team automatically creates a Cognito group for coaches</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Team Settings</h3>
        <p className="text-gray-600">
          Teams have configurable settings including week start day, auto-advance week, and scoring method.
          These can be updated through the team edit form.
        </p>
      </div>
    </div>
  )
}

function PlayersSection() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Player Management</h2>
      <p className="text-gray-600">
        Players are the individuals who track their consistency activities. Each player belongs to a team.
      </p>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Adding Players</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>Use the "Add Player" button to create players individually</li>
          <li>Or use CSV upload to bulk import multiple players at once</li>
          <li>Each player must be assigned to a team</li>
          <li>Players receive a unique link for passwordless access</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Player Invitations</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>If a player has an email address, invitation emails are sent automatically upon creation</li>
          <li>You can also manually send invitations using the "Invite" button</li>
          <li>Invitation emails include the player's unique link for accessing their dashboard</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Player Status</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>Players can be activated or deactivated</li>
          <li>Deactivated players cannot access the system but their data is preserved</li>
          <li>Use the deactivate action to temporarily remove access without deleting data</li>
        </ul>
      </div>
    </div>
  )
}

function ActivitiesSection() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Activities</h2>
      <p className="text-gray-600">
        Activities are the habits and tasks that players track for consistency. Activities can be club-wide or team-specific.
      </p>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Creating Activities</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>Activities can be created at the club level (visible to all teams) or team level (specific to one team)</li>
          <li>Each activity has a name, description, frequency, and point value</li>
          <li>Activities can be activated or deactivated without deletion</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Activity Properties</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li><strong>Frequency:</strong> How often the activity should be completed (e.g., daily, 3x/week)</li>
          <li><strong>Point Value:</strong> Points awarded for completing the activity</li>
          <li><strong>Display Order:</strong> Controls the order activities appear in player views</li>
        </ul>
      </div>
    </div>
  )
}

function ContentSection() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Content Management</h2>
      <p className="text-gray-600">
        Content pages provide resources, guidance, and information to players. Content can be club-wide or team-specific.
      </p>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Creating Content</h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>Content can be created at the club level (visible to all teams) or team level (specific to one team)</li>
          <li>Each content page has a title, category, slug (URL-friendly identifier), and HTML content</li>
          <li>Content can be published or kept as draft</li>
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Content Categories</h3>
        <p className="text-gray-600">
          Common categories include training guidance, workout plans, nutrition tips, mental performance, and general resources.
        </p>
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">Content Editor</h3>
        <p className="text-gray-600">
          The content editor supports rich text formatting, images, and links. Images are uploaded to secure cloud storage
          and served via CDN for optimal performance.
        </p>
      </div>
    </div>
  )
}

