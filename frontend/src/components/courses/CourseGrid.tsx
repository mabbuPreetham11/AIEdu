import type { Course } from "../../types";

export const CourseGrid = ({ courses }: { courses: Course[] }) => (
  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
    {courses.map((course) => (
      <article key={course.id} className="rounded-3xl border border-white/10 bg-white/5 p-5">
        <div className="flex items-center justify-between">
          <span className="rounded-full bg-lagoon/15 px-3 py-1 text-xs uppercase tracking-[0.2em] text-lagoon">
            {course.course_code}
          </span>
          <span className="text-sm text-slate-400">
            {course.semester} {course.year}
          </span>
        </div>
        <h3 className="mt-4 text-xl font-semibold">{course.title}</h3>
        <p className="mt-3 text-sm text-slate-300">Class code: {course.class_code}</p>
        <p className="mt-2 text-sm text-slate-400">
          AI syllabus extraction, grade weights, session notes, enrollment, and archive lifecycle ready.
        </p>
      </article>
    ))}
  </div>
);

