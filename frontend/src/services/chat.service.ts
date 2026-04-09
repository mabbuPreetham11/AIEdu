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
  async askClassroomVoiceQuestion(
    classroomId: number,
    audio: Blob,
  ): Promise<{
    transcript_original: string;
    transcript_english: string;
    detected_language_code?: string | null;
    answer_text: string;
    answer_language_code: string;
    answer_audio_base64: string;
    answer_audio_mime_type: string;
    assistant_message: ChatMessage;
  }> {
    const formData = new FormData();
    formData.append("file", audio, "recording.webm");
    const { data } = await api.post<{
      transcript_original: string;
      transcript_english: string;
      detected_language_code?: string | null;
      answer_text: string;
      answer_language_code: string;
      answer_audio_base64: string;
      answer_audio_mime_type: string;
      assistant_message: ChatMessage;
    }>(`/classrooms/${classroomId}/chat/voice`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
  async speechToText(
    audio: Blob,
    options?: {
      filename?: string;
      model?: string;
      mode?: string;
      language_code?: string;
    },
  ): Promise<{ transcript: string; language_code?: string | null }> {
    const formData = new FormData();
    formData.append("file", audio, options?.filename ?? "recording.webm");
    if (options?.model) formData.append("model", options.model);
    if (options?.mode) formData.append("mode", options.mode);
    if (options?.language_code) formData.append("language_code", options.language_code);
    const { data } = await api.post<{ transcript: string; language_code?: string | null }>(
      "/chat/speech-to-text",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return data;
  },
};
