import React, { useState } from 'react'
import Card from '../../ui/Card'
import Button from '../../ui/Button'
import {
  CsvValidationResponse,
  CsvUploadResults,
  CsvValidationRow,
  validateTeamsCsv,
  validatePlayersCsv,
  uploadTeamsCsv,
  uploadPlayersCsv,
  TeamCsvRow,
  PlayerCsvRow,
} from '../../../services/adminApi'

interface CsvUploadProps {
  type: 'teams' | 'players'
  onUploadComplete: (results: CsvUploadResults) => void
  onCancel?: () => void
}

export default function CsvUpload({ type, onUploadComplete, onCancel }: CsvUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [validation, setValidation] = useState<CsvValidationResponse | null>(null)
  const [results, setResults] = useState<CsvUploadResults | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] || null
    setFile(selected)
    setValidation(null)
    setResults(null)
    setError(null)
  }

  const handleValidate = async () => {
    if (!file) {
      setError('Please select a CSV file to upload.')
      return
    }

    setLoading(true)
    setError(null)
    setValidation(null)
    setResults(null)

    try {
      const data =
        type === 'teams' ? await validateTeamsCsv(file) : await validatePlayersCsv(file)
      setValidation(data)
      if (!data.valid && data.summary.invalidRows > 0) {
        setError('Some rows have validation errors. Please review before uploading.')
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to validate CSV file')
    } finally {
      setLoading(false)
    }
  }

  const mapValidatedRows = (preview: CsvValidationRow[]): (TeamCsvRow | PlayerCsvRow)[] => {
    if (type === 'teams') {
      return preview
        .filter((row) => !row.errors?.length)
        .map((row) => ({
          row: row.row,
          teamName: row.teamName,
          teamId: row.teamId || undefined,
        }))
    }

    // players
    return preview
      .filter((row) => !row.errors?.length)
      .map((row) => ({
        row: row.row,
        name: row.name,
        email: row.email || undefined,
        teamId: row.teamId,
        playerId: row.playerId || undefined,
      }))
  }

  const handleUpload = async () => {
    if (!validation) {
      setError('Please validate the CSV file before uploading.')
      return
    }

    const validRows = mapValidatedRows(validation.preview)
    if (validRows.length === 0) {
      setError('No valid rows to upload.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data =
        type === 'teams'
          ? await uploadTeamsCsv(validRows as TeamCsvRow[])
          : await uploadPlayersCsv(validRows as PlayerCsvRow[])
      setResults(data)
      onUploadComplete(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to upload CSV data')
    } finally {
      setLoading(false)
    }
  }

  const title = type === 'teams' ? 'Upload Teams via CSV' : 'Upload Players via CSV'
  const description =
    type === 'teams'
      ? 'Upload a CSV file to bulk-create teams. Required column: teamName. Optional: teamId.'
      : 'Upload a CSV file to bulk-create players. Required columns: name and teamName or teamId. Optional: email, playerId.'

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="max-w-3xl w-full">
        <Card className="max-h-[90vh] overflow-y-auto" title={title}>
          <p className="text-sm text-gray-600 mb-4">{description}</p>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-4 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                CSV File <span className="text-red-500">*</span>
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-700"
              />
              <p className="text-xs text-gray-500 mt-1">
                Maximum file size 5MB. Maximum 1000 rows per upload.
              </p>
            </div>

            <div className="flex space-x-3">
              <Button size="sm" onClick={handleValidate} disabled={loading || !file}>
                {loading ? 'Validating...' : 'Validate CSV'}
              </Button>
              <Button
                size="sm"
                onClick={handleUpload}
                disabled={loading || !validation || !validation.valid}
              >
                {loading ? 'Uploading...' : 'Upload Valid Rows'}
              </Button>
              {onCancel && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onCancel}
                  disabled={loading}
                >
                  Close
                </Button>
              )}
            </div>

            {validation && (
              <div className="mt-4">
                <h4 className="text-sm font-semibold text-gray-800 mb-2">
                  Validation Summary
                </h4>
                <p className="text-xs text-gray-600 mb-2">
                  Total rows: {validation.summary.totalRows} · Valid:{' '}
                  {validation.summary.validRows} · Invalid:{' '}
                  {validation.summary.invalidRows}
                </p>

                <div className="border border-gray-200 rounded-md max-h-64 overflow-y-auto text-xs">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium text-gray-700">
                          Row
                        </th>
                        {type === 'teams' ? (
                          <>
                            <th className="px-3 py-2 text-left font-medium text-gray-700">
                              Team Name
                            </th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700">
                              Team ID
                            </th>
                          </>
                        ) : (
                          <>
                            <th className="px-3 py-2 text-left font-medium text-gray-700">
                              Name
                            </th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700">
                              Email
                            </th>
                            <th className="px-3 py-2 text-left font-medium text-gray-700">
                              Team
                            </th>
                          </>
                        )}
                        <th className="px-3 py-2 text-left font-medium text-gray-700">
                          Errors / Warnings
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-100">
                      {validation.preview.map((row) => (
                        <tr key={row.row}>
                          <td className="px-3 py-1 whitespace-nowrap">{row.row}</td>
                          {type === 'teams' ? (
                            <>
                              <td className="px-3 py-1 whitespace-nowrap">
                                {row.teamName}
                              </td>
                              <td className="px-3 py-1 whitespace-nowrap">
                                {row.teamId || ''}
                              </td>
                            </>
                          ) : (
                            <>
                              <td className="px-3 py-1 whitespace-nowrap">{row.name}</td>
                              <td className="px-3 py-1 whitespace-nowrap">
                                {row.email || ''}
                              </td>
                              <td className="px-3 py-1 whitespace-nowrap">
                                {row.teamName || row.teamId || ''}
                              </td>
                            </>
                          )}
                          <td className="px-3 py-1">
                            {row.errors?.length ? (
                              <div className="text-red-600">
                                {row.errors.join('; ')}
                              </div>
                            ) : row.warnings?.length ? (
                              <div className="text-yellow-600">
                                {row.warnings.join('; ')}
                              </div>
                            ) : (
                              <span className="text-green-600">OK</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {results && (
              <div className="mt-4">
                <h4 className="text-sm font-semibold text-gray-800 mb-2">
                  Upload Results
                </h4>
                <p className="text-xs text-gray-600 mb-2">
                  Created: {results.summary.created} · Skipped:{' '}
                  {results.summary.skipped} · Errors: {results.summary.errors}
                </p>

                {results.skipped.length > 0 && (
                  <div className="mb-3">
                    <h5 className="text-xs font-semibold text-gray-700 mb-1">
                      Skipped rows
                    </h5>
                    <ul className="list-disc list-inside text-xs text-gray-600 space-y-1 max-h-32 overflow-y-auto">
                      {results.skipped.map((item: any, index: number) => (
                        <li key={index}>
                          Row {item.row}: {item.reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {results.errors.length > 0 && (
                  <div>
                    <h5 className="text-xs font-semibold text-gray-700 mb-1">
                      Errors
                    </h5>
                    <ul className="list-disc list-inside text-xs text-red-700 space-y-1 max-h-32 overflow-y-auto">
                      {results.errors.map((item, index) => (
                        <li key={index}>
                          Row {item.row}: {item.error}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}


