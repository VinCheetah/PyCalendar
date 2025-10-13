/**
 * Page principale du calendrier PyCalendar.
 * 
 * Intègre le composant Calendar qui gère :
 * - Affichage des matchs avec FullCalendar
 * - Drag & drop pour déplacer les matchs
 * - Modal pour voir détails et fixer/défixer
 * - Gestion des états (loading, error)
 * 
 * Phase 2.7 : Sélection dynamique de projet via ProjectSelector
 * Phase 3.4 : Boutons de résolution (CP-SAT et Greedy)
 * Phase 4.1 : Toast notifications pour meilleur feedback
 */

import { useState } from 'react'
import toast from 'react-hot-toast'
import GridCalendar from '@/components/calendar/GridCalendar'
import FilterBar, { type Filters } from '@/components/calendar/FilterBar'
import ViewControls, { type ViewOptions } from '@/components/calendar/ViewControls'
import StatsHeader from '@/components/calendar/StatsHeader'
import { ProjectSelector } from '@/components/Project'
import { useSolveProject, useProjects } from '@/hooks'

export default function CalendarPage() {
  // Phase 2.7 : Sélection dynamique de projet
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(1)
  
  // Filters and view options state
  const [filters, setFilters] = useState<Filters>({
    gender: '',
    pool: '',
    venue: '',
    week: null
  })
  
  const [viewOptions, setViewOptions] = useState<ViewOptions>({
    columnCount: 3,
    showAvailableSlots: false,
    timeGranularity: 60
  })
  
  // Phase 3.4 : Hook pour résolution de projet
  const solveProject = useSolveProject()
  
  // Get project details for nb_semaines
  const { data: projects } = useProjects()
  const selectedProject = projects?.find(p => p.id === selectedProjectId)
  
  // Hardcodé pour Phase 2, viendra du projet.semaine_min en Phase 3
  const semaineMin = selectedProject?.semaine_min ?? 1
  const nbSemaines = selectedProject?.nb_semaines ?? 10

  /**
   * Handler pour déclencher la résolution du projet.
   * 
   * @param strategy - Stratégie de résolution ('cpsat' ou 'greedy')
   */
  const handleSolve = async (strategy: 'cpsat' | 'greedy') => {
    if (!selectedProjectId) return
    
    // Toast de chargement
    const loadingToast = toast.loading(
      `🔄 Résolution en cours avec ${strategy === 'cpsat' ? 'CP-SAT (optimal)' : 'Greedy (rapide)'}...\n${strategy === 'cpsat' ? '⏱️ Peut prendre plusieurs minutes pour les gros projets' : ''}`,
      { duration: Infinity }
    )
    
    try {
      const result = await solveProject.mutateAsync({ 
        projectId: selectedProjectId, 
        strategy 
      })
      
      // Supprimer toast de chargement
      toast.dismiss(loadingToast)
      
      // Toast de succès avec détails
      toast.success(
        () => (
          <div className="flex flex-col gap-1">
            <div className="font-semibold">✅ Résolution terminée !</div>
            <div className="text-sm text-gray-600">
              Stratégie: <span className="font-medium">{result.strategy}</span>
            </div>
            <div className="text-sm text-gray-600">
              Matchs planifiés: <span className="font-medium">{result.nb_matchs_planifies}/{result.nb_matchs_total}</span>
            </div>
            <div className="text-sm text-gray-600">
              Matchs modifiés: <span className="font-medium">{result.nb_matchs_updated}</span>
            </div>
            <div className="text-sm text-gray-600">
              Temps: <span className="font-medium">{result.execution_time.toFixed(2)}s</span>
            </div>
          </div>
        ),
        { 
          duration: 6000,
          style: {
            maxWidth: '400px',
          }
        }
      )
    } catch (error: any) {
      // Supprimer toast de chargement
      toast.dismiss(loadingToast)
      
      // Extraire le message d'erreur détaillé du backend
      const errorMessage = error.response?.data?.detail || error.message || 'Erreur inconnue'
      
      // Toast d'erreur avec message détaillé
      toast.error(
        () => (
          <div className="flex flex-col gap-1">
            <div className="font-semibold">❌ Erreur lors de la résolution</div>
            <div className="text-sm text-gray-600">{errorMessage}</div>
            {error.response?.data?.erreurs && (
              <div className="text-xs text-red-600 mt-1">
                {error.response.data.erreurs.join(', ')}
              </div>
            )}
          </div>
        ),
        { 
          duration: 10000,
          style: {
            maxWidth: '500px',
          }
        }
      )
    }
  }

  // Rendu principal
  // Le composant Calendar gère lui-même :
  // - useMatches(projectId) pour récupérer les matchs
  // - useMoveMatch() pour drag & drop
  // - Modal EventDetailsModal pour clic sur match
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
      {/* Overlay de chargement pendant la résolution - Amélioré */}
      {solveProject.isPending && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-white rounded-2xl shadow-2xl p-10 max-w-md mx-4 border border-gray-200">
            <div className="flex flex-col items-center gap-6">
              {/* Spinner animé avec gradient */}
              <div className="relative">
                <svg className="animate-spin h-16 w-16 text-blue-600" viewBox="0 0 24 24">
                  <circle 
                    className="opacity-25" 
                    cx="12" 
                    cy="12" 
                    r="10" 
                    stroke="currentColor" 
                    strokeWidth="4" 
                    fill="none" 
                  />
                  <path 
                    className="opacity-75" 
                    fill="currentColor" 
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" 
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-8 h-8 bg-blue-500 rounded-full animate-pulse"></div>
                </div>
              </div>
              
              {/* Message de chargement */}
              <div className="text-center">
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  Optimisation en cours...
                </h3>
                <p className="text-gray-700 font-medium mb-2">
                  {solveProject.variables?.strategy === 'cpsat' 
                    ? '🎯 Solution optimale avec CP-SAT' 
                    : '⚡ Calcul rapide avec Greedy'}
                </p>
                <p className="text-sm text-gray-500">
                  Cela peut prendre quelques secondes
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header avec design French moderne */}
      <header style={{
        background: 'white',
        boxShadow: '0 4px 20px rgba(0, 85, 164, 0.1)',
        borderBottom: '3px solid #0055A4',
        position: 'sticky',
        top: 0,
        zIndex: 40
      }}>
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 style={{
                fontSize: '2.5rem',
                fontWeight: 800,
                background: 'linear-gradient(135deg, #0055A4 0%, #1E3A8A 50%, #EF4444 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                marginBottom: '0.5rem'
              }}>
                📅 Calendrier Sportif
              </h1>
              <p style={{ color: '#64748B', fontSize: '1rem' }}>
                Gestion et optimisation des plannings PyCalendar
              </p>
            </div>
            
            {/* Boutons de résolution - French style */}
            {selectedProjectId && (
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button
                  onClick={() => handleSolve('cpsat')}
                  disabled={solveProject.isPending}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.875rem 1.5rem',
                    borderRadius: '14px',
                    background: solveProject.isPending && solveProject.variables?.strategy === 'cpsat' 
                      ? 'linear-gradient(135deg, #94A3B8, #64748B)' 
                      : 'linear-gradient(135deg, #0055A4, #1E3A8A)',
                    color: 'white',
                    border: 'none',
                    fontSize: '0.9375rem',
                    fontWeight: 700,
                    cursor: solveProject.isPending ? 'not-allowed' : 'pointer',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    boxShadow: '0 8px 24px rgba(0, 85, 164, 0.3)'
                  }}
                  onMouseEnter={(e) => {
                    if (!solveProject.isPending) {
                      e.currentTarget.style.transform = 'translateY(-2px) scale(1.02)'
                      e.currentTarget.style.boxShadow = '0 12px 32px rgba(0, 85, 164, 0.4)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0) scale(1)'
                    e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 85, 164, 0.3)'
                  }}
                >
                  {solveProject.isPending && solveProject.variables?.strategy === 'cpsat' ? (
                    <>
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      <span>Calcul CP-SAT...</span>
                    </>
                  ) : (
                    <>
                      🎯
                      <span>Résoudre (CP-SAT)</span>
                    </>
                  )}
                </button>
                
                <button
                  onClick={() => handleSolve('greedy')}
                  disabled={solveProject.isPending}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.875rem 1.5rem',
                    borderRadius: '14px',
                    background: solveProject.isPending && solveProject.variables?.strategy === 'greedy'
                      ? 'linear-gradient(135deg, #94A3B8, #64748B)'
                      : 'linear-gradient(135deg, #10B981, #059669)',
                    color: 'white',
                    border: 'none',
                    fontSize: '0.9375rem',
                    fontWeight: 700,
                    cursor: solveProject.isPending ? 'not-allowed' : 'pointer',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    boxShadow: '0 8px 24px rgba(16, 185, 129, 0.3)'
                  }}
                  onMouseEnter={(e) => {
                    if (!solveProject.isPending) {
                      e.currentTarget.style.transform = 'translateY(-2px) scale(1.02)'
                      e.currentTarget.style.boxShadow = '0 12px 32px rgba(16, 185, 129, 0.4)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0) scale(1)'
                    e.currentTarget.style.boxShadow = '0 8px 24px rgba(16, 185, 129, 0.3)'
                  }}
                >
                  {solveProject.isPending && solveProject.variables?.strategy === 'greedy' ? (
                    <>
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      <span>Calcul Greedy...</span>
                    </>
                  ) : (
                    <>
                      ⚡
                      <span>Résoudre (Greedy)</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
          
          {/* Sélecteur de projet - French style */}
          <div style={{
            background: 'linear-gradient(135deg, #F8FAFC, #EFF6FF)',
            borderRadius: '14px',
            padding: '1rem',
            border: '2px solid #E2E8F0'
          }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: 700,
              color: '#1E293B',
              marginBottom: '0.75rem'
            }}>
              📁 Sélectionner un projet
            </label>
            <ProjectSelector
              value={selectedProjectId}
              onChange={setSelectedProjectId}
            />
          </div>
        </div>
      </header>

      {/* Statistiques du projet - Affichées seulement si un projet est sélectionné */}
      {selectedProjectId && (
        <div className="max-w-7xl mx-auto px-6 py-6">
          <StatsHeader projectId={selectedProjectId} />
        </div>
      )}

      {/* Filtres et Options - Affichés seulement si un projet est sélectionné */}
      {selectedProjectId && (
        <div className="max-w-7xl mx-auto px-6">
          <FilterBar
            projectId={selectedProjectId}
            filters={filters}
            onFiltersChange={setFilters}
          />
          <ViewControls
            options={viewOptions}
            onOptionsChange={setViewOptions}
          />
        </div>
      )}

      {/* Calendrier - Affiché seulement si un projet est sélectionné */}
      <div className="max-w-7xl mx-auto px-6 pb-8">
        {selectedProjectId ? (
          <GridCalendar
            projectId={selectedProjectId}
            semaineMin={semaineMin}
            nbSemaines={nbSemaines}
            filters={filters}
          />
        ) : (
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl border-2 border-dashed border-gray-300 p-16 text-center">
            <div className="max-w-md mx-auto">
              <svg className="w-24 h-24 mx-auto text-gray-400 mb-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h3 className="text-2xl font-bold text-gray-700 mb-3">
                Aucun projet sélectionné
              </h3>
              <p className="text-gray-600 text-lg">
                Veuillez sélectionner un projet ci-dessus pour afficher le calendrier des matchs
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Légende - Design amélioré */}
      <footer className="max-w-7xl mx-auto px-6 pb-8">
        <div className="bg-gradient-to-r from-gray-800 to-gray-900 rounded-2xl shadow-xl p-6">
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
      </footer>
    </div>
  )
}
