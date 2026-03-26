export type JobStatus =
  | "pending"
  | "downloading"
  | "transcribing"
  | "extracting"
  | "analyzing"
  | "done"
  | "failed";

export interface Job {
  id: string;
  youtube_url: string;
  video_title: string | null;
  video_duration: number | null;
  // YouTube metadata fields
  youtube_metadata: Record<string, any> | null;
  channel_title: string | null;
  channel_id: string | null;
  description: string | null;
  tags: string[] | null;
  category_id: string | null;
  published_at: string | null;
  view_count: number | null;
  like_count: number | null;
  comment_count: number | null;
  thumbnail_url: string | null;
  // Job fields
  status: JobStatus;
  progress: number;
  transcript: string | null;
  frames_count: number | null;
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
  } | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalysisResult {
  transcript: string;
  frame_count: number;
  analysis: {
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
  };
}

export interface JobListResponse {
  items: Job[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProgressUpdate {
  job_id: string;
  progress: number;
  status: JobStatus;
  message: string;
  error?: string;
  timestamp: string;
}

export interface UsageStatistics {
  overview: {
    total_jobs_completed: number;
    total_jobs_failed: number;
    total_jobs_processing: number;
    jobs_with_ai_usage: number;
    total_frames_extracted: number;
    avg_frames_per_job: number;
  };
  whisper: {
    total_duration_seconds: number;
    total_duration_minutes: number;
    total_cost_usd: number;
    avg_duration_per_job_seconds: number;
    model: string;
  };
  gpt4o: {
    total_prompt_tokens: number;
    total_completion_tokens: number;
    total_tokens: number;
    total_cost_usd: number;
    avg_tokens_per_job: number;
    model: string;
  };
  embeddings: {
    total_embeddings_generated: number;
    total_tokens: number;
    total_cost_usd: number;
    model: string;
  };
  total: {
    total_cost_usd: number;
    avg_cost_per_job_usd: number;
    cost_breakdown: {
      whisper_percentage: number;
      gpt4o_percentage: number;
      embeddings_percentage: number;
    };
  };
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  referenced_jobs?: string[];
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count?: number;
  messages?: ChatMessage[];
}
