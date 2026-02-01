/**
 * Layout Component
 * 
 * Main layout wrapper for authenticated pages.
 * Features a unified collapsible sidebar with:
 * - Navigation menu at top
 * - Chat history (context area in middle)
 * - User profile at bottom
 */

import { useState, useEffect, createContext, useContext } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  MessageSquare,
  FileText,
  User,
  LogOut,
  Menu,
  ChevronLeft,
  ChevronRight,
  BookOpen
} from 'lucide-react'

// Context to share sidebar state with child components
const SidebarContext = createContext()

/**
 * Hook to access sidebar context
 * 
 * @returns {Object} Sidebar context with state and functions
 */
export function useSidebar() {
  return useContext(SidebarContext)
}

/**
 * Layout with unified collapsible sidebar
 * 
 * @returns {React.ReactNode} Layout with sidebar and content
 */
function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  
  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  
  // Check if on mobile
  const [isMobile, setIsMobile] = useState(window.innerWidth < 1024)
  
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 1024
      setIsMobile(mobile)
      if (mobile) {
        setSidebarOpen(false)
      }
    }
    
    window.addEventListener('resize', handleResize)
    handleResize()
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Navigation items
  const navItems = [
    { path: '/chat', icon: MessageSquare, label: 'Chat' },
    { path: '/documents', icon: FileText, label: 'Documents' },
    { path: '/profiles', icon: User, label: 'Profiles' },
  ]

  /**
   * Check if a nav item is active
   * 
   * @param {string} path - Path to check
   * @returns {boolean} True if path is active
   */
  const isActive = (path) => {
    return location.pathname.startsWith(path)
  }

  /**
   * Toggle sidebar collapsed/expanded (desktop)
   */
  const toggleCollapse = () => {
    setSidebarCollapsed(!sidebarCollapsed)
  }

  // Sidebar context value for child components
  const sidebarValue = {
    isOpen: sidebarOpen,
    isCollapsed: sidebarCollapsed,
    isMobile,
    toggleSidebar: () => setSidebarOpen(!sidebarOpen),
    toggleCollapse,
    closeSidebar: () => setSidebarOpen(false)
  }

  // Dynamic sidebar width
  const sidebarWidth = sidebarCollapsed ? 'w-16' : 'w-72'

  return (
    <SidebarContext.Provider value={sidebarValue}>
      <div className="flex h-screen bg-gray-100">
        {/* Mobile sidebar overlay */}
        {isMobile && sidebarOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-20"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Unified Sidebar */}
        <aside
          className={`
            ${isMobile ? 'fixed inset-y-0 left-0 z-30' : 'relative'}
            ${sidebarWidth} bg-white shadow-lg flex flex-col
            transform transition-all duration-200 ease-in-out
            ${isMobile && !sidebarOpen ? '-translate-x-full' : 'translate-x-0'}
          `}
        >
          {/* Logo and collapse toggle */}
          <div className="flex items-center justify-between p-3 border-b flex-shrink-0">
            {!sidebarCollapsed ? (
              <div className="flex items-center gap-2">
                <BookOpen className="w-7 h-7 text-primary-600 flex-shrink-0" />
                <span className="text-lg font-bold text-gray-800">Learning Bot</span>
              </div>
            ) : (
              <BookOpen className="w-7 h-7 text-primary-600 mx-auto" />
            )}
            
            {/* Collapse button (desktop only) */}
            {!isMobile && (
              <button
                onClick={toggleCollapse}
                className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500 flex-shrink-0"
                title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              >
                {sidebarCollapsed ? (
                  <ChevronRight className="w-4 h-4" />
                ) : (
                  <ChevronLeft className="w-4 h-4" />
                )}
              </button>
            )}
          </div>

          {/* Navigation Menu */}
          <nav className="p-2 space-y-1 flex-shrink-0">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => isMobile && setSidebarOpen(false)}
                className={`
                  flex items-center gap-3 px-3 py-2 rounded-lg transition-colors
                  ${sidebarCollapsed ? 'justify-center' : ''}
                  ${isActive(item.path)
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                  }
                `}
                title={sidebarCollapsed ? item.label : undefined}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!sidebarCollapsed && <span className="text-sm">{item.label}</span>}
              </Link>
            ))}
          </nav>

          {/* Divider */}
          <div className="border-t mx-2" />

          {/* Middle area - for chat history or other contextual content */}
          {/* This area is filled by Outlet's sidebar slot */}
          <div className="flex-1 overflow-hidden" id="sidebar-content-slot" />

          {/* User Profile Section */}
          <div className="p-2 border-t bg-gray-50 flex-shrink-0">
            {sidebarCollapsed ? (
              // Collapsed view: avatar and logout icon stacked
              <div className="flex flex-col items-center gap-2">
                <div 
                  className="w-9 h-9 bg-primary-100 rounded-full flex items-center justify-center"
                  title={user?.username}
                >
                  <span className="text-primary-700 font-medium text-sm">
                    {user?.username?.charAt(0).toUpperCase()}
                  </span>
                </div>
                <button
                  onClick={logout}
                  className="p-2 text-gray-500 hover:bg-gray-200 rounded-lg transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              // Expanded view: full user info
              <>
                <div className="flex items-center gap-2 mb-2 px-1">
                  <div className="w-9 h-9 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-primary-700 font-medium text-sm">
                      {user?.username?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {user?.username}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {user?.email}
                    </p>
                  </div>
                </div>
                <button
                  onClick={logout}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </>
            )}
          </div>
        </aside>

        {/* Main content area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Mobile header */}
          {isMobile && (
            <header className="flex items-center gap-4 p-4 bg-white shadow-sm flex-shrink-0">
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <Menu className="w-6 h-6" />
              </button>
              <span className="text-lg font-semibold">Learning Bot</span>
            </header>
          )}

          {/* Page content - Outlet renders the current route */}
          <main className="flex-1 overflow-hidden">
            <Outlet context={{ sidebarCollapsed, isMobile, closeSidebar: () => setSidebarOpen(false) }} />
          </main>
        </div>
      </div>
    </SidebarContext.Provider>
  )
}

export default Layout
