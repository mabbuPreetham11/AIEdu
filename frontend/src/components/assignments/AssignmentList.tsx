import type { Assignment } from "../../types";

export const AssignmentList = ({ assignments }: { assignments: Assignment[] }) => (
  <div className="space-y-4">
    {assignments.map((assignment) => (
      <div key={assignment.id} className="rounded-3xl border border-white/10 bg-white/5 p-5">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-xl font-semibold">{assignment.title}</h3>
            <p className="mt-2 text-sm text-slate-300">{assignment.description}</p>
          </div>
          <div className="text-sm text-slate-400">
            <p>Type: {assignment.type}</p>
            <p>Due: {new Date(assignment.due_date).toLocaleString()}</p>
          </div>
        </div>
      </div>
    ))}
  </div>
);

