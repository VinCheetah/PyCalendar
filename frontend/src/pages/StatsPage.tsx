import { useState } from 'react'
import { useProjects, useProjectStats } from '@/hooks'
import {
  ChartBarIcon,
  TrophyIcon,
  UserGroupIcon,
  BuildingOfficeIcon,
  CalendarDaysIcon,
  LockClosedIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline'

/**
 * Page de statistiques PyCalendar.
 * 
 * Affiche des métriques visuelles et des graphiques
 * pour analyser les performances des projets.
 */
export default function StatsPage() {
  const { data: projects } = useProjects()
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(
    projects?.[0]?.id ?? null
  )
  const { data: stats, isLoading } = useProjectStats(selectedProjectId ?? 0)

  // Si pas de projet sélectionné, afficher les stats globales
  const totalProjects = projects?.length ?? 0
  const totalTeams = projects?.reduce((acc, p) => acc + (p.config_data?.nb_equipes ?? 0), 0) ?? 0
  const totalVenues = projects?.reduce((acc, p) => acc + (p.config_data?.nb_gymnases ?? 0), 0) ?? 0

  return (
    <div className="space-y-8">
      {/* En-tête avec gradient bleu-blanc-rouge */}
      <div 
        className="relative overflow-hidden rounded-3xl p-8 shadow-2xl"
        style={{
          background: 'linear-gradient(135deg, #0055A4 0%, #3B82F6 50%, #EF4444 100%)'
        }}
      >
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative z-10">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-white/20 backdrop-blur-sm rounded-xl">
                  <ChartBarIcon className="w-8 h-8 text-white" />
                </div>
                <h1 
                  className="text-4xl font-extrabold text-white tracking-tight"
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  Statistiques
                </h1>
              </div>
              <p className="text-white/90 text-lg max-w-2xl">
                Analysez les performances de vos projets et optimisez vos planifications sportives.
              </p>
              <div className="mt-6 flex items-center gap-4 text-white/90">
                <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-xl backdrop-blur-sm">
                  <TrophyIcon className="w-5 h-5" />
                  <span className="font-semibold">{totalProjects} projets</span>
                </div>
                <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-xl backdrop-blur-sm">
                  <UserGroupIcon className="w-5 h-5" />
                  <span className="font-semibold">{totalTeams} équipes</span>
                </div>
                <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-xl backdrop-blur-sm">
                  <BuildingOfficeIcon className="w-5 h-5" />
                  <span className="font-semibold">{totalVenues} gymnases</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-white/10 rounded-full blur-3xl"></div>
        <div className="absolute -left-10 -top-10 w-40 h-40 bg-white/10 rounded-full blur-3xl"></div>
      </div>

      {/* Barre tricolore française */}
      <div 
        className="h-2 rounded-full"
        style={{
          background: 'linear-gradient(90deg, #0055A4 0%, white 33%, white 66%, #EF4444 100%)'
        }}
      />

      {/* Sélecteur de projet */}
      {projects && projects.length > 0 && (
        <div 
          className="bg-white rounded-2xl p-6 border-l-4"
          style={{
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
            borderLeftColor: '#0055A4'
          }}
        >
          <label 
            className="block text-sm font-bold mb-3"
            style={{ 
              color: '#1E293B',
              fontFamily: 'Inter, sans-serif'
            }}
          >
            Sélectionner un projet pour voir les détails
          </label>
          <select
            value={selectedProjectId ?? ''}
            onChange={(e) => setSelectedProjectId(Number(e.target.value))}
            className="w-full px-4 py-3 rounded-xl border-2 transition-all duration-300 outline-none font-medium"
            style={{
              borderColor: '#E2E8F0',
              fontFamily: 'Inter, sans-serif'
            }}
          >
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.nom} - {project.sport}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Statistiques du projet sélectionné */}
      {selectedProjectId && stats ? (
        <div className="space-y-6">
          {/* Cartes de statistiques avec design français */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div 
              className="bg-white rounded-xl p-6 text-center transition-transform duration-300 hover:scale-105"
              style={{
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)'
              }}
            >
              <div className="flex items-center justify-center mb-4">
                <div 
                  className="p-3 rounded-xl"
                  style={{ background: '#EFF6FF' }}
                >
                  <UserGroupIcon className="w-6 h-6" style={{ color: '#0055A4' }} />
                </div>
              </div>
              <div 
                className="text-4xl font-extrabold mb-1"
                style={{ color: '#0055A4' }}
              >
                {stats.nb_equipes}
              </div>
              <div className="text-sm font-medium" style={{ color: '#64748B' }}>
                Équipes
              </div>
            </div>

            <div 
              className="bg-white rounded-xl p-6 text-center transition-transform duration-300 hover:scale-105"
              style={{
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)'
              }}
            >
              <div className="flex items-center justify-center mb-4">
                <div 
                  className="p-3 rounded-xl"
                  style={{ background: '#DBEAFE' }}
                >
                  <BuildingOfficeIcon className="w-6 h-6" style={{ color: '#3B82F6' }} />
                </div>
              </div>
              <div 
                className="text-4xl font-extrabold mb-1"
                style={{ color: '#3B82F6' }}
              >
                {stats.nb_gymnases}
              </div>
              <div className="text-sm font-medium" style={{ color: '#64748B' }}>
                Gymnases
              </div>
            </div>

            <div 
              className="bg-white rounded-xl p-6 text-center transition-transform duration-300 hover:scale-105"
              style={{
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)'
              }}
            >
              <div className="flex items-center justify-center mb-4">
                <div 
                  className="p-3 rounded-xl"
                  style={{ background: '#F3F4F6' }}
                >
                  <CalendarDaysIcon className="w-6 h-6" style={{ color: '#6B7280' }} />
                </div>
              </div>
              <div 
                className="text-4xl font-extrabold mb-1"
                style={{
                  background: 'linear-gradient(135deg, #0055A4 0%, #EF4444 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text'
                }}
              >
                {stats.nb_matchs_planifies}/{stats.nb_matchs_total}
              </div>
              <div className="text-sm font-medium" style={{ color: '#64748B' }}>
                Matchs planifiés
              </div>
            </div>

            <div 
              className="bg-white rounded-xl p-6 text-center transition-transform duration-300 hover:scale-105"
              style={{
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)'
              }}
            >
              <div className="flex items-center justify-center mb-4">
                <div 
                  className="p-3 rounded-xl"
                  style={{ background: '#FEE2E2' }}
                >
                  <LockClosedIcon className="w-6 h-6" style={{ color: '#EF4444' }} />
                </div>
              </div>
              <div 
                className="text-4xl font-extrabold mb-1"
                style={{ color: '#EF4444' }}
              >
                {stats.nb_matchs_fixes}
              </div>
              <div className="text-sm font-medium" style={{ color: '#64748B' }}>
                Matchs fixés
              </div>
            </div>
          </div>

          {/* Taux de planification */}
          <div className="bg-white rounded-2xl p-6 shadow-card border border-gray-100">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <ChartBarIcon className="w-5 h-5 text-emerald-600" />
              Taux de planification
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Matchs planifiés</span>
                  <span className="text-sm font-bold text-emerald-600">
                    {stats.nb_matchs_total > 0
                      ? ((stats.nb_matchs_planifies / stats.nb_matchs_total) * 100).toFixed(1)
                      : 0}%
                  </span>
                </div>
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full transition-all duration-500"
                    style={{
                      width: `${
                        stats.nb_matchs_total > 0
                          ? (stats.nb_matchs_planifies / stats.nb_matchs_total) * 100
                          : 0
                      }%`,
                    }}
                  ></div>
                </div>
              </div>

              {stats.nb_matchs_planifies > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Matchs fixés</span>
                    <span className="text-sm font-bold text-orange-600">
                      {((stats.nb_matchs_fixes / stats.nb_matchs_planifies) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-orange-500 to-red-500 rounded-full transition-all duration-500"
                      style={{
                        width: `${(stats.nb_matchs_fixes / stats.nb_matchs_planifies) * 100}%`,
                      }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Insights */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border-2 border-blue-200">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-blue-500 rounded-xl">
                  <ArrowTrendingUpIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-900 mb-2">Performance optimale</h4>
                  <p className="text-sm text-gray-600">
                    {stats.nb_matchs_planifies === stats.nb_matchs_total
                      ? 'Tous les matchs sont planifiés ! Excellent travail.'
                      : `${stats.nb_matchs_total - stats.nb_matchs_planifies} matchs restent à planifier.`}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 border-2 border-purple-200">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-purple-500 rounded-xl">
                  <TrophyIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-900 mb-2">Stabilité du calendrier</h4>
                  <p className="text-sm text-gray-600">
                    {stats.nb_matchs_fixes > 0
                      ? `${stats.nb_matchs_fixes} matchs sont fixés et ne peuvent être modifiés.`
                      : 'Aucun match fixé. Le calendrier est flexible.'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-emerald-600"></div>
          <p className="mt-4 text-gray-600">Chargement des statistiques...</p>
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <ChartBarIcon className="w-10 h-10 text-gray-400" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">Aucun projet sélectionné</h3>
          <p className="text-gray-600">Créez un projet pour voir les statistiques</p>
        </div>
      )}
    </div>
  )
}
