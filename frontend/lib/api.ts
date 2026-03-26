import axios from "axios";
import type { Job, JobListResponse, ProgressUpdate, UsageStatistics, ChatSession } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const api = {
  jobs: {
    create: async (youtubeUrl: string, disableTranscript: boolean = false): Promise<Job> => {
      const response = await apiClient.post<Job>("/api/jobs", {
        youtube_url: youtubeUrl,
        disable_transcript: disableTranscript,
      });
      return response.data;
    },

    list: async (limit = 20, offset = 0): Promise<JobListResponse> => {
      const response = await apiClient.get<JobListResponse>("/api/jobs", {
        params: { limit, offset },
      });
      return response.data;
    },

    get: async (jobId: string): Promise<Job> => {
      const response = await apiClient.get<Job>(`/api/jobs/${jobId}`);
      return response.data;
    },

    delete: async (jobId: string): Promise<void> => {
      await apiClient.delete(`/api/jobs/${jobId}`);
    },

    bulkDelete: async (jobIds: string[]): Promise<{ deleted_count: number; failed_count: number; failed_ids: string[]; total_requested: number }> => {
      const response = await apiClient.post(`/api/jobs/bulk-delete`, {
        job_ids: jobIds,
      });
      return response.data;
    },

    getChannelVideos: async (channelUrl: string, maxResults?: number): Promise<any> => {
      const response = await apiClient.post(`/api/jobs/channel-videos`, {
        channel_url: channelUrl,
        max_results: maxResults,
        order: "date",
      });
      return response.data;
    },

    bulkAnalyze: async (channelUrl: string, maxResults?: number, skipExisting: boolean = true, disableTranscript: boolean = false): Promise<any> => {
      const response = await apiClient.post(`/api/jobs/bulk-analyze`, {
        channel_url: channelUrl,
        max_results: maxResults,
        skip_existing: skipExisting,
        disable_transcript: disableTranscript,
      });
      return response.data;
    },

    processQueue: async (delaySeconds: number = 30, batchSize: number = 10, mode: string = 'sequential'): Promise<any> => {
      const response = await apiClient.post(`/api/jobs/process-queue`, null, {
        params: {
          delay_seconds: delaySeconds,
          batch_size: batchSize,
          mode: mode,
        },
      });
      return response.data;
    },

    retry: async (jobId: string): Promise<Job> => {
      const response = await apiClient.post<Job>(`/api/jobs/${jobId}/retry`);
      return response.data;
    },

    retryAllFailed: async (): Promise<{ retried_count: number; message: string }> => {
      const response = await apiClient.post(`/api/jobs/retry-failed`);
      return response.data;
    },

    stream: (jobId: string, onProgress: (update: ProgressUpdate) => void, onError?: (error: Error) => void): EventSource => {
      const eventSource = new EventSource(`${API_URL}/api/jobs/${jobId}/stream`);
      let isDone = false;

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Check for done event
          if (data.event === "done") {
            isDone = true;
            eventSource.close();
            return;
          }
          
          // Skip connection events
          if (data.event === "connected") {
            return;
          }
          
          onProgress(data);
        } catch (error) {
          console.error("Failed to parse SSE data:", error);
        }
      };

      eventSource.onerror = (error) => {
        console.error("SSE connection error:", error);
        
        // Only call error handler if job wasn't completed
        if (!isDone && onError) {
          onError(new Error("Connection to server lost"));
        }
        
        eventSource.close();
      };

      return eventSource;
    },
  },

  statistics: {
    getUsage: async (): Promise<UsageStatistics> => {
      const response = await apiClient.get<UsageStatistics>("/api/statistics/usage");
      return response.data;
    },
  },

  chat: {
    createSession: async (): Promise<ChatSession> => {
      const response = await apiClient.post<ChatSession>("/api/chat/sessions");
      return response.data;
    },

    listSessions: async (limit = 50): Promise<ChatSession[]> => {
      const response = await apiClient.get<ChatSession[]>("/api/chat/sessions", {
        params: { limit },
      });
      return response.data;
    },

    getSession: async (sessionId: string): Promise<ChatSession> => {
      const response = await apiClient.get<ChatSession>(`/api/chat/sessions/${sessionId}`);
      return response.data;
    },

    deleteSession: async (sessionId: string): Promise<void> => {
      await apiClient.delete(`/api/chat/sessions/${sessionId}`);
    },
  },
};
