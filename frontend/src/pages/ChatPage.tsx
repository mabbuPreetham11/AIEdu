import { ChatPanel } from "../components/chat/ChatPanel";

export const ChatPage = () => (
  <div className="space-y-6">
    <div>
      <p className="text-sm uppercase tracking-[0.3em] text-lagoon">AI Chat</p>
      <h2 className="mt-2 text-4xl font-semibold">Course Q&A and planning copilots</h2>
      <p className="mt-3 text-slate-300">Student-facing course RAG and teacher planning support with persistent history.</p>
    </div>
    <ChatPanel />
  </div>
);

