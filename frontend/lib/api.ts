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
};

// WebSocket Connection
export function createWebSocket(taskId: string, token: string) {
  // Convert HTTP URL to WebSocket URL
  const wsProtocol = API_URL.startsWith("https") ? "wss" : "ws";
  const wsHost = API_URL.replace("https://", "").replace("http://", "");
  const wsUrl = `${wsProtocol}://${wsHost}/api/v1/ws/tasks/${taskId}?token=${token}`;
  return new WebSocket(wsUrl);
}
