import { CalendarIcon, MapPinIcon } from '@heroicons/react/24/outline'

interface MatchCardProps {
  team1: string
  team2: string
  institution1?: string
  institution2?: string
  time?: string
  venue?: string
  category?: string
  gender?: 'M' | 'F'
  pool?: string
  onClick?: () => void
  className?: string
}

export function MatchCard({
  team1,
  team2,
  institution1,
  institution2,
  time,
  venue,
  category,
  gender,
  pool,
  onClick,
  className = ''
}: MatchCardProps) {
  return (
    <div
      onClick={onClick}
      className={`group cursor-pointer transition-all duration-300 ${className}`}
      style={{
        background: 'white',
        borderRadius: '16px',
        padding: '1.5rem',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 85, 164, 0.06)',
        borderLeft: '5px solid #3B82F6',
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
      {/* Header avec badges */}
      <div className="flex justify-between items-center mb-4 pb-3 border-b border-gray-200">
        <div className="flex gap-2 flex-wrap">
          {pool && (
            <span
              className="px-3 py-1 rounded-xl text-xs font-bold uppercase tracking-wide text-white"
              style={{
                background: 'linear-gradient(135deg, #0055A4, #1E3A8A)',
                boxShadow: '0 2px 8px rgba(0, 85, 164, 0.25)'
              }}
            >
              {pool}
            </span>
          )}
          {gender && (
            <span
              className="px-3 py-1 rounded-xl text-xs font-bold uppercase tracking-wide text-white"
              style={{
                background: 'linear-gradient(135deg, #3B82F6, #2563EB)',
                boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)'
              }}
            >
              {gender === 'M' ? '♂ Masculin' : '♀ Féminin'}
            </span>
          )}
          {category && (
            <span
              className="px-3 py-1 rounded-xl text-xs font-bold uppercase tracking-wide text-white"
              style={{
                background: '#8B5CF6'
              }}
            >
              {category}
            </span>
          )}
        </div>
        {time && (
          <div
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold text-sm"
            style={{
              background: '#EFF6FF',
              color: '#1E293B'
            }}
          >
            <CalendarIcon className="w-4 h-4" />
            {time}
          </div>
        )}
      </div>

      {/* Teams container - Design symétrique */}
      <div className="grid grid-cols-[1fr_auto_1fr] gap-4 items-center my-5 py-4">
        {/* Team 1 - Right aligned */}
        <div className="flex flex-col gap-2 items-end text-right">
          <div className="text-lg font-semibold text-gray-900">{team1}</div>
          {institution1 && (
            <div className="text-xs text-gray-500">{institution1}</div>
          )}
        </div>

        {/* VS Circle */}
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center relative transition-all duration-300 group-hover:scale-110 group-hover:rotate-[360deg]"
          style={{
            background: 'linear-gradient(135deg, #0055A4, #1E3A8A)',
            boxShadow: '0 4px 12px rgba(0, 85, 164, 0.3)'
          }}
        >
          <div
            className="absolute inset-[-3px] rounded-full border-2 opacity-30"
            style={{ borderColor: '#0055A4' }}
          />
          <span className="text-white font-extrabold text-sm tracking-wider">VS</span>
        </div>

        {/* Team 2 - Left aligned */}
        <div className="flex flex-col gap-2 items-start text-left">
          <div className="text-lg font-semibold text-gray-900">{team2}</div>
          {institution2 && (
            <div className="text-xs text-gray-500">{institution2}</div>
          )}
        </div>
      </div>

      {/* Footer avec venue */}
      {venue && (
        <div className="mt-4 pt-4 border-t-2 border-gray-200">
          <div
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg font-semibold"
            style={{
              background: '#F1F5F9',
              color: '#64748B'
            }}
          >
            <MapPinIcon className="w-5 h-5" />
            {venue}
          </div>
        </div>
      )}
    </div>
  )
}
