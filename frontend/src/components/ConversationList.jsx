/**
 * Conversation List Component
 * 
 * Displays list of past conversations in sidebar.
 */

import { Trash2, MessageSquare } from 'lucide-react'

/**
 * List of conversations
 * 
 * @param {Object} props - Component props
 * @param {Array} props.conversations - List of conversations
 * @param {number} props.activeId - Currently active conversation ID
 * @param {Function} props.onSelect - Called when conversation is selected
 * @param {Function} props.onDelete - Called when delete is clicked
 * @param {Function} props.onNewChat - Called when new chat is clicked
 * @returns {React.ReactNode} Conversation list
 */
function ConversationList({
  conversations = [],
  activeId,
  onSelect,
  onDelete,
  onNewChat,
}) {
  /**
   * Format date for display
   * 
   * @param {string} dateString - ISO date string
   * @returns {string} Formatted date
   */
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="flex flex-col h-full">
      {/* New chat button */}
      <button
        onClick={onNewChat}
        className="flex items-center gap-2 m-2 px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
      >
        <MessageSquare className="w-4 h-4" />
        <span>New Chat</span>
      </button>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <p className="text-center text-gray-500 py-8 px-4">
            No conversations yet. Start chatting!
          </p>
        ) : (
          <div className="space-y-1 p-2">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={`
                  group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
                  ${activeId === conv.id
                    ? 'bg-primary-50 text-primary-700'
                    : 'hover:bg-gray-100'
                  }
                `}
                onClick={() => onSelect(conv.id)}
              >
                <MessageSquare className="w-4 h-4 flex-shrink-0" />

                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{conv.title}</p>
                  <p className="text-xs text-gray-500">
                    {formatDate(conv.updated_at)}
                  </p>
                </div>

                {/* Delete button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(conv.id)
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-opacity"
                  title="Delete conversation"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ConversationList
