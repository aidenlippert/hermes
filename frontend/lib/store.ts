import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: string;
  subscription_tier: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken, isAuthenticated: true }),
      setAuth: (token, user) => set({ accessToken: token, user, isAuthenticated: true }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false }),
    }),
    {
      name: "hermes-auth",
      storage: createJSONStorage(() => localStorage),
    }
  )
);

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  taskId?: string;
}

interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  currentEvents: any[];
  addMessage: (message: Message) => void;
  addEvent: (event: any) => void;
  setStreaming: (streaming: boolean) => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>()((set) => ({
  messages: [],
  isStreaming: false,
  currentEvents: [],
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  addEvent: (event) =>
    set((state) => ({
      currentEvents: [...state.currentEvents, event],
    })),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  clearChat: () => set({ messages: [], currentEvents: [] }),
}));
