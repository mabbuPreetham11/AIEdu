import { FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import { login } from "../../store/slices/authSlice";

export const LoginForm = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { dispatch, isLoading, error } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const action = await dispatch(login({ email: email.trim().toLowerCase(), password }));
    if (login.fulfilled.match(action)) {
      const invite = searchParams.get("invite");
      navigate(invite ? `/?invite=${encodeURIComponent(invite)}` : "/");
    }
  };

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-md space-y-4 rounded-3xl border border-white/10 bg-white/5 p-8">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-lagoon">Sign in</p>
        <h2 className="mt-2 text-3xl font-semibold">Welcome back</h2>
      </div>
      <input
        className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
        placeholder="name@iiitdwd.ac.in"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />
      <input
        type="password"
        className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-paper outline-none"
        placeholder="Password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />
      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full rounded-2xl bg-brass px-4 py-3 font-medium text-ink transition hover:brightness-110 disabled:opacity-70"
      >
        {isLoading ? "Signing in..." : "Login"}
      </button>
      <p className="text-sm text-slate-300">
        No account yet?{" "}
        <Link to={searchParams.get("invite") ? `/register?invite=${encodeURIComponent(searchParams.get("invite") ?? "")}` : "/register"} className="text-lagoon">
          Create one
        </Link>
      </p>
    </form>
  );
};
