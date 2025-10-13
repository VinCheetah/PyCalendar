import type { ButtonHTMLAttributes, ReactNode } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'success' | 'danger' | 'outline' | 'ghost' | 'link'
type ButtonSize = 'sm' | 'md' | 'lg' | 'xl'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: ButtonVariant
  size?: ButtonSize
  fullWidth?: boolean
  isLoading?: boolean
  loadingText?: string
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-lg hover:shadow-xl hover:from-blue-700 hover:to-indigo-800 hover:scale-105 focus:ring-blue-200',
  secondary:
    'bg-gradient-to-r from-purple-600 to-pink-700 text-white shadow-lg hover:shadow-xl hover:from-purple-700 hover:to-pink-800 hover:scale-105 focus:ring-purple-200',
  success:
    'bg-gradient-to-r from-emerald-600 to-teal-700 text-white shadow-lg hover:shadow-xl hover:from-emerald-700 hover:to-teal-800 hover:scale-105 focus:ring-emerald-200',
  danger:
    'bg-gradient-to-r from-red-600 to-pink-700 text-white shadow-lg hover:shadow-xl hover:from-red-700 hover:to-pink-800 hover:scale-105 focus:ring-red-200',
  outline:
    'border-2 border-gray-300 text-gray-700 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-700 focus:ring-blue-100',
  ghost:
    'text-gray-700 hover:bg-gray-100 hover:text-gray-900 focus:ring-gray-100',
  link: 'text-blue-600 underline-offset-4 hover:underline focus:ring-0',
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-5 py-2.5 text-base',
  lg: 'px-6 py-3.5 text-lg',
  xl: 'px-8 py-4 text-xl',
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  className = '',
  isLoading,
  loadingText,
  disabled,
  ...props
}: ButtonProps) {
  const baseClasses = 'inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-300 focus:outline-none focus:ring-4 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none'
  
  const classes = [
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    fullWidth && 'w-full',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <button
      className={classes}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <svg
            className="animate-spin h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          {loadingText || 'Chargement...'}
        </>
      ) : (
        children
      )}
    </button>
  )
}
