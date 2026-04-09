import { BookOpen, Bot, ChartColumn, GraduationCap, LayoutDashboard } from "lucide-react";
import { Link, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/courses", label: "Courses", icon: BookOpen },
  { to: "/assignments", label: "Assignments", icon: GraduationCap },
  { to: "/grades", label: "Grades", icon: ChartColumn },
  { to: "/chat", label: "AI Chat", icon: Bot },
];

export const Shell = () => (
  <div className="min-h-screen bg-transparent text-paper">
    <div className="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-4 py-6 lg:flex-row">
      <aside className="w-full rounded-3xl border border-white/10 bg-white/5 p-5 shadow-soft backdrop-blur lg:w-72">
        <div className="mb-8">
          <p className="text-sm uppercase tracking-[0.3em] text-lagoon">IIIT Dharwad</p>
          <h1 className="mt-2 text-2xl font-semibold">AI Learning Hub</h1>
          <p className="mt-2 text-sm text-slate-300">Courses, notes, grading, and chatbot workflows in one place.</p>
        </div>
        <nav className="space-y-2">
          {navItems.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-slate-200 transition hover:bg-white/10"
            >
              <Icon className="h-4 w-4 text-brass" />
              {label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 rounded-3xl border border-white/10 bg-slate-900/70 p-6 shadow-soft backdrop-blur">
        <Outlet />
      </main>
    </div>
  </div>
);
