"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { LogIn, Sparkles, Loader2 } from "lucide-react";
import { useAuthStore } from "@/lib/store";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const response = await api.auth.login(email, password);
      setAuth(response.access_token, response.user);
      router.push("/chat");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickLogin = async () => {
    setEmail("test@hermes.ai");
    setPassword("test123");
    setError("");
    setIsLoading(true);

    try {
      const response = await api.auth.login("test@hermes.ai", "test123");
      setAuth(response.access_token, response.user);
      router.push("/chat");
    } catch (err: any) {
      // Try registering if login fails
      try {
        const registerResponse = await api.auth.register(
          "test@hermes.ai",
          "test123",
          "Test User"
        );
        setAuth(registerResponse.access_token, registerResponse.user);
        router.push("/chat");
      } catch (regErr: any) {
        setError("Quick login failed. Please use manual login.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
              <Sparkles className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-3xl font-bold gradient-text">Hermes</h1>
          </div>
          <p className="text-slate-600">Sign in to continue</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleLogin} className="card space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="input-field"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="input-field"
            />
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600"
            >
              {error}
            </motion.div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full button-primary flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <LogIn className="w-5 h-5" />
                Sign In
              </>
            )}
          </button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-slate-500">Or</span>
            </div>
          </div>

          <button
            type="button"
            onClick={handleQuickLogin}
            disabled={isLoading}
            className="w-full button-secondary disabled:opacity-50"
          >
            Quick Login (Test Account)
          </button>
        </form>

        <p className="text-center text-sm text-slate-600 mt-6">
          First time?{" "}
          <button
            onClick={() => router.push("/auth/register")}
            className="text-primary-600 font-medium hover:underline"
          >
            Create an account
          </button>
        </p>
      </motion.div>
    </div>
  );
}
