import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from '@/components/layout/Navbar'
import Dashboard from '@/pages/Dashboard'
import JobMatchPage from '@/pages/JobMatchPage'
import ResumeRecommendPage from '@/pages/ResumeRecommendPage'
import MatchDetailPage from '@/pages/MatchDetailPage'
import GeneratorControlPage from '@/pages/GeneratorControlPage'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen" style={{ background: 'var(--background)' }}>
        <Navbar />
        <main className="container mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/jobs" element={<JobMatchPage />} />
            <Route path="/resumes" element={<ResumeRecommendPage />} />
            <Route path="/match/:resumeId/:jobId" element={<MatchDetailPage />} />
            <Route path="/generator" element={<GeneratorControlPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App