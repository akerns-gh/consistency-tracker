import { useState, useEffect, useMemo } from 'react'
import { getClubs, createClub, updateClub, disableClub, enableClub, addClubAdmin, getClubAdmins, updateClubAdmin, deleteClubAdmin, resendClubAdminVerification, Club, ClubAdmin } from '../../../services/adminApi'
import Card from '../../ui/Card'
import Button from '../../ui/Button'
import Loading from '../../ui/Loading'

type SortColumn = 'clubName' | 'clubId' | 'status' | 'createdAt'
type SortDirection = 'asc' | 'desc'

export default function ClubManagement() {
  const [clubs, setClubs] = useState<Club[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingClub, setEditingClub] = useState<Club | null>(null)
  
  // Search and sort state
  const [searchTerm, setSearchTerm] = useState('')
  const [sortColumn, setSortColumn] = useState<SortColumn>('clubName')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  
  // Form state
  const [clubName, setClubName] = useState('')
  const [adminFirstName, setAdminFirstName] = useState('')
  const [adminLastName, setAdminLastName] = useState('')
  const [adminEmail, setAdminEmail] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  
  // Club admin management state
  const [expandedClubs, setExpandedClubs] = useState<Set<string>>(new Set())
  const [adminsByClub, setAdminsByClub] = useState<Record<string, ClubAdmin[]>>({})
  const [loadingAdmins, setLoadingAdmins] = useState<Set<string>>(new Set())
  const [editingAdmin, setEditingAdmin] = useState<{ clubId: string; admin: ClubAdmin } | null>(null)
  const [editAdminFirstName, setEditAdminFirstName] = useState('')
  const [editAdminLastName, setEditAdminLastName] = useState('')

  useEffect(() => {
    loadClubs()
  }, [])

  const loadClubs = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getClubs()
      setClubs(data.clubs || [])
    } catch (err) {
      console.error('Failed to load clubs:', err)
      setError((err as any)?.message || 'Failed to load clubs')
    } finally {
      setLoading(false)
    }
  }

  const loadAdminsForClub = async (clubId: string) => {
    if (adminsByClub[clubId]) {
      return // Already loaded
    }
    
    try {
      setLoadingAdmins(prev => new Set(prev).add(clubId))
      const data = await getClubAdmins(clubId)
      setAdminsByClub(prev => ({ ...prev, [clubId]: data.admins || [] }))
    } catch (err) {
      console.error(`Failed to load admins for club ${clubId}:`, err)
      setAdminsByClub(prev => ({ ...prev, [clubId]: [] }))
    } finally {
      setLoadingAdmins(prev => {
        const next = new Set(prev)
        next.delete(clubId)
        return next
      })
    }
  }

  const toggleClubExpanded = (clubId: string) => {
    setExpandedClubs(prev => {
      const next = new Set(prev)
      if (next.has(clubId)) {
        next.delete(clubId)
      } else {
        next.add(clubId)
        loadAdminsForClub(clubId)
      }
      return next
    })
  }

  const handleEditAdmin = (clubId: string, admin: ClubAdmin) => {
    setEditingAdmin({ clubId, admin })
    setEditAdminFirstName(admin.firstName)
    setEditAdminLastName(admin.lastName)
  }

  const handleSaveAdminEdit = async () => {
    if (!editingAdmin) return
    
    const firstName = editAdminFirstName.trim()
    const lastName = editAdminLastName.trim()
    
    if (!firstName || !lastName) {
      setFormError('First name and last name are required')
      return
    }
    
    try {
      setSubmitting(true)
      await updateClubAdmin(editingAdmin.clubId, editingAdmin.admin.adminId, {
        firstName,
        lastName
      })
      
      setEditingAdmin(null)
      setEditAdminFirstName('')
      setEditAdminLastName('')
      
      // Reload admins
      const data = await getClubAdmins(editingAdmin.clubId)
      setAdminsByClub(prev => ({ ...prev, [editingAdmin.clubId]: data.admins || [] }))
    } catch (err: any) {
      setFormError(err?.message || 'Failed to update club admin')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRemoveAdmin = async (clubId: string, adminId: string) => {
    if (!confirm('Are you sure you want to remove this club admin?')) {
      return
    }
    
    try {
      await deleteClubAdmin(clubId, adminId)
      // Reload admins
      const data = await getClubAdmins(clubId)
      setAdminsByClub(prev => ({ ...prev, [clubId]: data.admins || [] }))
    } catch (err: any) {
      alert(err?.message || 'Failed to remove club admin')
    }
  }

  const handleResendAdminVerification = async (clubId: string, admin: ClubAdmin) => {
    if (!admin.email) {
      alert('Club admin must have an email address to resend verification')
      return
    }
    try {
      await resendClubAdminVerification(clubId, admin.adminId)
      alert('Verification email sent successfully')
    } catch (err: any) {
      alert(err?.message || 'Failed to send verification email')
    }
  }

  const handleCreateClub = async () => {
    setFormError(null)
    const name = clubName.trim()
    if (!name) {
      setFormError('Please enter a club name')
      return
    }

    const firstName = adminFirstName.trim()
    const lastName = adminLastName.trim()
    const email = adminEmail.trim()
    
    // Admin firstName, lastName, and email are required (password auto-generated)
    if (!firstName) {
      setFormError('Please enter a first name for the club administrator')
      return
    }
    
    if (!lastName) {
      setFormError('Please enter a last name for the club administrator')
      return
    }
    
    if (!email) {
      setFormError('Please enter an email address for the club administrator')
      return
    }
    
    // Validate email format
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setFormError('Please enter a valid email address')
      return
    }

    try {
      setSubmitting(true)
      const createData = {
        clubName: name,
        firstName,
        lastName,
        adminEmail: email
      }
      
      await createClub(createData)
      setClubName('')
      setAdminFirstName('')
      setAdminLastName('')
      setAdminEmail('')
      setShowCreateForm(false)
      await loadClubs()
    } catch (err: any) {
      setFormError(err?.message || 'Failed to create club')
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdateClub = async () => {
    if (!editingClub) return
    
    setFormError(null)
    const name = clubName.trim()
    if (!name) {
      setFormError('Please enter a club name')
      return
    }

    const firstName = adminFirstName.trim()
    const lastName = adminLastName.trim()
    const email = adminEmail.trim()

    try {
      setSubmitting(true)
      await updateClub(editingClub.clubId, { clubName: name })

      // Optionally add an additional club admin if all fields provided
      if (firstName && lastName && email) {
        await addClubAdmin(editingClub.clubId, {
          firstName,
          lastName,
          adminEmail: email,
        })
      }

      setEditingClub(null)
      setClubName('')
      setAdminFirstName('')
      setAdminLastName('')
      setAdminEmail('')
      await loadClubs()
    } catch (err: any) {
      setFormError(err?.message || 'Failed to update club')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDisableClub = async (club: Club) => {
    if (!confirm(`Are you sure you want to disable "${club.clubName}"? All users will lose access immediately.`)) {
      return
    }

    try {
      await disableClub(club.clubId)
      await loadClubs()
    } catch (err: any) {
      alert(err?.message || 'Failed to disable club')
    }
  }

  const handleEnableClub = async (club: Club) => {
    if (!confirm(`Are you sure you want to enable "${club.clubName}"? Note: Users must be manually re-added to Cognito groups.`)) {
      return
    }

    try {
      await enableClub(club.clubId)
      await loadClubs()
    } catch (err: any) {
      alert(err?.message || 'Failed to enable club')
    }
  }

  const startEdit = (club: Club) => {
    setEditingClub(club)
    setClubName(club.clubName)
    setShowCreateForm(false)
    setFormError(null)
    // Automatically expand and load club admins when editing
    setExpandedClubs(prev => new Set([...prev, club.clubId]))
    loadAdminsForClub(club.clubId)
  }

  const cancelEdit = () => {
    setEditingClub(null)
    setClubName('')
    setFormError(null)
  }

  const cancelCreate = () => {
    setShowCreateForm(false)
    setClubName('')
    setAdminFirstName('')
    setAdminLastName('')
    setAdminEmail('')
    setFormError(null)
  }

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  const filteredAndSortedClubs = useMemo(() => {
    // Filter clubs based on search term
    let filtered = clubs.filter((club) => {
      const searchLower = searchTerm.toLowerCase()
      return (
        club.clubName?.toLowerCase().includes(searchLower) ||
        club.clubId?.toLowerCase().includes(searchLower)
      )
    })

    // Sort clubs
    filtered.sort((a, b) => {
      let aValue: any
      let bValue: any

      switch (sortColumn) {
        case 'clubName':
          aValue = a.clubName || ''
          bValue = b.clubName || ''
          break
        case 'clubId':
          aValue = a.clubId || ''
          bValue = b.clubId || ''
          break
        case 'status':
          aValue = a.isDisabled ? 1 : 0
          bValue = b.isDisabled ? 1 : 0
          break
        case 'createdAt':
          aValue = a.createdAt ? new Date(a.createdAt).getTime() : 0
          bValue = b.createdAt ? new Date(b.createdAt).getTime() : 0
          break
        default:
          return 0
      }

      // Handle string comparison
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        const comparison = aValue.localeCompare(bValue)
        return sortDirection === 'asc' ? comparison : -comparison
      }

      // Handle number comparison
      const comparison = aValue - bValue
      return sortDirection === 'asc' ? comparison : -comparison
    })

    return filtered
  }, [clubs, searchTerm, sortColumn, sortDirection])

  const getSortIcon = (column: SortColumn) => {
    if (sortColumn !== column) {
      return (
        <span className="ml-1 text-gray-400">
          <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
        </span>
      )
    }
    return (
      <span className="ml-1 text-primary">
        {sortDirection === 'asc' ? (
          <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        ) : (
          <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </span>
    )
  }

  if (loading) {
    return <Loading text="Loading clubs..." />
  }

  return (
    <div className="space-y-6">
      <Card title="Club Management">
        <div className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-700">
              Manage all clubs in the platform. Create new clubs, edit existing ones, or disable/enable clubs.
            </p>
            {!showCreateForm && !editingClub && (
              <Button onClick={() => setShowCreateForm(true)}>
                Create New Club
              </Button>
            )}
          </div>

          {/* Create/Edit Form */}
          {(showCreateForm || editingClub) && (
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold mb-4">
                {editingClub ? 'Edit Club' : 'Create New Club'}
              </h3>
              
              {formError && (
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-4">
                  {formError}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Club Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={clubName}
                    onChange={(e) => setClubName(e.target.value)}
                    placeholder="e.g. True Lacrosse"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    disabled={submitting}
                  />
                </div>

                {!editingClub ? (
                  <>
                    <div className="border-t border-gray-200 pt-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        Club Administrator <span className="text-red-500">*</span>
                      </h4>
                      <p className="text-xs text-gray-500 mb-3">
                        Create a club administrator account. The admin will receive a verification email to set their password.
                      </p>
                      
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            First Name <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={adminFirstName}
                            onChange={(e) => setAdminFirstName(e.target.value)}
                            placeholder="First Name"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                            disabled={submitting}
                            required
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Last Name <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={adminLastName}
                            onChange={(e) => setAdminLastName(e.target.value)}
                            placeholder="Last Name"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                            disabled={submitting}
                            required
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Admin Email <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="email"
                            value={adminEmail}
                            onChange={(e) => setAdminEmail(e.target.value)}
                            placeholder="admin@example.com"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                            disabled={submitting}
                            required
                          />
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    {/* Club Admins Management (only when editing) - moved to appear first */}
                    {editingClub && (
                      <div className="border-t border-gray-200 pt-4">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-sm font-medium text-gray-700">
                            Club Administrators
                          </h4>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => toggleClubExpanded(editingClub.clubId)}
                          >
                            {expandedClubs.has(editingClub.clubId) ? 'Hide' : 'Manage'} Admins
                          </Button>
                        </div>

                        {expandedClubs.has(editingClub.clubId) && (
                          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                            {/* Admins List */}
                            {loadingAdmins.has(editingClub.clubId) ? (
                              <div className="text-sm text-gray-500 py-2">Loading admins...</div>
                            ) : (adminsByClub[editingClub.clubId] || []).length === 0 ? (
                              <div className="text-sm text-gray-500 py-2">No club administrators found.</div>
                            ) : (
                              <div className="space-y-2 mb-4">
                                {adminsByClub[editingClub.clubId].map((admin) => (
                                  <div key={admin.adminId} className="flex items-center justify-between bg-white px-4 py-2 rounded border border-gray-200">
                                    <div className="flex-1">
                                  <div className="flex items-center space-x-2">
                                    <div className="text-sm font-medium text-gray-900">
                                      {admin.firstName} {admin.lastName}
                                    </div>
                                    {admin.verificationStatus === "pending" && (
                                      <span className="px-2 py-1 rounded text-xs bg-yellow-100 text-yellow-800">
                                        Verification Pending
                                      </span>
                                    )}
                                    {(() => {
                                      const isFullyActive = admin.isActive !== false && admin.verificationStatus !== "pending"
                                      return (
                                        <span
                                          className={`px-2 py-1 rounded text-xs ${
                                            isFullyActive
                                              ? 'bg-green-100 text-green-800'
                                              : 'bg-gray-100 text-gray-800'
                                          }`}
                                        >
                                          {isFullyActive ? 'Active' : 'Inactive'}
                                        </span>
                                      )
                                    })()}
                                  </div>
                                      <div className="text-xs text-gray-500 mt-1">
                                        {admin.email}
                                        {admin.createdAt && ` • Created ${new Date(admin.createdAt).toLocaleDateString()}`}
                                      </div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                      <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleEditAdmin(editingClub.clubId, admin)}
                                      >
                                        Edit
                                      </Button>
                                      {admin.isActive !== false && admin.email && (
                                        <Button
                                          variant="outline"
                                          size="sm"
                                          onClick={() => handleResendAdminVerification(editingClub.clubId, admin)}
                                        >
                                          Resend Verification
                                        </Button>
                                      )}
                                      {/* Remove button hidden - functionality not implemented yet */}
                                      {/* <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleRemoveAdmin(editingClub.clubId, admin.adminId)}
                                        className="text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
                                      >
                                        Remove
                                      </Button> */}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    <div className="border-t border-gray-200 pt-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        Additional Club Administrator <span className="text-gray-500 text-xs font-normal">(optional)</span>
                      </h4>
                      <p className="text-xs text-gray-500 mb-3">
                        Optionally add another club administrator for this club. If provided, they will receive a verification email to set their password.
                      </p>
                      
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            First Name
                          </label>
                          <input
                            type="text"
                            value={adminFirstName}
                            onChange={(e) => setAdminFirstName(e.target.value)}
                            placeholder="First Name"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                            disabled={submitting}
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Last Name
                          </label>
                          <input
                            type="text"
                            value={adminLastName}
                            onChange={(e) => setAdminLastName(e.target.value)}
                            placeholder="Last Name"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                            disabled={submitting}
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Admin Email
                          </label>
                          <input
                            type="email"
                            value={adminEmail}
                            onChange={(e) => setAdminEmail(e.target.value)}
                            placeholder="admin2@example.com"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                            disabled={submitting}
                          />
                        </div>
                      </div>
                    </div>
                  </>
                )}

                {/* Edit Admin Modal */}
                {editingAdmin && (
                  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                      <h3 className="text-lg font-semibold mb-4">Edit Club Admin</h3>
                      
                      {formError && (
                        <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded mb-4 text-sm">
                          {formError}
                        </div>
                      )}
                      
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            First Name <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={editAdminFirstName}
                            onChange={(e) => setEditAdminFirstName(e.target.value)}
                            placeholder="First Name"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                            disabled={submitting}
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Last Name <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={editAdminLastName}
                            onChange={(e) => setEditAdminLastName(e.target.value)}
                            placeholder="Last Name"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                            disabled={submitting}
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Email
                          </label>
                          <input
                            type="email"
                            value={editingAdmin.admin.email}
                            disabled
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-100 cursor-not-allowed"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Email cannot be changed
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex space-x-2 mt-6">
                        <Button
                          onClick={handleSaveAdminEdit}
                          disabled={submitting}
                        >
                          {submitting ? 'Saving...' : 'Save'}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setEditingAdmin(null)
                            setEditAdminFirstName('')
                            setEditAdminLastName('')
                            setFormError(null)
                          }}
                          disabled={submitting}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex space-x-2">
                  <Button
                    onClick={editingClub ? handleUpdateClub : handleCreateClub}
                    disabled={submitting}
                  >
                    {submitting ? 'Saving...' : editingClub ? 'Update Club' : 'Create Club'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={editingClub ? cancelEdit : cancelCreate}
                    disabled={submitting}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Search Bar */}
          {clubs.length > 0 && (
            <div className="mb-4">
              <input
                type="text"
                placeholder="Search clubs by name or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          )}

          {/* Clubs List */}
          {clubs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No clubs found. Create your first club to get started.</p>
            </div>
          ) : filteredAndSortedClubs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No clubs found matching your search.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('clubName')}
                    >
                      <div className="flex items-center">
                        Club Name
                        {getSortIcon('clubName')}
                      </div>
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('clubId')}
                    >
                      <div className="flex items-center">
                        Club ID
                        {getSortIcon('clubId')}
                      </div>
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('status')}
                    >
                      <div className="flex items-center">
                        Status
                        {getSortIcon('status')}
                      </div>
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                      onClick={() => handleSort('createdAt')}
                    >
                      <div className="flex items-center">
                        Created
                        {getSortIcon('createdAt')}
                      </div>
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredAndSortedClubs.map((club) => {
                      const isDisabled = club.isDisabled || false
                      return (
                        <tr
                          key={club.clubId}
                          className={`hover:bg-gray-50 ${isDisabled ? 'opacity-60 bg-gray-50' : ''}`}
                        >
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{club.clubName}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-500 font-mono">{club.clubId}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {isDisabled ? (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                Disabled
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                Enabled
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-500">
                              {club.createdAt
                                ? new Date(club.createdAt).toLocaleDateString()
                                : 'N/A'}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <div className="flex justify-end space-x-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => startEdit(club)}
                                disabled={editingClub?.clubId === club.clubId || isDisabled}
                              >
                                Edit
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => isDisabled ? handleEnableClub(club) : handleDisableClub(club)}
                                className={
                                  isDisabled
                                    ? "text-green-600 hover:text-green-700 border-green-300 hover:border-green-400"
                                    : "text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
                                }
                              >
                                {isDisabled ? "Enable" : "Disable"}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}

