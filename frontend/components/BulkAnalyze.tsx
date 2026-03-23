"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface BulkAnalyzeResult {
  channel_id: string;
  channel_title: string;
  total_videos_found: number;
  jobs_created: number;
  videos_skipped: number;
  errors: number;
  created_jobs: Array<{
    job_id: string;
    video_url: string;
    title: string;
  }>;
  skipped_videos: Array<{
    url: string;
    title: string;
    reason: string;
    job_id?: string;
  }>;
  error_details: Array<{
    url: string;
    title: string;
    error: string;
  }>;
}

export function BulkAnalyze() {
  const [channelUrl, setChannelUrl] = useState("");
  const [maxResults, setMaxResults] = useState<string>("");
  const [useAllVideos, setUseAllVideos] = useState(true);
  const [skipExisting, setSkipExisting] = useState(true);
  const [disableTranscript, setDisableTranscript] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fetchingVideos, setFetchingVideos] = useState(false);
  const [channelInfo, setChannelInfo] = useState<any>(null);
  const [result, setResult] = useState<BulkAnalyzeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFetchVideos = async () => {
    if (!channelUrl.trim()) {
      setError("Please enter a channel URL");
      return;
    }

    setFetchingVideos(true);
    setError(null);
    setChannelInfo(null);

    try {
      const maxResultsNum = useAllVideos ? undefined : parseInt(maxResults) || 10;
      const info = await api.jobs.getChannelVideos(channelUrl, maxResultsNum);
      setChannelInfo(info);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch channel videos";
      setError(errorMessage);
    } finally {
      setFetchingVideos(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!channelUrl.trim()) {
      setError("Please enter a channel URL");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const maxResultsNum = useAllVideos ? undefined : parseInt(maxResults) || 10;
      const response = await api.jobs.bulkAnalyze(channelUrl, maxResultsNum, skipExisting, disableTranscript);
      setResult(response);
      setChannelInfo(null);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to start bulk analysis";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setChannelUrl("");
    setMaxResults("");
    setUseAllVideos(true);
    setSkipExisting(true);
    setDisableTranscript(false);
    setResult(null);
    setError(null);
    setChannelInfo(null);
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-gray-900">Bulk Channel Analysis</h2>
              <p className="text-sm text-gray-600 mt-1">Analyze multiple videos from a YouTube channel</p>
            </div>
          </div>
        </div>

        {!result ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Channel URL Input */}
            <div>
              <label htmlFor="channelUrl" className="block text-sm font-medium text-gray-700 mb-2">
                YouTube Channel URL
              </label>
              <input
                type="text"
                id="channelUrl"
                value={channelUrl}
                onChange={(e) => setChannelUrl(e.target.value)}
                placeholder="https://www.youtube.com/@channelname or https://www.youtube.com/channel/CHANNEL_ID"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                disabled={loading || fetchingVideos}
              />
              <p className="text-xs text-gray-500 mt-2">
                Supports: @username, /channel/ID, /c/name, /user/username
              </p>
            </div>

            {/* Max Results */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700">
                Number of Videos
              </label>
              
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="useAllVideos"
                  checked={useAllVideos}
                  onChange={(e) => setUseAllVideos(e.target.checked)}
                  className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                  disabled={loading || fetchingVideos}
                />
                <label htmlFor="useAllVideos" className="text-sm text-gray-700">
                  Analyze all videos from channel
                </label>
              </div>

              {!useAllVideos && (
                <div>
                  <input
                    type="number"
                    id="maxResults"
                    value={maxResults}
                    onChange={(e) => setMaxResults(e.target.value)}
                    placeholder="10"
                    min="1"
                    max="500"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                    disabled={loading || fetchingVideos}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Enter number of recent videos to analyze (1-500)
                  </p>
                </div>
              )}
            </div>

            {/* Skip Existing */}
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="skipExisting"
                checked={skipExisting}
                onChange={(e) => setSkipExisting(e.target.checked)}
                className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                disabled={loading || fetchingVideos}
              />
              <label htmlFor="skipExisting" className="text-sm text-gray-700">
                Skip videos that are already analyzed (recommended)
              </label>
            </div>

            {/* Disable Transcript */}
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="disableTranscript"
                checked={disableTranscript}
                onChange={(e) => setDisableTranscript(e.target.checked)}
                className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                disabled={loading || fetchingVideos}
              />
              <label htmlFor="disableTranscript" className="text-sm text-gray-700">
                Skip audio transcription (faster, lower cost, visual analysis only)
              </label>
            </div>

            {/* Preview Button */}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleFetchVideos}
                disabled={loading || fetchingVideos}
                className="flex-1 px-5 py-3 bg-gray-600 text-white font-medium rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {fetchingVideos ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Fetching Videos...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    Preview Videos
                  </>
                )}
              </button>

              <button
                type="submit"
                disabled={loading || fetchingVideos}
                className="flex-1 px-5 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Starting Analysis...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Start Bulk Analysis
                  </>
                )}
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-red-900 font-semibold">Error</p>
                    <p className="text-red-700 text-sm">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Channel Preview */}
            {channelInfo && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-blue-900 mb-4">Channel Preview</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-blue-700">Channel:</span>
                    <span className="text-sm font-semibold text-blue-900">{channelInfo.channel_title}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-blue-700">Total Videos in Channel:</span>
                    <span className="text-sm font-semibold text-blue-900">{channelInfo.total_channel_videos}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-blue-700">Videos to Analyze:</span>
                    <span className="text-sm font-semibold text-blue-900">{channelInfo.total_fetched}</span>
                  </div>
                </div>
                <p className="text-xs text-blue-600 mt-4">
                  Ready to analyze {channelInfo.total_fetched} video(s) from this channel
                </p>
              </div>
            )}
          </form>
        ) : (
          /* Results */
          <div className="space-y-6">
            {/* Summary */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-green-900">Bulk Analysis Started!</h3>
                  <p className="text-sm text-green-700">{result.channel_title}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                <div className="bg-white rounded-lg p-4 border border-green-200">
                  <p className="text-2xl font-bold text-green-900">{result.total_videos_found}</p>
                  <p className="text-xs text-green-700 mt-1">Total Videos</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-green-200">
                  <p className="text-2xl font-bold text-green-900">{result.jobs_created}</p>
                  <p className="text-xs text-green-700 mt-1">Jobs Created</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-green-200">
                  <p className="text-2xl font-bold text-amber-600">{result.videos_skipped}</p>
                  <p className="text-xs text-green-700 mt-1">Skipped</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-green-200">
                  <p className="text-2xl font-bold text-red-600">{result.errors}</p>
                  <p className="text-xs text-green-700 mt-1">Errors</p>
                </div>
              </div>
            </div>

            {/* Created Jobs */}
            {result.created_jobs.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-900 mb-3">Created Jobs ({result.created_jobs.length})</h4>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {result.created_jobs.map((job, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded border border-gray-200 text-sm">
                      <span className="text-gray-700 truncate flex-1">{job.title}</span>
                      <a
                        href={`/jobs/${job.job_id}`}
                        className="ml-3 px-3 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors text-xs"
                      >
                        View
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Skipped Videos */}
            {result.skipped_videos.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-amber-900 mb-3">Skipped Videos ({result.videos_skipped})</h4>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {result.skipped_videos.slice(0, 10).map((video, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-white rounded border border-amber-200 text-sm">
                      <div className="flex-1">
                        <span className="text-gray-700 truncate block">{video.title}</span>
                        <span className="text-xs text-gray-500">{video.reason}</span>
                      </div>
                      {video.job_id && (
                        <a
                          href={`/jobs/${video.job_id}`}
                          className="ml-3 px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors text-xs"
                        >
                          View Existing
                        </a>
                      )}
                    </div>
                  ))}
                  {result.videos_skipped > 10 && (
                    <p className="text-xs text-amber-700 text-center pt-2">
                      ... and {result.videos_skipped - 10} more
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Errors */}
            {result.error_details.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-red-900 mb-3">Errors ({result.errors})</h4>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {result.error_details.map((error, index) => (
                    <div key={index} className="p-3 bg-white rounded border border-red-200 text-sm">
                      <span className="text-gray-700 truncate block">{error.title}</span>
                      <span className="text-xs text-red-600">{error.error}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={handleReset}
                className="flex-1 px-5 py-3 bg-gray-600 text-white font-medium rounded-lg hover:bg-gray-700 transition-colors"
              >
                Analyze Another Channel
              </button>
              <a
                href="/history"
                className="flex-1 px-5 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors text-center"
              >
                View All Jobs
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
