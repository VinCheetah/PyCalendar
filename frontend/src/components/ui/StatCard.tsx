interface StatCardProps {
  value: number | string
  label: string
  variant?: 'blue' | 'red' | 'gradient'
  className?: string
}

export function StatCard({ value, label, variant = 'blue', className = '' }: StatCardProps) {
  const getColor = () => {
    switch (variant) {
      case 'blue':
        return '#0055A4'
      case 'red':
        return '#EF4444'
      case 'gradient':
        return 'transparent'
      default:
        return '#0055A4'
    }
  }

  const valueStyle = variant === 'gradient' 
    ? {
        background: 'linear-gradient(135deg, #0055A4 0%, #EF4444 100%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text'
      }
    : { color: getColor() }

  return (
    <div
      className={`bg-white rounded-xl p-6 text-center ${className}`}
      style={{
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)'
      }}
    >
      <div
        className="text-4xl font-extrabold mb-2"
        style={valueStyle}
      >
        {value}
      </div>
      <div className="text-sm text-gray-500 mt-2">
        {label}
      </div>
    </div>
  )
}
