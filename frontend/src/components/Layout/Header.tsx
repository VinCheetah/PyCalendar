import { Link, useLocation } from 'react-router-dom'
import { useState } from 'react'
import {
  CalendarDaysIcon,
  FolderIcon,
  ChartBarIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

export default function Header() {
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navigation = [
    {
      name: 'Calendrier',
      href: '/calendar',
      icon: CalendarDaysIcon,
      emoji: '📊'
    },
    {
      name: 'Projets',
      href: '/projects',
      icon: FolderIcon,
      emoji: '📁'
    },
    {
      name: 'Statistiques',
      href: '/stats',
      icon: ChartBarIcon,
      emoji: '📈'
    },
  ]

  const isActive = (href: string) => location.pathname === href

  return (
    <header 
      className="sticky top-0 z-50"
      style={{
        background: 'linear-gradient(135deg, #0055A4 0%, #1E3A8A 50%, #EF4444 100%)',
        boxShadow: '0 8px 32px rgba(0, 85, 164, 0.3)',
        borderBottom: '2px solid rgba(255, 255, 255, 0.1)'
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-6 border-b border-white/10">
          <div className="flex items-center justify-between">
            <Link 
              to="/calendar" 
              className="flex items-center space-x-4 group"
            >
              <div 
                className="rounded-2xl p-4 shadow-2xl transform transition-all duration-300 group-hover:scale-110 group-hover:rotate-6"
                style={{
                  background: 'rgba(255, 255, 255, 0.2)',
                  backdropFilter: 'blur(12px)',
                  WebkitBackdropFilter: 'blur(12px)',
                  border: '2px solid rgba(255, 255, 255, 0.3)',
                  boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)'
                }}
              >
                <CalendarDaysIcon className="h-10 w-10 text-white" />
              </div>
              <div>
                <h1 
                  className="text-4xl font-extrabold tracking-tight"
                  style={{
                    color: 'white',
                    textShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
                    letterSpacing: '-1px'
                  }}
                >
                  📅 PyCalendar
                </h1>
                <p 
                  className="text-sm mt-1"
                  style={{
                    color: 'rgba(255, 255, 255, 0.9)',
                    fontWeight: 500
                  }}
                >
                  Système de création de calendriers sportifs
                </p>
              </div>
            </Link>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-xl"
              style={{
                background: 'rgba(255, 255, 255, 0.2)',
                border: '1px solid rgba(255, 255, 255, 0.3)'
              }}
            >
              {mobileMenuOpen ? (
                <XMarkIcon className="h-6 w-6 text-white" />
              ) : (
                <Bars3Icon className="h-6 w-6 text-white" />
              )}
            </button>
          </div>
        </div>

        <nav 
          className="hidden md:flex md:gap-2 md:pt-0"
          style={{
            marginBottom: '-2px'
          }}
        >
          {navigation.map((item) => {
            const active = isActive(item.href)
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className="group relative"
                style={{
                  padding: '1rem 1.5rem',
                  background: 'transparent',
                  color: active ? 'white' : 'rgba(255, 255, 255, 0.7)',
                  fontWeight: 600,
                  fontSize: '0.9375rem',
                  borderBottom: '3px solid transparent',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
                onMouseEnter={(e) => {
                  if (!active) {
                    e.currentTarget.style.color = 'white'
                    e.currentTarget.style.background = 'linear-gradient(to bottom, transparent 0%, rgba(255, 255, 255, 0.1) 100%)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!active) {
                    e.currentTarget.style.color = 'rgba(255, 255, 255, 0.7)'
                    e.currentTarget.style.background = 'transparent'
                  }
                }}
              >
                <span style={{ fontSize: '1.25rem' }}>{item.emoji}</span>
                <span>{item.name}</span>
                
                <div
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: '50%',
                    transform: active ? 'translateX(-50%) scaleX(1)' : 'translateX(-50%) scaleX(0)',
                    width: '80%',
                    height: '3px',
                    background: 'linear-gradient(90deg, #FFFFFF 0%, #10B981 50%, #FFFFFF 100%)',
                    transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    borderRadius: '3px 3px 0 0'
                  }}
                />
              </Link>
            )
          })}
        </nav>

        {mobileMenuOpen && (
          <nav className="md:hidden py-4 border-t border-white/10">
            {navigation.map((item) => {
              const Icon = item.icon
              const active = isActive(item.href)
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center space-x-3 px-4 py-3 rounded-xl mb-2"
                  style={{
                    background: active ? 'rgba(255, 255, 255, 0.2)' : 'transparent',
                    color: 'white',
                    border: active ? '1px solid rgba(255, 255, 255, 0.3)' : '1px solid transparent'
                  }}
                >
                  <Icon className="h-6 w-6" />
                  <span className="font-semibold">{item.name}</span>
                </Link>
              )
            })}
          </nav>
        )}
      </div>
    </header>
  )
}
