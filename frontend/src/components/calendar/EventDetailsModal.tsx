/**
 * Modale pour afficher les détails d'un match.
 * 
 * Fonctionnalités :
 * - Afficher équipes, gymnase, semaine
 * - Bouton Fixer/Défixer (seulement si match.semaine >= semaineMin)
 * - Bouton Supprimer
 */

import { Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { 
  XMarkIcon, 
  LockClosedIcon, 
  LockOpenIcon,
  TrashIcon 
} from '@heroicons/react/24/outline'

import { useFixMatch, useUnfixMatch, useDeleteMatch } from '@/hooks'
import { getErrorMessage } from '@/utils/apiHelpers'
import { showSuccess, showError } from '@/lib/toast'
import type { Match } from '@/types'

interface EventDetailsModalProps {
  match: Match
  isOpen: boolean
  onClose: () => void
  semaineMin: number
}

export default function EventDetailsModal({
  match,
  isOpen,
  onClose,
  semaineMin,
}: EventDetailsModalProps) {
  const fixMatch = useFixMatch()
  const unfixMatch = useUnfixMatch()
  const deleteMatch = useDeleteMatch()

  // Vérifier si le match est modifiable (semaine >= semaine_min)
  const isModifiable = (match.semaine ?? 0) >= semaineMin

  // Fixer match
  const handleFix = async () => {
    try {
      await fixMatch.mutateAsync(match.id)
      showSuccess('Match fixé avec succès')
      onClose()
    } catch (error) {
      showError(`Erreur : ${getErrorMessage(error)}`)
    }
  }

  // Défixer match
  const handleUnfix = async () => {
    try {
      await unfixMatch.mutateAsync(match.id)
      showSuccess('Match défixé avec succès')
      onClose()
    } catch (error) {
      showError(`Erreur : ${getErrorMessage(error)}`)
    }
  }

  // Supprimer match
  const handleDelete = async () => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce match ?')) return

    try {
      await deleteMatch.mutateAsync({
        id: match.id,
        projectId: match.project_id,
      })
      showSuccess('Match supprimé avec succès')
      onClose()
    } catch (error) {
      showError(`Erreur : ${getErrorMessage(error)}`)
    }
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        {/* Modal */}
        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 shadow-xl transition-all">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <Dialog.Title className="text-lg font-medium text-gray-900">
                    Détails du match
                  </Dialog.Title>
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-500"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                {/* Contenu */}
                <div className="space-y-4">
                  {/* Équipes */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Équipes
                    </label>
                    <div className="mt-1 text-base text-gray-900">
                      {match.equipe1_nom}
                      <span className="mx-2 text-gray-500">vs</span>
                      {match.equipe2_nom}
                    </div>
                  </div>

                  {/* Gymnase */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Gymnase
                    </label>
                    <div className="mt-1 text-base text-gray-900">
                      {match.gymnase || 'Non assigné'}
                    </div>
                  </div>

                  {/* Semaine */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Semaine
                    </label>
                    <div className="mt-1 text-base text-gray-900">
                      Semaine {match.semaine}
                      {match.semaine && match.semaine < semaineMin && (
                        <span className="ml-2 text-sm text-orange-600">
                          (Non modifiable - avant semaine {semaineMin})
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Horaire */}
                  {match.horaire && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Horaire
                      </label>
                      <div className="mt-1 text-base text-gray-900">
                        {match.horaire}
                      </div>
                    </div>
                  )}

                  {/* Poule */}
                  {match.poule && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Poule
                      </label>
                      <div className="mt-1 text-base text-gray-900">
                        {match.poule}
                      </div>
                    </div>
                  )}

                  {/* État */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      État
                    </label>
                    <div className="mt-1">
                      {match.est_fixe ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          <LockClosedIcon className="h-4 w-4 mr-1" />
                          Fixé (non modifiable par le solver)
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          <LockOpenIcon className="h-4 w-4 mr-1" />
                          Modifiable
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="mt-6 flex gap-3">
                  {/* Fixer/Défixer - Seulement si semaine >= semaine_min */}
                  {isModifiable && (
                    <>
                      {match.est_fixe ? (
                        <button
                          onClick={handleUnfix}
                          disabled={unfixMatch.isPending}
                          className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                        >
                          <LockOpenIcon className="h-5 w-5 mr-2" />
                          {unfixMatch.isPending ? 'Défixage...' : 'Défixer'}
                        </button>
                      ) : (
                        <button
                          onClick={handleFix}
                          disabled={fixMatch.isPending}
                          className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 disabled:opacity-50"
                        >
                          <LockClosedIcon className="h-5 w-5 mr-2" />
                          {fixMatch.isPending ? 'Fixage...' : 'Fixer'}
                        </button>
                      )}
                    </>
                  )}

                  {/* Supprimer */}
                  <button
                    onClick={handleDelete}
                    disabled={deleteMatch.isPending}
                    className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                  >
                    <TrashIcon className="h-5 w-5 mr-2" />
                    {deleteMatch.isPending ? 'Suppression...' : 'Supprimer'}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}
