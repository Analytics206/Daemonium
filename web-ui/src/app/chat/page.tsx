import ChatPageContainer from "../../components/chat/chat-page-container";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Daemonium - Chat (MCP)",
  description: "Chat interface using backend MCP flow by default (via /api/chat).",
};

export default function ChatPage() {
  return (
    <ChatPageContainer chatId="ollama-local" philosopher="Local LLM" endpoint="/api/chat" />
  );
}
