export type UserRole = "teacher" | "student";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
}

export interface Course {
  id: number;
  course_code: string;
  title: string;
  teacher_id: number;
  class_code: string;
  course_info_url?: string | null;
  syllabus?: Record<string, unknown> | null;
  grading_weights?: Record<string, number> | null;
  semester: string;
  year: number;
  is_archived: boolean;
}

export interface TeacherClassroom {
  id: number;
  name: string;
  teacher_id: number;
  invite_code: string;
  qr_code_data_url: string;
  created_at: string;
  updated_at: string;
}

export interface StudentClassroom {
  id: number;
  name: string;
  teacher_id: number;
  invite_code: string;
  joined_at: string;
}

export type MaterialType = "pdf" | "slide" | "video" | "link";

export interface Material {
  id: number;
  classroom_id: number;
  uploader_id: number;
  title: string;
  type: MaterialType;
  file_path?: string | null;
  url?: string | null;
  uploaded_at: string;
  file_url?: string | null;
}

export type QuizQuestionType = "mcq" | "true_false";

export interface QuizQuestionItem {
  id: number;
  quiz_id: number;
  question: string;
  type: QuizQuestionType;
  options?: string[] | null;
  correct_answer: string;
  explanation: string;
  order_number: number;
}

export interface Quiz {
  id: number;
  classroom_id: number;
  title: string;
  deadline: string;
  is_published: boolean;
  randomise_order: boolean;
  questions: QuizQuestionItem[];
  created_at: string;
  updated_at: string;
}

export interface QuizAttempt {
  id: number;
  quiz_id: number;
  student_id: number;
  score: number;
  answers: Record<string, string>;
  submitted_at: string;
}

export interface QuizQuestionPublicItem {
  id: number;
  quiz_id: number;
  question: string;
  type: QuizQuestionType;
  options?: string[] | null;
  order_number: number;
}

export interface QuizWithAttempt {
  id: number;
  classroom_id: number;
  title: string;
  deadline: string;
  is_published: boolean;
  randomise_order: boolean;
  questions: QuizQuestionPublicItem[];
  created_at: string;
  updated_at: string;
  my_attempt?: QuizAttempt | null;
}

export interface QuizAttemptQuestionResult {
  question_id: number;
  question: string;
  selected_answer: string;
  correct_answer: string;
  is_correct: boolean;
  explanation: string;
}

export interface QuizAttemptSubmitResponse {
  attempt_id: number;
  quiz_id: number;
  score: number;
  total_questions: number;
  correct_count: number;
  submitted_at: string;
  results: QuizAttemptQuestionResult[];
}

export interface QuizAnalyticsItem {
  student_id: number;
  student_name: string;
  student_email: string;
  score: number;
  submitted_at: string;
}

export interface QuizAnalyticsResponse {
  quiz_id: number;
  title: string;
  deadline: string;
  attempts: QuizAnalyticsItem[];
}

export interface Assignment {
  id: number;
  course_id: number;
  title: string;
  description: string;
  type: string;
  topics_covered?: string[] | null;
  assigned_date: string;
  due_date: string;
  weightage: number;
  max_score: number;
  ai_generated: boolean;
}

export interface Grade {
  id: number;
  submission_id: number;
  student_id: number;
  course_id: number;
  grade_type: string;
  score: number;
  max_score: number;
  ai_graded: boolean;
  ai_feedback?: Record<string, unknown> | null;
  improvement_suggestions?: string | null;
  focus_areas?: string[] | null;
  graded_by?: number | null;
  is_final: boolean;
}

export interface Conversation {
  id: number;
  user_id: number;
  course_id?: number | null;
  context_type: string;
  title: string;
  pdf_url?: string | null;
}

export interface ChatMessage {
  id: number;
  conversation_id: number;
  role: string;
  content: string;
  created_at: string;
  updated_at: string;
  citations?: Citation[];
}

export interface Citation {
  doc_name: string;
  page_number: number;
}
