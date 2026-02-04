/**
 * Documents Page
 * 
 * View available learning materials for RAG.
 * Documents are added by placing them in the backend's "documents" folder.
 */

import { useState, useEffect } from 'react'
import { getDocuments, openDocument } from '../services/documentService'

import LoadingSpinner from '../components/LoadingSpinner'
import {
  FileText,
  AlertCircle,
  BookOpen,
  FolderOpen,
  ExternalLink
} from 'lucide-react'

/**
 * Documents view page
 * 
 * @returns {React.ReactNode} Document list interface
 */
function DocumentsPage() {
  // State
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [openingDoc, setOpeningDoc] = useState(null)

  /**
   * Load documents on mount
   */
  useEffect(() => {
    loadDocuments()
  }, [])

  /**
   * Load all documents
   */
  const loadDocuments = async () => {
    try {
      const data = await getDocuments()
      setDocuments(data.documents || [])
    } catch (err) {
      setError('Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  /**
   * Handle opening a document
   * 
   * @param {Object} doc - Document to open
   */
  const handleOpenDocument = async (doc) => {
    try {
      setOpeningDoc(doc.id)
      await openDocument(doc.id)
    } catch (err) {
      setError(`Failed to open document: ${err.message}`)
    } finally {
      setOpeningDoc(null)
    }
  }

  /**
   * Format date for display
   * 
   * @param {string} dateString - ISO date string
   * @returns {string} Formatted date
   */
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="large" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto h-full overflow-y-auto flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Learning Materials</h1>
        <p className="text-gray-600 mt-1">
          Documents the chatbot can reference to help guide your learning
        </p>
      </div>

      {/* Info box about adding documents */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start gap-3">
          <FolderOpen className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-blue-700 font-medium">Adding Documents</p>
            <p className="text-blue-600 text-sm mt-1">
              Documents are managed by the administrator. To add new learning materials,
              place PDF, TXT, or EPUB files in the <code className="bg-blue-100 px-1 rounded">backend/documents</code> folder
              and restart the server.
            </p>
          </div>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Document list */}
      <div className="space-y-4">
        <h2 className="text-lg font-medium text-gray-900">
          Available Documents ({documents.length})
        </h2>

        {documents.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No documents available yet</p>
            <p className="text-gray-400 text-sm mt-2">
              Ask your administrator to add learning materials
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map(doc => (
              <div
                key={doc.id}
                onClick={() => handleOpenDocument(doc)}
                className="flex items-center gap-4 p-4 bg-white rounded-lg border shadow-sm hover:shadow-md hover:border-primary-300 cursor-pointer transition-all group"
              >
                {/* Icon */}
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-primary-200 transition-colors">
                  <FileText className="w-6 h-6 text-primary-600" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate group-hover:text-primary-700 transition-colors">
                    {doc.title || doc.filename}
                  </p>
                  <div className="flex items-center gap-3 text-sm text-gray-500">
                    <span className="uppercase">{doc.file_type}</span>
                    {doc.total_pages && (
                      <span>{doc.total_pages} chunks</span>
                    )}
                    <span>Added {formatDate(doc.upload_date)}</span>
                  </div>
                </div>

                {/* Open indicator */}
                <div className="flex-shrink-0">
                  {openingDoc === doc.id ? (
                    <LoadingSpinner size="small" />
                  ) : (
                    <ExternalLink className="w-5 h-5 text-gray-400 group-hover:text-primary-500 transition-colors" />
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentsPage
