import { create } from "zustand";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  streaming?: boolean;
}

export interface ContextAttachment {
  type: "file" | "selection" | "search" | "symbol" | "image";
  label: string;
  content: string;
}

interface AssistantStore {
  messages: ChatMessage[];
  streaming: boolean;
  abortController: AbortController | null;
  attachments: ContextAttachment[];
  mode: "chat" | "agent" | "completion";
  addMessage: (msg: Omit<ChatMessage, "id">) => string;
  updateMessage: (id: string, content: string, streaming?: boolean) => void;
  clearMessages: () => void;
  setStreaming: (streaming: boolean) => void;
  setAbortController: (controller: AbortController | null) => void;
  addAttachment: (attachment: ContextAttachment) => void;
  removeAttachment: (index: number) => void;
  clearAttachments: () => void;
  setMode: (mode: "chat" | "agent" | "completion") => void;
}

let msgCounter = 0;

export const useAssistantStore = create<AssistantStore>((set) => ({
  messages: [],
  streaming: false,
  abortController: null,
  attachments: [],
  mode: "chat",

  addMessage: (msg) => {
    const id = `msg-${++msgCounter}`;
    set((state) => ({ messages: [...state.messages, { ...msg, id }] }));
    return id;
  },

  updateMessage: (id, content, streaming) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, content, streaming: streaming ?? m.streaming } : m,
      ),
    })),

  clearMessages: () => set({ messages: [] }),

  setStreaming: (streaming) => set({ streaming }),

  setAbortController: (controller) => set({ abortController: controller }),

  addAttachment: (attachment) =>
    set((state) => ({ attachments: [...state.attachments, attachment] })),

  removeAttachment: (index) =>
    set((state) => ({
      attachments: state.attachments.filter((_, i) => i !== index),
    })),

  clearAttachments: () => set({ attachments: [] }),

  setMode: (mode) => set({ mode }),
}));
