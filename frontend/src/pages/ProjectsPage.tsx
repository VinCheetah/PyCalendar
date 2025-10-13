import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useProjects } from '@/hooks'
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  CalendarIcon,
  UserGroupIcon,
  BuildingOfficeIcon,
  ClockIcon,
  SparklesIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline'
import { StarIcon } from '@heroicons/react/24/solid'

/**
 * Page de gestion des projets PyCalendar.
 * 
 * Fonctionnalités :
 * - Liste des projets en cards avec design moderne
 * - Recherche et filtres
 * - Statistiques visuelles par projet
 * - Bouton de création de projet
 * - États de chargement animés
 */
export default function ProjectsPage() {
  const { data: projects, isLoading, error } = useProjects()
  const [searchQuery, setSearchQuery] = useState('')
  const [filterSport, setFilterSport] = useState<string>('all')

  // Filtrer les projets
  const filteredProjects = projects?.filter(project => {
    const matchesSearch = project.nom.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         project.sport.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesSport = filterSport === 'all' || project.sport === filterSport
    return matchesSearch && matchesSport
  })

  // Sports uniques pour le filtre
  const uniqueSports = Array.from(new Set(projects?.map(p => p.sport) || []))

  // État de chargement avec skeleton
  if (isLoading) {
    return (
      <div className="space-y-6">
        {/* Header skeleton */}
        <div className="animate-pulse">
          <div className="h-12 bg-gray-200 rounded-2xl w-1/3 mb-4"></div>
          <div className="h-6 bg-gray-200 rounded-lg w-1/2"></div>
        </div>

        {/* Cards skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="bg-white rounded-2xl p-6 shadow-card h-64">
                <div className="h-6 bg-gray-200 rounded-lg w-3/4 mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-6"></div>
                <div className="space-y-3">
                  <div className="h-4 bg-gray-200 rounded w-full"></div>
                  <div className="h-4 bg-gray-200 rounded w-full"></div>
                  <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // État d'erreur
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <SparklesIcon className="w-8 h-8 text-red-600" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">Erreur de chargement</h3>
          <p className="text-gray-600">Impossible de charger les projets</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* En-tête avec gradient bleu-blanc-rouge français */}
      <div 
        className="relative overflow-hidden rounded-3xl p-8 shadow-2xl"
        style={{
          background: 'linear-gradient(135deg, #1E3A8A 0%, #0055A4 50%, #3B82F6 100%)'
        }}
      >
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative z-10">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-white/20 backdrop-blur-sm rounded-xl">
                  <CalendarIcon className="w-8 h-8 text-white" />
                </div>
                <h1 
                  className="text-4xl font-extrabold text-white tracking-tight"
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  Projets
                </h1>
              </div>
              <p className="text-blue-100 text-lg max-w-2xl">
                Gérez vos différents projets de planification sportive. Créez, consultez et optimisez vos calendriers.
              </p>
              <div className="mt-6 flex items-center gap-4 text-white/90">
                <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-xl backdrop-blur-sm">
                  <SparklesIcon className="w-5 h-5" />
                  <span className="font-semibold">{projects?.length || 0} projets actifs</span>
                </div>
                <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-xl backdrop-blur-sm">
                  <ArrowTrendingUpIcon className="w-5 h-5" />
                  <span className="font-semibold">Optimisation CP-SAT</span>
                </div>
              </div>
            </div>
            <button
              className="px-6 py-3 bg-white text-blue-700 rounded-xl font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 flex items-center gap-2 group"
            >
              <PlusIcon className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
              Nouveau projet
            </button>
          </div>
        </div>
        {/* Décoration */}
        <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-white/10 rounded-full blur-3xl"></div>
        <div className="absolute -left-10 -top-10 w-40 h-40 bg-white/10 rounded-full blur-3xl"></div>
      </div>

      {/* Barre de recherche et filtres */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Recherche */}
        <div className="flex-1 relative group">
          <MagnifyingGlassIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-blue-600 transition-colors" />
          <input
            type="text"
            placeholder="Rechercher un projet..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3.5 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 outline-none bg-white shadow-card"
          />
        </div>

        {/* Filtre par sport */}
        <div className="relative">
          <FunnelIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
          <select
            value={filterSport}
            onChange={(e) => setFilterSport(e.target.value)}
            className="pl-12 pr-10 py-3.5 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-300 outline-none bg-white shadow-card appearance-none cursor-pointer font-medium"
          >
            <option value="all">Tous les sports</option>
            {uniqueSports.map(sport => (
              <option key={sport} value={sport}>{sport}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Grille de projets */}
      {filteredProjects && filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in-up">
          {filteredProjects.map((project, index) => (
            <Link
              key={project.id}
              to={`/calendar?project=${project.id}`}
              className="group relative"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div 
                className="bg-white rounded-2xl p-6 transition-all duration-300 border-l-4"
                style={{
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 85, 164, 0.06)',
                  borderLeftColor: '#3B82F6'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-6px) scale(1.02)'
                  e.currentTarget.style.boxShadow = '0 12px 28px rgba(0, 0, 0, 0.15)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0) scale(1)'
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 85, 164, 0.06)'
                }}
              >
                {/* Badge sport */}
                <div className="flex items-center justify-between mb-4">
                  <span 
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-white text-xs font-bold uppercase tracking-wide shadow-sm"
                    style={{
                      background: 'linear-gradient(135deg, #0055A4, #1E3A8A)'
                    }}
                  >
                    <StarIcon className="w-4 h-4" />
                    {project.sport}
                  </span>
                  <div 
                    className="p-2 rounded-lg transition-colors"
                    style={{ background: '#EFF6FF' }}
                  >
                    <CalendarIcon className="w-5 h-5" style={{ color: '#0055A4' }} />
                  </div>
                </div>

                {/* Nom du projet */}
                <h3 
                  className="text-xl font-bold mb-2 transition-colors"
                  style={{ 
                    color: '#1E293B',
                    fontFamily: 'Inter, sans-serif'
                  }}
                >
                  {project.nom}
                </h3>

                {/* Métadonnées */}
                <div className="space-y-2 mb-4">
                  <div className="flex items-center gap-2 text-sm" style={{ color: '#64748B' }}>
                    <ClockIcon className="w-4 h-4" />
                    <span>{project.nb_semaines} semaines (min: {project.semaine_min})</span>
                  </div>
                </div>

                {/* Statistiques */}
                {project.config_data && (
                  <div className="grid grid-cols-2 gap-3">
                    {project.config_data.nb_equipes !== undefined && (
                      <div className="flex items-center gap-2 p-3 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                          <UserGroupIcon className="w-4 h-4 text-blue-600" />
                        </div>
                        <div>
                          <div className="text-xs text-gray-600">Équipes</div>
                          <div className="text-lg font-bold text-gray-900">{project.config_data.nb_equipes}</div>
                        </div>
                      </div>
                    )}
                    {project.config_data.nb_gymnases !== undefined && (
                      <div className="flex items-center gap-2 p-3 bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl">
                        <div className="p-2 bg-green-500/10 rounded-lg">
                          <BuildingOfficeIcon className="w-4 h-4 text-green-600" />
                        </div>
                        <div>
                          <div className="text-xs text-gray-600">Gymnases</div>
                          <div className="text-lg font-bold text-gray-900">{project.config_data.nb_gymnases}</div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Config YAML */}
                {project.config_yaml_path && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <div className="text-xs text-gray-500 truncate" title={project.config_yaml_path}>
                      📄 {project.config_yaml_path.split('/').pop()}
                    </div>
                  </div>
                )}

                {/* Hover effect overlay */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/0 to-indigo-600/0 group-hover:from-blue-500/5 group-hover:to-indigo-600/5 transition-all duration-300 pointer-events-none"></div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <MagnifyingGlassIcon className="w-10 h-10 text-gray-400" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Aucun projet trouvé</h3>
            <p className="text-gray-600">Essayez de modifier vos critères de recherche</p>
          </div>
        </div>
      )}
    </div>
  )
}
