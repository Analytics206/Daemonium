import ChatInterface from "../../components/chat/chat-interface";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Daemonium - Chat (Ollama)",
  description: "Simple chat interface connected to local Ollama via API proxy.",
};

export default function ChatPage() {
  return (
    <main className="flex min-h-screen flex-col items-center">
      <div className="w-full max-w-4xl p-4 md:p-6">
        <div className="mb-4 md:mb-6">
          <h1 className="text-2xl md:text-3xl font-semibold text-slate-900 dark:text-slate-100">
            Local Model Chat (Ollama)
          </h1>
          <p className="mt-2 text-slate-600 dark:text-slate-400">
            This page connects to your local Ollama server through the Next.js API proxy at <code className="px-1 py-0.5 rounded bg-slate-100 dark:bg-slate-800">/api/ollama</code>.
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
          <ChatInterface chatId="ollama-local" philosopher="Local LLM" endpoint="/api/ollama" />
        </div>
      </div>
    </main>
  );
}
