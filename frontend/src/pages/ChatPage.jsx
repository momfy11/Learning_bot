/**
 * Chat Page
 * 
 * Main chat interface with conversation history and voice support.
 * Integrates with Layout's sidebar for conversation list.
 */

import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, useOutletContext } from 'react-router-dom'
import { createPortal } from 'react-dom'
import {
  sendMessage,
  getConversations,
  getConversation,
  deleteConversation
} from '../services/chatService'
import { getProfiles } from '../services/profileService'
import { useVoice } from '../hooks/useVoice'

import ChatMessage from '../components/ChatMessage'
import ChatInput from '../components/ChatInput'
import LoadingSpinner from '../components/LoadingSpinner'

import { Settings, ChevronDown, Plus, Trash2, MessageSquare } from 'lucide-react'

/**
 * Sidebar Conversation List Component
 * Rendered into the Layout's sidebar content slot
 */
function SidebarConversationList({
  conversations,
  activeId,
  onSelect,
  onDelete,
  onNewChat,
  collapsed
}) {
  if (collapsed) {
    // Collapsed view: just show new chat button
    return (
      <div className="p-2">
        <button
          onClick={onNewChat}
          className="w-full p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex justify-center"
          title="New Chat"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* New Chat button */}
      <div className="p-2">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {conversations.length === 0 ? (
          <p className="text-xs text-gray-500 text-center py-4">
            No conversations yet. Start chatting!
          </p>
        ) : (
          <div className="space-y-1">
            {conversations.map(conv => (
              <div
                key={conv.id}
                className={`
                  group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
                  ${activeId === conv.id
                    ? 'bg-primary-50 text-primary-700'
                    : 'hover:bg-gray-100 text-gray-700'
                  }
                `}
                onClick={() => onSelect(conv.id)}
              >
                <MessageSquare className="w-4 h-4 flex-shrink-0 opacity-60" />
                <span className="flex-1 text-sm truncate">{conv.title}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(conv.id)
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-200 rounded transition-opacity"
                  title="Delete"
                >
                  <Trash2 className="w-3.5 h-3.5 text-gray-500" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Main chat page component
 * 
 * @returns {React.ReactNode} Chat interface
 */
function ChatPage() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const messagesEndRef = useRef(null)
  const { sidebarCollapsed, isMobile, closeSidebar } = useOutletContext() || {}

  // State
  const [conversations, setConversations] = useState([])
  const [currentConversation, setCurrentConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [profiles, setProfiles] = useState([])
  const [selectedProfileId, setSelectedProfileId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [showProfileSelect, setShowProfileSelect] = useState(false)
  const [speakingMessageId, setSpeakingMessageId] = useState(null)

  // Voice hook
  const {
    isListening,
    transcript,
    isSpeaking,
    isSupported: voiceSupported,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    clearTranscript,
  } = useVoice()

  /**
   * Scroll to bottom of messages
   */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  /**
   * Load conversations and profiles on mount
   */
  useEffect(() => {
    const loadData = async () => {
      try {
        const [convData, profileData] = await Promise.all([
          getConversations(),
          getProfiles(),
        ])
        setConversations(convData)
        setProfiles(profileData)

        // Set default profile
        const defaultProfile = profileData.find(p => p.is_default)
        if (defaultProfile) {
          setSelectedProfileId(defaultProfile.id)
        }
      } catch (error) {
        console.error('Failed to load data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  /**
   * Load conversation when ID changes
   */
  useEffect(() => {
    const loadConversation = async () => {
      if (conversationId) {
        try {
          const conv = await getConversation(conversationId)
          setCurrentConversation(conv)
          setMessages(conv.messages || [])
        } catch (error) {
          console.error('Failed to load conversation:', error)
          navigate('/chat')
        }
      } else {
        setCurrentConversation(null)
        setMessages([])
      }
    }

    loadConversation()
  }, [conversationId, navigate])

  /**
   * Scroll to bottom when messages change
   */
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  /**
   * Handle sending a message
   * 
   * @param {string} text - Message text
   * @param {boolean} isVoice - Whether it was voice input
   * @param {Array} images - Array of image data objects
   */
  const handleSendMessage = async (text, isVoice = false, images = []) => {
    if ((!text.trim() && images.length === 0) || sending) return

    setSending(true)

    // Clear transcript if voice message
    if (isVoice) {
      clearTranscript()
    }

    // Add user message immediately for better UX
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text,
      is_voice: isVoice,
      images: images.map(img => img.base64), // Store base64 for display
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMessage])

    try {
      const response = await sendMessage(
        text,
        currentConversation?.id || null,
        selectedProfileId,
        isVoice,
        images
      )

      // Add assistant message
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.message,
        source_references: response.source_references,
        created_at: new Date().toISOString(),
      }
      setMessages(prev => [...prev, assistantMessage])

      // Update conversation
      if (!currentConversation) {
        // New conversation was created
        navigate(`/chat/${response.conversation_id}`)
        // Refresh conversation list
        const newConversations = await getConversations()
        setConversations(newConversations)
      }

      // Auto-speak response if it was voice input
      if (isVoice && voiceSupported) {
        speak(response.message)
        setSpeakingMessageId(assistantMessage.id)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      // Remove the user message on error
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setSending(false)
    }
  }

  /**
   * Handle speaking a message
   * 
   * @param {string} text - Text to speak
   * @param {number} messageId - Message ID
   */
  const handleSpeak = (text, messageId) => {
    if (isSpeaking && speakingMessageId === messageId) {
      stopSpeaking()
      setSpeakingMessageId(null)
    } else {
      speak(text)
      setSpeakingMessageId(messageId)
    }
  }

  /**
   * Handle selecting a conversation
   * 
   * @param {number} id - Conversation ID
   */
  const handleSelectConversation = (id) => {
    navigate(`/chat/${id}`)
    if (isMobile && closeSidebar) {
      closeSidebar()
    }
  }

  /**
   * Handle deleting a conversation
   * 
   * @param {number} id - Conversation ID
   */
  const handleDeleteConversation = async (id) => {
    if (!confirm('Delete this conversation?')) return

    try {
      await deleteConversation(id)
      setConversations(prev => prev.filter(c => c.id !== id))

      if (currentConversation?.id === id) {
        navigate('/chat')
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  /**
   * Handle starting a new chat
   */
  const handleNewChat = () => {
    navigate('/chat')
    if (isMobile && closeSidebar) {
      closeSidebar()
    }
  }

  /**
   * Handle feedback change on a message
   * 
   * @param {number} messageId - Message ID
   * @param {boolean} isHelpful - Feedback value
   */
  const handleFeedbackChange = (messageId, isHelpful) => {
    setMessages(prev => prev.map(msg =>
      msg.id === messageId ? { ...msg, feedback: isHelpful } : msg
    ))
  }

  // Get the sidebar slot element for portal rendering
  const sidebarSlot = document.getElementById('sidebar-content-slot')

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="large" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-white flex-shrink-0">
        <h2 className="font-medium text-gray-900 truncate">
          {currentConversation?.title || 'New Conversation'}
        </h2>

        {/* Profile selector */}
        <div className="relative">
          <button
            onClick={() => setShowProfileSelect(!showProfileSelect)}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            <Settings className="w-4 h-4" />
            <span className="hidden sm:inline">
              {profiles.find(p => p.id === selectedProfileId)?.name || 'No profile'}
            </span>
            <ChevronDown className="w-4 h-4" />
          </button>

          {showProfileSelect && (
            <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border py-1 z-10">
              <button
                onClick={() => {
                  setSelectedProfileId(null)
                  setShowProfileSelect(false)
                }}
                className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-100 ${!selectedProfileId ? 'bg-primary-50 text-primary-700' : ''
                  }`}
              >
                No profile
              </button>
              {profiles.map(profile => (
                <button
                  key={profile.id}
                  onClick={() => {
                    setSelectedProfileId(profile.id)
                    setShowProfileSelect(false)
                  }}
                  className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-100 ${selectedProfileId === profile.id ? 'bg-primary-50 text-primary-700' : ''
                    }`}
                >
                  {profile.name}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 chat-scrollbar">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
              <span className="text-3xl">📚</span>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Ready to learn?
            </h3>
            <p className="text-gray-500 max-w-md">
              Ask me a question and I'll guide you to find the answer yourself.
              I'll point you to the right resources instead of giving direct answers!
            </p>
          </div>
        ) : (
          messages.map(message => (
            <ChatMessage
              key={message.id}
              message={message}
              onSpeak={(text) => handleSpeak(text, message.id)}
              isSpeaking={isSpeaking && speakingMessageId === message.id}
              onFeedbackChange={handleFeedbackChange}
            />
          ))
        )}

        {/* Loading indicator */}
        {sending && (
          <div className="flex gap-3">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-green-600 text-sm">🤖</span>
            </div>
            <div className="bg-white border rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot" />
                <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot" />
                <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="p-4 border-t bg-white flex-shrink-0">
        <ChatInput
          onSend={handleSendMessage}
          isLoading={sending}
          isListening={isListening}
          transcript={transcript}
          onStartListening={startListening}
          onStopListening={stopListening}
          voiceSupported={voiceSupported}
        />
      </div>

      {/* Portal for sidebar content */}
      {sidebarSlot && createPortal(
        <SidebarConversationList
          conversations={conversations}
          activeId={currentConversation?.id}
          onSelect={handleSelectConversation}
          onDelete={handleDeleteConversation}
          onNewChat={handleNewChat}
          collapsed={sidebarCollapsed}
        />,
        sidebarSlot
      )}
    </div>
  )
}

export default ChatPage
