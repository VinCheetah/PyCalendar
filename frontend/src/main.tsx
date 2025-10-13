import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import './index.css'
import './debug.css'
import App from './App.tsx'

console.log('🎯 main.tsx is loading...')
console.log('🎨 DEBUG CSS loaded for visual verification')
console.log('🇫🇷 French colors: #1E3A8A → #0055A4 → #3B82F6 → #EF4444')

// Configuration React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,  // Ne pas refetch au focus
      retry: 1,                      // 1 seul retry en cas d'erreur
      staleTime: 5 * 60 * 1000,     // 5 minutes avant de considérer stale
    },
  },
})

console.log('✅ QueryClient created')

const rootElement = document.getElementById('root')
console.log('📍 Root element:', rootElement)

if (!rootElement) {
  console.error('❌ Root element not found!')
  throw new Error('Root element not found')
}

console.log('🔧 Creating React root...')

createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </StrictMode>,
)

console.log('✨ React app rendered!')
