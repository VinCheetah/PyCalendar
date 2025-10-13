/**
 * Exemples d'utilisation des hooks React Query PyCalendar.
 * 
 * Ce fichier démontre les patterns d'usage des hooks créés dans Tâche 2.4.
 */

import { 
  useProjects, useProject, useProjectStats,
  useMatches, useMatch, useMoveMatch, useFixMatch, useUnfixMatch,
  useTeams, useTeam,
  useVenues, useVenue,
  useCreateProject, useUpdateProject, useDeleteProject,
  useCreateMatch, useUpdateMatch, useDeleteMatch,
  useCreateTeam, useUpdateTeam, useDeleteTeam,
  useCreateVenue, useUpdateVenue, useDeleteVenue
} from '@/hooks'
import { getErrorMessage, isNotFoundError, isBadRequestError } from '@/utils/apiHelpers'

// ============================================
// Exemple 1: Query Simple
// ============================================

/**
 * Afficher la liste des projets.
 */
export function ExampleProjectList() {
  const { data: projects, isLoading, error } = useProjects()
  
  if (isLoading) return <div>Chargement des projets...</div>
  if (error) return <div>Erreur : {getErrorMessage(error)}</div>
  
  return (
    <ul>
      {projects?.map(project => (
        <li key={project.id}>
          {project.nom} - {project.sport}
        </li>
      ))}
    </ul>
  )
}

// ============================================
// Exemple 2: Query avec Filtrage
// ============================================

/**
 * Afficher les matchs d'une semaine spécifique.
 */
export function ExampleMatchList({ projectId, semaine }: { projectId: number; semaine: number }) {
  const { data: matches, isLoading } = useMatches(projectId, { 
    semaine, 
    poule: 'P1' 
  })
  
  if (isLoading) return <div>Chargement des matchs...</div>
  
  return (
    <div>
      <h3>Matchs Semaine {semaine} - Poule P1</h3>
      {matches?.map(match => (
        <div key={match.id}>
          {match.equipe_domicile_nom} vs {match.equipe_exterieur_nom}
          <span> - {match.gymnase_nom}</span>
          {match.est_fixe && <span> 🔒 Fixé</span>}
        </div>
      ))}
    </div>
  )
}

// ============================================
// Exemple 3: Mutation Simple
// ============================================

/**
 * Créer un nouveau projet.
 */
export function ExampleCreateProject() {
  const createProject = useCreateProject()
  
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    
    createProject.mutate({
      nom: formData.get('nom') as string,
      sport: formData.get('sport') as string,
      config_yaml_data: null,
      config_excel_data: null,
    })
  }
  
  return (
    <form onSubmit={handleSubmit}>
      <input name="nom" placeholder="Nom du projet" required />
      <input name="sport" placeholder="Sport" required />
      <button type="submit" disabled={createProject.isPending}>
        {createProject.isPending ? 'Création...' : 'Créer Projet'}
      </button>
      {createProject.isError && (
        <div className="error">{getErrorMessage(createProject.error)}</div>
      )}
    </form>
  )
}

// ============================================
// Exemple 4: Mutation avec mutateAsync
// ============================================

/**
 * Déplacer un match avec gestion d'erreur.
 */
export function ExampleMoveMatch({ matchId }: { matchId: number }) {
  const moveMatch = useMoveMatch()
  
  const handleMove = async (nouvelle_semaine: number) => {
    try {
      await moveMatch.mutateAsync({ 
        id: matchId, 
        payload: { nouvelle_semaine } 
      })
      alert('Match déplacé avec succès !')
    } catch (err) {
      if (isBadRequestError(err)) {
        alert('Impossible de déplacer ce match (peut-être fixé)')
      } else {
        alert(`Erreur : ${getErrorMessage(err)}`)
      }
    }
  }
  
  return (
    <div>
      <button onClick={() => handleMove(5)} disabled={moveMatch.isPending}>
        Déplacer vers semaine 5
      </button>
      <button onClick={() => handleMove(6)} disabled={moveMatch.isPending}>
        Déplacer vers semaine 6
      </button>
    </div>
  )
}

// ============================================
// Exemple 5: Mutation Spéciale (Fix/Unfix)
// ============================================

/**
 * Fixer/défixer un match.
 */
export function ExampleFixMatch({ matchId }: { matchId: number }) {
  const { data: match } = useMatch(matchId)
  const fixMatch = useFixMatch()
  const unfixMatch = useUnfixMatch()
  
  const handleToggleFix = async () => {
    try {
      if (match?.est_fixe) {
        await unfixMatch.mutateAsync(matchId)
        alert('Match défixé - modifiable par solver')
      } else {
        await fixMatch.mutateAsync(matchId)
        alert('Match fixé - non modifiable par solver')
      }
    } catch (err) {
      alert(getErrorMessage(err))
    }
  }
  
  return (
    <button onClick={handleToggleFix}>
      {match?.est_fixe ? '🔓 Défixer' : '🔒 Fixer'}
    </button>
  )
}

// ============================================
// Exemple 6: Queries Multiples
// ============================================

/**
 * Afficher détails projet + stats + matchs.
 */
export function ExampleProjectDashboard({ projectId }: { projectId: number }) {
  const { data: project, isLoading: loadingProject } = useProject(projectId)
  const { data: stats } = useProjectStats(projectId)
  const { data: matches } = useMatches(projectId, { semaine: 3 })
  
  if (loadingProject) return <div>Chargement...</div>
  
  return (
    <div>
      <h2>{project?.nom}</h2>
      
      <section>
        <h3>Statistiques</h3>
        <p>Matchs total : {stats?.nb_matchs_total}</p>
        <p>Matchs planifiés : {stats?.nb_matchs_planifies}</p>
        <p>Matchs fixes : {stats?.nb_matchs_fixes}</p>
        <p>À planifier : {stats?.nb_matchs_a_planifier}</p>
        <p>Équipes : {stats?.nb_equipes}</p>
        <p>Gymnases : {stats?.nb_gymnases}</p>
      </section>
      
      <section>
        <h3>Matchs Semaine 3 ({matches?.length})</h3>
        {matches?.map(m => (
          <div key={m.id}>
            {m.equipe_domicile_nom} vs {m.equipe_exterieur_nom}
          </div>
        ))}
      </section>
    </div>
  )
}

// ============================================
// Exemple 7: Workflow Complet CRUD
// ============================================

/**
 * Gestion complète des équipes d'un projet.
 */
export function ExampleTeamManagement({ projectId }: { projectId: number }) {
  const { data: teams, isLoading } = useTeams(projectId, { poule: 'P1' })
  const createTeam = useCreateTeam()
  const updateTeam = useUpdateTeam()
  const deleteTeam = useDeleteTeam()
  
  const handleCreate = async (nom: string) => {
    try {
      await createTeam.mutateAsync({
        project_id: projectId,
        nom,
        poule: 'P1',
        institution: 'Lycée X',
        genre: 'M',
        horaires_preferes: [],
        lieux_preferes: [],
      })
      alert('Équipe créée !')
    } catch (err) {
      alert(getErrorMessage(err))
    }
  }
  
  const handleUpdate = async (id: number, nom: string) => {
    try {
      await updateTeam.mutateAsync({ id, updates: { nom } })
      alert('Équipe mise à jour !')
    } catch (err) {
      alert(getErrorMessage(err))
    }
  }
  
  const handleDelete = async (id: number) => {
    if (confirm('Supprimer cette équipe ? (matchs supprimés aussi)')) {
      try {
        await deleteTeam.mutateAsync({ id, projectId })
        alert('Équipe supprimée !')
      } catch (err) {
        alert(getErrorMessage(err))
      }
    }
  }
  
  if (isLoading) return <div>Chargement des équipes...</div>
  
  return (
    <div>
      <h3>Équipes Poule P1</h3>
      
      <button onClick={() => handleCreate('Nouvelle Équipe')}>
        Créer Équipe
      </button>
      
      <ul>
        {teams?.map(team => (
          <li key={team.id}>
            {team.nom}
            <button onClick={() => handleUpdate(team.id, 'Nouveau Nom')}>
              Renommer
            </button>
            <button onClick={() => handleDelete(team.id)}>
              Supprimer
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

// ============================================
// Exemple 8: Gestion d'Erreurs Avancée
// ============================================

/**
 * Gestion d'erreurs avec différents types.
 */
export function ExampleAdvancedErrorHandling() {
  const { data: projects, error } = useProjects()
  const deleteProject = useDeleteProject()
  
  // Gestion erreur query
  if (error) {
    if (isNotFoundError(error)) {
      return <div>Aucun projet trouvé</div>
    }
    return <div>Erreur : {getErrorMessage(error)}</div>
  }
  
  // Gestion erreur mutation
  const handleDelete = async (id: number) => {
    try {
      await deleteProject.mutateAsync(id)
      alert('Projet supprimé')
    } catch (err) {
      if (isNotFoundError(err)) {
        alert('Projet non trouvé')
      } else if (isBadRequestError(err)) {
        alert('Impossible de supprimer ce projet')
      } else {
        alert(`Erreur : ${getErrorMessage(err)}`)
      }
    }
  }
  
  return (
    <ul>
      {projects?.map(p => (
        <li key={p.id}>
          {p.nom}
          <button onClick={() => handleDelete(p.id)}>Supprimer</button>
        </li>
      ))}
    </ul>
  )
}

// ============================================
// Exemple 9: Invalidation Manuelle
// ============================================

/**
 * Invalidation manuelle du cache.
 */
export function ExampleManualInvalidation({ projectId }: { projectId: number }) {
  const { data: matches } = useMatches(projectId)
  const { refetch } = useMatches(projectId)
  
  const handleRefresh = () => {
    refetch() // Refetch manuel
  }
  
  return (
    <div>
      <button onClick={handleRefresh}>Rafraîchir Matchs</button>
      <p>{matches?.length} matchs</p>
    </div>
  )
}

// ============================================
// Exemple 10: Workflow Complet avec États
// ============================================

/**
 * Workflow complet : créer projet → ajouter équipes → créer matchs → déplacer.
 */
export function ExampleCompleteWorkflow() {
  const { data: projects } = useProjects()
  const createProject = useCreateProject()
  const createTeam = useCreateTeam()
  const createMatch = useCreateMatch()
  const moveMatch = useMoveMatch()
  
  const handleCompleteWorkflow = async () => {
    try {
      // 1. Créer projet
      const project = await createProject.mutateAsync({
        nom: 'Projet Test',
        sport: 'Volleyball',
        config_yaml_data: null,
        config_excel_data: null,
      })
      console.log('✅ Projet créé:', project.id)
      
      // 2. Créer équipes
      const team1 = await createTeam.mutateAsync({
        project_id: project.id,
        nom: 'Équipe A',
        poule: 'P1',
        institution: 'Lycée A',
        genre: 'M',
        horaires_preferes: [],
        lieux_preferes: [],
      })
      const team2 = await createTeam.mutateAsync({
        project_id: project.id,
        nom: 'Équipe B',
        poule: 'P1',
        institution: 'Lycée B',
        genre: 'M',
        horaires_preferes: [],
        lieux_preferes: [],
      })
      console.log('✅ Équipes créées:', team1.id, team2.id)
      
      // 3. Créer match
      const match = await createMatch.mutateAsync({
        project_id: project.id,
        equipe_domicile_id: team1.id,
        equipe_exterieur_id: team2.id,
        gymnase_id: 1, // Supposé existant
        semaine: 3,
        horaire: '10:00',
      })
      console.log('✅ Match créé:', match.id)
      
      // 4. Déplacer match
      await moveMatch.mutateAsync({ 
        id: match.id, 
        payload: { nouvelle_semaine: 5 } 
      })
      console.log('✅ Match déplacé vers semaine 5')
      
      alert('Workflow complet terminé !')
    } catch (err) {
      console.error('❌ Erreur:', getErrorMessage(err))
      alert('Erreur dans le workflow')
    }
  }
  
  return (
    <div>
      <h2>Workflow Complet</h2>
      <p>{projects?.length} projets existants</p>
      <button onClick={handleCompleteWorkflow}>
        Exécuter Workflow Complet
      </button>
    </div>
  )
}
