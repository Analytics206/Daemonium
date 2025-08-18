import ChatPageContainer from "../../components/chat/chat-page-container";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Daemonium - Chat (Ollama)",
  description: "Simple chat interface connected to local Ollama via API proxy.",
};

export default function ChatPage() {
  return (
    <ChatPageContainer chatId="ollama-local" philosopher="Local LLM" endpoint="/api/ollama" />
  );
}
