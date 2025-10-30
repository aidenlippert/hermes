'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useParams } from 'next/navigation';

interface WorkflowRun {
  id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
  inputs: Record<string, any>;
  outputs: Record<string, any> | null;
  total_cost: number;
  nodes_completed: number;
  nodes_total: number;
}

interface NodeRun {
  id: string;
  workflow_run_id: string;
  node_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
  inputs: Record<string, any> | null;
  outputs: Record<string, any> | null;
  retry_count: number;
  cost: number;
}

export default function WorkflowRunPage() {
  const router = useRouter();
  const params = useParams();
  const runId = params.runId as string;

  const [run, setRun] = useState<WorkflowRun | null>(null);
  const [nodes, setNodes] = useState<NodeRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchRunData();
  }, [runId]);

  useEffect(() => {
    if (!autoRefresh || !run || run.status === 'completed' || run.status === 'failed' || run.status === 'cancelled') {
      return;
    }

    const interval = setInterval(() => {
      fetchRunData();
    }, 2000); // Refresh every 2 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, run]);

  const fetchRunData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/auth/login');
        return;
      }

      // Fetch run details
      const runResponse = await fetch(
        `http://localhost:8000/api/v1/workflows/runs/${runId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!runResponse.ok) {
        throw new Error('Failed to fetch workflow run');
      }

      const runData = await runResponse.json();
      setRun(runData);

      // Fetch node runs
      const nodesResponse = await fetch(
        `http://localhost:8000/api/v1/workflows/runs/${runId}/nodes`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!nodesResponse.ok) {
        throw new Error('Failed to fetch node runs');
      }

      const nodesData = await nodesResponse.json();
      setNodes(nodesData);
      setError(null);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel this workflow run?')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `http://localhost:8000/api/v1/workflows/runs/${runId}/cancel`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to cancel workflow');
      }

      fetchRunData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to cancel workflow');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200';
      case 'running':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200';
      case 'failed':
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200';
      case 'cancelled':
        return 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200';
      case 'pending':
        return 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200';
      default:
        return 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'running':
        return '⚡';
      case 'failed':
        return '❌';
      case 'cancelled':
        return '🚫';
      case 'pending':
        return '⏳';
      default:
        return '●';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-blue-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent"></div>
          <p className="mt-4 text-slate-600 dark:text-slate-400 text-lg">Loading workflow run...</p>
        </div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-blue-900 flex items-center justify-center">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 max-w-md">
          <p className="text-red-800 dark:text-red-200">⚠️ {error || 'Workflow run not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-blue-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <button
              onClick={() => router.back()}
              className="text-blue-600 dark:text-blue-400 hover:underline mb-2"
            >
              ← Back to Workflows
            </button>
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
              Workflow Run
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              ID: {runId}
            </p>
          </div>
          <div className="flex gap-3 items-center">
            <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              Auto-refresh
            </label>
            {(run.status === 'pending' || run.status === 'running') && (
              <button
                onClick={handleCancel}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all duration-200 font-semibold"
              >
                🚫 Cancel Run
              </button>
            )}
          </div>
        </div>

        {/* Status Card */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Status */}
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Status</p>
              <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full font-semibold ${getStatusColor(run.status)}`}>
                {getStatusIcon(run.status)} {run.status.toUpperCase()}
              </span>
            </div>

            {/* Progress */}
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Progress</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-500"
                    style={{
                      width: run.nodes_total > 0
                        ? `${(run.nodes_completed / run.nodes_total) * 100}%`
                        : '0%'
                    }}
                  ></div>
                </div>
                <span className="text-sm font-semibold text-slate-900 dark:text-white">
                  {run.nodes_completed}/{run.nodes_total}
                </span>
              </div>
            </div>

            {/* Duration */}
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Duration</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {run.started_at && run.completed_at ? (
                  `${Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s`
                ) : run.started_at ? (
                  `${Math.round((Date.now() - new Date(run.started_at).getTime()) / 1000)}s`
                ) : (
                  'Not started'
                )}
              </p>
            </div>

            {/* Cost */}
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Total Cost</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                ${run.total_cost.toFixed(4)}
              </p>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {run.error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <h3 className="font-bold text-red-800 dark:text-red-200 mb-2">❌ Error</h3>
            <pre className="text-sm text-red-700 dark:text-red-300 whitespace-pre-wrap">
              {run.error}
            </pre>
          </div>
        )}

        {/* Node Execution Timeline */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
            Node Execution Timeline
          </h2>

          {nodes.length === 0 ? (
            <p className="text-slate-600 dark:text-slate-400 text-center py-8">
              No node executions yet...
            </p>
          ) : (
            <div className="space-y-4">
              {nodes.map((node) => (
                <div
                  key={node.id}
                  className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-all"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full font-semibold text-sm ${getStatusColor(node.status)}`}>
                        {getStatusIcon(node.status)} {node.status}
                      </span>
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                        {node.node_id}
                      </h3>
                    </div>
                    <div className="text-right text-sm text-slate-600 dark:text-slate-400">
                      {node.retry_count > 0 && (
                        <p className="text-orange-600 dark:text-orange-400">
                          🔄 Retries: {node.retry_count}
                        </p>
                      )}
                      {node.cost > 0 && (
                        <p>💰 ${node.cost.toFixed(4)}</p>
                      )}
                    </div>
                  </div>

                  {/* Timing */}
                  <div className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                    {node.started_at && (
                      <span>
                        Started: {new Date(node.started_at).toLocaleTimeString()}
                      </span>
                    )}
                    {node.completed_at && (
                      <span className="ml-4">
                        • Completed: {new Date(node.completed_at).toLocaleTimeString()}
                      </span>
                    )}
                    {node.started_at && node.completed_at && (
                      <span className="ml-4 font-semibold">
                        • Duration: {Math.round((new Date(node.completed_at).getTime() - new Date(node.started_at).getTime()) / 1000)}s
                      </span>
                    )}
                  </div>

                  {/* Error */}
                  {node.error && (
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-3 mb-3">
                      <pre className="text-sm text-red-700 dark:text-red-300 whitespace-pre-wrap">
                        {node.error}
                      </pre>
                    </div>
                  )}

                  {/* Inputs/Outputs */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {node.inputs && Object.keys(node.inputs).length > 0 && (
                      <div>
                        <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                          📥 Inputs:
                        </p>
                        <pre className="text-xs bg-slate-100 dark:bg-slate-900 p-3 rounded overflow-x-auto">
                          {JSON.stringify(node.inputs, null, 2)}
                        </pre>
                      </div>
                    )}
                    {node.outputs && Object.keys(node.outputs).length > 0 && (
                      <div>
                        <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                          📤 Outputs:
                        </p>
                        <pre className="text-xs bg-slate-100 dark:bg-slate-900 p-3 rounded overflow-x-auto">
                          {JSON.stringify(node.outputs, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Final Outputs */}
        {run.outputs && Object.keys(run.outputs).length > 0 && (
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6 mt-6">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
              🎯 Final Outputs
            </h2>
            <pre className="bg-slate-100 dark:bg-slate-900 p-4 rounded overflow-x-auto">
              {JSON.stringify(run.outputs, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
