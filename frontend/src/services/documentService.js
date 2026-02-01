/**
 * Document Service
 * 
 * Functions for managing uploaded documents.
 */

import api from './api'

/**
 * Upload a document for RAG processing
 * 
 * @param {File} file - The file to upload
 * @param {string} title - Document title (optional)
 * @param {string} author - Document author (optional)
 * @returns {Promise<Object>} Uploaded document data
 */
export async function uploadDocument(file, title = '', author = '') {
  const formData = new FormData()
  formData.append('file', file)

  if (title) {
    formData.append('title', title)
  }
  if (author) {
    formData.append('author', author)
  }

  const response = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

/**
 * Get all uploaded documents
 * 
 * @returns {Promise<Object>} List of documents with count
 */
export async function getDocuments() {
  const response = await api.get('/documents/')
  return response.data
}

/**
 * Get a specific document's details
 * 
 * @param {number} documentId - ID of the document
 * @returns {Promise<Object>} Document details
 */
export async function getDocument(documentId) {
  const response = await api.get(`/documents/${documentId}`)
  return response.data
}

/**
 * Get the URL to view/download a document file
 * 
 * @param {number} documentId - ID of the document
 * @returns {string} URL to the document file
 */
export function getDocumentFileUrl(documentId) {
  // Get the base URL from the api instance
  const baseURL = api.defaults.baseURL || 'http://localhost:8000/api'
  return `${baseURL}/documents/${documentId}/file`
}

/**
 * Open a document in a new tab
 * 
 * @param {number} documentId - ID of the document
 */
export async function openDocument(documentId) {
  // Get token from localStorage
  const token = localStorage.getItem('token')
  
  // Fetch the file with auth header and open in new tab
  const baseURL = api.defaults.baseURL || 'http://localhost:8000/api'
  const response = await fetch(`${baseURL}/documents/${documentId}/file`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  
  if (!response.ok) {
    throw new Error('Failed to load document')
  }
  
  // Get the blob and create object URL
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  
  // Open in new tab
  window.open(url, '_blank')
}

/**
 * Delete a document
 * 
 * @param {number} documentId - ID of the document to delete
 * @returns {Promise<void>}
 */
export async function deleteDocument(documentId) {
  await api.delete(`/documents/${documentId}`)
}
