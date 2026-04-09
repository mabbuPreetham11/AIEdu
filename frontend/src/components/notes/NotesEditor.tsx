import { useState } from "react";

export const NotesEditor = () => {
  const [content, setContent] = useState("# Personal Notes\n\nEditable AI-generated note copy with auto-save.");

  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-semibold">Session Notes</h3>
        <span className="rounded-full bg-lagoon/15 px-3 py-1 text-xs uppercase tracking-[0.2em] text-lagoon">Auto-save</span>
      </div>
      <textarea
        value={content}
        onChange={(event) => setContent(event.target.value)}
        className="min-h-[320px] w-full rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-paper outline-none"
      />
    </div>
  );
};

