"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import Link from "next/link";

interface ExportableJob {
  id: string;
  title: string;
  duration: number;
  frames_count: number;
  created_at: string;
}

interface ImportResult {
  success: boolean;
  job_id: string;
  message: string;
  skipped: boolean;
}

export default function ExportImportPage() {
  const [exportableJobs, setExportableJobs] = useState<ExportableJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [skipExisting, setSkipExisting] = useState(true);

  useEffect(() => {
    loadExportableJobs();
  }, []);

  const loadExportableJobs = async () => {
    try {
      setLoading(true);
      const jobs = await api.export.listExportableJobs();
      setExportableJobs(jobs);
    } catch (error) {
      console.error("Failed to load exportable jobs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (jobId: string, title: string) => {
    try {
      setExporting(jobId);
      const blob = await api.export.exportJob(jobId);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeTitle = title.replace(/[^a-z0-9]/gi, "_").substring(0, 50);
      a.download = `${safeTitle}_${jobId.substring(0, 8)}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Export failed:", error);
      alert("Export failed. Check console for details.");
    } finally {
      setExporting(null);
    }
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith(".zip")) {
      alert("Please select a ZIP file");
      return;
    }

    try {
      setImporting(true);
      setImportResult(null);

      const result = await api.export.importJob(file, skipExisting);
      setImportResult(result);

      // Refresh job list if import was successful
      if (result.success && !result.skipped) {
        await loadExportableJobs();
      }
    } catch (error: any) {
      console.error("Import failed:", error);
      const message = error.response?.data?.detail || error.message || "Import failed";
      setImportResult({
        success: false,
        job_id: "",
        message: message,
        skipped: false,
      });
    } finally {
      setImporting(false);
      // Reset file input
      event.target.value = "";
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString("id-ID", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/"
            className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-4"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            Back to Home
          </Link>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Export & Import
          </h1>
          <p className="text-gray-600">
            Export video analysis untuk backup atau pindah ke server lain
          </p>
        </div>

        {/* Import Section */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Import Job
          </h2>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={skipExisting}
                  onChange={(e) => setSkipExisting(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-gray-700">
                  Skip jika job sudah ada (recommended)
                </span>
              </label>
            </div>

            <div>
              <label className="block w-full cursor-pointer">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
                  <svg
                    className="w-12 h-12 mx-auto mb-4 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                  <p className="text-gray-600 mb-2">
                    {importing ? "Importing..." : "Click to upload ZIP file"}
                  </p>
                  <p className="text-sm text-gray-500">
                    File .zip hasil export
                  </p>
                </div>
                <input
                  type="file"
                  accept=".zip"
                  onChange={handleImport}
                  disabled={importing}
                  className="hidden"
                />
              </label>
            </div>

            {/* Import Result */}
            {importResult && (
              <div
                className={`p-4 rounded-lg ${
                  importResult.success
                    ? importResult.skipped
                      ? "bg-yellow-50 border border-yellow-200"
                      : "bg-green-50 border border-green-200"
                    : "bg-red-50 border border-red-200"
                }`}
              >
                <div className="flex items-start gap-3">
                  <svg
                    className={`w-6 h-6 flex-shrink-0 ${
                      importResult.success
                        ? importResult.skipped
                          ? "text-yellow-600"
                          : "text-green-600"
                        : "text-red-600"
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    {importResult.success ? (
                      importResult.skipped ? (
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                        />
                      ) : (
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      )
                    ) : (
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    )}
                  </svg>
                  <div className="flex-1">
                    <h3
                      className={`font-semibold ${
                        importResult.success
                          ? importResult.skipped
                            ? "text-yellow-800"
                            : "text-green-800"
                          : "text-red-800"
                      }`}
                    >
                      {importResult.success
                        ? importResult.skipped
                          ? "Skipped"
                          : "Success"
                        : "Failed"}
                    </h3>
                    <p
                      className={`text-sm ${
                        importResult.success
                          ? importResult.skipped
                            ? "text-yellow-700"
                            : "text-green-700"
                          : "text-red-700"
                      }`}
                    >
                      {importResult.message}
                    </p>
                    {importResult.success && importResult.job_id && (
                      <Link
                        href={`/job/${importResult.job_id}`}
                        className="inline-block mt-2 text-sm text-blue-600 hover:text-blue-700 underline"
                      >
                        View Job →
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Export Section */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Export Jobs
          </h2>

          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading...</p>
            </div>
          ) : exportableJobs.length === 0 ? (
            <div className="text-center py-12">
              <svg
                className="w-16 h-16 mx-auto mb-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                />
              </svg>
              <p className="text-gray-600">
                Tidak ada job yang bisa di-export
              </p>
              <p className="text-sm text-gray-500 mt-2">
                Hanya job dengan status &quot;done&quot; yang memiliki video dan frames yang bisa di-export
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Video Title
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Frames
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {exportableJobs.map((job) => (
                    <tr key={job.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {job.title}
                        </div>
                        <div className="text-xs text-gray-500">
                          {job.id.substring(0, 8)}...
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">
                        {formatDuration(job.duration)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">
                        {job.frames_count} frames
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {formatDate(job.created_at)}
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => handleExport(job.id, job.title)}
                          disabled={exporting === job.id}
                          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                          {exporting === job.id ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              Exporting...
                            </>
                          ) : (
                            <>
                              <svg
                                className="w-4 h-4 mr-2"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                                />
                              </svg>
                              Export
                            </>
                          )}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
