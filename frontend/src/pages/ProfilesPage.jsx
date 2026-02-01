/**
 * Profiles Page
 * 
 * Manage chat profiles for personalized learning experiences.
 */

import { useState, useEffect } from 'react'
import {
  getProfiles,
  createProfile,
  updateProfile,
  deleteProfile
} from '../services/profileService'

import LoadingSpinner from '../components/LoadingSpinner'
import {
  Plus,
  Edit2,
  Trash2,
  X,
  Check,
  User,
  Star
} from 'lucide-react'

/**
 * Profiles management page
 * 
 * @returns {React.ReactNode} Profile management interface
 */
function ProfilesPage() {
  // State
  const [profiles, setProfiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingProfile, setEditingProfile] = useState(null)
  const [error, setError] = useState('')

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    learning_style: 'guided',
    difficulty_level: 'intermediate',
    is_default: false,
  })

  /**
   * Load profiles on mount
   */
  useEffect(() => {
    loadProfiles()
  }, [])

  /**
   * Load all profiles
   */
  const loadProfiles = async () => {
    try {
      const data = await getProfiles()
      setProfiles(data)
    } catch (err) {
      setError('Failed to load profiles')
    } finally {
      setLoading(false)
    }
  }

  /**
   * Reset form to initial state
   */
  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      learning_style: 'guided',
      difficulty_level: 'intermediate',
      is_default: false,
    })
    setEditingProfile(null)
    setShowForm(false)
  }

  /**
   * Open form for editing a profile
   * 
   * @param {Object} profile - Profile to edit
   */
  const handleEdit = (profile) => {
    setFormData({
      name: profile.name,
      description: profile.description || '',
      learning_style: profile.learning_style,
      difficulty_level: profile.difficulty_level,
      is_default: profile.is_default,
    })
    setEditingProfile(profile)
    setShowForm(true)
  }

  /**
   * Handle form submission
   * 
   * @param {Event} e - Form submit event
   */
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    try {
      if (editingProfile) {
        // Update existing profile
        const updated = await updateProfile(editingProfile.id, formData)
        setProfiles(prev =>
          prev.map(p => p.id === updated.id ? updated :
            // Unset other defaults if this one is now default
            (updated.is_default ? { ...p, is_default: false } : p)
          )
        )
      } else {
        // Create new profile
        const created = await createProfile(formData)
        setProfiles(prev => [
          // Unset other defaults if this one is default
          ...prev.map(p => created.is_default ? { ...p, is_default: false } : p),
          created
        ])
      }
      resetForm()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save profile')
    }
  }

  /**
   * Handle profile deletion
   * 
   * @param {number} id - Profile ID
   */
  const handleDelete = async (id) => {
    if (!confirm('Delete this profile?')) return

    try {
      await deleteProfile(id)
      setProfiles(prev => prev.filter(p => p.id !== id))
    } catch (err) {
      setError('Failed to delete profile')
    }
  }

  // Learning style options with descriptions
  const learningStyles = [
    { value: 'guided', label: 'Guided', desc: 'Step-by-step hints' },
    { value: 'socratic', label: 'Socratic', desc: 'Questions to guide thinking' },
    { value: 'exploratory', label: 'Exploratory', desc: 'Minimal guidance' },
  ]

  // Difficulty options with descriptions
  const difficultyLevels = [
    { value: 'beginner', label: 'Beginner', desc: 'More detailed hints' },
    { value: 'intermediate', label: 'Intermediate', desc: 'Balanced approach' },
    { value: 'advanced', label: 'Advanced', desc: 'Brief pointers only' },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="large" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Chat Profiles</h1>
          <p className="text-gray-600 mt-1">
            Customize how the bot guides your learning
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Profile
        </button>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
          <button onClick={() => setError('')} className="ml-2 underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Profile form modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">
                {editingProfile ? 'Edit Profile' : 'Create Profile'}
              </h2>
              <button onClick={resetForm} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Profile Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  maxLength={100}
                  className="input-field"
                  placeholder="e.g., Math Study"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (optional)
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="input-field"
                  rows={2}
                  placeholder="What is this profile for?"
                />
              </div>

              {/* Learning Style */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Learning Style
                </label>
                <div className="space-y-2">
                  {learningStyles.map(style => (
                    <label
                      key={style.value}
                      className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer ${formData.learning_style === style.value
                          ? 'border-primary-500 bg-primary-50'
                          : 'hover:bg-gray-50'
                        }`}
                    >
                      <input
                        type="radio"
                        name="learning_style"
                        value={style.value}
                        checked={formData.learning_style === style.value}
                        onChange={(e) => setFormData({ ...formData, learning_style: e.target.value })}
                        className="mt-1"
                      />
                      <div>
                        <span className="font-medium">{style.label}</span>
                        <p className="text-sm text-gray-500">{style.desc}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Difficulty Level */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Difficulty Level
                </label>
                <div className="space-y-2">
                  {difficultyLevels.map(level => (
                    <label
                      key={level.value}
                      className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer ${formData.difficulty_level === level.value
                          ? 'border-primary-500 bg-primary-50'
                          : 'hover:bg-gray-50'
                        }`}
                    >
                      <input
                        type="radio"
                        name="difficulty_level"
                        value={level.value}
                        checked={formData.difficulty_level === level.value}
                        onChange={(e) => setFormData({ ...formData, difficulty_level: e.target.value })}
                        className="mt-1"
                      />
                      <div>
                        <span className="font-medium">{level.label}</span>
                        <p className="text-sm text-gray-500">{level.desc}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Set as default */}
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_default}
                  onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                  className="w-4 h-4 text-primary-600 rounded"
                />
                <span className="text-sm text-gray-700">Set as default profile</span>
              </label>

              {/* Submit buttons */}
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={resetForm} className="btn-secondary flex-1">
                  Cancel
                </button>
                <button type="submit" className="btn-primary flex-1">
                  {editingProfile ? 'Save Changes' : 'Create Profile'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Profile list */}
      {profiles.length === 0 ? (
        <div className="text-center py-12">
          <User className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No profiles created yet</p>
          <p className="text-gray-400 text-sm">
            Create a profile to customize your learning experience
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {profiles.map(profile => (
            <div
              key={profile.id}
              className="bg-white rounded-lg border shadow-sm p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-primary-600" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-gray-900">{profile.name}</h3>
                      {profile.is_default && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary-100 text-primary-700 text-xs rounded-full">
                          <Star className="w-3 h-3" />
                          Default
                        </span>
                      )}
                    </div>
                    {profile.description && (
                      <p className="text-sm text-gray-500 mt-1">{profile.description}</p>
                    )}
                    <div className="flex gap-4 mt-2 text-sm text-gray-500">
                      <span>Style: <strong className="capitalize">{profile.learning_style}</strong></span>
                      <span>Difficulty: <strong className="capitalize">{profile.difficulty_level}</strong></span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-1">
                  <button
                    onClick={() => handleEdit(profile)}
                    className="p-2 text-gray-400 hover:text-primary-600"
                    title="Edit profile"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(profile.id)}
                    className="p-2 text-gray-400 hover:text-red-500"
                    title="Delete profile"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ProfilesPage
