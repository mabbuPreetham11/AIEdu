import { RegisterForm } from "../components/auth/RegisterForm";

export const RegisterPage = () => (
  <div className="flex min-h-screen items-center justify-center px-4">
    <div className="grid w-full max-w-6xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="rounded-[2rem] border border-white/10 bg-white/5 p-8 shadow-soft backdrop-blur">
        <p className="text-sm uppercase tracking-[0.35em] text-brass">Local access</p>
        <h1 className="mt-4 max-w-xl text-5xl font-semibold leading-tight">
          Create a local IIIT Dharwad-style account for testing the LMS flows.
        </h1>
        <p className="mt-5 max-w-2xl text-lg text-slate-300">
          You can also use seeded demo accounts after the backend starts for the first time.
        </p>
      </section>
      <RegisterForm />
    </div>
  </div>
);
