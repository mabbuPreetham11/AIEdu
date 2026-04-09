import { useEffect, useMemo, useState } from "react";
import axios from "axios";

import { AssignmentList } from "../components/assignments/AssignmentList";
import { useAssignments } from "../hooks/useAssignments";
import { useAuth } from "../hooks/useAuth";
import { classroomService } from "../services/classroom.service";
import { materialService } from "../services/material.service";
import { quizService, type GeneratedQuizQuestion } from "../services/quiz.service";
import type { Material, TeacherClassroom } from "../types";

export const AssignmentsPage = () => {
  const { assignments, isLoading } = useAssignments();
  const { user } = useAuth();

  const [classrooms, setClassrooms] = useState<TeacherClassroom[]>([]);
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
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTeacherClassrooms = async () => {
      if (user?.role !== "teacher") return;
      try {
        const rows = await classroomService.listTeacherClassrooms();
        setClassrooms(rows);
        if (rows.length > 0) {
          setSelectedClassroomId(rows[0].id);
        }
      } catch {
        setError("Failed to load classrooms");
      }
    };
    void loadTeacherClassrooms();
  }, [user?.role]);

  useEffect(() => {
    const loadMaterials = async () => {
      if (!selectedClassroomId) return;
      try {
        const rows = await materialService.list(selectedClassroomId);
        setMaterialsByClassroom((current) => ({ ...current, [selectedClassroomId]: rows }));
      } catch {
        setError("Failed to load classroom materials");
      }
    };
    void loadMaterials();
  }, [selectedClassroomId]);

  const classroomMaterials = useMemo(() => {
    if (!selectedClassroomId) return [];
    return materialsByClassroom[selectedClassroomId] ?? [];
  }, [materialsByClassroom, selectedClassroomId]);

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

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-lagoon">Assignments</p>
        <h2 className="mt-2 text-4xl font-semibold">AI quiz creation and assignment workflows</h2>
      </div>

      {user?.role === "teacher" ? (
        <section className="space-y-4 rounded-3xl border border-white/10 bg-white/5 p-5">
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

          {error ? <p className="rounded-xl border border-rose-400/40 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{error}</p> : null}
          {message ? <p className="rounded-xl border border-emerald-400/40 bg-emerald-400/10 px-3 py-2 text-sm text-emerald-200">{message}</p> : null}

          <div className="grid gap-3 md:grid-cols-2">
            <select
              value={selectedClassroomId}
              onChange={(event) => setSelectedClassroomId(event.target.value ? Number(event.target.value) : "")}
              className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
            >
              <option value="">Select classroom</option>
              {classrooms.map((item) => (
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
        </section>
      ) : null}

      {isLoading ? <p className="text-slate-300">Loading assignments...</p> : <AssignmentList assignments={assignments} />}
    </div>
  );
};
