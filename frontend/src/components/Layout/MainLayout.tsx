import type { ReactNode } from 'react'
import Header from './Header'

interface MainLayoutProps {
  children: ReactNode
}

/**
 * Layout principal de l'application.
 * 
 * Structure :
 * - Header fixe en haut avec backdrop blur
 * - Contenu principal scrollable avec gradient background
 * - Design moderne et professionnel
 * 
 * Utilisé pour wrapper toutes les pages de l'app.
 */
export function MainLayout({ children }: MainLayoutProps) {
  console.log('🏗️ MainLayout rendering with French gradient background')
  console.log('🎨 Background gradient: linear-gradient(135deg, #1E3A8A 0%, #0055A4 35%, #3B82F6 70%, #EF4444 100%)')
  
  return (
    <div 
      className="min-h-screen relative"
      style={{
        background: 'linear-gradient(135deg, #1E3A8A 0%, #0055A4 35%, #3B82F6 70%, #EF4444 100%)',
        position: 'relative'
      }}
      data-testid="main-layout-french-gradient"
    >
      <Header />
      <main className="relative z-10 animate-fade-in p-8">
        <div 
          className="max-w-7xl mx-auto"
          style={{
            background: 'white',
            borderRadius: '24px',
            padding: '3rem',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.3)'
          }}
          data-testid="main-content-white-card"
        >
          {children}
        </div>
      </main>
    </div>
  )
}
