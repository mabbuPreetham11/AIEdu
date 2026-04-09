import { useEffect, useMemo, useState } from "react";
import axios from "axios";

import { AssignmentList } from "../components/assignments/AssignmentList";
import { useAssignments } from "../hooks/useAssignments";
import { useAuth } from "../hooks/useAuth";
import { classroomService } from "../services/classroom.service";
import { materialService } from "../services/material.service";
import { quizService, type GeneratedQuizQuestion } from "../services/quiz.service";
import type {
  Material,
  QuizAnalyticsResponse,
  QuizAttemptSubmitResponse,
  QuizWithAttempt,
  StudentClassroom,
  TeacherClassroom,
} from "../types";

export const AssignmentsPage = () => {
  const { assignments, isLoading } = useAssignments();
  const { user } = useAuth();

  const isTeacher = user?.role === "teacher";
  const isStudent = user?.role === "student";

  const [teacherClassrooms, setTeacherClassrooms] = useState<TeacherClassroom[]>([]);
  const [studentClassrooms, setStudentClassrooms] = useState<StudentClassroom[]>([]);
  const [materialsByClassroom, setMaterialsByClassroom] = useState<Record<number, Material[]>>({});
  const [selectedClassroomId, setSelectedClassroomId] = useState<number | "">("");
  const [topic, setTopic] = useState("");
  const [selectedMaterialId, setSelectedMaterialId] = useState<number | "">("");
  const [draftQuestions, setDraftQuestions] = useState<GeneratedQuizQuestion[]>([]);
  const [quizTitle, setQuizTitle] = useState("");
  const [deadline, setDeadline] = useState("");
  const [randomiseOrder, setRandomiseOrder] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);

  const [quizzes, setQuizzes] = useState<QuizWithAttempt[]>([]);
  const [activeQuizId, setActiveQuizId] = useState<number | null>(null);
  const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);
  const [attemptAnswers, setAttemptAnswers] = useState<Record<string, string>>({});
  const [submitResult, setSubmitResult] = useState<QuizAttemptSubmitResponse | null>(null);
  const [isSubmittingAttempt, setIsSubmittingAttempt] = useState(false);

  const [selectedAnalyticsQuizId, setSelectedAnalyticsQuizId] = useState<number | "">("");
  const [analytics, setAnalytics] = useState<QuizAnalyticsResponse | null>(null);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);

  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadClassrooms = async () => {
      setError(null);
      if (isTeacher) {
        try {
          const rows = await classroomService.listTeacherClassrooms();
          setTeacherClassrooms(rows);
          if (rows.length > 0) {
            setSelectedClassroomId(rows[0].id);
          }
        } catch {
          setError("Failed to load classrooms");
        }
        return;
      }
      if (isStudent) {
        try {
          const rows = await classroomService.listStudentClassrooms();
          setStudentClassrooms(rows);
          if (rows.length > 0) {
            setSelectedClassroomId(rows[0].id);
          }
        } catch {
          setError("Failed to load classrooms");
        }
      }
    };
    void loadClassrooms();
  }, [isTeacher, isStudent]);

  useEffect(() => {
    const loadData = async () => {
      if (!selectedClassroomId) return;
      setError(null);
      try {
        const [materials, classroomQuizzes] = await Promise.all([
          materialService.list(selectedClassroomId),
          quizService.listClassroomQuizzes(selectedClassroomId),
        ]);
        setMaterialsByClassroom((current) => ({ ...current, [selectedClassroomId]: materials }));
        setQuizzes(classroomQuizzes);
      } catch {
        setError("Failed to load classroom quiz data");
      }
    };
    void loadData();
  }, [selectedClassroomId]);

  useEffect(() => {
    if (!isStudent || !selectedClassroomId) return;
    const refresh = async () => {
      try {
        const classroomQuizzes = await quizService.listClassroomQuizzes(selectedClassroomId);
        setQuizzes(classroomQuizzes);
      } catch {
        // keep existing data; avoid interrupting user flow with noisy background errors
      }
    };
    const intervalId = window.setInterval(() => {
      void refresh();
    }, 10000);
    const onFocus = () => {
      void refresh();
    };
    window.addEventListener("focus", onFocus);
    return () => {
      window.clearInterval(intervalId);
      window.removeEventListener("focus", onFocus);
    };
  }, [isStudent, selectedClassroomId]);

  const classroomMaterials = useMemo(() => {
    if (!selectedClassroomId) return [];
    return materialsByClassroom[selectedClassroomId] ?? [];
  }, [materialsByClassroom, selectedClassroomId]);

  const activeQuiz = useMemo(
    () => quizzes.find((quiz) => quiz.id === activeQuizId) ?? null,
    [quizzes, activeQuizId],
  );
  const activeQuestion = activeQuiz?.questions[activeQuestionIndex] ?? null;
  const progressPercent = activeQuiz
    ? Math.round(((activeQuestionIndex + 1) / Math.max(activeQuiz.questions.length, 1)) * 100)
    : 0;

  const refreshQuizzes = async (classroomId: number) => {
    const rows = await quizService.listClassroomQuizzes(classroomId);
    setQuizzes(rows);
  };

  const generateQuiz = async () => {
    if (!selectedClassroomId) return;
    if (!topic.trim() && !selectedMaterialId) {
      setError("Provide a topic or select a material");
      return;
    }

    setIsGenerating(true);
    setError(null);
    setMessage(null);
    try {
      const questions = await quizService.generateQuestions(selectedClassroomId, {
        topic: topic.trim() || undefined,
        material_id: selectedMaterialId || undefined,
      });
      setDraftQuestions(questions);
      if (!quizTitle.trim()) {
        setQuizTitle(`Quiz - ${new Date().toLocaleDateString()}`);
      }
      setMessage("Quiz questions generated. Review and edit before publishing.");
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === "string" ? detail : "Failed to generate quiz");
      } else {
        setError("Failed to generate quiz");
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const updateQuestion = (index: number, patch: Partial<GeneratedQuizQuestion>) => {
    setDraftQuestions((current) => current.map((item, idx) => (idx === index ? { ...item, ...patch } : item)));
  };

  const removeQuestion = (index: number) => {
    setDraftQuestions((current) => current.filter((_, idx) => idx !== index));
  };

  const addQuestion = () => {
    setDraftQuestions((current) => [
      ...current,
      {
        question: "",
        type: "mcq",
        options: ["", "", "", ""],
        correct_answer: "",
        explanation: "",
      },
    ]);
  };

  const publishQuiz = async () => {
    if (!selectedClassroomId) return;
    if (!quizTitle.trim()) {
      setError("Quiz title is required");
      return;
    }
    if (!deadline) {
      setError("Quiz deadline is required");
      return;
    }
    if (draftQuestions.length === 0) {
      setError("Add at least one quiz question");
      return;
    }

    setIsPublishing(true);
    setError(null);
    setMessage(null);
    try {
      await quizService.publishQuiz(selectedClassroomId, {
        title: quizTitle.trim(),
        deadline: new Date(deadline).toISOString(),
        is_published: true,
        randomise_order: randomiseOrder,
        questions: draftQuestions.map((item) => ({
          ...item,
          options: item.type === "true_false" ? ["True", "False"] : item.options,
        })),
      });
      setMessage("Quiz published successfully");
      setDraftQuestions([]);
      setTopic("");
      setSelectedMaterialId("");
      setDeadline("");
      setRandomiseOrder(false);
      await refreshQuizzes(selectedClassroomId);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === "string" ? detail : "Failed to publish quiz");
      } else {
        setError("Failed to publish quiz");
      }
    } finally {
      setIsPublishing(false);
    }
  };

  const startQuiz = (quizId: number) => {
    const quiz = quizzes.find((item) => item.id === quizId);
    if (!quiz || quiz.my_attempt) return;
    setSubmitResult(null);
    setActiveQuizId(quizId);
    setActiveQuestionIndex(0);
    setAttemptAnswers({});
    setError(null);
    setMessage(null);
  };

  const submitQuiz = async () => {
    if (!selectedClassroomId || !activeQuiz) return;
    if (activeQuiz.my_attempt) {
      setError("You have already submitted this quiz");
      return;
    }
    setIsSubmittingAttempt(true);
    setError(null);
    try {
      const result = await quizService.submitAttempt(selectedClassroomId, activeQuiz.id, { answers: attemptAnswers });
      setSubmitResult(result);
      setMessage("Quiz submitted and graded instantly.");
      await refreshQuizzes(selectedClassroomId);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === "string" ? detail : "Failed to submit quiz");
      } else {
        setError("Failed to submit quiz");
      }
    } finally {
      setIsSubmittingAttempt(false);
    }
  };

  const loadAnalytics = async () => {
    if (!selectedClassroomId || !selectedAnalyticsQuizId) return;
    setIsLoadingAnalytics(true);
    setError(null);
    try {
      const data = await quizService.getQuizAnalytics(selectedClassroomId, selectedAnalyticsQuizId);
      setAnalytics(data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === "string" ? detail : "Failed to load analytics");
      } else {
        setError("Failed to load analytics");
      }
    } finally {
      setIsLoadingAnalytics(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-lagoon">Assignments</p>
        <h2 className="mt-2 text-4xl font-semibold">Quiz workflows</h2>
      </div>

      {error ? <p className="rounded-xl border border-rose-400/40 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{error}</p> : null}
      {message ? <p className="rounded-xl border border-emerald-400/40 bg-emerald-400/10 px-3 py-2 text-sm text-emerald-200">{message}</p> : null}

      {isTeacher ? (
        <section className="space-y-5 rounded-3xl border border-white/10 bg-white/5 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-2xl font-semibold">Create Quiz</h3>
            <button
              type="button"
              onClick={generateQuiz}
              disabled={isGenerating}
              className="rounded-2xl bg-brass px-4 py-2 font-medium text-ink disabled:opacity-70"
            >
              {isGenerating ? "Generating..." : "Generate Questions"}
            </button>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <select
              value={selectedClassroomId}
              onChange={(event) => setSelectedClassroomId(event.target.value ? Number(event.target.value) : "")}
              className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
            >
              <option value="">Select classroom</option>
              {teacherClassrooms.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            <input
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="Topic (optional if material selected)"
              className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
            />
          </div>

          <select
            value={selectedMaterialId}
            onChange={(event) => setSelectedMaterialId(event.target.value ? Number(event.target.value) : "")}
            className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
          >
            <option value="">Select uploaded material (optional)</option>
            {classroomMaterials.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title} ({item.type})
              </option>
            ))}
          </select>

          {draftQuestions.length > 0 ? (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2">
                <input
                  value={quizTitle}
                  onChange={(event) => setQuizTitle(event.target.value)}
                  placeholder="Quiz title"
                  className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
                />
                <input
                  type="datetime-local"
                  value={deadline}
                  onChange={(event) => setDeadline(event.target.value)}
                  className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
                />
              </div>

              <label className="inline-flex items-center gap-2 text-sm text-slate-200">
                <input
                  type="checkbox"
                  checked={randomiseOrder}
                  onChange={(event) => setRandomiseOrder(event.target.checked)}
                />
                Randomise order when published
              </label>

              <div className="space-y-3">
                {draftQuestions.map((item, index) => (
                  <article key={`quiz-${index}`} className="space-y-3 rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Question {index + 1}</p>
                      <button type="button" onClick={() => removeQuestion(index)} className="text-sm text-rose-300">
                        Remove
                      </button>
                    </div>
                    <input
                      value={item.question}
                      onChange={(event) => updateQuestion(index, { question: event.target.value })}
                      placeholder="Question text"
                      className="w-full rounded-xl border border-white/10 bg-slate-950/70 px-4 py-2 text-paper outline-none"
                    />
                    <select
                      value={item.type}
                      onChange={(event) =>
                        updateQuestion(index, {
                          type: event.target.value as "mcq" | "true_false",
                          options: event.target.value === "true_false" ? ["True", "False"] : ["", "", "", ""],
                        })
                      }
                      className="rounded-xl border border-white/10 bg-slate-950/70 px-4 py-2 text-paper outline-none"
                    >
                      <option value="mcq">MCQ</option>
                      <option value="true_false">True/False</option>
                    </select>
                    {item.type === "mcq" ? (
                      <div className="grid gap-2 md:grid-cols-2">
                        {(item.options ?? ["", "", "", ""]).map((option, optIndex) => (
                          <input
                            key={`opt-${optIndex}`}
                            value={option}
                            onChange={(event) => {
                              const next = [...(item.options ?? ["", "", "", ""])];
                              next[optIndex] = event.target.value;
                              updateQuestion(index, { options: next });
                            }}
                            placeholder={`Option ${optIndex + 1}`}
                            className="rounded-xl border border-white/10 bg-slate-950/70 px-4 py-2 text-paper outline-none"
                          />
                        ))}
                      </div>
                    ) : null}
                    <input
                      value={item.correct_answer}
                      onChange={(event) => updateQuestion(index, { correct_answer: event.target.value })}
                      placeholder="Correct answer"
                      className="w-full rounded-xl border border-white/10 bg-slate-950/70 px-4 py-2 text-paper outline-none"
                    />
                    <textarea
                      value={item.explanation}
                      onChange={(event) => updateQuestion(index, { explanation: event.target.value })}
                      placeholder="Explanation"
                      className="w-full rounded-xl border border-white/10 bg-slate-950/70 px-4 py-2 text-paper outline-none"
                    />
                  </article>
                ))}
              </div>

              <div className="flex flex-wrap gap-3">
                <button type="button" onClick={addQuestion} className="rounded-2xl border border-white/20 px-4 py-2 text-sm text-slate-200">
                  Add Question
                </button>
                <button
                  type="button"
                  onClick={publishQuiz}
                  disabled={isPublishing}
                  className="rounded-2xl bg-brass px-4 py-2 font-medium text-ink disabled:opacity-70"
                >
                  {isPublishing ? "Publishing..." : "Publish Quiz"}
                </button>
              </div>
            </div>
          ) : null}

          <div className="space-y-3 rounded-2xl border border-white/10 bg-slate-950/40 p-4">
            <h4 className="text-lg font-semibold">Quiz Analytics</h4>
            <div className="flex flex-wrap gap-3">
              <select
                value={selectedAnalyticsQuizId}
                onChange={(event) => setSelectedAnalyticsQuizId(event.target.value ? Number(event.target.value) : "")}
                className="min-w-[280px] rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
              >
                <option value="">Select published quiz</option>
                {quizzes.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => void loadAnalytics()}
                disabled={isLoadingAnalytics || !selectedAnalyticsQuizId}
                className="rounded-2xl border border-white/20 px-4 py-2 text-sm text-slate-200 disabled:opacity-70"
              >
                {isLoadingAnalytics ? "Loading..." : "View Analytics"}
              </button>
            </div>
            {analytics ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="text-slate-300">
                    <tr>
                      <th className="px-3 py-2">Student</th>
                      <th className="px-3 py-2">Email</th>
                      <th className="px-3 py-2">Score</th>
                      <th className="px-3 py-2">Submitted At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.attempts.map((item) => (
                      <tr key={`${item.student_id}-${item.submitted_at}`} className="border-t border-white/10">
                        <td className="px-3 py-2">{item.student_name}</td>
                        <td className="px-3 py-2">{item.student_email}</td>
                        <td className="px-3 py-2">{item.score}%</td>
                        <td className="px-3 py-2">{new Date(item.submitted_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </div>
        </section>
      ) : null}

      {isStudent ? (
        <section className="space-y-4 rounded-3xl border border-white/10 bg-white/5 p-5">
          <h3 className="text-2xl font-semibold">Take Quiz</h3>
          <select
            value={selectedClassroomId}
            onChange={(event) => {
              setSelectedClassroomId(event.target.value ? Number(event.target.value) : "");
              setActiveQuizId(null);
              setSubmitResult(null);
            }}
            className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
          >
            <option value="">Select classroom</option>
            {studentClassrooms.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
          {selectedClassroomId ? (
            <p className="text-xs uppercase tracking-[0.18em] text-slate-400">
              Viewing classroom:{" "}
              {studentClassrooms.find((item) => item.id === selectedClassroomId)?.name ?? "Selected classroom"}
            </p>
          ) : null}

          {!activeQuiz ? (
            <div className="space-y-3">
              {quizzes.map((quiz) => (
                <article key={quiz.id} className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-lg font-semibold">{quiz.title}</p>
                      <p className="text-sm text-slate-300">Deadline: {new Date(quiz.deadline).toLocaleString()}</p>
                    </div>
                    <button
                      type="button"
                      disabled={Boolean(quiz.my_attempt)}
                      onClick={() => startQuiz(quiz.id)}
                      className="rounded-2xl bg-brass px-4 py-2 font-medium text-ink disabled:cursor-not-allowed disabled:opacity-70"
                    >
                      {quiz.my_attempt ? "Already Submitted" : "Start Quiz"}
                    </button>
                  </div>
                  {quiz.my_attempt ? (
                    <p className="mt-2 text-sm text-emerald-300">
                      Submitted: {new Date(quiz.my_attempt.submitted_at).toLocaleString()} | Score: {quiz.my_attempt.score}%
                    </p>
                  ) : null}
                </article>
              ))}
              {quizzes.length === 0 ? <p className="text-sm text-slate-300">No published quizzes yet for this classroom.</p> : null}
            </div>
          ) : (
            <div className="space-y-4 rounded-2xl border border-white/10 bg-slate-950/40 p-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm text-slate-300">
                  <span>
                    Question {activeQuestionIndex + 1} / {activeQuiz.questions.length}
                  </span>
                  <span>{progressPercent}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-brass" style={{ width: `${progressPercent}%` }} />
                </div>
              </div>

              {activeQuestion ? (
                <article className="space-y-3">
                  <p className="text-lg font-medium">{activeQuestion.question}</p>
                  <div className="space-y-2">
                    {(activeQuestion.type === "true_false" ? ["True", "False"] : activeQuestion.options ?? []).map((option, index) => (
                      <label key={`${option}-${index}`} className="flex cursor-pointer items-center gap-2 rounded-xl border border-white/10 px-3 py-2">
                        <input
                          type="radio"
                          name={`q-${activeQuestion.id}`}
                          checked={attemptAnswers[String(activeQuestion.id)] === option}
                          onChange={() =>
                            setAttemptAnswers((current) => ({
                              ...current,
                              [String(activeQuestion.id)]: option,
                            }))
                          }
                        />
                        <span>{option}</span>
                      </label>
                    ))}
                  </div>
                </article>
              ) : null}

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={activeQuestionIndex === 0}
                  onClick={() => setActiveQuestionIndex((current) => Math.max(current - 1, 0))}
                  className="rounded-2xl border border-white/20 px-4 py-2 text-sm text-slate-200 disabled:opacity-70"
                >
                  Previous
                </button>
                {activeQuiz && activeQuestionIndex < activeQuiz.questions.length - 1 ? (
                  <button
                    type="button"
                    onClick={() => setActiveQuestionIndex((current) => Math.min(current + 1, activeQuiz.questions.length - 1))}
                    className="rounded-2xl border border-white/20 px-4 py-2 text-sm text-slate-200"
                  >
                    Next
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled={isSubmittingAttempt}
                    onClick={() => void submitQuiz()}
                    className="rounded-2xl bg-brass px-4 py-2 font-medium text-ink disabled:opacity-70"
                  >
                    {isSubmittingAttempt ? "Submitting..." : "Submit Quiz"}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => {
                    setActiveQuizId(null);
                    setSubmitResult(null);
                    setAttemptAnswers({});
                    setActiveQuestionIndex(0);
                  }}
                  className="rounded-2xl border border-white/20 px-4 py-2 text-sm text-slate-200"
                >
                  Exit
                </button>
              </div>
            </div>
          )}

          {submitResult ? (
            <div className="space-y-3 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4">
              <h4 className="text-xl font-semibold">Result</h4>
              <p className="text-sm text-slate-200">
                Score: <span className="font-semibold">{submitResult.score}%</span> | Correct: {submitResult.correct_count} /{" "}
                {submitResult.total_questions}
              </p>
              <div className="space-y-2">
                {submitResult.results.map((item) => (
                  <article key={item.question_id} className="rounded-xl border border-white/10 bg-slate-950/40 p-3">
                    <p className="text-sm font-medium">{item.question}</p>
                    <p className={`text-sm ${item.is_correct ? "text-emerald-300" : "text-rose-300"}`}>
                      {item.is_correct ? "Correct" : "Incorrect"}
                    </p>
                    <p className="text-xs text-slate-300">Your answer: {item.selected_answer || "Not answered"}</p>
                    <p className="text-xs text-slate-300">Correct answer: {item.correct_answer}</p>
                    {!item.is_correct ? <p className="mt-1 text-xs text-slate-200">Explanation: {item.explanation}</p> : null}
                  </article>
                ))}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {isLoading ? <p className="text-slate-300">Loading assignments...</p> : <AssignmentList assignments={assignments} />}
    </div>
  );
};
