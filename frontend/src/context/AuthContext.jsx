/**
 * Authentication Context
 * 
 * Provides authentication state and functions throughout the app.
 * Handles login, logout, and token management.
 */

import { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'

// Create the context
const AuthContext = createContext(null)

/**
 * Auth Provider Component
 * 
 * Wraps the app and provides authentication state to all children.
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components
 * @returns {React.ReactNode} Provider wrapped children
 */
export function AuthProvider({ children }) {
  // User state - null if not logged in
  const [user, setUser] = useState(null)
  // Loading state - true while checking initial auth
  const [loading, setLoading] = useState(true)

  /**
   * Check if user is already logged in on app load
   * 
   * Reads token from localStorage and validates it
   */
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token')

      if (token) {
        try {
          // Validate token by fetching user info
          const response = await api.get('/auth/me')
          setUser(response.data)
        } catch (error) {
          // Token is invalid, remove it
          localStorage.removeItem('token')
          setUser(null)
        }
      }

      setLoading(false)
    }

    checkAuth()
  }, [])

  /**
   * Login function
   * 
   * Authenticates user and stores token.
   * 
   * @param {string} email - User's email
   * @param {string} password - User's password
   * @returns {Promise<Object>} User data on success
   * @throws {Error} On authentication failure
   */
  const login = async (email, password) => {
    // API expects form data for OAuth2
    const formData = new URLSearchParams()
    formData.append('username', email)  // OAuth2 uses 'username' field
    formData.append('password', password)

    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    // Store token
    const { access_token } = response.data
    localStorage.setItem('token', access_token)

    // Fetch user data
    const userResponse = await api.get('/auth/me')
    setUser(userResponse.data)

    return userResponse.data
  }

  /**
   * Register function
   * 
   * Creates a new user account.
   * 
   * @param {string} email - User's email
   * @param {string} username - User's display name
   * @param {string} password - User's password
   * @returns {Promise<Object>} Created user data
   * @throws {Error} On registration failure
   */
  const register = async (email, username, password) => {
    const response = await api.post('/auth/register', {
      email,
      username,
      password,
    })

    return response.data
  }

  /**
   * Logout function
   * 
   * Clears user state and removes stored token.
   */
  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  // Context value provided to children
  const value = {
    user,        // Current user object or null
    loading,     // True while checking initial auth
    login,       // Login function
    register,    // Register function
    logout,      // Logout function
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Custom hook to use auth context
 * 
 * @returns {Object} Auth context value
 * @throws {Error} If used outside AuthProvider
 * 
 * @example
 * const { user, login, logout } = useAuth()
 */
export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }

  return context
}
