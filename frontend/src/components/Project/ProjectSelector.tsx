import { useState, useRef, useEffect } from 'react'
import { ChevronDownIcon, MagnifyingGlassIcon, FolderIcon, CheckIcon } from '@heroicons/react/24/outline'
import { useProjects } from '@/hooks'

interface ProjectSelectorProps {
  value: number | null
  onChange: (projectId: number) => void
}

export function ProjectSelector({ value, onChange }: ProjectSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  const { data: projects, isLoading } = useProjects()

  const selectedProject = projects?.find(p => p.id === value)

  const filteredProjects = projects?.filter(p =>
    p.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.sport?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (isLoading) {
    return (
      <div 
        className="flex items-center justify-center px-6 py-3 rounded-2xl animate-pulse min-w-[280px]"
        style={{
          background: 'rgba(255, 255, 255, 0.95)',
          border: '2px solid rgba(0, 85, 164, 0.2)'
        }}
      >
        <div className="h-6 w-40 bg-gray-200 rounded"></div>
      </div>
    )
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between px-6 py-3 rounded-2xl shadow-xl transition-all duration-300 hover:scale-105 min-w-[280px]"
        style={{
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          border: '2px solid rgba(0, 85, 164, 0.2)',
          boxShadow: '0 8px 32px rgba(0, 85, 164, 0.15)'
        }}
      >
        <div className="flex items-center space-x-3">
          <div 
            className="p-2 rounded-xl"
            style={{
              background: 'linear-gradient(135deg, #0055A4 0%, #1E3A8A 100%)'
            }}
          >
            <FolderIcon className="h-5 w-5 text-white" />
          </div>
          <div className="text-left">
            <p className="text-xs font-medium" style={{ color: '#64748B' }}>
              Projet actif
            </p>
            <p className="font-bold" style={{ color: '#0055A4' }}>
              {selectedProject?.nom || 'Sélectionner un projet'}
            </p>
            {selectedProject?.sport && (
              <p className="text-xs" style={{ color: '#94A3B8' }}>
                {selectedProject.sport}
              </p>
            )}
          </div>
        </div>
        <ChevronDownIcon 
          className="h-5 w-5 transition-transform duration-300"
          style={{ 
            color: '#0055A4',
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)'
          }}
        />
      </button>

      {isOpen && (
        <div 
          className="absolute top-full mt-3 left-0 right-0 rounded-2xl shadow-2xl overflow-hidden z-50"
          style={{
            background: 'rgba(255, 255, 255, 0.98)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            border: '2px solid rgba(0, 85, 164, 0.2)',
            boxShadow: '0 20px 60px rgba(0, 85, 164, 0.25)',
            animation: 'slideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            minWidth: '320px'
          }}
        >
          <div className="p-4 border-b" style={{ borderColor: 'rgba(0, 85, 164, 0.1)' }}>
            <div className="relative">
              <MagnifyingGlassIcon 
                className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5"
                style={{ color: '#94A3B8' }}
              />
              <input
                type="text"
                placeholder="Rechercher un projet..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-xl border-2 focus:outline-none focus:border-[#0055A4] transition-colors"
                style={{
                  borderColor: 'rgba(0, 85, 164, 0.2)',
                  backgroundColor: 'rgba(248, 250, 252, 0.8)'
                }}
              />
            </div>
          </div>

          <div className="max-h-80 overflow-y-auto">
            {filteredProjects.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-gray-500">Aucun projet trouvé</p>
              </div>
            ) : (
              filteredProjects.map((project) => (
                <button
                  key={project.id}
                  onClick={() => {
                    onChange(project.id)
                    setIsOpen(false)
                    setSearchTerm('')
                  }}
                  className="w-full text-left p-4 transition-all duration-200"
                  style={{
                    background: project.id === value 
                      ? 'linear-gradient(135deg, rgba(0, 85, 164, 0.1) 0%, rgba(30, 58, 138, 0.1) 100%)'
                      : 'transparent',
                    borderBottom: '1px solid rgba(0, 85, 164, 0.05)'
                  }}
                  onMouseEnter={(e) => {
                    if (project.id !== value) {
                      e.currentTarget.style.background = 'linear-gradient(135deg, rgba(0, 85, 164, 0.05) 0%, rgba(30, 58, 138, 0.05) 100%)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (project.id !== value) {
                      e.currentTarget.style.background = 'transparent'
                    }
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <FolderIcon 
                          className="h-5 w-5"
                          style={{ color: project.id === value ? '#0055A4' : '#64748B' }}
                        />
                        <p 
                          className="font-bold"
                          style={{ color: project.id === value ? '#0055A4' : '#1E293B' }}
                        >
                          {project.nom}
                        </p>
                        {project.id === value && (
                          <CheckIcon className="h-5 w-5" style={{ color: '#10B981' }} />
                        )}
                      </div>
                      <div className="flex flex-wrap gap-2 text-sm mt-1">
                        {project.sport && (
                          <span 
                            className="px-2 py-0.5 rounded-full font-medium"
                            style={{ 
                              background: 'rgba(0, 85, 164, 0.1)',
                              color: '#0055A4'
                            }}
                          >
                            🏐 {project.sport}
                          </span>
                        )}
                        <span style={{ color: '#64748B' }}>
                          � {project.nb_semaines} semaines
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}

      <style>{`
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  )
}
