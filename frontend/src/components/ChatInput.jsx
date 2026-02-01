/**
 * Chat Input Component
 * 
 * Input field for typing messages with voice input and image upload support.
 * Supports file picker, drag & drop, and paste from clipboard.
 */

import { useState, useEffect, useRef } from 'react'
import { Send, Mic, MicOff, Loader2, Paperclip, X, Image as ImageIcon } from 'lucide-react'

/**
 * Convert file to base64 string
 * 
 * @param {File} file - File to convert
 * @returns {Promise<string>} Base64 encoded string
 */
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result)
    reader.onerror = (error) => reject(error)
  })
}

/**
 * Check if file is a valid image
 * 
 * @param {File} file - File to check
 * @returns {boolean} True if valid image
 */
const isValidImage = (file) => {
  const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  return validTypes.includes(file.type)
}

/**
 * Chat input with text, voice, and image support
 * 
 * @param {Object} props - Component props
 * @param {Function} props.onSend - Called when message is sent (text, isVoice, images)
 * @param {boolean} props.isLoading - Loading state
 * @param {boolean} props.isListening - Voice recording state
 * @param {string} props.transcript - Voice transcript
 * @param {Function} props.onStartListening - Start voice recording
 * @param {Function} props.onStopListening - Stop voice recording
 * @param {boolean} props.voiceSupported - Browser supports voice
 * @returns {React.ReactNode} Input component
 */
function ChatInput({
  onSend,
  isLoading = false,
  isListening = false,
  transcript = '',
  onStartListening,
  onStopListening,
  voiceSupported = true,
}) {
  const [message, setMessage] = useState('')
  const [attachedImages, setAttachedImages] = useState([]) // Array of {file, preview, base64}
  const wasListeningRef = useRef(false)
  const fileInputRef = useRef(null)
  const textareaRef = useRef(null)

  // Use transcript as message when listening
  const displayMessage = isListening ? transcript : message

  /**
   * Effect to send voice message when listening stops automatically
   */
  useEffect(() => {
    if (wasListeningRef.current && !isListening) {
      if (transcript.trim()) {
        handleSend(transcript.trim(), true)
      }
    }
    wasListeningRef.current = isListening
  }, [isListening, transcript])

  /**
   * Handle sending message with optional images
   * 
   * @param {string} text - Message text
   * @param {boolean} isVoice - Whether it was voice input
   */
  const handleSend = async (text, isVoice = false) => {
    const textToSend = text || displayMessage.trim()
    if ((!textToSend && attachedImages.length === 0) || isLoading) return

    // Convert images to base64 if not already done
    const imageData = await Promise.all(
      attachedImages.map(async (img) => ({
        base64: img.base64 || await fileToBase64(img.file),
        type: img.file.type
      }))
    )

    onSend(textToSend, isVoice, imageData)
    setMessage('')
    setAttachedImages([])
  }

  /**
   * Handle form submission
   * 
   * @param {Event} e - Form submit event
   */
  const handleSubmit = (e) => {
    e.preventDefault()
    handleSend(displayMessage.trim(), isListening)
  }

  /**
   * Handle file selection from input
   * 
   * @param {Event} e - Change event
   */
  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files || [])
    await addImages(files)
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  /**
   * Add images to attachments
   * 
   * @param {File[]} files - Files to add
   */
  const addImages = async (files) => {
    const validFiles = files.filter(isValidImage)
    
    if (validFiles.length === 0) {
      alert('Please select valid image files (JPEG, PNG, GIF, or WebP)')
      return
    }

    // Limit to 4 images total
    const remainingSlots = 4 - attachedImages.length
    const filesToAdd = validFiles.slice(0, remainingSlots)

    const newImages = await Promise.all(
      filesToAdd.map(async (file) => ({
        file,
        preview: URL.createObjectURL(file),
        base64: await fileToBase64(file)
      }))
    )

    setAttachedImages(prev => [...prev, ...newImages])
  }

  /**
   * Remove an attached image
   * 
   * @param {number} index - Index of image to remove
   */
  const removeImage = (index) => {
    setAttachedImages(prev => {
      const newImages = [...prev]
      // Revoke object URL to free memory
      URL.revokeObjectURL(newImages[index].preview)
      newImages.splice(index, 1)
      return newImages
    })
  }

  /**
   * Handle paste event for images
   * 
   * @param {ClipboardEvent} e - Paste event
   */
  const handlePaste = async (e) => {
    const items = Array.from(e.clipboardData?.items || [])
    const imageItems = items.filter(item => item.type.startsWith('image/'))
    
    if (imageItems.length > 0) {
      e.preventDefault()
      const files = imageItems.map(item => item.getAsFile()).filter(Boolean)
      await addImages(files)
    }
  }

  /**
   * Handle drag over
   * 
   * @param {DragEvent} e - Drag event
   */
  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  /**
   * Handle drop event for images
   * 
   * @param {DragEvent} e - Drop event
   */
  const handleDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    const files = Array.from(e.dataTransfer?.files || [])
    await addImages(files)
  }

  /**
   * Handle voice button click
   */
  const handleVoiceClick = () => {
    if (isListening) {
      onStopListening()
    } else {
      onStartListening()
    }
  }

  // Cleanup object URLs on unmount
  useEffect(() => {
    return () => {
      attachedImages.forEach(img => URL.revokeObjectURL(img.preview))
    }
  }, [])

  return (
    <div className="space-y-2">
      {/* Image previews */}
      {attachedImages.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {attachedImages.map((img, index) => (
            <div key={index} className="relative group">
              <img
                src={img.preview}
                alt={`Attachment ${index + 1}`}
                className="w-16 h-16 object-cover rounded-lg border border-gray-200"
              />
              <button
                type="button"
                onClick={() => removeImage(index)}
                className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 text-white rounded-full 
                           flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
          {attachedImages.length < 4 && (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-16 h-16 border-2 border-dashed border-gray-300 rounded-lg
                         flex items-center justify-center text-gray-400 hover:border-gray-400 hover:text-gray-500"
            >
              <ImageIcon className="w-6 h-6" />
            </button>
          )}
        </div>
      )}

      {/* Input form */}
      <form 
        onSubmit={handleSubmit} 
        className="flex items-end gap-2"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp"
          multiple
          className="hidden"
          onChange={handleFileSelect}
        />

        {/* Attachment button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading || attachedImages.length >= 4}
          className="p-3 text-gray-500 hover:bg-gray-100 rounded-xl transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed"
          title="Attach image (or paste/drag)"
        >
          <Paperclip className="w-5 h-5" />
        </button>

        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={displayMessage}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
            onPaste={handlePaste}
            placeholder={isListening ? 'Listening...' : attachedImages.length > 0 ? 'Add a message or send images...' : 'Ask a question...'}
            disabled={isLoading || isListening}
            rows={1}
            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl resize-none
                       focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                       disabled:bg-gray-50 disabled:text-gray-500"
            style={{ minHeight: '48px', maxHeight: '120px' }}
          />

          {/* Voice recording indicator */}
          {isListening && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <div className="w-3 h-3 bg-red-500 rounded-full voice-recording-pulse" />
            </div>
          )}
        </div>

        {/* Voice button */}
        {voiceSupported && (
          <button
            type="button"
            onClick={handleVoiceClick}
            disabled={isLoading}
            className={`
              p-3 rounded-xl transition-colors
              ${isListening
                ? 'bg-red-500 text-white hover:bg-red-600'
                : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
            title={isListening ? 'Stop recording' : 'Start voice input'}
          >
            {isListening ? (
              <MicOff className="w-5 h-5" />
            ) : (
              <Mic className="w-5 h-5" />
            )}
          </button>
        )}

        {/* Send button */}
        <button
          type="submit"
          disabled={isLoading || (!displayMessage.trim() && attachedImages.length === 0 && !isListening)}
          className="p-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Send message"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </form>

      {/* Drop zone hint (shown when dragging) */}
      <p className="text-xs text-gray-400 text-center">
        Tip: You can paste or drag & drop images
      </p>
    </div>
  )
}

export default ChatInput
