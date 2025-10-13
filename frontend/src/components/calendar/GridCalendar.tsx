/**
 * Grid Calendar Component - Google Calendar style layout
 * Inspired by visualization/calendar-grid-view.js
 * 
 * Features:
 * - Time slots as rows (8:00-22:00)
 * - Venues as columns
 * - Match blocks absolutely positioned by time
 * - French color scheme
 * - Week navigation
 */

import { useState, useMemo } from 'react'
import { ChevronLeftIcon, ChevronRightIcon, MapPinIcon } from '@heroicons/react/24/outline'
import { useMatches, useVenues } from '@/hooks'
import type { Match } from '@/types'

interface Filters {
  gender: '' | 'M' | 'F'
  pool: string
  venue: string
  week: number | null
}

interface GridCalendarProps {
  projectId: number
  semaineMin: number
  nbSemaines: number
  filters?: Filters
}

// Reference date: Thursday October 16, 2025 (Week 1)
const REFERENCE_DATE = new Date(2025, 9, 16)

// Time configuration
const START_HOUR = 8
const END_HOUR = 22
const SLOT_HEIGHT = 60 // pixels per hour
const MATCH_DURATION = 90 // minutes

export default function GridCalendar({ projectId, semaineMin, nbSemaines, filters }: GridCalendarProps) {
  const [currentWeek, setCurrentWeek] = useState(1)
  
  const { data: matches, isLoading: loadingMatches } = useMatches(projectId)
  const { data: venues, isLoading: loadingVenues } = useVenues(projectId)

  // Apply filters to matches
  const filteredMatches = useMemo(() => {
    if (!matches) return []
    
    let filtered = [...matches]
    
    // Gender filter
    if (filters?.gender) {
      filtered = filtered.filter(m => {
        const gender = m.equipe1_genre?.toUpperCase() || m.equipe2_genre?.toUpperCase()
        return gender === filters.gender
      })
    }
    
    // Pool filter
    if (filters?.pool) {
      filtered = filtered.filter(m => m.poule === filters.pool)
    }
    
    // Venue filter
    if (filters?.venue) {
      filtered = filtered.filter(m => m.gymnase === filters.venue)
    }
    
    // Week filter (overrides currentWeek)
    if (filters?.week !== null && filters?.week !== undefined) {
      filtered = filtered.filter(m => m.semaine === filters.week)
    }
    
    return filtered
  }, [matches, filters])

  // Filter matches for current week (if no week filter active)
  const weekMatches = useMemo(() => {
    if (filters?.week !== null && filters?.week !== undefined) {
      return filteredMatches.filter(m => m.horaire && m.gymnase)
    }
    return filteredMatches.filter(m => m.semaine === currentWeek && m.horaire && m.gymnase)
  }, [filteredMatches, currentWeek, filters])

  // Calculate Thursday date
  const currentThursday = useMemo(() => {
    const date = new Date(REFERENCE_DATE)
    date.setDate(date.getDate() + (currentWeek - 1) * 7)
    return date
  }, [currentWeek])

  // Generate time slots
  const timeSlots = useMemo(() => {
    const slots = []
    for (let hour = START_HOUR; hour <= END_HOUR; hour++) {
      slots.push(`${hour}:00`)
    }
    return slots
  }, [])

  // Calculate position for match block
  const calculatePosition = (horaire: string): { top: number; height: number } | null => {
    const [hours, minutes] = horaire.split(':').map(Number)
    if (isNaN(hours) || isNaN(minutes)) return null
    
    const startMinutes = (hours - START_HOUR) * 60 + minutes
    const top = (startMinutes / 60) * SLOT_HEIGHT
    const height = (MATCH_DURATION / 60) * SLOT_HEIGHT
    
    return { top, height }
  }

  // Group matches by venue
  const matchesByVenue = useMemo(() => {
    const grouped: Record<string, Match[]> = {}
    
    venues?.forEach(venue => {
      grouped[venue.nom] = weekMatches.filter(m => m.gymnase === venue.nom)
    })
    
    return grouped
  }, [venues, weekMatches])

  // Get gender color
  const getGenderColor = (match: Match): string => {
    const gender = match.equipe1_genre?.toLowerCase() === 'f' || 
                   match.equipe2_genre?.toLowerCase() === 'f' ? 'female' : 'male'
    return gender === 'female' ? '#EC4899' : '#3B82F6'
  }

  const handlePrevWeek = () => {
    if (currentWeek > 1) setCurrentWeek(currentWeek - 1)
  }

  const handleNextWeek = () => {
    if (currentWeek < nbSemaines) setCurrentWeek(currentWeek + 1)
  }

  if (loadingMatches || loadingVenues) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Chargement du calendrier...</div>
      </div>
    )
  }

  if (!venues || venues.length === 0) {
    return (
      <div className="p-6 bg-white rounded-lg shadow">
        <div className="text-center text-gray-600">Aucun gymnase disponible</div>
      </div>
    )
  }

  const gridHeight = (END_HOUR - START_HOUR + 1) * SLOT_HEIGHT

  return (
    <div style={{
      background: 'white',
      borderRadius: '16px',
      boxShadow: '0 10px 40px rgba(0, 85, 164, 0.15)',
      overflow: 'hidden'
    }}>
      {/* Header with week navigation - French gradient */}
      <div style={{
        background: 'linear-gradient(135deg, #0055A4 0%, #1E3A8A 100%)',
        padding: '2rem'
      }}>
        <div className="flex items-center justify-between">
          <button
            onClick={handlePrevWeek}
            disabled={currentWeek <= 1}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.25rem',
              borderRadius: '12px',
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: 'white',
              fontWeight: 600,
              transition: 'all 0.2s',
              opacity: currentWeek <= 1 ? 0.3 : 1,
              cursor: currentWeek <= 1 ? 'not-allowed' : 'pointer'
            }}
          >
            <ChevronLeftIcon className="w-5 h-5" />
            <span className="hidden sm:inline">Précédent</span>
          </button>

          <div className="text-center">
            <h2 style={{
              fontSize: '2rem',
              fontWeight: 800,
              color: 'white',
              marginBottom: '0.5rem'
            }}>
              Semaine {currentWeek}
            </h2>
            <p style={{
              color: 'rgba(255, 255, 255, 0.9)',
              fontSize: '1.125rem'
            }}>
              Jeudi {currentThursday.toLocaleDateString('fr-FR', { 
                day: 'numeric', 
                month: 'long', 
                year: 'numeric' 
              })}
            </p>
            <div style={{
              marginTop: '0.75rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              borderRadius: '20px',
              background: 'rgba(255, 255, 255, 0.2)',
              backdropFilter: 'blur(10px)'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#10B981',
                animation: 'pulse 2s ease-in-out infinite'
              }} />
              <span style={{ color: 'white', fontSize: '0.875rem', fontWeight: 600 }}>
                {weekMatches.length} match{weekMatches.length > 1 ? 's' : ''} planifié{weekMatches.length > 1 ? 's' : ''}
              </span>
            </div>
          </div>

          <button
            onClick={handleNextWeek}
            disabled={currentWeek >= nbSemaines}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.25rem',
              borderRadius: '12px',
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: 'white',
              fontWeight: 600,
              transition: 'all 0.2s',
              opacity: currentWeek >= nbSemaines ? 0.3 : 1,
              cursor: currentWeek >= nbSemaines ? 'not-allowed' : 'pointer'
            }}
          >
            <span className="hidden sm:inline">Suivant</span>
            <ChevronRightIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Calendar Grid */}
      <div style={{ 
        display: 'flex', 
        overflow: 'auto',
        maxHeight: '70vh'
      }}>
        {/* Time column */}
        <div style={{
          width: '80px',
          flexShrink: 0,
          borderRight: '2px solid #E2E8F0',
          background: '#F8FAFC'
        }}>
          <div style={{
            height: '60px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '2px solid #E2E8F0',
            fontWeight: 700,
            color: '#1E293B',
            fontSize: '0.875rem'
          }}>
            Horaire
          </div>
          <div style={{ position: 'relative', height: `${gridHeight}px` }}>
            {timeSlots.map((time, idx) => (
              <div
                key={time}
                style={{
                  position: 'absolute',
                  top: `${idx * SLOT_HEIGHT}px`,
                  width: '100%',
                  height: `${SLOT_HEIGHT}px`,
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'center',
                  paddingTop: '0.25rem',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#64748B',
                  borderBottom: '1px solid #E2E8F0'
                }}
              >
                {time}
              </div>
            ))}
          </div>
        </div>

        {/* Venue columns */}
        <div style={{ display: 'flex', flex: 1 }}>
          {venues.map((venue, venueIdx) => (
            <div
              key={venue.id}
              style={{
                flex: 1,
                minWidth: '250px',
                borderRight: venueIdx < venues.length - 1 ? '1px solid #E2E8F0' : 'none'
              }}
            >
              {/* Venue header */}
              <div style={{
                height: '60px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.25rem',
                borderBottom: '2px solid #E2E8F0',
                background: '#F8FAFC',
                padding: '0.5rem'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <MapPinIcon style={{
                    width: '1.25rem',
                    height: '1.25rem',
                    color: '#0055A4'
                  }} />
                  <span style={{
                    fontWeight: 700,
                    fontSize: '0.9375rem',
                    color: '#1E293B'
                  }}>
                    {venue.nom}
                  </span>
                </div>
                <span style={{
                  fontSize: '0.75rem',
                  color: '#64748B',
                  fontWeight: 500
                }}>
                  {matchesByVenue[venue.nom]?.length || 0} matchs
                </span>
              </div>

              {/* Match grid */}
              <div style={{
                position: 'relative',
                height: `${gridHeight}px`
              }}>
                {/* Grid lines */}
                {timeSlots.map((time, idx) => (
                  <div
                    key={time}
                    style={{
                      position: 'absolute',
                      top: `${idx * SLOT_HEIGHT}px`,
                      width: '100%',
                      height: `${SLOT_HEIGHT}px`,
                      borderBottom: '1px solid #F1F5F9',
                      background: idx % 2 === 0 ? '#FAFAFA' : 'white'
                    }}
                  />
                ))}

                {/* Match blocks */}
                {matchesByVenue[venue.nom]?.map((match) => {
                  const position = match.horaire ? calculatePosition(match.horaire) : null
                  if (!position) return null

                  const genderColor = getGenderColor(match)

                  return (
                    <div
                      key={match.id}
                      style={{
                        position: 'absolute',
                        top: `${position.top}px`,
                        left: '8px',
                        right: '8px',
                        height: `${position.height}px`,
                        background: 'white',
                        borderRadius: '12px',
                        padding: '0.75rem',
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                        borderLeft: `4px solid ${genderColor}`,
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        overflow: 'hidden'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 85, 164, 0.2)'
                        e.currentTarget.style.transform = 'translateY(-2px)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.08)'
                        e.currentTarget.style.transform = 'translateY(0)'
                      }}
                    >
                      {/* Match header */}
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        marginBottom: '0.5rem'
                      }}>
                        <span style={{
                          background: 'linear-gradient(135deg, #0055A4, #1E3A8A)',
                          color: 'white',
                          padding: '0.125rem 0.5rem',
                          borderRadius: '6px',
                          fontSize: '0.6875rem',
                          fontWeight: 700
                        }}>
                          {match.poule}
                        </span>
                        <span style={{
                          background: '#EFF6FF',
                          color: '#1E40AF',
                          padding: '0.125rem 0.5rem',
                          borderRadius: '6px',
                          fontSize: '0.6875rem',
                          fontWeight: 600
                        }}>
                          {match.horaire}
                        </span>
                      </div>

                      {/* Teams */}
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr auto 1fr',
                        gap: '0.5rem',
                        alignItems: 'center',
                        marginBottom: '0.5rem'
                      }}>
                        <div style={{
                          textAlign: 'right',
                          fontSize: '0.875rem',
                          fontWeight: 600,
                          color: '#1E293B',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {match.equipe1_nom}
                        </div>

                        <div style={{
                          width: '32px',
                          height: '32px',
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, #0055A4, #1E3A8A)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          boxShadow: '0 2px 8px rgba(0, 85, 164, 0.3)',
                          flexShrink: 0
                        }}>
                          <span style={{
                            color: 'white',
                            fontWeight: 800,
                            fontSize: '0.625rem'
                          }}>
                            VS
                          </span>
                        </div>

                        <div style={{
                          textAlign: 'left',
                          fontSize: '0.875rem',
                          fontWeight: 600,
                          color: '#1E293B',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {match.equipe2_nom}
                        </div>
                      </div>

                      {/* Gender indicator */}
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.25rem',
                        paddingTop: '0.5rem',
                        borderTop: '1px solid #E2E8F0'
                      }}>
                        <div style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          background: genderColor
                        }} />
                        <span style={{
                          fontSize: '0.6875rem',
                          color: '#64748B',
                          fontWeight: 500
                        }}>
                          {match.equipe1_genre?.toLowerCase() === 'f' || 
                           match.equipe2_genre?.toLowerCase() === 'f' ? 'Féminin' : 'Masculin'}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
