'use client';

import { useEffect, useState } from 'react';
import {
  Activity,
  AlertCircle,
  CheckCircle,
  Clock,
  Cpu,
  PlayCircle,
  RefreshCw,
  Server,
  Shield,
  XCircle,
} from 'lucide-react';

interface WorkerStatus {
  status: string;
  is_healthy: boolean;
  pid: number | null;
  uptime_seconds: number | null;
  active_tasks: number;
  pending_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  monitor_running: boolean;
  monitor_pid: number | null;
  last_health_check: string | null;
  redis_connected: boolean;
  timestamp: string;
}

export default function WorkerStatusPage() {
  const [status, setStatus] = useState<WorkerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [restarting, setRestarting] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchStatus = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/worker/status`);
      if (!response.ok) throw new Error('Failed to fetch worker status');
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleRestart = async () => {
    if (!confirm('Are you sure you want to restart the worker? This will interrupt any running tasks.')) {
      return;
    }

    setRestarting(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/worker/restart`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to restart worker');
      alert('Worker restarted successfully!');
      setTimeout(fetchStatus, 3000); // Refresh after 3 seconds
    } catch (err) {
      alert(`Failed to restart worker: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setRestarting(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchStatus, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const formatUptime = (seconds: number | null): string => {
    if (!seconds) return 'N/A';
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);

    return parts.join(' ');
  };

  const formatTimestamp = (timestamp: string | null): string => {
    if (!timestamp) return 'Never';
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return 'Invalid';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading worker status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchStatus}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!status) return null;

  const isRunning = status.status === 'running';
  const isHealthy = status.is_healthy;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Server className="w-8 h-8 text-blue-500" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Worker Status</h1>
                <p className="text-sm text-gray-500">Real-time monitoring of Celery worker</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded"
                />
                Auto-refresh (5s)
              </label>
              <button
                onClick={fetchStatus}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                title="Refresh now"
              >
                <RefreshCw className="w-5 h-5 text-gray-600" />
              </button>
              <button
                onClick={handleRestart}
                disabled={restarting || !isRunning}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  restarting || !isRunning
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-red-500 text-white hover:bg-red-600'
                }`}
              >
                {restarting ? 'Restarting...' : 'Restart Worker'}
              </button>
            </div>
          </div>

          {/* Overall Status */}
          <div className="flex items-center gap-6 pt-4 border-t">
            <div className="flex items-center gap-2">
              {isRunning ? (
                <CheckCircle className="w-6 h-6 text-green-500" />
              ) : (
                <XCircle className="w-6 h-6 text-red-500" />
              )}
              <div>
                <p className="text-xs text-gray-500">Status</p>
                <p className={`font-semibold ${isRunning ? 'text-green-600' : 'text-red-600'}`}>
                  {status.status.toUpperCase()}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {isHealthy ? (
                <Activity className="w-6 h-6 text-green-500" />
              ) : (
                <AlertCircle className="w-6 h-6 text-orange-500" />
              )}
              <div>
                <p className="text-xs text-gray-500">Health</p>
                <p className={`font-semibold ${isHealthy ? 'text-green-600' : 'text-orange-600'}`}>
                  {isHealthy ? 'HEALTHY' : 'UNHEALTHY'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Clock className="w-6 h-6 text-blue-500" />
              <div>
                <p className="text-xs text-gray-500">Uptime</p>
                <p className="font-semibold text-gray-900">{formatUptime(status.uptime_seconds)}</p>
              </div>
            </div>

            {status.pid && (
              <div className="flex items-center gap-2">
                <Cpu className="w-6 h-6 text-purple-500" />
                <div>
                  <p className="text-xs text-gray-500">PID</p>
                  <p className="font-semibold text-gray-900">{status.pid}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          {/* Active Tasks */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-2">
              <PlayCircle className="w-8 h-8 text-blue-500" />
              <span className="text-3xl font-bold text-gray-900">{status.active_tasks}</span>
            </div>
            <p className="text-sm text-gray-600">Active Tasks</p>
            <p className="text-xs text-gray-400 mt-1">Currently processing</p>
          </div>

          {/* Pending Tasks */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-2">
              <Clock className="w-8 h-8 text-orange-500" />
              <span className="text-3xl font-bold text-gray-900">{status.pending_tasks}</span>
            </div>
            <p className="text-sm text-gray-600">Pending Tasks</p>
            <p className="text-xs text-gray-400 mt-1">Waiting in queue</p>
          </div>

          {/* Completed Tasks */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-2">
              <CheckCircle className="w-8 h-8 text-green-500" />
              <span className="text-3xl font-bold text-gray-900">{status.completed_tasks}</span>
            </div>
            <p className="text-sm text-gray-600">Completed</p>
            <p className="text-xs text-gray-400 mt-1">Successfully finished</p>
          </div>

          {/* Failed Tasks */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-2">
              <XCircle className="w-8 h-8 text-red-500" />
              <span className="text-3xl font-bold text-gray-900">{status.failed_tasks}</span>
            </div>
            <p className="text-sm text-gray-600">Failed</p>
            <p className="text-xs text-gray-400 mt-1">Errors occurred</p>
          </div>
        </div>

        {/* System Status */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Monitor Status */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="w-6 h-6 text-purple-500" />
              <h2 className="text-lg font-semibold text-gray-900">Monitor Status</h2>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Monitor Running</span>
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    status.monitor_running
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {status.monitor_running ? 'Yes' : 'No'}
                </span>
              </div>
              {status.monitor_pid && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Monitor PID</span>
                  <span className="text-sm font-medium text-gray-900">{status.monitor_pid}</span>
                </div>
              )}
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Last Health Check</span>
                <span className="text-sm font-medium text-gray-900">
                  {formatTimestamp(status.last_health_check)}
                </span>
              </div>
            </div>
          </div>

          {/* System Status */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center gap-3 mb-4">
              <Server className="w-6 h-6 text-blue-500" />
              <h2 className="text-lg font-semibold text-gray-900">System Status</h2>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Redis Connection</span>
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    status.redis_connected
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {status.redis_connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Last Updated</span>
                <span className="text-sm font-medium text-gray-900">
                  {formatTimestamp(status.timestamp)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Info Banner */}
        {!isHealthy && isRunning && (
          <div className="mt-6 bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-orange-900">Worker is unhealthy</p>
                <p className="text-sm text-orange-700 mt-1">
                  The worker is running but not responding to health checks. This might be normal if
                  it&apos;s processing a heavy task. If this persists, consider restarting the worker.
                </p>
              </div>
            </div>
          </div>
        )}

        {!isRunning && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-900">Worker is not running</p>
                <p className="text-sm text-red-700 mt-1">
                  The Celery worker is currently stopped. Start the worker to process jobs.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
