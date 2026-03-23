"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { UsageStatistics } from "@/lib/types";
import { Header } from "@/components/Header";

export default function UsagePage() {
  const [stats, setStats] = useState<UsageStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const data = await api.statistics.getUsage();
        setStats(data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch statistics:", err);
        setError("Failed to load usage statistics");
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat("en-US").format(num);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 4,
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-center h-64">
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-12">
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 border-3 border-gray-200 border-t-indigo-600 rounded-full animate-spin" />
                <p className="text-gray-700 font-medium text-lg">Loading statistics...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="bg-red-50 border border-red-200 rounded-lg shadow-sm p-8">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-red-900 font-semibold text-lg">Error</p>
                <p className="text-red-700 text-sm mt-1">{error || "No data available"}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-semibold text-gray-900">
                AI Usage Statistics
              </h1>
              <p className="text-gray-600 mt-1">Overview of AI token usage and costs across all video analyses</p>
            </div>
          </div>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="text-xs font-semibold text-gray-600 uppercase">Total Jobs Completed</div>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {formatNumber(stats.overview.total_jobs_completed)}
            </div>
            <div className="text-sm text-gray-600">
              {stats.overview.total_jobs_processing} processing · {stats.overview.total_jobs_failed} failed
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="text-xs font-semibold text-gray-600 uppercase">Total Frames Analyzed</div>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {formatNumber(stats.overview.total_frames_extracted)}
            </div>
            <div className="text-sm text-gray-600">
              ~{stats.overview.avg_frames_per_job.toFixed(1)} frames per job
            </div>
          </div>

          <div className="bg-emerald-600 rounded-lg shadow-sm p-6 text-white hover:bg-emerald-700 transition-colors">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="text-xs font-semibold uppercase opacity-95">Total Cost</div>
            </div>
            <div className="text-3xl font-bold mb-2">
              {formatCurrency(stats.total.total_cost_usd)}
            </div>
            <div className="text-sm opacity-90">
              ~{formatCurrency(stats.total.avg_cost_per_job_usd)} per job
            </div>
          </div>
        </div>

        {/* Whisper Statistics */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-8 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-900">
              Audio Transcription (Whisper API)
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Model</div>
              <div className="text-lg font-mono font-semibold text-gray-900">
                {stats.whisper.model}
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Total Duration</div>
              <div className="text-lg font-semibold text-gray-900">
                {stats.whisper.total_duration_minutes.toFixed(1)} min
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.whisper.total_duration_seconds.toFixed(0)}s
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Avg Duration/Job</div>
              <div className="text-lg font-semibold text-gray-900">
                {stats.whisper.avg_duration_per_job_seconds.toFixed(0)}s
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Total Cost</div>
              <div className="text-lg font-bold text-gray-900">
                {formatCurrency(stats.whisper.total_cost_usd)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.total.cost_breakdown.whisper_percentage.toFixed(1)}% of total
              </div>
            </div>
          </div>
        </div>

        {/* GPT-4o Statistics */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-8 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-900">
              Video Analysis (GPT-4o)
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Model</div>
              <div className="text-lg font-mono font-semibold text-gray-900">
                {stats.gpt4o.model}
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Prompt Tokens</div>
              <div className="text-lg font-semibold text-gray-900">
                {formatNumber(stats.gpt4o.total_prompt_tokens)}
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Completion Tokens</div>
              <div className="text-lg font-semibold text-gray-900">
                {formatNumber(stats.gpt4o.total_completion_tokens)}
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Total Tokens</div>
              <div className="text-lg font-semibold text-gray-900">
                {formatNumber(stats.gpt4o.total_tokens)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                ~{formatNumber(stats.gpt4o.avg_tokens_per_job)} per job
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Total Cost</div>
              <div className="text-lg font-bold text-gray-900">
                {formatCurrency(stats.gpt4o.total_cost_usd)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.total.cost_breakdown.gpt4o_percentage.toFixed(1)}% of total
              </div>
            </div>
          </div>
        </div>

        {/* Embeddings Statistics */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-8 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-900">
              Semantic Search (Embeddings)
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Model</div>
              <div className="text-lg font-mono font-semibold text-gray-900">
                {stats.embeddings.model}
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Total Embeddings</div>
              <div className="text-lg font-semibold text-gray-900">
                {formatNumber(stats.embeddings.total_embeddings_generated)}
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Total Tokens</div>
              <div className="text-lg font-semibold text-gray-900">
                {formatNumber(stats.embeddings.total_tokens)}
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
              <div className="text-xs text-gray-600 mb-2 font-semibold uppercase">Total Cost</div>
              <div className="text-lg font-bold text-gray-900">
                {formatCurrency(stats.embeddings.total_cost_usd)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.total.cost_breakdown.embeddings_percentage.toFixed(1)}% of total
              </div>
            </div>
          </div>
        </div>

        {/* Cost Breakdown Chart */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-8 mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Cost Breakdown</h2>
          <div className="space-y-6">
            {/* Whisper Bar */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-indigo-600" />
                  <span className="text-sm font-semibold text-gray-700">Whisper API</span>
                </div>
                <span className="text-sm font-bold text-gray-900">
                  {formatCurrency(stats.whisper.total_cost_usd)} ({stats.total.cost_breakdown.whisper_percentage.toFixed(1)}%)
                </span>
              </div>
              <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-600 transition-all duration-700"
                  style={{ width: `${stats.total.cost_breakdown.whisper_percentage}%` }}
                />
              </div>
            </div>

            {/* GPT-4o Bar */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-indigo-600" />
                  <span className="text-sm font-semibold text-gray-700">GPT-4o API</span>
                </div>
                <span className="text-sm font-bold text-gray-900">
                  {formatCurrency(stats.gpt4o.total_cost_usd)} ({stats.total.cost_breakdown.gpt4o_percentage.toFixed(1)}%)
                </span>
              </div>
              <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-600 transition-all duration-700"
                  style={{ width: `${stats.total.cost_breakdown.gpt4o_percentage}%` }}
                />
              </div>
            </div>

            {/* Embeddings Bar */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-indigo-600" />
                  <span className="text-sm font-semibold text-gray-700">Embeddings API</span>
                </div>
                <span className="text-sm font-bold text-gray-900">
                  {formatCurrency(stats.embeddings.total_cost_usd)} ({stats.total.cost_breakdown.embeddings_percentage.toFixed(1)}%)
                </span>
              </div>
              <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-600 transition-all duration-700"
                  style={{ width: `${stats.total.cost_breakdown.embeddings_percentage}%` }}
                />
              </div>
            </div>
          </div>

          {/* Total */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="flex justify-between items-center">
              <span className="text-xl font-semibold text-gray-900">Total Cost</span>
              <span className="text-3xl font-bold text-emerald-600">
                {formatCurrency(stats.total.total_cost_usd)}
              </span>
            </div>
          </div>
        </div>

        {/* Info Footer */}
        <div className="bg-indigo-50 border border-indigo-100 rounded-lg shadow-sm p-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-indigo-900 font-semibold mb-1">
                Pricing: Whisper API at $0.006/minute · GPT-4o at $5/1M input tokens + $15/1M output tokens · Embeddings at $0.02/1M tokens
              </p>
              <p className="text-sm text-indigo-700">
                Statistics are updated in real-time from completed jobs. Auto-refreshes every 30 seconds.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
