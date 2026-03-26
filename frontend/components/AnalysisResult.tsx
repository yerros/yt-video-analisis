"use client";

interface AnalysisResultProps {
  transcript: string;
  analysis: {
    summary: {
      summary: string;
      topics: string[];
      key_points: Array<{
        point: string;
        timestamp: string;
      }>;
      sentiment: string;
      language: string;
      content_type: string;
      insights: string;
      frames?: Array<{
        filename: string;
        path: string;
        timestamp: number;
        frame_number: number;
      }>;
    };
    ai_usage?: {
      whisper_model: string;
      whisper_duration_seconds: number;
      whisper_cost_usd: number;
      gpt_model: string;
      gpt_prompt_tokens: number;
      gpt_completion_tokens: number;
      gpt_total_tokens: number;
      gpt_cost_usd: number;
      total_cost_usd: number;
    };
  };
  framesCount: number;
}

export function AnalysisResultComponent({ transcript, analysis, framesCount }: AnalysisResultProps) {
  const analysisData = analysis.summary;
  const aiUsage = analysis.ai_usage;
  const frames = analysisData.frames || [];
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full max-w-4xl space-y-6">
      {/* AI Usage Information */}
      {aiUsage && (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
          <h2 className="text-2xl font-semibold mb-6 text-gray-900">AI Usage & Cost</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Whisper Info */}
            <div className="bg-indigo-600 rounded-lg p-5 text-white">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </div>
                <div className="text-sm font-semibold">Audio Transcription</div>
              </div>
              <div className="space-y-1.5 mb-3">
                <div className="text-sm">Model: <span className="font-mono font-semibold">{aiUsage.whisper_model}</span></div>
                <div className="text-sm">Duration: <span className="font-semibold">{aiUsage.whisper_duration_seconds}s</span></div>
              </div>
              <div className="text-2xl font-bold">${aiUsage.whisper_cost_usd.toFixed(4)}</div>
            </div>

            {/* GPT Info */}
            <div className="bg-indigo-600 rounded-lg p-5 text-white">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div className="text-sm font-semibold">Video Analysis</div>
              </div>
              <div className="space-y-1.5 mb-3">
                <div className="text-sm">Model: <span className="font-mono font-semibold">{aiUsage.gpt_model}</span></div>
                <div className="text-sm">Tokens: <span className="font-semibold">{aiUsage.gpt_total_tokens.toLocaleString()}</span></div>
                <div className="text-xs opacity-90">
                  {aiUsage.gpt_prompt_tokens.toLocaleString()} in · {aiUsage.gpt_completion_tokens.toLocaleString()} out
                </div>
              </div>
              <div className="text-2xl font-bold">${aiUsage.gpt_cost_usd.toFixed(4)}</div>
            </div>

            {/* Total Cost */}
            <div className="bg-emerald-600 rounded-lg p-5 text-white">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="text-sm font-semibold">Total Cost</div>
              </div>
              <div className="text-3xl font-bold mb-1">${aiUsage.total_cost_usd.toFixed(4)}</div>
              <div className="text-sm opacity-90">Estimated USD</div>
            </div>
          </div>
        </div>
      )}

      {/* Summary */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-semibold mb-4 text-gray-900">Summary</h2>
        <p className="text-gray-700 leading-relaxed">{analysisData.summary}</p>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
          <div className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-1">Content Type</div>
          <div className="text-base font-semibold text-gray-900 capitalize">{analysisData.content_type}</div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
          <div className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-1">Sentiment</div>
          <div className="text-base font-semibold text-gray-900 capitalize">{analysisData.sentiment}</div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
          <div className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-1">Language</div>
          <div className="text-base font-semibold text-gray-900">{analysisData.language}</div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
          <div className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-1">Frames Analyzed</div>
          <div className="text-base font-semibold text-gray-900">{framesCount}</div>
        </div>
      </div>

      {/* Analyzed Frames */}
      {frames.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900">Analyzed Frames</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {frames.map((frame, idx) => (
              <div key={idx} className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
                <div className="relative aspect-video bg-gray-100">
                  <img
                    src={frame.path.startsWith('http') ? frame.path : `${apiUrl}${frame.path}`}
                    alt={`Frame ${idx + 1} at ${formatTime(frame.timestamp)}`}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                </div>
                <div className="p-3 border-t border-gray-200">
                  <div className="text-xs text-gray-600 font-medium">
                    Frame {idx + 1}
                  </div>
                  <div className="text-sm font-semibold text-indigo-600 mt-0.5">
                    {formatTime(frame.timestamp)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Topics */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-semibold mb-4 text-gray-900">Topics</h2>
        <div className="flex flex-wrap gap-2">
          {analysisData.topics.map((topic, idx) => (
            <span
              key={idx}
              className="px-3 py-1.5 bg-gray-100 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
            >
              {topic}
            </span>
          ))}
        </div>
      </div>

      {/* Key Points */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-semibold mb-4 text-gray-900">Key Points</h2>
        <div className="space-y-4">
          {analysisData.key_points.map((point, idx) => (
            <div key={idx} className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center font-semibold text-sm">
                {idx + 1}
              </div>
              <div className="flex-1">
                <p className="text-gray-700 leading-relaxed">{point.point}</p>
                {point.timestamp !== "N/A" && (
                  <p className="text-sm text-gray-600 mt-1.5">
                    {point.timestamp}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Insights */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-semibold mb-4 text-gray-900">Detailed Insights</h2>
        <p className="text-gray-700 leading-relaxed whitespace-pre-line">
          {analysisData.insights}
        </p>
      </div>

      {/* Transcript */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-semibold mb-4 text-gray-900">Full Transcript</h2>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto">
          <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-line">
            {transcript}
          </p>
        </div>
      </div>
    </div>
  );
}
