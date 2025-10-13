import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline'

interface ErrorFallbackProps {
  error: Error
  onReset: () => void
}

/**
 * Composant UI affiché quand une erreur est capturée par ErrorBoundary.
 * 
 * Affiche :
 * - Message d'erreur user-friendly
 * - Stack trace (en mode dev uniquement)
 * - Bouton "Réessayer" pour reset l'erreur
 * - Bouton "Recharger la page" en dernier recours
 */
export function ErrorFallback({ error, onReset }: ErrorFallbackProps) {
  const isDev = import.meta.env.DEV

  const handleReload = () => {
    window.location.reload()
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-8">
        {/* Icône et titre */}
        <div className="flex items-center justify-center mb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
            <ExclamationTriangleIcon className="h-10 w-10 text-red-600" aria-hidden="true" />
          </div>
        </div>

        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Une erreur s'est produite
          </h1>
          <p className="text-gray-600">
            Nous sommes désolés, quelque chose s'est mal passé. Vous pouvez réessayer ou recharger la page.
          </p>
        </div>

        {/* Message d'erreur */}
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <h2 className="text-sm font-semibold text-red-800 mb-2">
            Message d'erreur :
          </h2>
          <p className="text-sm text-red-700 font-mono">
            {error.message}
          </p>
        </div>

        {/* Stack trace (dev uniquement) */}
        {isDev && error.stack && (
          <details className="mb-6">
            <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 mb-2">
              Détails techniques (développement)
            </summary>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 overflow-auto max-h-96">
              <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                {error.stack}
              </pre>
            </div>
          </details>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={onReset}
            className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <ArrowPathIcon className="h-5 w-5 mr-2" aria-hidden="true" />
            Réessayer
          </button>
          
          <button
            onClick={handleReload}
            className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            Recharger la page
          </button>
        </div>

        {/* Note en développement */}
        {isDev && (
          <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              <span className="font-semibold">Mode développement :</span> Cette erreur a été capturée par ErrorBoundary. 
              En production, la stack trace ne sera pas visible.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
