import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryErrorResetBoundary } from '@tanstack/react-query'
import { MainLayout } from '@/components/Layout'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ErrorFallback } from '@/components/ErrorFallback'
import { Toaster } from '@/components/Toaster'
import CalendarPage from '@/pages/CalendarPage'
import ProjectsPage from '@/pages/ProjectsPage'
import StatsPage from '@/pages/StatsPage'
import './App.css'

function App() {
  console.log('🚀 App component is rendering!')
  console.log('🎨 MainLayout background should be: linear-gradient(135deg, #1E3A8A 0%, #0055A4 35%, #3B82F6 70%, #EF4444 100%)')
  console.log('🔵 Header logo gradient should be: linear-gradient(135deg, #0055A4 0%, #EF4444 100%)')
  
  return (
    <BrowserRouter>
      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            fallback={(error, resetError) => {
              console.error('❌ Error caught by ErrorBoundary:', error)
              return (
                <ErrorFallback 
                  error={error} 
                  onReset={() => {
                    reset() // Reset React Query
                    resetError() // Reset ErrorBoundary
                  }} 
                />
              )
            }}
            onReset={reset}
          >
            <MainLayout>
              <Routes>
                <Route path="/" element={<Navigate to="/calendar" replace />} />
                <Route path="/calendar" element={<CalendarPage />} />
                <Route path="/projects" element={<ProjectsPage />} />
                <Route path="/stats" element={<StatsPage />} />
              </Routes>
            </MainLayout>
            <Toaster />
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </BrowserRouter>
  )
}

export default App
