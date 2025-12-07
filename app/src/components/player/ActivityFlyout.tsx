import React, { useEffect } from 'react'
import DOMPurify from 'dompurify'

interface ActivityFlyoutProps {
  isOpen: boolean
  onClose: () => void
  activityName: string
  content: string
}

export default function ActivityFlyout({ isOpen, onClose, activityName, content }: ActivityFlyoutProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  if (!isOpen) return null

  const sanitizedHtml = DOMPurify.sanitize(content)

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Flyout Panel */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden transform transition-all"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="bg-gray-50 px-6 py-4 border-b flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-800">{activityName}</h3>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 transition-colors p-2 rounded-lg hover:bg-gray-200"
              aria-label="Close flyout"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* Content */}
          <div className="overflow-y-auto max-h-[calc(80vh-80px)] p-6">
            <div
              className="prose max-w-none"
              dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
            />
          </div>
        </div>
      </div>
    </>
  )
}

