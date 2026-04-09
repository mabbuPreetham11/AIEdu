import type { Grade } from "../../types";

export const GradeTable = ({ grades }: { grades: Grade[] }) => (
  <div className="overflow-hidden rounded-3xl border border-white/10">
    <table className="min-w-full bg-white/5 text-left text-sm">
      <thead className="bg-white/10 text-slate-300">
        <tr>
          <th className="px-4 py-3">Student</th>
          <th className="px-4 py-3">Type</th>
          <th className="px-4 py-3">Score</th>
          <th className="px-4 py-3">AI</th>
          <th className="px-4 py-3">Finalized</th>
        </tr>
      </thead>
      <tbody>
        {grades.map((grade) => (
          <tr key={grade.id} className="border-t border-white/10">
            <td className="px-4 py-3">Student #{grade.student_id}</td>
            <td className="px-4 py-3">{grade.grade_type}</td>
            <td className="px-4 py-3">
              {grade.score}/{grade.max_score}
            </td>
            <td className="px-4 py-3">{grade.ai_graded ? "Yes" : "No"}</td>
            <td className="px-4 py-3">{grade.is_final ? "Approved" : "Pending"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

