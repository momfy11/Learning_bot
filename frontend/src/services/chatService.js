/**
 * Chat Service
 * 
 * Functions for interacting with chat-related API endpoints.
 */

import api from './api'

/**
 * Send a message and get a learning response
 * 
 * @param {string} message - The user's question
 * @param {number|null} conversationId - Existing conversation ID (optional)
 * @param {number|null} profileId - Chat profile ID to use (optional)
 * @param {boolean} isVoice - Whether this was voice input
 * @param {Array<{base64: string, type: string}>} images - Array of images to send (optional)
 * @returns {Promise<Object>} Chat response with guidance
 */
export async function sendMessage(message, conversationId = null, profileId = null, isVoice = false, images = []) {
  const response = await api.post('/chat/send', {
    message,
    conversation_id: conversationId,
    profile_id: profileId,
    is_voice: isVoice,
    images: images.map(img => ({
      data: img.base64,  // Full data URL (data:image/jpeg;base64,...)
      type: img.type     // MIME type
    }))
  })
  return response.data
}

/**
 * Get all conversations for the current user
 * 
 * @returns {Promise<Array>} List of conversation summaries
 */
export async function getConversations() {
  const response = await api.get('/chat/conversations')
  return response.data
}

/**
 * Get a specific conversation with all messages
 * 
 * @param {number} conversationId - ID of the conversation
 * @returns {Promise<Object>} Conversation with messages
 */
export async function getConversation(conversationId) {
  const response = await api.get(`/chat/conversations/${conversationId}`)
  return response.data
}

/**
 * Delete a conversation
 * 
 * @param {number} conversationId - ID of the conversation to delete
 * @returns {Promise<void>}
 */
export async function deleteConversation(conversationId) {
  await api.delete(`/chat/conversations/${conversationId}`)
}

/**
 * Submit feedback on a response
 * 
 * @param {number} messageId - Message ID to give feedback on
 * @param {boolean} isHelpful - True = thumbs up, False = thumbs down
 * @returns {Promise<Object>} Confirmation with feedback details
 */
export async function submitFeedback(messageId, isHelpful) {
  const response = await api.post('/chat/feedback', {
    message_id: messageId,
    is_helpful: isHelpful,
  })
  return response.data
}
