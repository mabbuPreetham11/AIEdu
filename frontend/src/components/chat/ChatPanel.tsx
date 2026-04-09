import { useEffect, useState } from "react";
import axios from "axios";
import { Send } from "lucide-react";

import { useAuth } from "../../hooks/useAuth";
import { chatService } from "../../services/chat.service";
import { classroomService } from "../../services/classroom.service";
import type { ChatMessage, StudentClassroom } from "../../types";

export const ChatPanel = () => {
  const CHAT_COOLDOWN_MS = 3000;
  const { user } = useAuth();
  const [classrooms, setClassrooms] = useState<StudentClassroom[]>([]);
  const [selectedClassroomId, setSelectedClassroomId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [lastSentAt, setLastSentAt] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadClassrooms = async () => {
      if (user?.role !== "student") return;
      setIsLoading(true);
      setError(null);
      try {
        const joined = await classroomService.listStudentClassrooms();
        setClassrooms(joined);
        if (joined.length > 0) {
          setSelectedClassroomId(joined[0].id);
        }
      } catch (err) {
        if (axios.isAxiosError(err)) {
          const detail = err.response?.data?.detail;
          setError(typeof detail === "string" ? detail : "Failed to load classrooms");
        } else {
          setError("Failed to load classrooms");
        }
      } finally {
        setIsLoading(false);
      }
    };
    void loadClassrooms();
  }, [user?.role]);

  useEffect(() => {
    const loadMessages = async () => {
      if (!selectedClassroomId) {
        setMessages([]);
        return;
      }
      setIsLoading(true);
      setError(null);
      try {
        const rows = await chatService.listClassroomMessages(selectedClassroomId);
        setMessages(rows);
      } catch (err) {
        if (axios.isAxiosError(err)) {
          const detail = err.response?.data?.detail;
          setError(typeof detail === "string" ? detail : "Failed to load chat history");
        } else {
          setError("Failed to load chat history");
        }
      } finally {
        setIsLoading(false);
      }
    };
    void loadMessages();
  }, [selectedClassroomId]);

  const askQuestion = async () => {
    if (!selectedClassroomId || !question.trim()) return;
    const now = Date.now();
    if (now - lastSentAt < CHAT_COOLDOWN_MS) {
      setError("Please wait a few seconds before sending another question.");
      return;
    }
    setIsSending(true);
    setError(null);

    const optimisticUser: ChatMessage = {
      id: Date.now(),
      conversation_id: selectedClassroomId,
      role: "user",
      content: question.trim(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      citations: [],
    };
    setMessages((current) => [...current, optimisticUser]);
    setQuestion("");
    setLastSentAt(now);

    try {
      const assistant = await chatService.askClassroomQuestion(selectedClassroomId, optimisticUser.content);
      setMessages((current) => [...current.filter((msg) => msg.id !== optimisticUser.id), optimisticUser, assistant]);
    } catch (err) {
      setMessages((current) => current.filter((msg) => msg.id !== optimisticUser.id));
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === "string" ? detail : "Failed to get AI answer");
      } else {
        setError("Failed to get AI answer");
      }
    } finally {
      setIsSending(false);
    }
  };

  if (user?.role !== "student") {
    return (
      <div className="rounded-3xl border border-white/10 bg-white/5 p-5 text-slate-300">
        AI classroom chat is available for students in joined classrooms.
      </div>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
      <aside className="rounded-3xl border border-white/10 bg-white/5 p-4">
        <h3 className="text-lg font-semibold">Joined Classrooms</h3>
        <div className="mt-4 space-y-2">
          {classrooms.map((classroom) => (
            <button
              key={classroom.id}
              className={`w-full rounded-2xl border px-4 py-3 text-left ${
                selectedClassroomId === classroom.id ? "border-brass/50 bg-brass/10" : "border-white/10 hover:bg-white/10"
              }`}
              onClick={() => setSelectedClassroomId(classroom.id)}
            >
              <p className="font-medium">{classroom.name}</p>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-400">{classroom.invite_code}</p>
            </button>
          ))}
          {classrooms.length === 0 && !isLoading ? <p className="text-sm text-slate-400">No joined classrooms yet.</p> : null}
        </div>
      </aside>

      <section className="rounded-3xl border border-white/10 bg-white/5 p-4">
        {error ? <p className="mb-3 rounded-xl border border-rose-400/40 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{error}</p> : null}
        <div className="mb-4 h-[460px] space-y-3 overflow-y-auto rounded-2xl bg-slate-950/40 p-4">
          {messages.map((message) => (
            <div
              key={`${message.id}-${message.created_at}`}
              className={`max-w-2xl rounded-2xl px-4 py-3 text-sm ${
                message.role === "assistant" ? "bg-lagoon/15 text-paper" : "ml-auto bg-brass/20 text-paper"
              }`}
            >
              <p>{message.content}</p>
              {message.role === "assistant" && message.citations && message.citations.length > 0 ? (
                <div className="mt-2 flex flex-wrap gap-2">
                  {message.citations.map((citation, idx) => (
                    <span key={`${citation.doc_name}-${citation.page_number}-${idx}`} className="rounded-full border border-white/20 px-2 py-0.5 text-xs">
                      {citation.doc_name} p.{citation.page_number}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
          {messages.length === 0 && !isLoading ? (
            <p className="text-sm text-slate-400">Ask a question and AI will answer from uploaded classroom material only.</p>
          ) : null}
        </div>
        <div className="flex gap-3">
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void askQuestion();
              }
            }}
            placeholder="Ask from uploaded classroom PDFs..."
            className="flex-1 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-paper"
          />
          <button
            type="button"
            disabled={isSending || !selectedClassroomId}
            onClick={() => void askQuestion()}
            className="inline-flex items-center gap-2 rounded-2xl bg-brass px-4 py-3 font-medium text-ink disabled:opacity-70"
          >
            <Send className="h-4 w-4" />
            Ask
          </button>
        </div>
      </section>
    </div>
  );
};
