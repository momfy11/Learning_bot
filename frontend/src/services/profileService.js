/**
 * Profile Service
 * 
 * Functions for managing chat profiles.
 */

import api from './api'

/**
 * Get all chat profiles for the current user
 * 
 * @returns {Promise<Array>} List of profiles
 */
export async function getProfiles() {
  const response = await api.get('/profiles/')
  return response.data
}

/**
 * Get a specific profile
 * 
 * @param {number} profileId - ID of the profile
 * @returns {Promise<Object>} Profile data
 */
export async function getProfile(profileId) {
  const response = await api.get(`/profiles/${profileId}`)
  return response.data
}

/**
 * Create a new chat profile
 * 
 * @param {Object} profileData - Profile settings
 * @param {string} profileData.name - Profile name
 * @param {string} profileData.description - Profile description
 * @param {string} profileData.learning_style - guided/socratic/exploratory
 * @param {string} profileData.difficulty_level - beginner/intermediate/advanced
 * @param {boolean} profileData.is_default - Set as default profile
 * @returns {Promise<Object>} Created profile
 */
export async function createProfile(profileData) {
  const response = await api.post('/profiles/', profileData)
  return response.data
}

/**
 * Update a chat profile
 * 
 * @param {number} profileId - ID of the profile to update
 * @param {Object} profileData - Fields to update
 * @returns {Promise<Object>} Updated profile
 */
export async function updateProfile(profileId, profileData) {
  const response = await api.put(`/profiles/${profileId}`, profileData)
  return response.data
}

/**
 * Delete a chat profile
 * 
 * @param {number} profileId - ID of the profile to delete
 * @returns {Promise<void>}
 */
export async function deleteProfile(profileId) {
  await api.delete(`/profiles/${profileId}`)
}
