'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

interface Node {
  node_id: string;
  name: string;
  node_type: 'agent_call' | 'tool_call' | 'human_gate' | 'condition';
  agent_id?: string;
  tool_name?: string;
  config?: Record<string, any>;
  inputs?: Record<string, any>;
  retry_count: number;
  timeout_seconds?: number;
}

interface Edge {
  from_node_id: string;
  to_node_id: string;
  condition?: string;
}

export default function NewWorkflowPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Node form state
  const [showNodeForm, setShowNodeForm] = useState(false);
  const [editingNode, setEditingNode] = useState<Node | null>(null);

  // Edge form state
  const [showEdgeForm, setShowEdgeForm] = useState(false);
  const [newEdge, setNewEdge] = useState<Edge>({ from_node_id: '', to_node_id: '', condition: '' });

  const handleAddNode = (node: Node) => {
    if (editingNode) {
      setNodes(nodes.map(n => n.node_id === editingNode.node_id ? node : n));
    } else {
      setNodes([...nodes, node]);
    }
    setShowNodeForm(false);
    setEditingNode(null);
  };

  const handleRemoveNode = (nodeId: string) => {
    setNodes(nodes.filter(n => n.node_id !== nodeId));
    setEdges(edges.filter(e => e.from_node_id !== nodeId && e.to_node_id !== nodeId));
  };

  const handleAddEdge = () => {
    if (newEdge.from_node_id && newEdge.to_node_id) {
      setEdges([...edges, newEdge]);
      setNewEdge({ from_node_id: '', to_node_id: '', condition: '' });
      setShowEdgeForm(false);
    }
  };

  const handleRemoveEdge = (from: string, to: string) => {
    setEdges(edges.filter(e => !(e.from_node_id === from && e.to_node_id === to)));
  };

  const handleSaveWorkflow = async () => {
    if (!name.trim()) {
      alert('Please enter a workflow name');
      return;
    }

    if (nodes.length === 0) {
      alert('Please add at least one node');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/auth/login');
        return;
      }

      const response = await fetch('http://localhost:8000/api/v1/workflows', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          description,
          nodes,
          edges,
          timeout_seconds: null,
          max_retries: 3,
          on_error: 'fail',
          tags: [],
          is_public: false,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || 'Failed to create workflow');
      }

      const workflow = await response.json();
      router.push(`/workflows/${workflow.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-blue-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="text-blue-600 dark:text-blue-400 hover:underline mb-2"
          >
            ← Back to Workflows
          </button>
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
            ✨ Create New Workflow
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Build a multi-agent workflow by defining nodes and connections
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-200">⚠️ {error}</p>
          </div>
        )}

        {/* Main Form */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Basic Info & Nodes */}
          <div className="space-y-6">
            {/* Basic Info */}
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
                Basic Information
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Workflow Name *
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="My Awesome Workflow"
                    className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Description
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="What does this workflow do?"
                    rows={3}
                    className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                  />
                </div>
              </div>
            </div>

            {/* Nodes */}
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                  Nodes ({nodes.length})
                </h2>
                <button
                  onClick={() => {
                    setEditingNode(null);
                    setShowNodeForm(true);
                  }}
                  className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all font-semibold"
                >
                  + Add Node
                </button>
              </div>

              {nodes.length === 0 ? (
                <p className="text-slate-600 dark:text-slate-400 text-center py-8">
                  No nodes yet. Add your first node to get started.
                </p>
              ) : (
                <div className="space-y-3">
                  {nodes.map((node) => (
                    <div
                      key={node.node_id}
                      className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-bold text-slate-900 dark:text-white">
                            {node.name}
                          </h3>
                          <p className="text-sm text-slate-600 dark:text-slate-400">
                            ID: {node.node_id} • Type: {node.node_type}
                          </p>
                          {node.agent_id && (
                            <p className="text-sm text-blue-600 dark:text-blue-400">
                              Agent: {node.agent_id}
                            </p>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              setEditingNode(node);
                              setShowNodeForm(true);
                            }}
                            className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleRemoveNode(node.node_id)}
                            className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Edges & Actions */}
          <div className="space-y-6">
            {/* Edges */}
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                  Connections ({edges.length})
                </h2>
                <button
                  onClick={() => setShowEdgeForm(true)}
                  disabled={nodes.length < 2}
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  + Add Connection
                </button>
              </div>

              {edges.length === 0 ? (
                <p className="text-slate-600 dark:text-slate-400 text-center py-8">
                  No connections yet. {nodes.length < 2 ? 'Add at least 2 nodes first.' : 'Add connections to link nodes.'}
                </p>
              ) : (
                <div className="space-y-3">
                  {edges.map((edge, idx) => (
                    <div
                      key={idx}
                      className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-bold text-slate-900 dark:text-white">
                            {edge.from_node_id} → {edge.to_node_id}
                          </p>
                          {edge.condition && (
                            <p className="text-sm text-slate-600 dark:text-slate-400">
                              Condition: {edge.condition}
                            </p>
                          )}
                        </div>
                        <button
                          onClick={() => handleRemoveEdge(edge.from_node_id, edge.to_node_id)}
                          className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Visual DAG Preview */}
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
                DAG Preview
              </h2>
              <div className="bg-slate-100 dark:bg-slate-900 rounded-lg p-6 text-center">
                <p className="text-slate-600 dark:text-slate-400 mb-2">
                  {nodes.length} nodes, {edges.length} edges
                </p>
                <div className="text-6xl mb-4">🔄</div>
                <p className="text-sm text-slate-500 dark:text-slate-500">
                  Visual graph editor coming soon!
                </p>
              </div>
            </div>

            {/* Save Button */}
            <button
              onClick={handleSaveWorkflow}
              disabled={loading || nodes.length === 0}
              className="w-full py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all duration-200 shadow-lg hover:shadow-xl font-bold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '⏳ Creating Workflow...' : '💾 Save Workflow'}
            </button>
          </div>
        </div>
      </div>

      {/* Node Form Modal */}
      {showNodeForm && (
        <NodeFormModal
          node={editingNode}
          onSave={handleAddNode}
          onCancel={() => {
            setShowNodeForm(false);
            setEditingNode(null);
          }}
        />
      )}

      {/* Edge Form Modal */}
      {showEdgeForm && (
        <EdgeFormModal
          nodes={nodes}
          edge={newEdge}
          onChange={setNewEdge}
          onSave={handleAddEdge}
          onCancel={() => setShowEdgeForm(false)}
        />
      )}
    </div>
  );
}

// Node Form Modal Component
function NodeFormModal({
  node,
  onSave,
  onCancel,
}: {
  node: Node | null;
  onSave: (node: Node) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<Node>(
    node || {
      node_id: '',
      name: '',
      node_type: 'agent_call',
      retry_count: 3,
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.node_id || !formData.name) {
      alert('Please fill in all required fields');
      return;
    }
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit} className="p-6">
          <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
            {node ? 'Edit Node' : 'Add New Node'}
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Node ID *
              </label>
              <input
                type="text"
                value={formData.node_id}
                onChange={(e) => setFormData({ ...formData, node_id: e.target.value })}
                placeholder="step1"
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                disabled={!!node}
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Search for flights"
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Type *
              </label>
              <select
                value={formData.node_type}
                onChange={(e) => setFormData({ ...formData, node_type: e.target.value as any })}
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
              >
                <option value="agent_call">Agent Call</option>
                <option value="tool_call">Tool Call</option>
                <option value="human_gate">Human Gate (Approval)</option>
                <option value="condition">Condition (Branch)</option>
              </select>
            </div>

            {formData.node_type === 'agent_call' && (
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Agent ID
                </label>
                <input
                  type="text"
                  value={formData.agent_id || ''}
                  onChange={(e) => setFormData({ ...formData, agent_id: e.target.value })}
                  placeholder="flight-search-agent"
                  className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                />
              </div>
            )}

            {formData.node_type === 'tool_call' && (
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Tool Name
                </label>
                <input
                  type="text"
                  value={formData.tool_name || ''}
                  onChange={(e) => setFormData({ ...formData, tool_name: e.target.value })}
                  placeholder="web_search"
                  className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Retry Count
              </label>
              <input
                type="number"
                value={formData.retry_count}
                onChange={(e) => setFormData({ ...formData, retry_count: parseInt(e.target.value) })}
                min="0"
                max="10"
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Timeout (seconds)
              </label>
              <input
                type="number"
                value={formData.timeout_seconds || ''}
                onChange={(e) => setFormData({ ...formData, timeout_seconds: e.target.value ? parseInt(e.target.value) : undefined })}
                placeholder="30"
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
              />
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="submit"
              className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-semibold"
            >
              {node ? 'Update Node' : 'Add Node'}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="px-6 py-3 bg-slate-300 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg hover:bg-slate-400 dark:hover:bg-slate-600 transition-all font-semibold"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Edge Form Modal Component
function EdgeFormModal({
  nodes,
  edge,
  onChange,
  onSave,
  onCancel,
}: {
  nodes: Node[];
  edge: Edge;
  onChange: (edge: Edge) => void;
  onSave: () => void;
  onCancel: () => void;
}) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-2xl max-w-lg w-full">
        <form onSubmit={handleSubmit} className="p-6">
          <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
            Add Connection
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                From Node *
              </label>
              <select
                value={edge.from_node_id}
                onChange={(e) => onChange({ ...edge, from_node_id: e.target.value })}
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                required
              >
                <option value="">Select a node...</option>
                {nodes.map((node) => (
                  <option key={node.node_id} value={node.node_id}>
                    {node.name} ({node.node_id})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                To Node *
              </label>
              <select
                value={edge.to_node_id}
                onChange={(e) => onChange({ ...edge, to_node_id: e.target.value })}
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                required
              >
                <option value="">Select a node...</option>
                {nodes.map((node) => (
                  <option key={node.node_id} value={node.node_id}>
                    {node.name} ({node.node_id})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Condition (optional)
              </label>
              <input
                type="text"
                value={edge.condition || ''}
                onChange={(e) => onChange({ ...edge, condition: e.target.value })}
                placeholder="result.success == true"
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
              />
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="submit"
              className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all font-semibold"
            >
              Add Connection
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="px-6 py-3 bg-slate-300 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg hover:bg-slate-400 dark:hover:bg-slate-600 transition-all font-semibold"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
