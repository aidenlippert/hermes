import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    username: string;
    full_name: string;
    role: string;
    subscription_tier: string;
  };
}

export interface ChatRequest {
  query: string;
  conversation_id?: string;
}

export interface ChatResponse {
  task_id: string;
  conversation_id: string;
  status: string;
  message: string;
  result?: any;
  steps?: any[];
  agents?: any[];
  extracted_info?: any;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  category: string;
  capabilities: string[];
  average_rating: number;
  total_calls: number;
  is_free: boolean;
  cost_per_request: number;
}

// Auth API
export const api = {
  auth: {
    async register(email: string, password: string, full_name?: string) {
      const response = await axios.post<AuthResponse>(
        `${API_URL}/api/v1/auth/register`,
        { email, password, full_name }
      );
      return response.data;
    },

    async login(email: string, password: string) {
      const response = await axios.post<AuthResponse>(
        `${API_URL}/api/v1/auth/login`,
        { email, password }
      );
      return response.data;
    },

    async getMe(token: string) {
      const response = await axios.get(`${API_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    },
  },

  chat: {
    async send(request: ChatRequest, token: string) {
      const response = await axios.post<ChatResponse>(
        `${API_URL}/api/v1/chat`,
        request,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async approve(
      request: { task_id: string; conversation_id: string; approved?: boolean; extracted_info?: any },
      token: string
    ) {
      const response = await axios.post<ChatResponse>(
        `${API_URL}/api/v1/chat/approve`,
        { approved: true, ...request },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async history(token: string) {
      try {
        const response = await axios.get(
          `${API_URL}/api/v1/conversations`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
      } catch (error) {
        console.error("Failed to load chat history:", error);
        return { conversations: [] };
      }
    },
  },

  agents: {
    async list(token: string) {
      const response = await axios.get<{ agents: Agent[]; total: number }>(
        `${API_URL}/api/v1/marketplace`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async search(query: string, token: string) {
      const response = await axios.post<{ agents: Agent[]; total: number }>(
        `${API_URL}/api/v1/marketplace/search`,
        { query },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },
  },

  conversations: {
    async list(token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/conversations`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async get(id: string, token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/conversations/${id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },
  },

  // Payments & Credits (Sprint 3)
  payments: {
    async purchaseCredits(amount: number, provider: string, token: string) {
      const response = await axios.post(
        `${API_URL}/api/v1/payments/credits/purchase`,
        { amount, provider },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async getBalance(token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/payments/credits/balance`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async getTransactions(token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/payments/credits/transactions`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },
  },

  // Contracts (Sprint 3)
  contracts: {
    async create(title: string, description: string, budget: number, token: string) {
      const response = await axios.post(
        `${API_URL}/api/v1/contracts`,
        { title, description, budget },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async list(token: string, status?: string) {
      const params = status ? { status } : {};
      const response = await axios.get(
        `${API_URL}/api/v1/contracts`,
        { headers: { Authorization: `Bearer ${token}` }, params }
      );
      return response.data;
    },

    async get(id: string, token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/contracts/${id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },
  },

  // Orchestration (Sprint 2)
  orchestration: {
    async createPlan(query: string, token: string) {
      const response = await axios.post(
        `${API_URL}/api/v1/orchestration/plan`,
        { query },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async executePlan(planId: string, token: string) {
      const response = await axios.post(
        `${API_URL}/api/v1/orchestration/plan/${planId}/execute`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async getPlan(planId: string, token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/orchestration/plan/${planId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },
  },

  // Security & Reputation (Sprint 4)
  security: {
    async getReputation(agentId: string, token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/security/reputation/${agentId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async getFraudAlerts(token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/security/fraud-alerts`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async getTrustOverview(agentId: string, token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/security/trust-overview/${agentId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },
  },

  // Analytics (Sprint 5)
  analytics: {
    async getDashboard(days: number, token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/analytics/dashboard`,
        { headers: { Authorization: `Bearer ${token}` }, params: { days } }
      );
      return response.data;
    },

    async getUserAnalytics(userId: string, token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/analytics/user/${userId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async getAgentAnalytics(agentId: string, token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/analytics/agent/${agentId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async getPerformance(token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/analytics/performance`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },

    async getHealth(token: string) {
      const response = await axios.get(
        `${API_URL}/api/v1/analytics/monitoring/health`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },
  },
};

// WebSocket Connection
export function createWebSocket(taskId: string, token: string) {
  // Convert HTTP URL to WebSocket URL
  const wsProtocol = API_URL.startsWith("https") ? "wss" : "ws";
  const wsHost = API_URL.replace("https://", "").replace("http://", "");
  const wsUrl = `${wsProtocol}://${wsHost}/api/v1/ws/tasks/${taskId}?token=${token}`;
  return new WebSocket(wsUrl);
}
