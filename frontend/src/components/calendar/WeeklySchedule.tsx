/**
 * Calendrier hebdomadaire optimisé pour les matchs de jeudi.
 * 
 * Fonctionnalités :
 * - Affichage par semaine avec une colonne par gymnase
 * - Gestion des capacités multiples (plusieurs matchs simultanés)
 * - Vue claire des horaires et emplacements
 * - Navigation entre semaines
 */

import { useState, useMemo } from 'react'
import { ChevronLeftIcon, ChevronRightIcon, MapPinIcon, UserGroupIcon } from '@heroicons/react/24/outline'
import { useMatches, useVenues } from '@/hooks'
import type { Match } from '@/types'
import EventDetailsModal from './EventDetailsModal'

interface WeeklyScheduleProps {
  projectId: number
  semaineMin: number
  nbSemaines: number
}

// Référence : Jeudi 16 octobre 2025 (Semaine 1)
const REFERENCE_DATE = new Date(2025, 9, 16)

export default function WeeklySchedule({ projectId, semaineMin, nbSemaines }: WeeklyScheduleProps) {
  const [currentWeek, setCurrentWeek] = useState(1)
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const { data: matches, isLoading: loadingMatches } = useMatches(projectId)
  const { data: venues, isLoading: loadingVenues } = useVenues(projectId)

  // Horaires disponibles (triés)
  const timeSlots = useMemo(() => {
    if (!matches) return []
    const slots = new Set(matches.map(m => m.horaire).filter(Boolean))
    return Array.from(slots).sort()
  }, [matches])

  // Matchs de la semaine courante
  const weekMatches = useMemo(() => {
    if (!matches) return []
    return matches.filter(m => m.semaine === currentWeek && m.horaire && m.gymnase)
  }, [matches, currentWeek])

  // Organiser matchs par horaire et gymnase
  const scheduleGrid = useMemo(() => {
    if (!venues || !weekMatches) return {}

    const grid: Record<string, Record<string, Match[]>> = {}

    // Initialiser la grille
    timeSlots.forEach(time => {
      if (time) {
        grid[time] = {}
        venues.forEach(venue => {
          grid[time][venue.nom] = []
        })
      }
    })

    // Remplir la grille
    weekMatches.forEach(match => {
      if (match.horaire && match.gymnase && grid[match.horaire]?.[match.gymnase]) {
        grid[match.horaire][match.gymnase].push(match)
      }
    })

    return grid
  }, [venues, weekMatches, timeSlots])

  // Calculer la date du jeudi
  const currentThursday = useMemo(() => {
    const date = new Date(REFERENCE_DATE)
    date.setDate(date.getDate() + (currentWeek - 1) * 7)
    return date
  }, [currentWeek])

  const handlePrevWeek = () => {
    if (currentWeek > 1) setCurrentWeek(currentWeek - 1)
  }

  const handleNextWeek = () => {
    if (currentWeek < nbSemaines) setCurrentWeek(currentWeek + 1)
  }

  const handleMatchClick = (match: Match) => {
    setSelectedMatch(match)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedMatch(null)
  }

  if (loadingMatches || loadingVenues) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Chargement du planning...</div>
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

  return (
    <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl shadow-2xl overflow-hidden">
      {/* En-tête avec navigation - Design moderne */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-8 py-6">
        <div className="flex items-center justify-between">
          <button
            onClick={handlePrevWeek}
            disabled={currentWeek <= 1}
            className="group flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 
                     disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200
                     border border-white/20 hover:border-white/40"
          >
            <ChevronLeftIcon className="w-5 h-5 text-white" />
            <span className="text-white font-medium hidden sm:inline">Précédent</span>
          </button>

          <div className="text-center">
            <h2 className="text-3xl font-bold text-white mb-1">
              Semaine {currentWeek}
            </h2>
            <p className="text-blue-100 text-lg">
              Jeudi {currentThursday.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })}
            </p>
            <div className="mt-2 inline-flex items-center gap-2 px-4 py-1 rounded-full bg-white/20 backdrop-blur-sm">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-white text-sm font-medium">
                {weekMatches.length} match{weekMatches.length > 1 ? 's' : ''} planifié{weekMatches.length > 1 ? 's' : ''}
              </span>
            </div>
          </div>

          <button
            onClick={handleNextWeek}
            disabled={currentWeek >= nbSemaines}
            className="group flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 
                     disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200
                     border border-white/20 hover:border-white/40"
          >
            <span className="text-white font-medium hidden sm:inline">Suivant</span>
            <ChevronRightIcon className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>

      {/* Grille du planning - Design amélioré */}
      <div className="p-6 overflow-x-auto">
        <table className="w-full border-collapse bg-white rounded-lg overflow-hidden shadow-lg">
          <thead>
            <tr className="bg-gradient-to-r from-gray-800 to-gray-900">
              <th className="p-4 text-left font-bold text-white w-28 border-r border-gray-700">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Horaire</span>
                </div>
              </th>
              {venues.map((venue, idx) => (
                <th key={venue.id} className={`p-4 text-center font-bold text-white min-w-[220px] ${idx < venues.length - 1 ? 'border-r border-gray-700' : ''}`}>
                  <div className="flex flex-col items-center gap-2">
                    <div className="flex items-center justify-center gap-2">
                      <MapPinIcon className="w-5 h-5 text-blue-400" />
                      <span className="text-lg">{venue.nom}</span>
                    </div>
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/30">
                      <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                      <span className="text-xs text-blue-200">
                        {venue.capacite > 1 ? `${venue.capacite} terrains` : '1 terrain'}
                      </span>
                    </div>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {timeSlots.map((time, timeIdx) => (
              <tr key={time} className={timeIdx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                <td className="p-4 text-center font-bold text-gray-800 bg-gradient-to-r from-gray-100 to-gray-50 border-r border-gray-200">
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500"></div>
                    <span className="text-lg">{time}</span>
                  </div>
                </td>
                {venues.map((venue, venueIdx) => {
                  const matchesInSlot = time ? (scheduleGrid[time]?.[venue.nom] || []) : []
                  
                  return (
                    <td key={venue.id} className={`p-3 align-top ${venueIdx < venues.length - 1 ? 'border-r border-gray-200' : ''} ${timeIdx < timeSlots.length - 1 ? 'border-b border-gray-200' : ''}`}>
                      {matchesInSlot.length === 0 ? (
                        <div className="text-center text-gray-300 py-6 text-sm font-medium">—</div>
                      ) : (
                        <div className="space-y-2.5">
                          {matchesInSlot.map((match: Match) => (
                            <MatchCard
                              key={match.id}
                              match={match}
                              onClick={() => handleMatchClick(match)}
                              semaineMin={semaineMin}
                            />
                          ))}
                        </div>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Légende - Design moderne */}
      <div className="px-8 py-6 bg-gradient-to-r from-gray-800 to-gray-900 border-t border-gray-700">
        <div className="flex items-center justify-center gap-8 flex-wrap">
          <div className="flex items-center gap-3 group">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg group-hover:scale-110 transition-transform"></div>
            <span className="text-white font-medium">Match Normal</span>
          </div>
          <div className="flex items-center gap-3 group">
            <div className="w-8 h-8 bg-gradient-to-br from-red-500 to-red-600 rounded-lg shadow-lg group-hover:scale-110 transition-transform"></div>
            <span className="text-white font-medium">Match Fixé</span>
          </div>
          <div className="flex items-center gap-3 group">
            <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow-lg group-hover:scale-110 transition-transform"></div>
            <span className="text-white font-medium">Match Terminé</span>
          </div>
        </div>
      </div>

      {/* Modale détails match */}
      {selectedMatch && (
        <EventDetailsModal
          match={selectedMatch}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          semaineMin={semaineMin}
        />
      )}
    </div>
  )
}

/**
 * Carte de match dans la grille
 */
interface MatchCardProps {
  match: Match
  onClick: () => void
  semaineMin?: number  // Optional for future use
}

function MatchCard({ match, onClick }: MatchCardProps) {
  const bgColor = match.est_fixe || match.statut === 'fixe' 
    ? 'from-red-500 to-red-600' 
    : match.statut === 'termine' 
    ? 'from-green-500 to-green-600' 
    : 'from-blue-500 to-blue-600'

  return (
    <div
      onClick={onClick}
      className={`bg-gradient-to-br ${bgColor} text-white p-3 rounded-lg cursor-pointer 
                 transform hover:scale-105 hover:shadow-xl transition-all duration-200
                 border border-white/20 backdrop-blur-sm`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold px-2 py-1 bg-white/20 rounded-md backdrop-blur-sm">
          {match.poule}
        </span>
        {match.est_fixe && (
          <span className="text-xs flex items-center gap-1 bg-red-700/50 px-2 py-1 rounded-md backdrop-blur-sm">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
            </svg>
            Fixé
          </span>
        )}
      </div>
      
      <div className="space-y-1.5">
        <div className="flex items-center gap-2 bg-white/10 rounded-md p-1.5">
          <UserGroupIcon className="w-4 h-4 flex-shrink-0" />
          <span className="text-sm font-medium truncate">{match.equipe1_nom}</span>
        </div>
        
        <div className="text-center">
          <span className="text-xs font-bold bg-white/20 px-3 py-1 rounded-full">VS</span>
        </div>
        
        <div className="flex items-center gap-2 bg-white/10 rounded-md p-1.5">
          <UserGroupIcon className="w-4 h-4 flex-shrink-0" />
          <span className="text-sm font-medium truncate">{match.equipe2_nom}</span>
        </div>
      </div>
    </div>
  )
}
