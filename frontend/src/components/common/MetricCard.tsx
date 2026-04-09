import type { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: string;
  helper: string;
  icon: ReactNode;
}

export const MetricCard = ({ label, value, helper, icon }: MetricCardProps) => (
  <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-lagoon/15 text-lagoon">{icon}</div>
    <p className="text-sm text-slate-400">{label}</p>
    <p className="mt-2 text-3xl font-semibold text-paper">{value}</p>
    <p className="mt-2 text-sm text-slate-400">{helper}</p>
  </div>
);

