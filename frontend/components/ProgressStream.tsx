"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ProgressUpdate, JobStatus } from "@/lib/types";

interface ProgressStreamProps {
  jobId: string;
  onComplete?: () => void;
}

const statusLabels: Record<JobStatus, string> = {
  pending: "Waiting to start...",
  downloading: "Downloading video...",
  transcribing: "Transcribing audio...",
  extracting: "Extracting key frames...",
  analyzing: "Analyzing with AI...",
  done: "Analysis completed!",
  failed: "Processing failed",
};

export function ProgressStream({ jobId, onComplete }: ProgressStreamProps) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<JobStatus>("pending");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const eventSource = api.jobs.stream(
      jobId,
      (update: ProgressUpdate) => {
        setProgress(update.progress);
        setStatus(update.status);
        setMessage(update.message);
        
        if (update.error) {
          setError(update.error);
        }

        if (update.status === "done" && onComplete) {
          onComplete();
        }
      },
      (err: Error) => {
        // Only set error if we're not at 100% (which means job completed successfully)
        if (progress < 100) {
          setError(err.message);
        }
      }
    );

    return () => {
      eventSource.close();
    };
  }, [jobId, onComplete]);

  return (
    <div className="w-full max-w-2xl">
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-8">
        {/* Status Header */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-3">
            <div className="flex items-center gap-2.5">
              {/* Status Indicator Dot */}
              <div className={`w-2.5 h-2.5 rounded-full ${
                status === "failed"
                  ? "bg-red-500"
                  : status === "done"
                  ? "bg-emerald-500"
                  : "bg-indigo-600 animate-pulse"
              }`} />
              <span className="text-lg font-semibold text-gray-900">
                {statusLabels[status]}
              </span>
            </div>
            <span className="text-2xl font-bold text-gray-900 tabular-nums">{progress}%</span>
          </div>

          {/* Progress Bar */}
          <div className="relative w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`absolute top-0 left-0 h-full transition-all duration-500 ease-out ${
                status === "failed"
                  ? "bg-red-500"
                  : status === "done"
                  ? "bg-emerald-500"
                  : "bg-indigo-600"
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Status Message */}
        {message && (
          <div className="mb-4 px-4 py-3 bg-indigo-50 border border-indigo-100 rounded-lg">
            <p className="text-sm text-gray-700">{message}</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="mt-4 px-4 py-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-red-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-red-900 font-semibold">Error</p>
                <p className="text-red-700 text-sm mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Success State */}
        {status === "done" && (
          <div className="mt-4 px-4 py-4 bg-emerald-50 border border-emerald-200 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-emerald-900 font-semibold">
                Video analysis completed successfully
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
