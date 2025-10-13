# Calendrier FullCalendar - Guide Rapide

## 📦 Import et Usage

```tsx
import Calendar from '@/components/calendar/Calendar'

function CalendarPage() {
  const projectId = 1
  const project = useProject(projectId)
  
  return (
    <Calendar 
      projectId={projectId} 
      semaineMin={project.data?.semaine_min ?? 1}
      referenceDate={new Date(2025, 9, 14)}  // 14 octobre 2025
    />
  )
}
```

## 🎨 Coloration des Matchs

| Couleur | État | Condition |
|---------|------|-----------|
| 🔴 Rouge (#ef4444) | Fixé | `est_fixe=true` ou `statut='fixe'` |
| 🟢 Vert (#22c55e) | Terminé | `statut='termine'` |
| 🔵 Bleu (#3b82f6) | Normal | Autres (planifiés, modifiables) |

## 🖱️ Drag & Drop

**Conditions pour drag & drop** :
- ✅ `!match.est_fixe` (pas fixé)
- ✅ `match.semaine >= semaineMin` (après semaine minimum)

**Flow** :
1. User drag événement
2. `handleEventDrop()` appelé
3. Calcul `nouvelle_semaine = getWeekNumber(newDate)`
4. `useMoveMatch().mutateAsync({ id, payload: { nouvelle_semaine } })`
5. Succès → refetch matchs | Erreur → `info.revert()`

## 📅 Calcul des Dates

### semaine + horaire → Date

```typescript
calculateDate(semaine: number, horaire: string, referenceDate: Date): Date
// Exemple: semaine=3, horaire="14:00" → 28 octobre 2025 14:00
```

**Formule** : `referenceDate + (semaine - 1) * 7 jours` + horaire

### Date → semaine

```typescript
getWeekNumber(date: Date, referenceDate: Date): number
// Exemple: 28 octobre 2025 → semaine 3
```

**Formule** : `Math.floor((date - referenceDate) / (7 jours)) + 1`

### Parser horaire

```typescript
parseTime(horaire: string): { hours: number, minutes: number }
// Exemple: "14:00" → { hours: 14, minutes: 0 }
```

## 🎯 Modale Détails Match

**Ouverture** : Clic sur événement

**Actions disponibles** :

| Action | Condition | Hook |
|--------|-----------|------|
| Fixer | `semaine >= semaineMin` et `!est_fixe` | `useFixMatch()` |
| Défixer | `semaine >= semaineMin` et `est_fixe` | `useUnfixMatch()` |
| Supprimer | Toujours | `useDeleteMatch()` |

**Si `semaine < semaineMin`** :
- Affiche message "Non modifiable - avant semaine X"
- Pas de boutons Fixer/Défixer
- Bouton Supprimer disponible

## 🔧 Configuration FullCalendar

```tsx
<FullCalendar
  plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
  initialView="dayGridMonth"
  locale="fr"
  firstDay={1}  // Lundi
  events={events}
  editable={true}
  eventDrop={handleEventDrop}
  eventClick={handleEventClick}
  eventContent={renderEventContent}
/>
```

**Vues disponibles** :
- `dayGridMonth` : Vue mensuelle
- `dayGridWeek` : Vue hebdomadaire

**Extensions possibles** :
- `timeGridWeek` : Vue horaire hebdomadaire
- `timeGridDay` : Vue horaire journalière
- `listWeek` : Vue liste (nécessite @fullcalendar/list)

## 🏷️ Badge "Fixé"

Affiché via `renderEventContent()` :

```tsx
{match.est_fixe && (
  <span className="inline-block px-1 py-0.5 text-xs bg-red-500 text-white rounded">
    Fixé
  </span>
)}
```

## 📊 Transformation Match → EventInput

```typescript
const events: EventInput[] = matches
  .filter(m => m.semaine !== null && m.horaire !== null)
  .map(match => ({
    id: match.id.toString(),
    title: `${match.equipe1_nom} vs ${match.equipe2_nom}`,
    start: calculateDate(match.semaine!, match.horaire!, referenceDate),
    backgroundColor: getMatchColor(match),
    editable: !match.est_fixe && (match.semaine ?? 0) >= semaineMin,
    extendedProps: { match }
  }))
```

## 🔄 Intégration React Query

**Hooks utilisés** :
- `useMatches(projectId)` : Query matchs
- `useMoveMatch()` : Mutation déplacer
- `useFixMatch()` : Mutation fixer
- `useUnfixMatch()` : Mutation défixer
- `useDeleteMatch()` : Mutation supprimer

**Invalidation automatique** :
- Après mutation → React Query invalide cache
- Matchs refetch automatiquement
- Calendrier mis à jour sans refresh manuel

## 🎨 Styles CSS

Fichier : `@/assets/styles/calendar.css`

**Classes principales** :
- `.fc-event` : Styles événement de base
- `.fc-event:hover` : Hover effect (opacity 0.9)
- `.fc-event:not(.fc-event-draggable)` : Non draggable (opacity 0.6)
- `.fc-event-dragging` : En cours de drag (opacity 0.5)
- `.badge-fixed` : Badge "Fixé"

## 📱 Responsive

FullCalendar est responsive par défaut :
- Desktop : Vue mois/semaine
- Tablette : Vue semaine adaptée
- Mobile : Vue liste recommandée (à ajouter)

## 🐛 Gestion Erreurs

**Drag & drop échoué** :
```tsx
try {
  await moveMatch.mutateAsync(...)
} catch (error) {
  info.revert()  // Revenir position initiale
  alert(`Erreur: ${getErrorMessage(error)}`)
}
```

**Validation backend** :
- Backend vérifie `est_fixe=false` et `semaine >= semaine_min`
- Si validation échoue → HTTP 400
- Frontend affiche erreur et annule déplacement

## 🚀 Extensions Futures

### Filtres

```tsx
// Ajouter au-dessus du calendrier
const [filters, setFilters] = useState({ poule: null })
const { data: matches } = useMatches(projectId, filters)
```

### Vue Horaire

```tsx
// Activer timeGrid
<FullCalendar
  initialView="timeGridWeek"
  slotMinTime="08:00:00"
  slotMaxTime="22:00:00"
/>
```

### Export PDF

```bash
npm install jspdf html2canvas
```

```tsx
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

const exportPDF = async () => {
  const calendar = document.querySelector('.fc')
  const canvas = await html2canvas(calendar)
  const pdf = new jsPDF()
  pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0)
  pdf.save('calendrier.pdf')
}
```

## 📝 Points Clés à Retenir

1. **Date de référence** : 14 octobre 2025 = Semaine 1 (configurable)
2. **Modificabilité** : `!est_fixe` ET `semaine >= semaine_min`
3. **Coloration** : Rouge (fixé), Vert (terminé), Bleu (normal)
4. **Drag & drop** : Revert automatique si erreur backend
5. **Modale** : Actions conditionnelles selon semaine_min
6. **React Query** : Invalidation automatique après mutations
7. **TypeScript** : Tout est typé avec interfaces Match, EventInput

## 🔗 Fichiers Liés

- `frontend/src/components/calendar/Calendar.tsx`
- `frontend/src/components/calendar/EventDetailsModal.tsx`
- `frontend/src/assets/styles/calendar.css`
- `frontend/src/hooks/useMatches.ts`
- `frontend/src/types/match.ts`
- `frontend/docs/TASK_2.5_FULLCALENDAR_COMPONENT_COMPLETE.md`
