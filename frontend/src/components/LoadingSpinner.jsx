/**
 * Loading Spinner Component
 * 
 * Displays a loading indicator while content is being fetched.
 */

/**
 * Loading spinner with customizable size
 * 
 * @param {Object} props - Component props
 * @param {string} props.size - Size: 'small', 'medium', 'large'
 * @returns {React.ReactNode} Spinning loader
 */
function LoadingSpinner({ size = 'medium' }) {
  // Size classes
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12',
  }

  return (
    <div className="flex items-center justify-center">
      <div
        className={`
          ${sizeClasses[size]}
          border-4 border-gray-200 border-t-primary-600
          rounded-full animate-spin
        `}
      />
    </div>
  )
}

export default LoadingSpinner
