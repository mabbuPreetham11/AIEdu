import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import { Bot, BookOpen, ClipboardCheck, Copy, Download, ExternalLink, FileText, Film, Link2, Presentation, Sparkles, Upload } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { MetricCard } from "../components/common/MetricCard";
import { NotesEditor } from "../components/notes/NotesEditor";
import { useAuth } from "../hooks/useAuth";
import { classroomService } from "../services/classroom.service";
import { materialService, toYouTubeEmbedUrl } from "../services/material.service";
import type { Material, MaterialType, StudentClassroom, TeacherClassroom } from "../types";

type MaterialsByClassroom = Record<number, Material[]>;

export const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const inviteJoinHandledRef = useRef<string | null>(null);
  const [classroomName, setClassroomName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [teacherClassrooms, setTeacherClassrooms] = useState<TeacherClassroom[]>([]);
  const [studentClassrooms, setStudentClassrooms] = useState<StudentClassroom[]>([]);
  const [materialsByClassroom, setMaterialsByClassroom] = useState<MaterialsByClassroom>({});
  const [isLoadingClassrooms, setIsLoadingClassrooms] = useState(true);
  const [isCreatingClassroom, setIsCreatingClassroom] = useState(false);
  const [isJoiningClassroom, setIsJoiningClassroom] = useState(false);
  const [isUploadingMaterial, setIsUploadingMaterial] = useState(false);
  const [activePreviewKey, setActivePreviewKey] = useState<string | null>(null);
  const [classroomError, setClassroomError] = useState<string | null>(null);
  const [classroomMessage, setClassroomMessage] = useState<string | null>(null);
  const [hiddenQrByClassroom, setHiddenQrByClassroom] = useState<Record<number, boolean>>({});

  const [materialClassroomId, setMaterialClassroomId] = useState<number | "">("");
  const [materialTitle, setMaterialTitle] = useState("");
  const [materialType, setMaterialType] = useState<MaterialType>("pdf");
  const [materialUrl, setMaterialUrl] = useState("");
  const [materialFile, setMaterialFile] = useState<File | null>(null);

  const classroomOptions = useMemo(
    () => (user?.role === "teacher" ? teacherClassrooms.map((item) => ({ id: item.id, name: item.name })) : []),
    [teacherClassrooms, user?.role],
  );

  const loadMaterialsForClassroom = async (classroomId: number) => {
    const data = await materialService.list(classroomId);
    setMaterialsByClassroom((current) => ({ ...current, [classroomId]: data }));
  };

  useEffect(() => {
    const loadClassrooms = async () => {
      if (!user) {
        setIsLoadingClassrooms(false);
        return;
      }

      setIsLoadingClassrooms(true);
      setClassroomError(null);

      try {
        if (user.role === "teacher") {
          const data = await classroomService.listTeacherClassrooms();
          setTeacherClassrooms(data);
          if (!materialClassroomId && data.length > 0) setMaterialClassroomId(data[0].id);
          await Promise.all(data.map((classroom) => loadMaterialsForClassroom(classroom.id)));
        } else if (user.role === "student") {
          const data = await classroomService.listStudentClassrooms();
          setStudentClassrooms(data);
          await Promise.all(data.map((classroom) => loadMaterialsForClassroom(classroom.id)));
        }
      } catch (err) {
        if (axios.isAxiosError(err)) {
          const detail = err.response?.data?.detail;
          setClassroomError(typeof detail === "string" ? detail : "Failed to load classroom data");
        } else {
          setClassroomError("Failed to load classroom data");
        }
      } finally {
        setIsLoadingClassrooms(false);
      }
    };

    void loadClassrooms();
  }, [user]);

  useEffect(() => {
    if (user?.role !== "student") return;
    const invite = searchParams.get("invite")?.trim().toUpperCase();
    if (!invite) return;
    if (inviteJoinHandledRef.current === invite) return;
    inviteJoinHandledRef.current = invite;

    const joinFromInvite = async () => {
      setIsJoiningClassroom(true);
      setClassroomError(null);
      setClassroomMessage(null);
      try {
        const classroom = await classroomService.joinClassroom(invite);
        setStudentClassrooms((current) => (current.some((item) => item.id === classroom.id) ? current : [classroom, ...current]));
        await loadMaterialsForClassroom(classroom.id);
        setClassroomMessage(`Joined classroom ${classroom.name}`);
      } catch (err) {
        if (axios.isAxiosError(err)) {
          const detail = err.response?.data?.detail;
          if (typeof detail === "string" && detail.toLowerCase().includes("already joined")) {
            setClassroomMessage("You are already a member of this classroom.");
          } else {
            setClassroomError(typeof detail === "string" ? detail : "Failed to join classroom");
          }
        } else {
          setClassroomError("Failed to join classroom");
        }
      } finally {
        setIsJoiningClassroom(false);
        navigate("/", { replace: true });
      }
    };

    void joinFromInvite();
  }, [navigate, searchParams, user?.role]);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem("teacher_hidden_qr");
      if (!raw) return;
      const parsed = JSON.parse(raw) as Record<string, boolean>;
      const normalized: Record<number, boolean> = {};
      for (const [key, value] of Object.entries(parsed)) {
        const id = Number(key);
        if (!Number.isNaN(id) && typeof value === "boolean") {
          normalized[id] = value;
        }
      }
      setHiddenQrByClassroom(normalized);
    } catch {
      // ignore localStorage parse errors
    }
  }, []);

  useEffect(() => {
    if (user?.role !== "teacher") return;
    try {
      const serializable: Record<string, boolean> = {};
      for (const [key, value] of Object.entries(hiddenQrByClassroom)) {
        serializable[String(key)] = value;
      }
      window.localStorage.setItem("teacher_hidden_qr", JSON.stringify(serializable));
    } catch {
      // ignore localStorage write errors
    }
  }, [hiddenQrByClassroom, user?.role]);

  const onCreateClassroom = async (event: FormEvent) => {
    event.preventDefault();
    if (!classroomName.trim()) return;

    setIsCreatingClassroom(true);
    setClassroomError(null);
    setClassroomMessage(null);
    try {
      const classroom = await classroomService.createClassroom(classroomName.trim());
      setTeacherClassrooms((current) => [classroom, ...current]);
      setMaterialsByClassroom((current) => ({ ...current, [classroom.id]: [] }));
      setMaterialClassroomId(classroom.id);
      setClassroomName("");
      setClassroomMessage(`Classroom created. Invite code: ${classroom.invite_code}`);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setClassroomError(typeof detail === "string" ? detail : "Failed to create classroom");
      } else {
        setClassroomError("Failed to create classroom");
      }
    } finally {
      setIsCreatingClassroom(false);
    }
  };

  const onJoinClassroom = async (event: FormEvent) => {
    event.preventDefault();
    if (!inviteCode.trim()) return;

    setIsJoiningClassroom(true);
    setClassroomError(null);
    setClassroomMessage(null);
    try {
      const classroom = await classroomService.joinClassroom(inviteCode.trim().toUpperCase());
      setStudentClassrooms((current) => [classroom, ...current]);
      await loadMaterialsForClassroom(classroom.id);
      setInviteCode("");
      setClassroomMessage(`Joined classroom ${classroom.name}`);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setClassroomError(typeof detail === "string" ? detail : "Failed to join classroom");
      } else {
        setClassroomError("Failed to join classroom");
      }
    } finally {
      setIsJoiningClassroom(false);
    }
  };

  const onUploadMaterial = async (event: FormEvent) => {
    event.preventDefault();
    if (!materialClassroomId || !materialTitle.trim()) return;

    setIsUploadingMaterial(true);
    setClassroomError(null);
    setClassroomMessage(null);
    try {
      const created = await materialService.upload({
        classroomId: materialClassroomId,
        title: materialTitle.trim(),
        type: materialType,
        file: materialType === "pdf" || materialType === "slide" ? materialFile : null,
        url: materialType === "video" || materialType === "link" ? materialUrl.trim() : undefined,
      });
      setMaterialsByClassroom((current) => ({
        ...current,
        [materialClassroomId]: [created, ...(current[materialClassroomId] ?? [])],
      }));
      setMaterialTitle("");
      setMaterialUrl("");
      setMaterialFile(null);
      setClassroomMessage("Material uploaded and indexed for AI chat");
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setClassroomError(typeof detail === "string" ? detail : "Failed to upload material");
      } else {
        setClassroomError("Failed to upload material");
      }
    } finally {
      setIsUploadingMaterial(false);
    }
  };

  const copyCode = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setClassroomMessage(`Invite code ${code} copied`);
      setClassroomError(null);
    } catch {
      setClassroomError("Unable to copy invite code");
    }
  };

  const toggleQrVisibility = (classroomId: number) => {
    setHiddenQrByClassroom((current) => ({
      ...current,
      [classroomId]: !(current[classroomId] ?? true),
    }));
  };

  const onDownloadMaterial = async (classroomId: number, material: Material) => {
    try {
      await materialService.download(classroomId, material.id, material.title);
    } catch {
      setClassroomError("Failed to download material");
    }
  };

  const renderMaterialList = (classroomId: number) => {
    const materials = materialsByClassroom[classroomId] ?? [];
    if (materials.length === 0) return <p className="text-sm text-slate-400">No materials uploaded yet.</p>;

    return (
      <div className="space-y-3">
        {materials.map((material) => {
          const previewKey = `${classroomId}-${material.id}`;
          const isPreviewOpen = activePreviewKey === previewKey;
          const fileUrl = materialService.resolvePublicUrl(material.file_url);
          const youtubeEmbed = material.url ? toYouTubeEmbedUrl(material.url) : null;
          const uploadedAt = new Date(material.uploaded_at).toLocaleString();

          const icon =
            material.type === "pdf" ? (
              <FileText className="h-4 w-4 text-brass" />
            ) : material.type === "slide" ? (
              <Presentation className="h-4 w-4 text-brass" />
            ) : material.type === "video" ? (
              <Film className="h-4 w-4 text-brass" />
            ) : (
              <Link2 className="h-4 w-4 text-brass" />
            );

          return (
            <article key={material.id} className="space-y-3 rounded-xl border border-white/10 bg-slate-900/50 p-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  {icon}
                  <p className="font-medium">{material.title}</p>
                  <span className="rounded-md border border-white/15 px-2 py-0.5 text-xs uppercase text-slate-300">{material.type}</span>
                </div>
                <p className="text-xs text-slate-400">{uploadedAt}</p>
              </div>

              {(material.type === "pdf" || material.type === "slide") && fileUrl ? (
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    className="rounded-lg border border-white/20 px-3 py-1 text-sm text-slate-200 hover:bg-white/10"
                    onClick={() => setActivePreviewKey((current) => (current === previewKey ? null : previewKey))}
                  >
                    {isPreviewOpen ? "Hide preview" : "View PDF"}
                  </button>
                  <button
                    type="button"
                    className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-3 py-1 text-sm text-slate-200 hover:bg-white/10"
                    onClick={() => onDownloadMaterial(classroomId, material)}
                  >
                    <Download className="h-4 w-4" />
                    Download
                  </button>
                </div>
              ) : null}

              {isPreviewOpen && (material.type === "pdf" || material.type === "slide") && fileUrl ? (
                <iframe src={fileUrl} title={`${material.title}-viewer`} className="h-80 w-full rounded-lg border border-white/10 bg-white" />
              ) : null}

              {material.type === "video" && material.url ? (
                <div className="space-y-2">
                  {youtubeEmbed ? (
                    <iframe
                      title={`${material.title}-video`}
                      src={youtubeEmbed}
                      className="h-64 w-full rounded-lg border border-white/10"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    />
                  ) : (
                    <a
                      href={material.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-3 py-1 text-sm text-slate-200 hover:bg-white/10"
                    >
                      <ExternalLink className="h-4 w-4" />
                      Open video link
                    </a>
                  )}
                </div>
              ) : null}

              {material.type === "link" && material.url ? (
                <a
                  href={material.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-3 py-1 text-sm text-slate-200 hover:bg-white/10"
                >
                  <ExternalLink className="h-4 w-4" />
                  Open external link
                </a>
              ) : null}
            </article>
          );
        })}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <section>
        <p className="text-sm uppercase tracking-[0.3em] text-lagoon">Overview</p>
        <h2 className="mt-2 text-4xl font-semibold">Learning command center</h2>
        <p className="mt-3 max-w-3xl text-slate-300">
          Centralized workflows for courses, AI notes, assignments, grade approval, and student-facing academic progress.
        </p>
      </section>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Active courses" value="12" helper="Spring semester sections being taught now." icon={<BookOpen className="h-5 w-5" />} />
        <MetricCard label="AI notes generated" value="148" helper="Class session summaries personalized for students." icon={<Sparkles className="h-5 w-5" />} />
        <MetricCard label="Pending grading" value="31" helper="Submissions awaiting teacher approval." icon={<ClipboardCheck className="h-5 w-5" />} />
        <MetricCard label="Chat questions" value="420" helper="Course and planning assistant requests processed." icon={<Bot className="h-5 w-5" />} />
      </section>

      {classroomError ? <p className="rounded-xl border border-rose-400/40 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">{classroomError}</p> : null}
      {classroomMessage ? <p className="rounded-xl border border-emerald-400/40 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200">{classroomMessage}</p> : null}

      {user?.role === "teacher" ? (
        <section className="space-y-6 rounded-3xl border border-white/10 bg-white/5 p-5">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-lagoon">Classrooms</p>
            <h3 className="mt-2 text-2xl font-semibold">Create, invite, and upload materials</h3>
          </div>
          <form onSubmit={onCreateClassroom} className="flex flex-col gap-3 md:flex-row">
            <input
              className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
              placeholder="Classroom name"
              value={classroomName}
              onChange={(event) => setClassroomName(event.target.value)}
            />
            <button
              type="submit"
              disabled={isCreatingClassroom}
              className="rounded-2xl bg-brass px-4 py-3 font-medium text-ink transition hover:brightness-110 disabled:opacity-70"
            >
              {isCreatingClassroom ? "Creating..." : "Create classroom"}
            </button>
          </form>

          <form onSubmit={onUploadMaterial} className="space-y-3 rounded-2xl border border-white/10 bg-slate-950/50 p-4">
            <div className="grid gap-3 md:grid-cols-2">
              <select
                className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
                value={materialClassroomId}
                onChange={(event) => setMaterialClassroomId(event.target.value ? Number(event.target.value) : "")}
              >
                <option value="">Select classroom</option>
                {classroomOptions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
              <select
                className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
                value={materialType}
                onChange={(event) => setMaterialType(event.target.value as MaterialType)}
              >
                <option value="pdf">PDF</option>
                <option value="slide">Slide (PDF)</option>
                <option value="video">Video link (YouTube)</option>
                <option value="link">External link</option>
              </select>
            </div>

            <input
              className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
              placeholder="Material title"
              value={materialTitle}
              onChange={(event) => setMaterialTitle(event.target.value)}
            />

            {materialType === "pdf" || materialType === "slide" ? (
              <input
                type="file"
                accept="application/pdf,.pdf"
                className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
                onChange={(event) => setMaterialFile(event.target.files?.[0] ?? null)}
              />
            ) : (
              <input
                className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
                placeholder={materialType === "video" ? "https://www.youtube.com/watch?v=..." : "https://example.com/resource"}
                value={materialUrl}
                onChange={(event) => setMaterialUrl(event.target.value)}
              />
            )}

            <button
              type="submit"
              disabled={isUploadingMaterial}
              className="inline-flex items-center gap-2 rounded-2xl bg-brass px-4 py-3 font-medium text-ink transition hover:brightness-110 disabled:opacity-70"
            >
              <Upload className="h-4 w-4" />
              {isUploadingMaterial ? "Uploading..." : "Upload material"}
            </button>
          </form>

          {isLoadingClassrooms ? <p className="text-slate-300">Loading classrooms...</p> : null}
          <div className="grid gap-4 md:grid-cols-2">
            {teacherClassrooms.map((classroom) => {
              const isQrHidden = hiddenQrByClassroom[classroom.id] ?? true;
              return (
              <article key={classroom.id} className="space-y-3 rounded-2xl border border-white/10 bg-slate-950/60 p-4">
                <h4 className="text-lg font-semibold">{classroom.name}</h4>
                <div className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/20 px-3 py-2">
                  <p className="font-mono text-lg tracking-wider">{classroom.invite_code}</p>
                  <button
                    type="button"
                    onClick={() => copyCode(classroom.invite_code)}
                    className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-3 py-1 text-sm text-slate-200 hover:bg-white/10"
                  >
                    <Copy className="h-4 w-4" />
                    Copy
                  </button>
                </div>
                <div className="space-y-2">
                  <button
                    type="button"
                    onClick={() => toggleQrVisibility(classroom.id)}
                    className="rounded-lg border border-white/20 px-3 py-1 text-sm text-slate-200 hover:bg-white/10"
                  >
                    {isQrHidden ? "Show QR code" : "Hide QR code"}
                  </button>
                  {!isQrHidden ? (
                    <img
                      src={classroom.qr_code_data_url}
                      alt={`QR code for invite code ${classroom.invite_code}`}
                      className="h-36 w-36 rounded-lg bg-white p-2"
                    />
                  ) : (
                    <p className="text-sm text-slate-400">QR code hidden for this classroom.</p>
                  )}
                </div>
                <div className="space-y-2">
                  <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Materials</p>
                  {renderMaterialList(classroom.id)}
                </div>
              </article>
              );
            })}
          </div>
        </section>
      ) : null}

      {user?.role === "student" ? (
        <section className="space-y-4 rounded-3xl border border-white/10 bg-white/5 p-5">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-lagoon">Classrooms</p>
            <h3 className="mt-2 text-2xl font-semibold">Join and view materials</h3>
          </div>
          <form onSubmit={onJoinClassroom} className="flex flex-col gap-3 md:flex-row">
            <input
              className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 uppercase tracking-widest text-paper outline-none"
              placeholder="ABC123"
              value={inviteCode}
              maxLength={6}
              onChange={(event) => setInviteCode(event.target.value)}
            />
            <button
              type="submit"
              disabled={isJoiningClassroom}
              className="rounded-2xl bg-brass px-4 py-3 font-medium text-ink transition hover:brightness-110 disabled:opacity-70"
            >
              {isJoiningClassroom ? "Joining..." : "Join classroom"}
            </button>
          </form>

          {isLoadingClassrooms ? <p className="text-slate-300">Loading classrooms...</p> : null}
          <div className="grid gap-3">
            {studentClassrooms.map((classroom) => (
              <article key={`${classroom.id}-${classroom.joined_at}`} className="space-y-3 rounded-2xl border border-white/10 bg-slate-950/60 p-4">
                <h4 className="text-lg font-semibold">{classroom.name}</h4>
                <p className="text-sm text-slate-300">Invite code: {classroom.invite_code}</p>
                <div className="space-y-2">
                  <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Materials</p>
                  {renderMaterialList(classroom.id)}
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <NotesEditor />
    </div>
  );
};
