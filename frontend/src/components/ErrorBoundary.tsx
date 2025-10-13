import { Component, type ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback: (error: Error, reset: () => void) => ReactNode
  onReset?: () => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

/**
 * Error Boundary pour capturer les erreurs React.
 * 
 * Capture toutes les erreurs dans le sous-arbre React et affiche
 * un fallback UI au lieu de crasher toute l'application.
 * 
 * Usage :
 * ```tsx
 * <ErrorBoundary fallback={(error, reset) => <ErrorFallback error={error} onReset={reset} />}>
 *   <App />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
    }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Mettre à jour l'état pour afficher le fallback UI au prochain rendu
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log l'erreur dans la console en développement
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, errorInfo)
    }
    
    // Ici on pourrait envoyer l'erreur à un service de monitoring (Sentry, etc.)
    // this.logErrorToService(error, errorInfo)
  }

  reset = (): void => {
    this.setState({
      hasError: false,
      error: null,
    })
    
    // Appeler le callback de reset si fourni
    this.props.onReset?.()
  }

  render(): ReactNode {
    if (this.state.hasError && this.state.error) {
      return this.props.fallback(this.state.error, this.reset)
    }

    return this.props.children
  }
}
