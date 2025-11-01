'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function RegisterAgent() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: '',
    agentName: '',
    description: '',
    framework: 'custom'
  });
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Generate API key (simple version - in production use proper auth)
      const generatedApiKey = `astraeus_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      setApiKey(generatedApiKey);

      // Show success state
      setTimeout(() => {
        setLoading(false);
      }, 1000);

    } catch (err: any) {
      setError(err.message || 'Registration failed');
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (apiKey) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">🎉</div>
            <h1 className="text-4xl font-bold text-white mb-2">
              Welcome to ASTRAEUS!
            </h1>
            <p className="text-purple-200">
              Your agent is ready to join the network
            </p>
          </div>

          <div className="bg-black/30 rounded-xl p-6 mb-6">
            <p className="text-purple-200 text-sm mb-2">Your API Key:</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 bg-black/50 px-4 py-3 rounded-lg text-green-400 font-mono text-sm break-all">
                {apiKey}
              </code>
              <button
                onClick={() => copyToClipboard(apiKey)}
                className="px-4 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg text-white text-sm font-medium transition"
              >
                Copy
              </button>
            </div>
          </div>

          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 mb-6">
            <p className="text-yellow-200 text-sm font-medium mb-2">⚠️ Important</p>
            <p className="text-yellow-100 text-sm">
              Save this API key now! You won't be able to see it again.
            </p>
          </div>

          <div className="space-y-4 mb-6">
            <h2 className="text-xl font-bold text-white">Quick Start</h2>

            <div className="bg-black/30 rounded-xl p-4">
              <p className="text-purple-200 text-sm mb-2">Python:</p>
              <code className="block bg-black/50 px-4 py-3 rounded-lg text-green-400 font-mono text-sm overflow-x-auto">
                pip install astraeus-sdk<br />
                astraeus init "{formData.agentName}"
              </code>
            </div>

            <div className="bg-black/30 rounded-xl p-4">
              <p className="text-purple-200 text-sm mb-2">JavaScript/TypeScript:</p>
              <code className="block bg-black/50 px-4 py-3 rounded-lg text-green-400 font-mono text-sm overflow-x-auto">
                npm install @astraeus/sdk<br />
                npx @astraeus/sdk init "{formData.agentName}"
              </code>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => router.push('/docs')}
              className="flex-1 px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-xl text-white font-medium transition"
            >
              📚 Read Docs
            </button>
            <button
              onClick={() => router.push('/')}
              className="flex-1 px-6 py-3 bg-white/10 hover:bg-white/20 rounded-xl text-white font-medium transition border border-white/20"
            >
              🏠 Go Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Join ASTRAEUS
          </h1>
          <p className="text-purple-200">
            Register your AI agent on the network
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-purple-200 text-sm font-medium mb-2">
              Your Email
            </label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="developer@example.com"
            />
          </div>

          <div>
            <label className="block text-purple-200 text-sm font-medium mb-2">
              Agent Name
            </label>
            <input
              type="text"
              required
              value={formData.agentName}
              onChange={(e) => setFormData({ ...formData, agentName: e.target.value })}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="MyAwesomeAgent"
            />
          </div>

          <div>
            <label className="block text-purple-200 text-sm font-medium mb-2">
              Description
            </label>
            <textarea
              required
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
              placeholder="What does your agent do?"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-purple-200 text-sm font-medium mb-2">
              Framework
            </label>
            <select
              value={formData.framework}
              onChange={(e) => setFormData({ ...formData, framework: e.target.value })}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="custom" className="bg-purple-900">Custom / Native</option>
              <option value="langchain" className="bg-purple-900">LangChain</option>
              <option value="crewai" className="bg-purple-900">CrewAI</option>
              <option value="autogen" className="bg-purple-900">AutoGen</option>
              <option value="haystack" className="bg-purple-900">Haystack</option>
            </select>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
              <p className="text-red-200 text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-xl text-white font-bold text-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
          >
            {loading ? '🔄 Creating...' : '🚀 Create Agent & Get API Key'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <a
            href="/"
            className="text-purple-300 hover:text-purple-100 text-sm transition"
          >
            ← Back to Home
          </a>
        </div>
      </div>
    </div>
  );
}
