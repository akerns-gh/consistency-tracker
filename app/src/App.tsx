import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import PlayerLogin from './pages/PlayerLogin'
import AdminLogin from './pages/AdminLogin'
import AdminDashboard from './pages/AdminDashboard'
import PlayerView from './pages/PlayerView'
import MyProgressView from './pages/MyProgressView'
import LeaderboardView from './pages/LeaderboardView'
import ReflectionView from './pages/ReflectionView'
import ContentListView from './pages/ContentListView'
import ContentPageView from './pages/ContentPageView'
import ProtectedRoute from './components/auth/ProtectedRoute'
import ErrorBoundary from './components/ui/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<PlayerLogin />} />
            <Route path="/admin/login" element={<AdminLogin />} />
            
            {/* Player routes (protected, no admin required) */}
            <Route
              path="/player"
              element={
                <ProtectedRoute>
                  <PlayerView />
                </ProtectedRoute>
              }
            />
            <Route
              path="/player/progress"
              element={
                <ProtectedRoute>
                  <MyProgressView />
                </ProtectedRoute>
              }
            />
            <Route
              path="/player/leaderboard"
              element={
                <ProtectedRoute>
                  <LeaderboardView />
                </ProtectedRoute>
              }
            />
            <Route
              path="/player/reflection"
              element={
                <ProtectedRoute>
                  <ReflectionView />
                </ProtectedRoute>
              }
            />
            <Route
              path="/player/resource-list"
              element={
                <ProtectedRoute>
                  <ContentListView />
                </ProtectedRoute>
              }
            />
            <Route
              path="/player/content-page/:slug"
              element={
                <ProtectedRoute>
                  <ContentPageView />
                </ProtectedRoute>
              }
            />
            
            {/* Admin routes (protected, admin required) */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute requireAdmin>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            
            {/* Redirect root to login */}
            <Route path="/" element={<Navigate to="/login" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App

