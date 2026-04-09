import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

import { CourseGrid } from "../components/courses/CourseGrid";
import { useAuth } from "../hooks/useAuth";
import { useCourses } from "../hooks/useCourses";
import { classroomService } from "../services/classroom.service";
import type { StudentClassroom, TeacherClassroom } from "../types";

export const CoursesPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { courses, isLoading } = useCourses();
  const [teacherClassrooms, setTeacherClassrooms] = useState<TeacherClassroom[]>([]);
  const [studentClassrooms, setStudentClassrooms] = useState<StudentClassroom[]>([]);
  const [classroomError, setClassroomError] = useState<string | null>(null);

  useEffect(() => {
    const loadClassrooms = async () => {
      if (!user) return;
      setClassroomError(null);
      try {
        if (user.role === "teacher") {
          const rows = await classroomService.listTeacherClassrooms();
          setTeacherClassrooms(rows);
        } else {
          const rows = await classroomService.listStudentClassrooms();
          setStudentClassrooms(rows);
        }
      } catch (err) {
        if (axios.isAxiosError(err)) {
          const detail = err.response?.data?.detail;
          setClassroomError(typeof detail === "string" ? detail : "Failed to load joined classrooms");
        } else {
          setClassroomError("Failed to load joined classrooms");
        }
      }
    };
    void loadClassrooms();
  }, [user]);

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-lagoon">Courses</p>
        <h2 className="mt-2 text-4xl font-semibold">Manage teaching and enrollment</h2>
      </div>
      {classroomError ? <p className="rounded-xl border border-rose-400/40 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{classroomError}</p> : null}
      {user?.role === "student" ? (
        <section className="space-y-3 rounded-3xl border border-white/10 bg-white/5 p-5">
          <h3 className="text-xl font-semibold">Joined Classrooms</h3>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {studentClassrooms.map((classroom) => (
              <article key={`${classroom.id}-${classroom.joined_at}`} className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                <p className="text-lg font-semibold">{classroom.name}</p>
                <p className="mt-2 text-sm text-slate-300">Invite code: {classroom.invite_code}</p>
                <p className="mt-1 text-xs text-slate-400">Joined: {new Date(classroom.joined_at).toLocaleString()}</p>
                <button
                  type="button"
                  onClick={() => navigate("/assignments")}
                  className="mt-3 rounded-xl border border-white/20 px-3 py-1.5 text-sm text-slate-200 hover:bg-white/10"
                >
                  Open Classroom Quizzes
                </button>
              </article>
            ))}
            {studentClassrooms.length === 0 ? <p className="text-sm text-slate-300">No joined classrooms yet.</p> : null}
          </div>
        </section>
      ) : null}
      {user?.role === "teacher" ? (
        <section className="space-y-3 rounded-3xl border border-white/10 bg-white/5 p-5">
          <h3 className="text-xl font-semibold">Your Classrooms</h3>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {teacherClassrooms.map((classroom) => (
              <article key={classroom.id} className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                <p className="text-lg font-semibold">{classroom.name}</p>
                <p className="mt-2 text-sm text-slate-300">Invite code: {classroom.invite_code}</p>
                <button
                  type="button"
                  onClick={() => navigate("/assignments")}
                  className="mt-3 rounded-xl border border-white/20 px-3 py-1.5 text-sm text-slate-200 hover:bg-white/10"
                >
                  Open Quiz Workspace
                </button>
              </article>
            ))}
            {teacherClassrooms.length === 0 ? <p className="text-sm text-slate-300">No classrooms created yet.</p> : null}
          </div>
        </section>
      ) : null}
      {isLoading ? <p className="text-slate-300">Loading courses...</p> : <CourseGrid courses={courses} />}
    </div>
  );
};
