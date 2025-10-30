'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';

interface WorkflowDetail {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  version: number;
  is_public: boolean;
  is_active: boolean;
  timeout_seconds: number | null;
  max_retries: number;
  on_error: string;
  tags: string[];
  created_at: string;
  updated_at: string | null;
  node_count: number;
  edge_count: number;
  nodes: any[];
  edges: any[];
}

export default function WorkflowDetailPage() {
  const router = useRouter();
  const params = useParams();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<WorkflowDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWorkflow();
  }, [workflowId]);

  const fetchWorkflow = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/auth/login');
        return;
      }

      const response = await fetch(
        `http://localhost:8000/api/v1/workflows/${workflowId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch workflow');
      }

      const data = await response.json();
      setWorkflow(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleRun = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `http://localhost:8000/api/v1/workflows/${workflowId}/run`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ inputs: {} }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to start workflow');
      }

      const run = await response.json();
      router.push(`/workflows/runs/${run.id}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to start workflow');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-blue-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent"></div>
          <p className="mt-4 text-slate-600 dark:text-slate-400 text-lg">Loading workflow...</p>
        </div>
      </div>
    );
  }

  if (error || !workflow) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-blue-900 flex items-center justify-center">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 max-w-md">
          <p className="text-red-800 dark:text-red-200">⚠️ {error || 'Workflow not found'}</p>
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
            <Link
              href="/workflows"
              className="text-blue-600 dark:text-blue-400 hover:underline mb-2 inline-block"
            >
              ← Back to Workflows
            </Link>
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
              {workflow.name}
            </h1>
            {workflow.description && (
              <p className="text-slate-600 dark:text-slate-400">
                {workflow.description}
              </p>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleRun}
              className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all duration-200 shadow-lg hover:shadow-xl font-semibold"
            >
              ▶ Run Workflow
            </button>
          </div>
        </div>

        {/* Metadata */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
            Workflow Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Version</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                v{workflow.version}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Status</p>
              <span className={`inline-flex px-3 py-1 rounded-full font-semibold text-sm ${
                workflow.is_active
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200'
              }`}>
                {workflow.is_active ? '✅ Active' : '⏸️ Inactive'}
              </span>
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Visibility</p>
              <span className={`inline-flex px-3 py-1 rounded-full font-semibold text-sm ${
                workflow.is_public
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200'
              }`}>
                {workflow.is_public ? '🌍 Public' : '🔒 Private'}
              </span>
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Max Retries</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {workflow.max_retries}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">On Error</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {workflow.on_error}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Timeout</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {workflow.timeout_seconds ? `${workflow.timeout_seconds}s` : 'None'}
              </p>
            </div>
          </div>

          {workflow.tags && workflow.tags.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Tags</p>
              <div className="flex flex-wrap gap-2">
                {workflow.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200 text-sm rounded-full font-semibold"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* DAG Structure */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Nodes */}
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
              Nodes ({workflow.node_count})
            </h2>
            {workflow.nodes && workflow.nodes.length > 0 ? (
              <div className="space-y-3">
                {workflow.nodes.map((node) => (
                  <div
                    key={node.node_id}
                    className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-all"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-bold text-slate-900 dark:text-white">
                          {node.name}
                        </h3>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          ID: {node.node_id}
                        </p>
                        <span className="inline-flex mt-2 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 text-xs rounded font-semibold">
                          {node.node_type}
                        </span>
                      </div>
                      <div className="text-right text-sm text-slate-600 dark:text-slate-400">
                        {node.agent_id && (
                          <p className="text-blue-600 dark:text-blue-400">
                            🤖 {node.agent_id}
                          </p>
                        )}
                        {node.tool_name && (
                          <p className="text-purple-600 dark:text-purple-400">
                            🔧 {node.tool_name}
                          </p>
                        )}
                        <p className="mt-1">
                          Retries: {node.retry_count}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-600 dark:text-slate-400 text-center py-8">
                No nodes defined
              </p>
            )}
          </div>

          {/* Edges */}
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
              Connections ({workflow.edge_count})
            </h2>
            {workflow.edges && workflow.edges.length > 0 ? (
              <div className="space-y-3">
                {workflow.edges.map((edge, idx) => (
                  <div
                    key={idx}
                    className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 font-mono text-sm">
                          <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 rounded font-semibold">
                            {edge.from_node_id}
                          </span>
                          <span className="text-slate-400">→</span>
                          <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded font-semibold">
                            {edge.to_node_id}
                          </span>
                        </div>
                        {edge.condition && (
                          <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                            Condition: <code className="bg-slate-100 dark:bg-slate-900 px-2 py-1 rounded">
                              {edge.condition}
                            </code>
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-600 dark:text-slate-400 text-center py-8">
                No connections defined
              </p>
            )}
          </div>
        </div>

        {/* Visual Graph Placeholder */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6 mt-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
            Visual DAG Editor
          </h2>
          <div className="bg-slate-100 dark:bg-slate-900 rounded-lg p-12 text-center">
            <div className="text-8xl mb-4">🔄</div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              Interactive Graph Editor Coming Soon!
            </h3>
            <p className="text-slate-600 dark:text-slate-400 mb-4">
              Visual workflow builder with drag-and-drop nodes, real-time validation, and more.
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-500">
              Will integrate React Flow for beautiful interactive DAG editing
            </p>
          </div>
        </div>

        {/* Timestamps */}
        <div className="text-sm text-slate-500 dark:text-slate-500 mt-6 text-center">
          Created {new Date(workflow.created_at).toLocaleString()}
          {workflow.updated_at && (
            <> • Updated {new Date(workflow.updated_at).toLocaleString()}</>
          )}
        </div>
      </div>
    </div>
  );
}
