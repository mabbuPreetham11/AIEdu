import { api } from "./api";
import type { Quiz, QuizAnalyticsResponse, QuizAttemptSubmitResponse, QuizQuestionType, QuizWithAttempt } from "../types";

export interface GeneratedQuizQuestion {
  question: string;
  type: QuizQuestionType;
  options: string[];
  correct_answer: string;
  explanation: string;
}

export const quizService = {
  async generateQuestions(classroomId: number, payload: { topic?: string; material_id?: number }) {
    const { data } = await api.post<{ questions: GeneratedQuizQuestion[] }>(`/classrooms/${classroomId}/quizzes/generate`, payload);
    return data.questions;
  },
  async publishQuiz(
    classroomId: number,
    payload: {
      title: string;
      deadline: string;
      is_published: boolean;
      randomise_order: boolean;
      questions: GeneratedQuizQuestion[];
    },
  ) {
    const { data } = await api.post<Quiz>(`/classrooms/${classroomId}/quizzes`, payload);
    return data;
  },
  async listClassroomQuizzes(classroomId: number) {
    const { data } = await api.get<QuizWithAttempt[]>(`/classrooms/${classroomId}/quizzes`);
    return data;
  },
  async submitAttempt(classroomId: number, quizId: number, payload: { answers: Record<string, string> }) {
    const { data } = await api.post<QuizAttemptSubmitResponse>(`/classrooms/${classroomId}/quizzes/${quizId}/attempt`, payload);
    return data;
  },
  async getQuizAnalytics(classroomId: number, quizId: number) {
    const { data } = await api.get<QuizAnalyticsResponse>(`/classrooms/${classroomId}/quizzes/${quizId}/analytics`);
    return data;
  },
};
