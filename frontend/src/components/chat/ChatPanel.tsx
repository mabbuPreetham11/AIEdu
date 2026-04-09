import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { Mic, Pause, Play, Send, Square, Volume2 } from "lucide-react";

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
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [lastSentAt, setLastSentAt] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [playingAudioKey, setPlayingAudioKey] = useState<string | null>(null);
  const [audioProgressByKey, setAudioProgressByKey] = useState<Record<string, number>>({});
  const audioRefs = useRef<Record<string, HTMLAudioElement | null>>({});

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

  const startRecording = async () => {
    if (isRecording) return;
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const sessionChunks: Blob[] = [];
      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          sessionChunks.push(event.data);
        }
      };
      recorder.onstop = async () => {
        try {
          const blob = new Blob(sessionChunks, { type: recorder.mimeType || "audio/webm" });
          if (blob.size === 0) {
            setError("Recorded audio is empty. Please try again.");
            return;
          }
          if (!selectedClassroomId) {
            setError("Select a classroom before sending voice input.");
            return;
          }
          setIsTranscribing(true);
          const response = await chatService.askClassroomVoiceQuestion(selectedClassroomId, blob);

          const voiceUserMessage: ChatMessage = {
            id: Date.now(),
            conversation_id: selectedClassroomId,
            role: "user",
            content: response.transcript_original,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            citations: [],
          };
          const assistantFromVoice: ChatMessage = {
            ...response.assistant_message,
            content: response.answer_text,
            audio_data_url: `data:${response.answer_audio_mime_type};base64,${response.answer_audio_base64}`,
          };
          setMessages((current) => [...current, voiceUserMessage, assistantFromVoice]);
        } catch (err) {
          if (axios.isAxiosError(err)) {
            const detail = err.response?.data?.detail;
            setError(typeof detail === "string" ? detail : "Voice transcription failed");
          } else {
            setError("Voice transcription failed");
          }
        } finally {
          setIsTranscribing(false);
          stream.getTracks().forEach((track) => track.stop());
        }
      };
      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch {
      setError("Microphone access was denied or unavailable.");
    }
  };

  const stopRecording = () => {
    if (!mediaRecorder || mediaRecorder.state !== "recording") return;
    mediaRecorder.stop();
    setIsRecording(false);
  };

  const toggleAudioPlayback = (key: string) => {
    const current = audioRefs.current[key];
    if (!current) return;
    if (playingAudioKey === key) {
      current.pause();
      setPlayingAudioKey(null);
      return;
    }
    Object.entries(audioRefs.current).forEach(([audioKey, element]) => {
      if (audioKey !== key && element) {
        element.pause();
      }
    });
    void current.play();
    setPlayingAudioKey(key);
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
              {message.role === "assistant" && message.audio_data_url ? (() => {
                const audioKey = `${message.id}-${message.created_at}`;
                const progress = audioProgressByKey[audioKey] ?? 0;
                const isPlaying = playingAudioKey === audioKey;
                return (
                  <div className="mt-3 rounded-xl border border-white/20 bg-slate-900/40 p-3">
                    <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-300">
                      <Volume2 className="h-3.5 w-3.5" />
                      Voice Response
                    </div>
                    <audio
                      ref={(element) => {
                        audioRefs.current[audioKey] = element;
                      }}
                      className="hidden"
                      onTimeUpdate={(event) => {
                        const audio = event.currentTarget;
                        const duration = audio.duration || 0;
                        const progressValue = duration > 0 ? (audio.currentTime / duration) * 100 : 0;
                        setAudioProgressByKey((current) => ({ ...current, [audioKey]: progressValue }));
                      }}
                      onEnded={() => {
                        setPlayingAudioKey((current) => (current === audioKey ? null : current));
                      }}
                    >
                      <source src={message.audio_data_url} />
                    </audio>
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        onClick={() => toggleAudioPlayback(audioKey)}
                        className="inline-flex items-center gap-2 rounded-lg border border-white/25 px-3 py-1.5 text-xs font-medium text-slate-100 hover:bg-white/10"
                      >
                        {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                        {isPlaying ? "Pause" : "Play"}
                      </button>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-700/60">
                        <div className="h-full rounded-full bg-lagoon" style={{ width: `${progress}%` }} />
                      </div>
                    </div>
                  </div>
                );
              })() : null}
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
            disabled={isTranscribing}
            onClick={() => {
              if (isRecording) {
                stopRecording();
              } else {
                void startRecording();
              }
            }}
            className="inline-flex items-center gap-2 rounded-2xl border border-white/20 px-4 py-3 font-medium text-paper disabled:opacity-70"
          >
            {isRecording ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            {isRecording ? "Stop" : isTranscribing ? "Transcribing..." : "Voice"}
          </button>
          <button
            type="button"
            disabled={isSending || !selectedClassroomId || isRecording || isTranscribing}
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
