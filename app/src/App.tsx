import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import PlayerView from './pages/PlayerView'
import MyProgressView from './pages/MyProgressView'
import LeaderboardView from './pages/LeaderboardView'
import ReflectionView from './pages/ReflectionView'
import ContentListView from './pages/ContentListView'
import ContentPageView from './pages/ContentPageView'
import ErrorBoundary from './components/ui/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <Routes>
          <Route path="/player/:uniqueLink" element={<PlayerView />} />
          <Route path="/player/:uniqueLink/progress" element={<MyProgressView />} />
          <Route path="/player/:uniqueLink/leaderboard" element={<LeaderboardView />} />
          <Route path="/player/:uniqueLink/reflection" element={<ReflectionView />} />
          <Route path="/player/:uniqueLink/resource-list" element={<ContentListView />} />
          <Route path="/player/:uniqueLink/content-page/:slug" element={<ContentPageView />} />
        </Routes>
      </Router>
    </ErrorBoundary>
  )
}

export default App

