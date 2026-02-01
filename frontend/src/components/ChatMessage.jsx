/**
 * Chat Message Component
 * 
 * Displays a single message in the chat.
 * Shows source references for bot responses.
 * Includes feedback buttons (thumbs up/down) for assistant messages.
 */

import { useState } from 'react'
import { User, Bot, BookOpen, Volume2, VolumeX, ThumbsUp, ThumbsDown } from 'lucide-react'
import { submitFeedback } from '../services/chatService'

/**
 * Single chat message display
 * 
 * @param {Object} props - Component props
 * @param {Object} props.message - Message data
 * @param {number} props.message.id - Message ID
 * @param {string} props.message.role - 'user' or 'assistant'
 * @param {string} props.message.content - Message text
 * @param {Array} props.message.source_references - Document references
 * @param {boolean} props.message.is_voice - Was voice input
 * @param {boolean|null} props.message.feedback - Existing feedback (true/false/null)
 * @param {Function} props.onSpeak - Function to speak the message
 * @param {boolean} props.isSpeaking - Currently speaking this message
 * @param {Function} props.onFeedbackChange - Callback when feedback is given
 * @returns {React.ReactNode} Message bubble
 */
function ChatMessage({ message, onSpeak, isSpeaking, onFeedbackChange }) {
  const isUser = message.role === 'user'
  const [feedbackLoading, setFeedbackLoading] = useState(false)
  const [localFeedback, setLocalFeedback] = useState(message.feedback)

  /**
   * Handle feedback button click
   * 
   * @param {boolean} isHelpful - True for thumbs up, false for thumbs down
   */
  const handleFeedback = async (isHelpful) => {
    if (feedbackLoading) return
    
    setFeedbackLoading(true)
    try {
      await submitFeedback(message.id, isHelpful)
      setLocalFeedback(isHelpful)
      if (onFeedbackChange) {
        onFeedbackChange(message.id, isHelpful)
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    } finally {
      setFeedbackLoading(false)
    }
  }

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`
          w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
          ${isUser ? 'bg-primary-100' : 'bg-green-100'}
        `}
      >
        {isUser ? (
          <User className="w-4 h-4 text-primary-700" />
        ) : (
          <Bot className="w-4 h-4 text-green-700" />
        )}
      </div>

      {/* Message content */}
      <div className={`flex flex-col max-w-[80%] ${isUser ? 'items-end' : ''}`}>
        <div
          className={`
            px-4 py-3 rounded-2xl
            ${isUser
              ? 'bg-primary-600 text-white rounded-tr-sm'
              : 'bg-white border border-gray-200 rounded-tl-sm'
            }
          `}
        >
          {/* Voice indicator */}
          {message.is_voice && (
            <span className="text-xs opacity-70 block mb-1">
              🎤 Voice message
            </span>
          )}

          {/* Attached images */}
          {message.images && message.images.length > 0 && (
            <div className="flex gap-2 flex-wrap mb-2">
              {message.images.map((img, index) => (
                <img
                  key={index}
                  src={img}
                  alt={`Attachment ${index + 1}`}
                  className="max-w-[200px] max-h-[200px] rounded-lg object-cover"
                />
              ))}
            </div>
          )}

          {/* Message text */}
          {message.content && (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>

        {/* Source references (for assistant messages) */}
        {!isUser && message.source_references && message.source_references.length > 0 && (
          <div className="mt-2 space-y-1">
            <p className="text-xs text-gray-500 font-medium">📚 Find more in:</p>
            {message.source_references.map((ref, index) => (
              <div
                key={index}
                className="flex items-center gap-2 text-xs bg-gray-50 px-3 py-2 rounded-lg"
              >
                <BookOpen className="w-3 h-3 text-gray-400" />
                <span className="text-gray-700">{ref.document_title}</span>
                {ref.chapter && (
                  <span className="text-gray-500">• {ref.chapter}</span>
                )}
                {ref.page_number && (
                  <span className="text-primary-600 font-medium">
                    Page {ref.page_number}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Feedback and speak buttons for assistant messages */}
        {!isUser && (
          <div className="mt-2 flex items-center gap-4">
            {/* Feedback buttons */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">Did this help?</span>
              <button
                onClick={() => handleFeedback(true)}
                disabled={feedbackLoading}
                className={`
                  p-1 rounded transition-colors
                  ${localFeedback === true 
                    ? 'text-green-600 bg-green-50' 
                    : 'text-gray-400 hover:text-green-600 hover:bg-green-50'
                  }
                `}
                title="Helpful"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => handleFeedback(false)}
                disabled={feedbackLoading}
                className={`
                  p-1 rounded transition-colors
                  ${localFeedback === false 
                    ? 'text-red-600 bg-red-50' 
                    : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
                  }
                `}
                title="Not helpful"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>
            </div>
            
            {/* Speak button */}
            {onSpeak && (
              <button
                onClick={() => onSpeak(message.content)}
                className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
              >
                {isSpeaking ? (
                  <>
                    <VolumeX className="w-3 h-3" />
                    Stop
                  </>
                ) : (
                  <>
                    <Volume2 className="w-3 h-3" />
                    Listen
                  </>
                )}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatMessage
