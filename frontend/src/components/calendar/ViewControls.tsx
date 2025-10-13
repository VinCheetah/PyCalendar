/**
 * ViewControls Component - Display options
 * Inspired by visualization display options
 * 
 * Controls:
 * - Column count (for list views)
 * - Show available slots toggle
 * - Time granularity (30/60/120 min)
 */

export interface ViewOptions {
  columnCount: number
  showAvailableSlots: boolean
  timeGranularity: 30 | 60 | 120
}

interface ViewControlsProps {
  options: ViewOptions
  onOptionsChange: (options: ViewOptions) => void
}

export default function ViewControls({ options, onOptionsChange }: ViewControlsProps) {
  const handleColumnChange = (delta: number) => {
    const newCount = Math.max(2, Math.min(8, options.columnCount + delta))
    onOptionsChange({ ...options, columnCount: newCount })
  }

  const handleToggleSlots = () => {
    onOptionsChange({ ...options, showAvailableSlots: !options.showAvailableSlots })
  }

  const handleGranularityChange = (granularity: 30 | 60 | 120) => {
    onOptionsChange({ ...options, timeGranularity: granularity })
  }

  return (
    <div style={{
      background: 'white',
      borderRadius: '16px',
      padding: '1.5rem',
      boxShadow: '0 4px 12px rgba(0, 85, 164, 0.1)',
      marginBottom: '1.5rem'
    }}>
      {/* Header */}
      <h3 style={{
        fontSize: '1.125rem',
        fontWeight: 700,
        color: '#1E293B',
        margin: 0,
        marginBottom: '1.25rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}>
        ⚙️ Options d'affichage
      </h3>

      {/* Controls Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '1.25rem'
      }}>
        {/* Column Count Control */}
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: '#64748B',
            marginBottom: '0.625rem'
          }}>
            📊 Nombre de colonnes
          </label>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            background: '#F8FAFC',
            padding: '0.625rem',
            borderRadius: '12px',
            border: '2px solid #E2E8F0'
          }}>
            <button
              onClick={() => handleColumnChange(-1)}
              disabled={options.columnCount <= 2}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                border: 'none',
                background: options.columnCount <= 2 ? '#E2E8F0' : 'linear-gradient(135deg, #0055A4, #1E3A8A)',
                color: options.columnCount <= 2 ? '#94A3B8' : 'white',
                fontSize: '1.25rem',
                fontWeight: 700,
                cursor: options.columnCount <= 2 ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              −
            </button>
            
            <div style={{
              flex: 1,
              textAlign: 'center',
              fontSize: '0.9375rem',
              fontWeight: 700,
              color: '#0055A4'
            }}>
              {options.columnCount} colonnes
            </div>
            
            <button
              onClick={() => handleColumnChange(1)}
              disabled={options.columnCount >= 8}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                border: 'none',
                background: options.columnCount >= 8 ? '#E2E8F0' : 'linear-gradient(135deg, #0055A4, #1E3A8A)',
                color: options.columnCount >= 8 ? '#94A3B8' : 'white',
                fontSize: '1.25rem',
                fontWeight: 700,
                cursor: options.columnCount >= 8 ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              +
            </button>
          </div>
        </div>

        {/* Available Slots Toggle */}
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: '#64748B',
            marginBottom: '0.625rem'
          }}>
            📅 Créneaux disponibles
          </label>
          <button
            onClick={handleToggleSlots}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.75rem 1rem',
              borderRadius: '12px',
              border: '2px solid #E2E8F0',
              background: options.showAvailableSlots ? '#DBEAFE' : 'white',
              color: options.showAvailableSlots ? '#1E40AF' : '#64748B',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            {/* Toggle Switch */}
            <div style={{
              width: '44px',
              height: '24px',
              borderRadius: '12px',
              background: options.showAvailableSlots ? '#3B82F6' : '#CBD5E1',
              position: 'relative',
              transition: 'all 0.2s'
            }}>
              <div style={{
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                background: 'white',
                position: 'absolute',
                top: '2px',
                left: options.showAvailableSlots ? '22px' : '2px',
                transition: 'all 0.2s',
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
              }} />
            </div>
            <span>
              {options.showAvailableSlots ? 'Affichés' : 'Masqués'}
            </span>
          </button>
        </div>

        {/* Time Granularity */}
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: '#64748B',
            marginBottom: '0.625rem'
          }}>
            ⏱️ Granularité horaire
          </label>
          <div style={{
            display: 'flex',
            gap: '0.5rem'
          }}>
            {[30, 60, 120].map((granularity) => (
              <button
                key={granularity}
                onClick={() => handleGranularityChange(granularity as 30 | 60 | 120)}
                style={{
                  flex: 1,
                  padding: '0.625rem',
                  borderRadius: '10px',
                  border: options.timeGranularity === granularity ? '2px solid #0055A4' : '2px solid #E2E8F0',
                  background: options.timeGranularity === granularity ? '#EFF6FF' : 'white',
                  color: options.timeGranularity === granularity ? '#0055A4' : '#64748B',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {granularity} min
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
