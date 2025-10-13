import { Toaster as HotToaster } from 'react-hot-toast'

/**
 * Composant Toaster global pour afficher les notifications toast.
 * 
 * Utilise react-hot-toast avec configuration personnalisée Tailwind.
 * À placer une seule fois dans App.tsx.
 * 
 * Types de toasts disponibles :
 * - toast.success() - Succès (vert)
 * - toast.error() - Erreur (rouge)
 * - toast() - Info (bleu)
 * - toast.loading() - Chargement (spinner)
 */
export function Toaster() {
  return (
    <HotToaster
      position="top-right"
      reverseOrder={false}
      gutter={8}
      containerClassName=""
      containerStyle={{}}
      toastOptions={{
        // Options par défaut pour tous les toasts
        duration: 4000, // 4 secondes
        
        style: {
          background: '#fff',
          color: '#374151',
          padding: '16px',
          borderRadius: '0.5rem',
          fontSize: '14px',
          fontWeight: '500',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          maxWidth: '400px',
        },
        
        // Success toast (vert)
        success: {
          duration: 3000,
          iconTheme: {
            primary: '#10b981', // green-500
            secondary: '#fff',
          },
          style: {
            background: '#fff',
            color: '#065f46', // green-800
          },
        },
        
        // Error toast (rouge)
        error: {
          duration: 5000,
          iconTheme: {
            primary: '#ef4444', // red-500
            secondary: '#fff',
          },
          style: {
            background: '#fff',
            color: '#991b1b', // red-800
          },
        },
        
        // Loading toast
        loading: {
          duration: Infinity, // Ne disparaît pas automatiquement
          style: {
            background: '#fff',
            color: '#1f2937', // gray-800
          },
        },
      }}
    />
  )
}
