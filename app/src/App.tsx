import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ViewAsPlayerProvider } from './contexts/ViewAsPlayerContext'
import { ViewAsClubAdminProvider } from './contexts/ViewAsClubAdminContext'
import Login from './pages/Login'
import AdminDashboard from './pages/AdminDashboard'
import PlayerView from './pages/PlayerView'
import MyProgressView from './pages/MyProgressView'
import LeaderboardView from './pages/LeaderboardView'
import ReflectionView from './pages/ReflectionView'
import ContentListView from './pages/ContentListView'
import ContentPageView from './pages/ContentPageView'
import HelpView from './pages/HelpView'
import EmailVerificationView from './pages/EmailVerificationView'
import ProtectedRoute from './components/auth/ProtectedRoute'
import ErrorBoundary from './components/ui/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ViewAsPlayerProvider>
          <ViewAsClubAdminProvider>
            <Router>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/admin/login" element={<Login />} />
              <Route path="/verify-email" element={<EmailVerificationView />} />
              
              {/* Player routes with uniqueLink (for admin view-as) */}
              <Route
                path="/player/:uniqueLink"
                element={
                  <ProtectedRoute>
                    <PlayerView />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/player/:uniqueLink/progress"
                element={
                  <ProtectedRoute>
                    <MyProgressView />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/player/:uniqueLink/leaderboard"
                element={
                  <ProtectedRoute>
                    <LeaderboardView />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/player/:uniqueLink/reflection"
                element={
                  <ProtectedRoute>
                    <ReflectionView />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/player/:uniqueLink/resource-list"
                element={
                  <ProtectedRoute>
                    <ContentListView />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/player/:uniqueLink/content-page/:slug"
                element={
                  <ProtectedRoute>
                    <ContentPageView />
                  </ProtectedRoute>
                }
              />
              
              {/* Player routes (protected, no admin required) - JWT based */}
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
              <Route
                path="/help"
                element={
                  <ProtectedRoute>
                    <HelpView />
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
              
              {/* Catch-all route - redirect based on user role */}
              <Route
                path="*"
                element={
                  <ProtectedRoute>
                    <CatchAllRedirect />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </Router>
          </ViewAsClubAdminProvider>
        </ViewAsPlayerProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

// Catch-all redirect component
function CatchAllRedirect() {
  const { isAdmin } = useAuth()
  return <Navigate to={isAdmin ? "/admin" : "/player"} replace />
}

export default App

