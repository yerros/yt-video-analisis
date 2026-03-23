"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { AnalysisResultComponent } from "@/components/AnalysisResult";
import { ProgressStream } from "@/components/ProgressStream";
import { ExportPDFButton } from "@/components/ExportPDFButton";
import type { Job } from "@/lib/types";

export default function JobDetailsPage() {
  const params = useParams();
  const jobId = params.id as string;

  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  const loadJob = useCallback(async () => {
    try {
      setLoading(true);
      const jobData = await api.jobs.get(jobId);
      setJob(jobData);
    } catch (err: unknown) {
      const errorMessage = err && typeof err === 'object' && 'response' in err 
        ? (err.response as { data?: { detail?: string } })?.data?.detail || "Failed to load job"
        : "Failed to load job";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  const handleRetry = async () => {
    if (!job) return;

    if (!confirm("Retry this job? This will restart the analysis from the beginning.")) {
      return;
    }

    setIsRetrying(true);
    try {
      await api.jobs.retry(job.id);
      // Reload the job to show updated status
      await loadJob();
      alert("Job has been restarted successfully!");
    } catch (err: unknown) {
      const errorMessage = err && typeof err === 'object' && 'response' in err 
        ? (err.response as { data?: { detail?: string } })?.data?.detail || "Failed to retry job"
        : "Failed to retry job";
      alert(errorMessage);
    } finally {
      setIsRetrying(false);
    }
  };

  useEffect(() => {
    if (jobId) {
      loadJob();
    }
  }, [jobId, loadJob]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <main className="container mx-auto px-4 py-12">
          <div className="max-w-4xl mx-auto">
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-12 text-center">
              <div className="flex items-center justify-center gap-3">
                <div className="w-6 h-6 border-3 border-gray-200 border-t-indigo-600 rounded-full animate-spin" />
                <p className="text-gray-700 font-medium text-lg">Loading job details...</p>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-gray-50">
        <main className="container mx-auto px-4 py-12">
          <div className="max-w-4xl mx-auto">
            <div className="bg-red-50 border border-red-200 rounded-lg shadow-sm p-8 mb-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-red-900 font-semibold text-lg">{error || "Job not found"}</p>
                </div>
              </div>
            </div>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
            >
              Back to Home
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const isProcessing = !["done", "failed"].includes(job.status);
  const canRetry = job.status !== "pending" || job.progress > 0; // Allow retry unless it's brand new pending job

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <nav className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link 
              href="/" 
              className="flex items-center gap-2"
            >
              <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <span className="text-xl font-semibold text-gray-900">
                Video Analysis AI
              </span>
            </Link>
            <div className="flex items-center gap-2">
              <Link
                href="/"
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Home
              </Link>
              <Link
                href="/history"
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
              >
                View History
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Page Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h1 className="text-3xl font-semibold text-gray-900">Job Details</h1>
              </div>
              <div className="flex items-center gap-2">
                {job.status === "done" && <ExportPDFButton job={job} />}
                {canRetry && (
                  <button
                    onClick={handleRetry}
                    disabled={isRetrying}
                    className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {isRetrying ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Retrying...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Retry Job
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
              <div className="space-y-3 text-sm">
                <div className="flex items-start gap-2">
                  <span className="font-semibold text-gray-600 min-w-[90px]">Job ID:</span>
                  <span className="text-gray-900 font-mono">{job.id}</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="font-semibold text-gray-600 min-w-[90px]">Video URL:</span>
                  <a
                    href={job.youtube_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-600 hover:text-indigo-700 hover:underline transition-colors break-all"
                  >
                    {job.youtube_url}
                  </a>
                </div>
                <div className="flex items-start gap-2">
                  <span className="font-semibold text-gray-600 min-w-[90px]">Created:</span>
                  <span className="text-gray-900">{new Date(job.created_at).toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* YouTube Metadata Section */}
          {(job.video_title || job.channel_title || job.thumbnail_url) && (
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
                Video Information
              </h2>
              <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
                {job.thumbnail_url && (
                  <div className="aspect-video relative bg-gray-100">
                    <img 
                      src={job.thumbnail_url} 
                      alt={job.video_title || "Video thumbnail"}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
                <div className="p-6 space-y-4">
                  {job.video_title && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">{job.video_title}</h3>
                    </div>
                  )}
                  
                  {job.channel_title && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      <span className="font-medium">{job.channel_title}</span>
                    </div>
                  )}

                  {job.published_at && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span>Published {new Date(job.published_at).toLocaleDateString()}</span>
                    </div>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
                    {job.view_count !== null && (
                      <div className="flex flex-col">
                        <span className="text-xs text-gray-500 uppercase tracking-wide">Views</span>
                        <span className="text-lg font-semibold text-gray-900">{job.view_count.toLocaleString()}</span>
                      </div>
                    )}
                    {job.like_count !== null && (
                      <div className="flex flex-col">
                        <span className="text-xs text-gray-500 uppercase tracking-wide">Likes</span>
                        <span className="text-lg font-semibold text-gray-900">{job.like_count.toLocaleString()}</span>
                      </div>
                    )}
                    {job.comment_count !== null && (
                      <div className="flex flex-col">
                        <span className="text-xs text-gray-500 uppercase tracking-wide">Comments</span>
                        <span className="text-lg font-semibold text-gray-900">{job.comment_count.toLocaleString()}</span>
                      </div>
                    )}
                    {job.video_duration && (
                      <div className="flex flex-col">
                        <span className="text-xs text-gray-500 uppercase tracking-wide">Duration</span>
                        <span className="text-lg font-semibold text-gray-900">
                          {Math.floor(job.video_duration / 60)}:{String(job.video_duration % 60).padStart(2, '0')}
                        </span>
                      </div>
                    )}
                  </div>

                  {job.description && (
                    <div className="pt-4 border-t border-gray-200">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Description</h4>
                      <p className="text-sm text-gray-600 whitespace-pre-wrap line-clamp-3">
                        {job.description}
                      </p>
                    </div>
                  )}

                  {job.tags && job.tags.length > 0 && (
                    <div className="pt-4 border-t border-gray-200">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Tags</h4>
                      <div className="flex flex-wrap gap-2">
                        {job.tags.map((tag, index) => (
                          <span 
                            key={index}
                            className="px-3 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {isProcessing && (
            <ProgressStream jobId={jobId} onComplete={() => loadJob()} />
          )}

          {job.status === "failed" && (
            <div className="bg-red-50 border border-red-200 rounded-lg shadow-sm p-8 mb-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-red-900 font-semibold text-lg">Processing Failed</p>
                  {job.error_message && (
                    <p className="text-red-700 text-sm mt-2">{job.error_message}</p>
                  )}
                  <button
                    onClick={handleRetry}
                    disabled={isRetrying}
                    className="mt-4 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {isRetrying ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Retrying...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Retry Job
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

          {job.status === "done" && job.analysis && (
            <AnalysisResultComponent 
              transcript={job.transcript || ""} 
              analysis={job.analysis} 
              framesCount={job.frames_count || 0}
            />
          )}
        </div>
      </main>
    </div>
  );
}
