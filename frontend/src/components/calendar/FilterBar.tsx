/**
 * FilterBar Component - Inspired by visualization/main.html
 * 
 * Provides filtering controls for:
 * - Gender (Male, Female, All)
 * - Pool
 * - Venue
 * - Week
 * 
 * French design with badges and icons
 */

import { useMatches, useVenues } from '@/hooks'

export interface Filters {
  gender: '' | 'M' | 'F'
  pool: string
  venue: string
  week: number | null
}

interface FilterBarProps {
  projectId: number
  filters: Filters
  onFiltersChange: (filters: Filters) => void
}

export default function FilterBar({ projectId, filters, onFiltersChange }: FilterBarProps) {
  const { data: matches } = useMatches(projectId)
  const { data: venues } = useVenues(projectId)

  // Extract unique pools and weeks from matches
  const pools = [...new Set(matches?.map(m => m.poule).filter(Boolean) as string[])].sort()
  const weeks = [...new Set(matches?.map(m => m.semaine).filter(Boolean) as number[])].sort((a, b) => a - b)

  const handleGenderClick = (gender: '' | 'M' | 'F') => {
    onFiltersChange({ ...filters, gender })
  }

  const handlePoolChange = (pool: string) => {
    onFiltersChange({ ...filters, pool })
  }

  const handleVenueChange = (venue: string) => {
    onFiltersChange({ ...filters, venue })
  }

  const handleWeekChange = (week: number | null) => {
    onFiltersChange({ ...filters, week })
  }

  const handleReset = () => {
    onFiltersChange({ gender: '', pool: '', venue: '', week: null })
  }

  // Count active filters
  const activeFiltersCount = [
    filters.gender,
    filters.pool,
    filters.venue,
    filters.week !== null
  ].filter(Boolean).length

  return (
    <div style={{
      background: 'white',
      borderRadius: '16px',
      padding: '1.5rem',
      boxShadow: '0 4px 12px rgba(0, 85, 164, 0.1)',
      marginBottom: '1.5rem'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '1.25rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <h3 style={{
            fontSize: '1.125rem',
            fontWeight: 700,
            color: '#1E293B',
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            🔍 Filtres
          </h3>
          {activeFiltersCount > 0 && (
            <span style={{
              background: 'linear-gradient(135deg, #0055A4, #1E3A8A)',
              color: 'white',
              padding: '0.25rem 0.625rem',
              borderRadius: '12px',
              fontSize: '0.75rem',
              fontWeight: 700
            }}>
              {activeFiltersCount}
            </span>
          )}
        </div>
        <button
          onClick={handleReset}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 1rem',
            borderRadius: '10px',
            background: activeFiltersCount > 0 ? '#EF4444' : '#F1F5F9',
            color: activeFiltersCount > 0 ? 'white' : '#64748B',
            border: 'none',
            fontSize: '0.875rem',
            fontWeight: 600,
            cursor: activeFiltersCount > 0 ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s',
            opacity: activeFiltersCount > 0 ? 1 : 0.5
          }}
          disabled={activeFiltersCount === 0}
        >
          🔄 Réinitialiser
        </button>
      </div>

      {/* Filters Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem'
      }}>
        {/* Gender Filter */}
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: '#64748B',
            marginBottom: '0.5rem'
          }}>
            ⚧️ Genre
          </label>
          <div style={{
            display: 'flex',
            gap: '0.5rem'
          }}>
            <button
              onClick={() => handleGenderClick('')}
              style={{
                flex: 1,
                padding: '0.625rem',
                borderRadius: '10px',
                border: filters.gender === '' ? '2px solid #0055A4' : '2px solid #E2E8F0',
                background: filters.gender === '' ? '#EFF6FF' : 'white',
                color: filters.gender === '' ? '#0055A4' : '#64748B',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              Tous
            </button>
            <button
              onClick={() => handleGenderClick('M')}
              style={{
                flex: 1,
                padding: '0.625rem',
                borderRadius: '10px',
                border: filters.gender === 'M' ? '2px solid #3B82F6' : '2px solid #E2E8F0',
                background: filters.gender === 'M' ? '#DBEAFE' : 'white',
                color: filters.gender === 'M' ? '#1E40AF' : '#64748B',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              ♂ M
            </button>
            <button
              onClick={() => handleGenderClick('F')}
              style={{
                flex: 1,
                padding: '0.625rem',
                borderRadius: '10px',
                border: filters.gender === 'F' ? '2px solid #EC4899' : '2px solid #E2E8F0',
                background: filters.gender === 'F' ? '#FCE7F3' : 'white',
                color: filters.gender === 'F' ? '#BE185D' : '#64748B',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              ♀ F
            </button>
          </div>
        </div>

        {/* Pool Filter */}
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: '#64748B',
            marginBottom: '0.5rem'
          }}>
            🎯 Poule
          </label>
          <select
            value={filters.pool}
            onChange={(e) => handlePoolChange(e.target.value)}
            style={{
              width: '100%',
              padding: '0.625rem 0.75rem',
              borderRadius: '10px',
              border: filters.pool ? '2px solid #0055A4' : '2px solid #E2E8F0',
              background: filters.pool ? '#EFF6FF' : 'white',
              color: filters.pool ? '#0055A4' : '#1E293B',
              fontSize: '0.875rem',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            <option value="">Toutes les poules</option>
            {pools.map(pool => (
              <option key={pool} value={pool}>{pool}</option>
            ))}
          </select>
        </div>

        {/* Venue Filter */}
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: '#64748B',
            marginBottom: '0.5rem'
          }}>
            🏢 Gymnase
          </label>
          <select
            value={filters.venue}
            onChange={(e) => handleVenueChange(e.target.value)}
            style={{
              width: '100%',
              padding: '0.625rem 0.75rem',
              borderRadius: '10px',
              border: filters.venue ? '2px solid #0055A4' : '2px solid #E2E8F0',
              background: filters.venue ? '#EFF6FF' : 'white',
              color: filters.venue ? '#0055A4' : '#1E293B',
              fontSize: '0.875rem',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            <option value="">Tous les gymnases</option>
            {venues?.map(venue => (
              <option key={venue.id} value={venue.nom}>{venue.nom}</option>
            ))}
          </select>
        </div>

        {/* Week Filter */}
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: '#64748B',
            marginBottom: '0.5rem'
          }}>
            📅 Semaine
          </label>
          <select
            value={filters.week ?? ''}
            onChange={(e) => handleWeekChange(e.target.value ? parseInt(e.target.value) : null)}
            style={{
              width: '100%',
              padding: '0.625rem 0.75rem',
              borderRadius: '10px',
              border: filters.week !== null ? '2px solid #0055A4' : '2px solid #E2E8F0',
              background: filters.week !== null ? '#EFF6FF' : 'white',
              color: filters.week !== null ? '#0055A4' : '#1E293B',
              fontSize: '0.875rem',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            <option value="">Toutes les semaines</option>
            {weeks.map(week => (
              <option key={week} value={week}>Semaine {week}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}
