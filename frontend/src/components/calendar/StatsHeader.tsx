/**
 * StatsHeader Component - Dashboard statistics
 * Inspired by visualization stats-grid
 * 
 * Displays key metrics:
 * - Planned matches
 * - Unscheduled matches
 * - Weeks
 * - Pools
 * - Venues
 */

import { useMatches, useVenues } from '@/hooks'

interface StatsHeaderProps {
  projectId: number
}

export default function StatsHeader({ projectId }: StatsHeaderProps) {
  const { data: matches } = useMatches(projectId)
  const { data: venues } = useVenues(projectId)

  // Calculate stats
  const totalMatches = matches?.length ?? 0
  const plannedMatches = matches?.filter(m => m.semaine && m.horaire && m.gymnase).length ?? 0
  const unscheduledMatches = totalMatches - plannedMatches
  const totalWeeks = [...new Set(matches?.map(m => m.semaine).filter(Boolean))].length
  const totalPools = [...new Set(matches?.map(m => m.poule).filter(Boolean))].length
  const totalVenues = venues?.length ?? 0

  const stats = [
    { 
      label: 'Matchs planifiés', 
      value: plannedMatches, 
      icon: '✅',
      color: 'linear-gradient(135deg, #10B981, #059669)',
      textColor: '#10B981'
    },
    { 
      label: 'Non planifiés', 
      value: unscheduledMatches, 
      icon: '⚠️',
      color: 'linear-gradient(135deg, #F59E0B, #D97706)',
      textColor: '#F59E0B'
    },
    { 
      label: 'Semaines', 
      value: totalWeeks, 
      icon: '📅',
      color: 'linear-gradient(135deg, #0055A4, #1E3A8A)',
      textColor: '#0055A4'
    },
    { 
      label: 'Poules', 
      value: totalPools, 
      icon: '🎯',
      color: 'linear-gradient(135deg, #8B5CF6, #7C3AED)',
      textColor: '#8B5CF6'
    },
    { 
      label: 'Gymnases', 
      value: totalVenues, 
      icon: '🏢',
      color: 'linear-gradient(135deg, #EF4444, #DC2626)',
      textColor: '#EF4444'
    },
  ]

  return (
    <div style={{
      background: 'linear-gradient(135deg, #0055A4 0%, #1E3A8A 50%, #EF4444 100%)',
      borderRadius: '20px',
      padding: '2rem',
      marginBottom: '1.5rem',
      boxShadow: '0 20px 60px rgba(0, 85, 164, 0.3)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Decorative overlay */}
      <div style={{
        position: 'absolute',
        inset: 0,
        background: 'radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%)',
        pointerEvents: 'none'
      }} />

      {/* Title */}
      <div style={{ 
        position: 'relative', 
        zIndex: 1,
        marginBottom: '1.5rem' 
      }}>
        <h2 style={{
          fontSize: '1.875rem',
          fontWeight: 800,
          color: 'white',
          margin: 0,
          marginBottom: '0.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem'
        }}>
          📊 Tableau de Bord
        </h2>
        <p style={{
          fontSize: '1rem',
          color: 'rgba(255, 255, 255, 0.9)',
          margin: 0
        }}>
          Vue d'ensemble de votre projet PyCalendar
        </p>
      </div>

      {/* Stats Grid */}
      <div style={{
        position: 'relative',
        zIndex: 1,
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '1rem'
      }}>
        {stats.map((stat, idx) => (
          <div
            key={idx}
            style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
              borderRadius: '16px',
              padding: '1.25rem',
              textAlign: 'center',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              cursor: 'default'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px) scale(1.02)'
              e.currentTarget.style.boxShadow = '0 12px 40px rgba(0, 85, 164, 0.2)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0) scale(1)'
              e.currentTarget.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.1)'
            }}
          >
            {/* Icon */}
            <div style={{
              fontSize: '2rem',
              marginBottom: '0.5rem'
            }}>
              {stat.icon}
            </div>
            
            {/* Value */}
            <div style={{
              fontSize: '2.5rem',
              fontWeight: 800,
              background: stat.color,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              marginBottom: '0.25rem',
              lineHeight: 1
            }}>
              {stat.value}
            </div>
            
            {/* Label */}
            <div style={{
              fontSize: '0.875rem',
              color: '#64748B',
              fontWeight: 600
            }}>
              {stat.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
