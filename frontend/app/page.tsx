"use client";

import { useState } from "react";
import { UrlForm } from "@/components/UrlForm";
import { BulkAnalyze } from "@/components/BulkAnalyze";
import { ProgressStream } from "@/components/ProgressStream";
import { Header } from "@/components/Header";

export default function HomePage() {
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [showProgress, setShowProgress] = useState(false);
  const [activeTab, setActiveTab] = useState<"single" | "bulk">("single");

  const handleJobCreated = (jobId: string) => {
    setCurrentJobId(jobId);
    setShowProgress(true);
  };

  const handleComplete = () => {
    if (currentJobId) {
      window.location.href = `/jobs/${currentJobId}`;
    }
  };

  const handleReset = () => {
    setCurrentJobId(null);
    setShowProgress(false);
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <Header />
      {/* Hero Section */}
      <div className="max-w-5xl mx-auto px-6 pt-16 pb-12">
        <div className="text-center space-y-4 mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-indigo-50 rounded-full border border-indigo-100 mb-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-indigo-700">AI-POWERED ANALYSIS</span>
          </div>
          
          <h1 className="text-5xl font-bold tracking-tight text-gray-900">
            Analyze YouTube Videos
            <span className="block text-gray-600 mt-2 text-4xl">with Multimodal AI</span>
          </h1>
          
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Extract insights, transcripts, and visual analysis from any YouTube video using GPT-4o and Whisper AI
          </p>
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {!showProgress ? (
            <div className="space-y-6">
              {/* Tabs */}
              <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg p-1">
                <button
                  onClick={() => setActiveTab("single")}
                  className={`flex-1 px-4 py-2.5 rounded-md font-medium text-sm transition-colors ${
                    activeTab === "single"
                      ? "bg-indigo-600 text-white"
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  Single Video
                </button>
                <button
                  onClick={() => setActiveTab("bulk")}
                  className={`flex-1 px-4 py-2.5 rounded-md font-medium text-sm transition-colors ${
                    activeTab === "bulk"
                      ? "bg-purple-600 text-white"
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  Bulk Channel Analysis
                </button>
              </div>

              {/* Content */}
              {activeTab === "single" ? (
                <UrlForm onJobCreated={handleJobCreated} />
              ) : (
                <BulkAnalyze />
              )}
            </div>
          ) : (
            <div className="space-y-6">
              <ProgressStream
                jobId={currentJobId!}
                onComplete={handleComplete}
              />
              <div className="flex justify-center">
                <button
                  onClick={handleReset}
                  className="px-5 py-2.5 text-sm font-medium text-gray-700 hover:text-gray-900 bg-white hover:bg-gray-50 rounded-lg border border-gray-200 transition-colors"
                >
                  Analyze Another Video
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Features Grid */}
        {!showProgress && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16">
            <div className="p-6 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-indigo-600 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Scene Detection</h3>
              <p className="text-gray-600 text-sm">Automatically extract and analyze key frames from videos with precision</p>
            </div>

            <div className="p-6 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-indigo-600 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Audio Transcription</h3>
              <p className="text-gray-600 text-sm">Convert speech to text with OpenAI Whisper&apos;s advanced technology</p>
            </div>

            <div className="p-6 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-indigo-600 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Insights</h3>
              <p className="text-gray-600 text-sm">Deep analysis with GPT-4o multimodal capabilities for comprehensive understanding</p>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

