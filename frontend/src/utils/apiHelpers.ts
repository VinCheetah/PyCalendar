/**
 * Utilitaires pour la gestion des erreurs API.
 * 
 * FastAPI retourne des erreurs au format : { detail: "Message d'erreur" }
 */

import { AxiosError } from 'axios'
import type { ApiError } from '@/types'

/**
 * Extrait le message d'erreur depuis une erreur Axios.
 * 
 * FastAPI retourne : { detail: "Message d'erreur" }
 * Axios retourne : AxiosError avec response.data
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const apiError = error.response?.data as ApiError | undefined
    if (apiError?.detail) {
      return apiError.detail
    }
    return error.message
  }
  
  if (error instanceof Error) {
    return error.message
  }
  
  return 'Une erreur inconnue est survenue'
}

/**
 * Vérifie si l'erreur est une erreur 404 (Not Found).
 * 
 * Utilisé pour détecter les ressources inexistantes.
 */
export function isNotFoundError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 404
  }
  return false
}

/**
 * Vérifie si l'erreur est une erreur 400 (Bad Request).
 * 
 * Utilisé pour détecter les requêtes invalides (ex: match non modifiable).
 */
export function isBadRequestError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 400
  }
  return false
}

/**
 * Vérifie si l'erreur est une erreur de validation (422 Unprocessable Entity).
 * 
 * Utilisé pour détecter les erreurs de validation de données.
 */
export function isValidationError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 422
  }
  return false
}

/**
 * Vérifie si l'erreur est une erreur serveur (5xx).
 * 
 * Utilisé pour détecter les erreurs côté serveur.
 */
export function isServerError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    const status = error.response?.status
    return status !== undefined && status >= 500 && status < 600
  }
  return false
}

/**
 * Vérifie si l'erreur est une erreur réseau (pas de réponse).
 * 
 * Utilisé pour détecter les problèmes de connexion.
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return !error.response && error.code === 'ERR_NETWORK'
  }
  return false
}
