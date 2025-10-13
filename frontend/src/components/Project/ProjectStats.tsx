import { useProjectStats } from '@/hooks'
import { 
  UserGroupIcon, 
  BuildingOfficeIcon, 
  CalendarDaysIcon,
  CheckCircleIcon 
} from '@heroicons/react/24/outline'

interface ProjectStatsProps {
  projectId: number | null
}

/**
 * Composant d'affichage des statistiques d'un projet.
 * 
 * Affiche 4 cartes de statistiques :
 * - Nombre d'équipes
 * - Nombre de gymnases
 * - Nombre de matchs planifiés
 * - Nombre de matchs fixés
 * 
 * Grid responsive : 1 colonne mobile, 2 colonnes tablette, 4 colonnes desktop
 * 
 * @param projectId - ID du projet dont afficher les stats
 */
export function ProjectStats({ projectId }: ProjectStatsProps) {
  const { data: stats, isLoading, error } = useProjectStats(projectId ?? 0)

  // Pas de projet sélectionné
  if (!projectId) {
    return null
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="animate-pulse">
            <div className="bg-gray-200 rounded-lg p-6 h-32"></div>
          </div>
        ))}
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-sm text-red-600">
          Erreur lors du chargement des statistiques
        </p>
      </div>
    )
  }

  // No data
  if (!stats) {
    return null
  }

  // Cartes de statistiques
  const statCards = [
    {
      id: 'equipes',
      title: 'Équipes',
      value: stats.nb_equipes,
      icon: UserGroupIcon,
      bgGradient: 'from-blue-500 to-blue-600',
      iconBg: 'bg-blue-400/20',
    },
    {
      id: 'gymnases',
      title: 'Gymnases',
      value: stats.nb_gymnases,
      icon: BuildingOfficeIcon,
      bgGradient: 'from-green-500 to-green-600',
      iconBg: 'bg-green-400/20',
    },
    {
      id: 'planifies',
      title: 'Matchs planifiés',
      value: stats.nb_matchs_planifies,
      subValue: `sur ${stats.nb_matchs_total}`,
      icon: CalendarDaysIcon,
      bgGradient: 'from-purple-500 to-purple-600',
      iconBg: 'bg-purple-400/20',
    },
    {
      id: 'fixes',
      title: 'Matchs fixés',
      value: stats.nb_matchs_fixes,
      subValue: `sur ${stats.nb_matchs_planifies}`,
      icon: CheckCircleIcon,
      bgGradient: 'from-orange-500 to-orange-600',
      iconBg: 'bg-orange-400/20',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {statCards.map((card) => {
        const Icon = card.icon
        return (
          <div
            key={card.id}
            className={`bg-gradient-to-br ${card.bgGradient} rounded-2xl p-6 shadow-xl 
                       transform hover:scale-105 hover:shadow-2xl transition-all duration-200
                       border border-white/20 backdrop-blur-sm`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-semibold text-white/90 mb-3 uppercase tracking-wider">
                  {card.title}
                </p>
                <p className="text-4xl font-bold text-white mb-1">
                  {card.value}
                </p>
                {card.subValue && (
                  <p className="text-sm text-white/80 font-medium">
                    {card.subValue}
                  </p>
                )}
              </div>
              <div className={`${card.iconBg} rounded-xl p-3`}>
                <Icon className="w-8 h-8 text-white" />
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
