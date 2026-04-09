import { create } from "zustand";

import { chatService } from "../services/chat.service";
import type { ChatMessage, Conversation } from "../types";

interface ChatState {
  conversations: Conversation[];
  messages: ChatMessage[];
  isLoading: boolean;
  loadConversations: () => Promise<void>;
  loadMessages: (conversationId: number) => Promise<void>;
  sendMessage: (conversationId: number, content: string) => Promise<void>;
}

export const useChat = create<ChatState>((set) => ({
  conversations: [],
  messages: [],
  isLoading: false,
  async loadConversations() {
    set({ isLoading: true });
    const conversations = await chatService.listConversations();
    set({ conversations, isLoading: false });
  },
  async loadMessages(conversationId) {
    set({ isLoading: true });
    const messages = await chatService.listMessages(conversationId);
    set({ messages, isLoading: false });
  },
  async sendMessage(conversationId, content) {
    const message = await chatService.sendMessage(conversationId, content);
    set((state) => ({ messages: [...state.messages, message] }));
  },
}));
