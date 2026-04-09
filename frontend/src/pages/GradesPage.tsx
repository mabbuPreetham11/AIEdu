import { GradeTable } from "../components/grades/GradeTable";

const demoGrades = [
  { id: 1, submission_id: 1, student_id: 22, course_id: 1, grade_type: "essay", score: 17, max_score: 20, ai_graded: true, is_final: false },
  { id: 2, submission_id: 2, student_id: 23, course_id: 1, grade_type: "quiz", score: 9, max_score: 10, ai_graded: false, is_final: true },
];

export const GradesPage = () => (
  <div className="space-y-6">
    <div>
      <p className="text-sm uppercase tracking-[0.3em] text-lagoon">Grades</p>
      <h2 className="mt-2 text-4xl font-semibold">Teacher gradebook and student feedback</h2>
      <p className="mt-3 text-slate-300">Spreadsheet-style review, AI-assisted scoring, approval workflow, and export support.</p>
    </div>
    <GradeTable grades={demoGrades} />
  </div>
);

