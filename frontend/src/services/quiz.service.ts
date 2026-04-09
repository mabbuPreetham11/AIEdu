import { api } from "./api";
import type { Quiz, QuizQuestionType } from "../types";

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
    const { data } = await api.get<Quiz[]>(`/classrooms/${classroomId}/quizzes`);
    return data;
  },
};
