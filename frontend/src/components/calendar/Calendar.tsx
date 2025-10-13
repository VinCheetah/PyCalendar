/**
 * Composant calendrier principal avec FullCalendar.
 * 
 * Fonctionnalités :
 * - Affichage matchs par semaine avec FullCalendar
 * - Drag & drop pour déplacer matchs (si modifiable)
 * - Clic pour voir détails + fixer/défixer
 * - Couleurs par état (fixé=rouge, terminé=vert, normal=bleu)
 * - Badge "Fixé" sur matchs fixes
 */

import { useState, useMemo } from 'react'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import type { EventInput, EventDropArg, EventClickArg } from '@fullcalendar/core'

import { useMatches, useMoveMatch } from '@/hooks'
import { getErrorMessage } from '@/utils/apiHelpers'
import { showError } from '@/lib/toast'
import type { Match } from '@/types'
import EventDetailsModal from '../calendar/EventDetailsModal'
import '@/assets/styles/calendar.css'

interface CalendarProps {
  projectId: number
  semaineMin: number  // Depuis project.semaine_min
  referenceDate?: Date  // Date de début Semaine 1 - JEUDI 16 octobre 2025 (jour des matchs)
}

export default function Calendar({ projectId, semaineMin, referenceDate = new Date(2025, 9, 16) }: CalendarProps) {
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Récupérer tous les matchs du projet
  const { data: matches, isLoading } = useMatches(projectId)

  // Mutation pour déplacer match
  const moveMatch = useMoveMatch()

  // Transformer matchs en événements FullCalendar
  const events: EventInput[] = useMemo(() => {
    if (!matches) return []

    return matches
      .filter(m => m.semaine !== null && m.horaire !== null)  // Seulement matchs planifiés
      .map(match => {
        const isModifiable = !match.est_fixe && (match.semaine ?? 0) >= semaineMin
        
        return {
          id: match.id.toString(),
          title: `${match.horaire} - ${match.equipe1_nom} vs ${match.equipe2_nom}`,  // Include time in title
          start: calculateDate(match.semaine!, match.horaire!, referenceDate),
          backgroundColor: getMatchColor(match),
          borderColor: getMatchColor(match),
          textColor: '#ffffff',
          editable: isModifiable,  // Drag & drop seulement si modifiable
          extendedProps: {
            match,
            isModifiable,
            venue: match.gymnase,  // Add venue to display
          },
        }
      })
  }, [matches, semaineMin, referenceDate])

  // Gérer drop d'un événement (déplacement match)
  const handleEventDrop = async (info: EventDropArg) => {
    const match = info.event.extendedProps.match as Match
    const newDate = info.event.start!
    const nouvelleSemaine = getWeekNumber(newDate, referenceDate)

    try {
      await moveMatch.mutateAsync({
        id: match.id,
        payload: { nouvelle_semaine: nouvelleSemaine },
      })
    } catch (error) {
      // Revert position en cas d'erreur
      info.revert()
      showError(`Impossible de déplacer le match : ${getErrorMessage(error)}`)
    }
  }

  // Gérer clic sur événement (ouvrir modale)
  const handleEventClick = (info: EventClickArg) => {
    const match = info.event.extendedProps.match as Match
    setSelectedMatch(match)
    setIsModalOpen(true)
  }

  // Fermer modale
  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedMatch(null)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Chargement du calendrier...</div>
      </div>
    )
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="timeGridWeek"  // Start with week view to see times
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay',
        }}
        locale="fr"
        firstDay={1}  // Lundi
        events={events}
        editable={true}
        eventDrop={handleEventDrop}
        eventClick={handleEventClick}
        eventContent={renderEventContent}
        height="auto"
        slotMinTime="14:00:00"  // Start display at 14:00 (earliest match)
        slotMaxTime="21:00:00"  // End display at 21:00 (after latest match)
        allDaySlot={false}  // Hide all-day slot since all matches have times
        eventTimeFormat={{
          hour: '2-digit',
          minute: '2-digit',
          meridiem: false,
        }}
      />

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
 * Rendu personnalisé d'un événement (avec badge "Fixé" et info gymnase).
 */
function renderEventContent(eventInfo: any) {
  const match = eventInfo.event.extendedProps.match as Match
  const venue = eventInfo.event.extendedProps.venue as string

  return (
    <div className="p-1 truncate">
      <div className="font-medium text-sm">{eventInfo.timeText}</div>
      <div className="text-xs">{match.equipe1_nom} vs {match.equipe2_nom}</div>
      <div className="text-xs opacity-90">📍 {venue}</div>
      {match.est_fixe && (
        <span className="inline-block px-1 py-0.5 text-xs bg-red-500 text-white rounded mt-1">
          Fixé
        </span>
      )}
    </div>
  )
}

/**
 * Détermine la couleur d'un match selon son état.
 * - Rouge (#ef4444) : Fixé (est_fixe=true ou statut='fixe')
 * - Vert (#22c55e) : Terminé (statut='termine')
 * - Bleu (#3b82f6) : Normal
 */
function getMatchColor(match: Match): string {
  if (match.est_fixe || match.statut === 'fixe') return '#ef4444' // rouge
  if (match.statut === 'termine') return '#22c55e' // vert
  return '#3b82f6' // bleu
}

/**
 * Calcule la date complète à partir du numéro de semaine et de l'horaire.
 * 
 * @param semaine - Numéro de semaine (1-26)
 * @param horaire - Horaire format "HH:MM" (ex: "14:00")
 * @param referenceDate - Date de début de la semaine 1 - JEUDI 16 octobre 2025
 * @returns Date complète avec heure
 * 
 * Exemple : semaine=3, horaire="14:00" → Jeudi 30 octobre 2025 14:00
 */
function calculateDate(semaine: number, horaire: string, referenceDate: Date = new Date(2025, 9, 16)): Date {
  const { hours, minutes } = parseTime(horaire)
  
  // Calculer la date : referenceDate + (semaine - 1) * 7 jours
  const date = new Date(referenceDate)
  date.setDate(date.getDate() + (semaine - 1) * 7)
  date.setHours(hours, minutes, 0, 0)
  
  return date
}

/**
 * Calcule le numéro de semaine à partir d'une date.
 * 
 * @param date - Date à convertir
 * @param referenceDate - Date de début de la semaine 1 - JEUDI 16 octobre 2025
 * @returns Numéro de semaine
 * 
 * Exemple : Jeudi 30 octobre 2025 → semaine 3
 */
function getWeekNumber(date: Date, referenceDate: Date = new Date(2025, 9, 16)): number {
  const diff = date.getTime() - referenceDate.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  return Math.floor(days / 7) + 1
}

/**
 * Parse un horaire format "HH:MM" en heures et minutes.
 * 
 * @param horaire - Format "HH:MM" (ex: "14:00")
 * @returns { hours, minutes }
 */
function parseTime(horaire: string): { hours: number; minutes: number } {
  const parts = horaire.split(':')
  return {
    hours: parseInt(parts[0], 10),
    minutes: parseInt(parts[1], 10)
  }
}
