import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import Navbar from '@/components/layout/Navbar'
import Dashboard from '@/pages/Dashboard'
import JobMatchPage from '@/pages/JobMatchPage'
import ResumeRecommendPage from '@/pages/ResumeRecommendPage'
import MatchDetailPage from '@/pages/MatchDetailPage'
import GeneratorControlPage from '@/pages/GeneratorControlPage'
import BatchControlPage from '@/pages/BatchControlPage'

function AnimatedRoutes() {
  const location = useLocation()
  return (
    <main className="container mx-auto px-4 py-6">
      <div key={location.pathname} className="page-enter">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs" element={<JobMatchPage />} />
          <Route path="/resumes" element={<ResumeRecommendPage />} />
          <Route path="/match/:resumeId/:jobId" element={<MatchDetailPage />} />
          <Route path="/generator" element={<GeneratorControlPage />} />
          <Route path="/batch" element={<BatchControlPage />} />
        </Routes>
      </div>
    </main>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen" style={{ background: 'var(--background)' }}>
        <Navbar />
        <AnimatedRoutes />
      </div>
    </BrowserRouter>
  )
}

export default App
