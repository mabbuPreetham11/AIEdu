import { FormEvent, useState } from "react";
import axios from "axios";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { authService } from "../../services/auth.service";

export const RegisterForm = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    role: "student" as "teacher" | "student",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await authService.register({
        ...form,
        email: form.email.trim(),
      });
      const invite = searchParams.get("invite");
      navigate(invite ? `/login?invite=${encodeURIComponent(invite)}` : "/login");
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (typeof detail === "string") {
          setError(detail);
        } else if (Array.isArray(detail) && detail.length > 0 && typeof detail[0]?.msg === "string") {
          setError(detail[0].msg);
        } else {
          setError("Registration failed. Please check your details and try again.");
        }
      } else {
        setError("Registration failed. Please check your details and try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-md space-y-4 rounded-3xl border border-white/10 bg-white/5 p-8">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-lagoon">Sign up</p>
        <h2 className="mt-2 text-3xl font-semibold">Create local account</h2>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <input
          className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
          placeholder="First name"
          value={form.first_name}
          onChange={(event) => setForm((current) => ({ ...current, first_name: event.target.value }))}
        />
        <input
          className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
          placeholder="Last name"
          value={form.last_name}
          onChange={(event) => setForm((current) => ({ ...current, last_name: event.target.value }))}
        />
      </div>
      <input
        className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
        placeholder="name@iiitdwd.ac.in"
        value={form.email}
        onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
      />
      <input
        type="password"
        className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
        placeholder="Password"
        value={form.password}
        onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
      />
      <select
        className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
        value={form.role}
        onChange={(event) => setForm((current) => ({ ...current, role: event.target.value as "teacher" | "student" }))}
      >
        <option value="student">Student</option>
        <option value="teacher">Teacher</option>
      </select>
      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full rounded-2xl bg-brass px-4 py-3 font-medium text-ink transition hover:brightness-110 disabled:opacity-70"
      >
        {isSubmitting ? "Creating account..." : "Register"}
      </button>
      <p className="text-sm text-slate-300">
        Already have an account?{" "}
        <Link to={searchParams.get("invite") ? `/login?invite=${encodeURIComponent(searchParams.get("invite") ?? "")}` : "/login"} className="text-lagoon">
          Go to login
        </Link>
      </p>
    </form>
  );
};
