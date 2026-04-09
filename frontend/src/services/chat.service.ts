import { api } from "./api";
import type { ChatMessage, Conversation } from "../types";

export const chatService = {
  async listConversations(): Promise<Conversation[]> {
    const { data } = await api.get<Conversation[]>("/chat/conversations");
    return data;
  },
  async listMessages(conversationId: number): Promise<ChatMessage[]> {
    const { data } = await api.get<ChatMessage[]>(`/chat/conversations/${conversationId}/messages`);
    return data;
  },
  async sendMessage(conversationId: number, content: string): Promise<ChatMessage> {
    const { data } = await api.post<ChatMessage>(`/chat/conversations/${conversationId}/messages`, { content });
    return data;
  },
  async listClassroomMessages(classroomId: number): Promise<ChatMessage[]> {
    const { data } = await api.get<ChatMessage[]>(`/classrooms/${classroomId}/chat/messages`);
    return data;
  },
  async askClassroomQuestion(classroomId: number, question: string): Promise<ChatMessage> {
    const { data } = await api.post<ChatMessage>(`/classrooms/${classroomId}/chat/messages`, { question });
    return data;
  },
};
