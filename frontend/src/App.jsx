/**
 * Main App Component
 * 
 * Sets up routing for the application.
 * Handles authenticated vs public routes.
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'

// Pages
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ChatPage from './pages/ChatPage'
import DocumentsPage from './pages/DocumentsPage'
import ProfilesPage from './pages/ProfilesPage'

// Components
import Layout from './components/Layout'
import LoadingSpinner from './components/LoadingSpinner'

/**
 * Protected Route Component
 * 
 * Wraps routes that require authentication.
 * Redirects to login if user is not authenticated.
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components to render if authenticated
 * @returns {React.ReactNode} Protected content or redirect
 */
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  // Show loading spinner while checking auth status
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!user) {
    return <Navigate to="/login" replace />
  }

  return children
}

/**
 * Public Route Component
 * 
 * Wraps routes that should only be accessible when NOT logged in.
 * Redirects to chat if user is already authenticated.
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components to render if not authenticated
 * @returns {React.ReactNode} Public content or redirect
 */
function PublicRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
      </div>
    )
  }

  // Redirect to chat if already logged in
  if (user) {
    return <Navigate to="/chat" replace />
  }

  return children
}

/**
 * Main App Component
 * 
 * Defines all routes for the application.
 */
function App() {
  return (
    <Routes>
      {/* Public routes - accessible without login */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        }
      />

      {/* Protected routes - require authentication */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        {/* Default redirect to chat */}
        <Route index element={<Navigate to="/chat" replace />} />

        {/* Main chat page */}
        <Route path="chat" element={<ChatPage />} />
        <Route path="chat/:conversationId" element={<ChatPage />} />

        {/* Document management */}
        <Route path="documents" element={<DocumentsPage />} />

        {/* Profile settings */}
        <Route path="profiles" element={<ProfilesPage />} />
      </Route>

      {/* Catch all - redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
