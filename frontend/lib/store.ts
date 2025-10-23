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
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
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
