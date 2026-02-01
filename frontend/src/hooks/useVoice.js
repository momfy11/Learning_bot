/**
 * useVoice Hook
 * 
 * Custom hook for voice input/output using Web Speech API.
 * Handles speech recognition and speech synthesis.
 * 
 * Note: Web Speech API is browser-native, no backend needed!
 */

import { useState, useCallback, useRef, useEffect } from 'react'

/**
 * Voice hook for speech recognition and synthesis
 * 
 * @returns {Object} Voice controls and state
 * 
 * @example
 * const { 
 *   isListening, 
 *   transcript, 
 *   startListening, 
 *   stopListening,
 *   speak 
 * } = useVoice()
 */
export function useVoice() {
  // State
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isSupported, setIsSupported] = useState(false)

  // Refs for API instances
  const recognitionRef = useRef(null)
  const synthesisRef = useRef(null)

  /**
   * Initialize speech recognition on mount
   */
  useEffect(() => {
    // Check browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

    if (SpeechRecognition) {
      setIsSupported(true)

      // Create recognition instance
      const recognition = new SpeechRecognition()
      recognition.continuous = false
      recognition.interimResults = true
      recognition.lang = 'en-US'

      // Handle results
      recognition.onresult = (event) => {
        let finalTranscript = ''
        let interimTranscript = ''

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript
          } else {
            interimTranscript += transcript
          }
        }

        setTranscript(finalTranscript || interimTranscript)
      }

      // Handle end
      recognition.onend = () => {
        setIsListening(false)
      }

      // Handle errors
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error)
        setIsListening(false)
      }

      recognitionRef.current = recognition
    }

    // Check speech synthesis support
    if ('speechSynthesis' in window) {
      synthesisRef.current = window.speechSynthesis
    }

    // Cleanup
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
      if (synthesisRef.current) {
        synthesisRef.current.cancel()
      }
    }
  }, [])

  /**
   * Start listening for voice input
   */
  const startListening = useCallback(() => {
    if (!recognitionRef.current) {
      console.warn('Speech recognition not supported')
      return
    }

    setTranscript('')
    setIsListening(true)
    recognitionRef.current.start()
  }, [])

  /**
   * Stop listening for voice input
   */
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      // Note: isListening will be set to false by the onend event
    }
  }, [])

  /**
   * Speak text using speech synthesis
   * 
   * @param {string} text - Text to speak
   * @param {Object} options - Speech options
   * @param {number} options.rate - Speech rate (0.1-10)
   * @param {number} options.pitch - Voice pitch (0-2)
   */
  const speak = useCallback((text, options = {}) => {
    if (!synthesisRef.current) {
      console.warn('Speech synthesis not supported')
      return
    }

    // Cancel any ongoing speech
    synthesisRef.current.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = options.rate || 1.0
    utterance.pitch = options.pitch || 1.0
    utterance.lang = 'en-US'

    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)

    synthesisRef.current.speak(utterance)
  }, [])

  /**
   * Stop any ongoing speech
   */
  const stopSpeaking = useCallback(() => {
    if (synthesisRef.current) {
      synthesisRef.current.cancel()
    }
    setIsSpeaking(false)
  }, [])

  /**
   * Clear the transcript
   */
  const clearTranscript = useCallback(() => {
    setTranscript('')
  }, [])

  return {
    // State
    isListening,    // True while recording
    transcript,     // Current transcript text
    isSpeaking,     // True while speaking
    isSupported,    // True if browser supports Web Speech API

    // Actions
    startListening, // Start voice recording
    stopListening,  // Stop voice recording
    speak,          // Speak text aloud
    stopSpeaking,   // Stop speaking
    clearTranscript, // Clear the transcript
  }
}
