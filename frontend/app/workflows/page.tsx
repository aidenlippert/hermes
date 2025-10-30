'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface Workflow {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  version: number;
  is_public: boolean;
  is_active: boolean;
  node_count: number;
  edge_count: number;
  created_at: string;
  updated_at: string | null;
  tags: string[];
}

export default function WorkflowsPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'mine' | 'public'>('all');

  useEffect(() => {
    fetchWorkflows();
  }, [filter]);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/auth/login');
        return;
      }

      const params = new URLSearchParams();
      if (filter === 'public') {
        params.append('is_public', 'true');
      }

      const response = await fetch(
        `http://localhost:8000/api/v1/workflows?${params.toString()}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch workflows');
      }

      const data = await response.json();
      setWorkflows(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (workflowId: string) => {
    if (!confirm('Are you sure you want to delete this workflow?')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `http://localhost:8000/api/v1/workflows/${workflowId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to delete workflow');
      }

      // Refresh list
      fetchWorkflows();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete workflow');
    }
  };

  const handleRun = async (workflowId: string) => {
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
      // Navigate to run viewer
      router.push(`/workflows/runs/${run.id}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to start workflow');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-blue-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
              🔄 Multi-Agent Workflows
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Orchestrate complex agent interactions with visual DAG workflows
            </p>
          </div>
          <Link
            href="/workflows/new"
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl font-semibold"
          >
            ✨ Create Workflow
          </Link>
        </div>

        {/* Filters */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              filter === 'all'
                ? 'bg-blue-600 text-white shadow-md'
                : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            All Workflows
          </button>
          <button
            onClick={() => setFilter('mine')}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              filter === 'mine'
                ? 'bg-blue-600 text-white shadow-md'
                : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            My Workflows
          </button>
          <button
            onClick={() => setFilter('public')}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              filter === 'public'
                ? 'bg-blue-600 text-white shadow-md'
                : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            Public Templates
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
            <p className="mt-4 text-slate-600 dark:text-slate-400">Loading workflows...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-200">⚠️ {error}</p>
          </div>
        )}

        {/* Workflows Grid */}
        {!loading && !error && (
          <>
            {workflows.length === 0 ? (
              <div className="text-center py-16 bg-white dark:bg-slate-800 rounded-lg shadow-lg">
                <div className="text-6xl mb-4">🔄</div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                  No workflows yet
                </h2>
                <p className="text-slate-600 dark:text-slate-400 mb-6">
                  Create your first multi-agent workflow to get started
                </p>
                <Link
                  href="/workflows/new"
                  className="inline-block px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl font-semibold"
                >
                  ✨ Create Workflow
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {workflows.map((workflow) => (
                  <div
                    key={workflow.id}
                    className="bg-white dark:bg-slate-800 rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 overflow-hidden"
                  >
                    <div className="p-6">
                      {/* Header */}
                      <div className="flex justify-between items-start mb-4">
                        <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                          {workflow.name}
                        </h3>
                        {workflow.is_public && (
                          <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 text-xs font-semibold rounded">
                            Public
                          </span>
                        )}
                      </div>

                      {/* Description */}
                      {workflow.description && (
                        <p className="text-slate-600 dark:text-slate-400 text-sm mb-4 line-clamp-2">
                          {workflow.description}
                        </p>
                      )}

                      {/* Stats */}
                      <div className="flex gap-4 mb-4 text-sm">
                        <div className="flex items-center gap-1">
                          <span className="text-blue-600 dark:text-blue-400">●</span>
                          <span className="text-slate-600 dark:text-slate-400">
                            {workflow.node_count} nodes
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-purple-600 dark:text-purple-400">→</span>
                          <span className="text-slate-600 dark:text-slate-400">
                            {workflow.edge_count} edges
                          </span>
                        </div>
                      </div>

                      {/* Tags */}
                      {workflow.tags && workflow.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-4">
                          {workflow.tags.map((tag, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex gap-2 pt-4 border-t border-slate-200 dark:border-slate-700">
                        <button
                          onClick={() => handleRun(workflow.id)}
                          className="flex-1 px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all duration-200 font-semibold text-sm"
                        >
                          ▶ Run
                        </button>
                        <Link
                          href={`/workflows/${workflow.id}`}
                          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all duration-200 font-semibold text-sm text-center"
                        >
                          📝 Edit
                        </Link>
                        <button
                          onClick={() => handleDelete(workflow.id)}
                          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all duration-200 font-semibold text-sm"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>

                    {/* Footer */}
                    <div className="px-6 py-3 bg-slate-50 dark:bg-slate-900/50 text-xs text-slate-500 dark:text-slate-500">
                      Created {new Date(workflow.created_at).toLocaleDateString()}
                      {workflow.updated_at && (
                        <> • Updated {new Date(workflow.updated_at).toLocaleDateString()}</>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
