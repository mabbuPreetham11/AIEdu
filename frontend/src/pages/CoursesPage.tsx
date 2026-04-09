import { CourseGrid } from "../components/courses/CourseGrid";
import { useCourses } from "../hooks/useCourses";

export const CoursesPage = () => {
  const { courses, isLoading } = useCourses();

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-lagoon">Courses</p>
        <h2 className="mt-2 text-4xl font-semibold">Manage teaching and enrollment</h2>
      </div>
      {isLoading ? <p className="text-slate-300">Loading courses...</p> : <CourseGrid courses={courses} />}
    </div>
  );
};

