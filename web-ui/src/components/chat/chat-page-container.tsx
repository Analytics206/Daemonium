"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";
import {
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  Star,
  Settings,
  Plus,
  Users,
  History,
} from "lucide-react";
import ChatInterface from "./chat-interface";

interface ChatSummaryItem {
  chat_id: string;
  title: string;
  first_user_text?: string;
  created_at?: string;
  last_updated?: string;
  key?: string;
  count?: number;
}

interface ChatPageContainerProps {
  chatId: string;
  philosopher?: string;
  endpoint?: string;
}

export default function ChatPageContainer({
  chatId,
  philosopher,
  endpoint = "/api/chat",
}: ChatPageContainerProps) {
  const [expanded, setExpanded] = useState<boolean>(true);
  const [activeChatId, setActiveChatId] = useState<string>(chatId);

  // Hardcoded user and backend URL (no auth wiring yet)
  const userId = "analytics206@gmail";
  const backendBaseUrl =
    process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000";

  // Recent chats state
  const [recents, setRecents] = useState<ChatSummaryItem[]>([]);
  const [loadingRecents, setLoadingRecents] = useState<boolean>(false);
  const [recentsError, setRecentsError] = useState<string | null>(null);

  const loadRecents = async () => {
    try {
      setLoadingRecents(true);
      setRecentsError(null);
      const url = `${backendBaseUrl}/api/v1/chat/redis/${encodeURIComponent(
        userId
      )}/summaries`;
      const res = await fetch(url, { method: "GET" });
      if (!res.ok) throw new Error(`Failed to load recents: ${res.status}`);
      const data = await res.json();
      const rawItems: ChatSummaryItem[] = Array.isArray(data?.data) ? data.data : [];
      // Exclude sessions that never had a user message (only session_start)
      const items = rawItems.filter((it) => {
        const t = (it.first_user_text ?? "").trim();
        return t.length > 0 && t !== "(no user input)";
      });
      setRecents(items);
    } catch (e: any) {
      setRecentsError(String(e?.message || e));
    } finally {
      setLoadingRecents(false);
    }
  };

  useEffect(() => {
    // Initial fetch of recent chats
    loadRecents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex h-screen bg-white dark:bg-slate-950">
      {/* Sidebar */}
      <aside
        className={cn(
          "relative flex flex-col border-r border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 transition-all duration-300 ease-in-out",
          expanded ? "w-64" : "w-16"
        )}
      >
        <div className="flex items-center h-14 px-3 border-b border-slate-200 dark:border-slate-800">
          <MessageSquare className="w-5 h-5 text-blue-600" />
          {expanded && (
            <span className="ml-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
              Conversations
            </span>
          )}
        </div>

        <nav className="p-2 space-y-1 flex-1 overflow-y-auto">
          <Link href="#" onClick={(e) => { e.preventDefault(); setActiveChatId(""); }}>
            <Button variant="ghost" className="w-full justify-start">
              <Plus className="w-4 h-4 mr-3" />
              {expanded && <span>New chat</span>}
            </Button>
          </Link>

          <div className="w-full">
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={(e) => {
                e.preventDefault();
                loadRecents();
              }}
            >
              <History className="w-4 h-4 mr-3" />
              {expanded && (
                <span>
                  Recent{loadingRecents ? " (loading...)" : ""}
                </span>
              )}
            </Button>

            {/* Recent items list */}
            {expanded && (
              <div className="mt-1 space-y-1">
                {recentsError && (
                  <div className="text-xs text-red-600 px-3 py-1">{recentsError}</div>
                )}
                {!recentsError && recents.length === 0 && !loadingRecents && (
                  <div className="text-xs text-slate-500 px-3 py-1">No recent chats</div>
                )}
                {recents.map((item) => (
                  <button
                    key={item.chat_id}
                    className={cn(
                      "w-full text-left px-3 py-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800",
                      activeChatId === item.chat_id
                        ? "bg-slate-100 dark:bg-slate-800"
                        : ""
                    )}
                    onClick={() => setActiveChatId(item.chat_id)}
                    title={item.first_user_text || item.title}
                  >
                    <div className="truncate text-sm text-slate-900 dark:text-slate-100">
                      {item.title}
                    </div>
                    <div className="text-[10px] text-slate-500">
                      {item.last_updated || item.created_at || ""}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <Link href="#">
            <Button variant="ghost" className="w-full justify-start">
              <Users className="w-4 h-4 mr-3" />
              {expanded && <span>Philosophers</span>}
            </Button>
          </Link>

          <Link href="#">
            <Button variant="ghost" className="w-full justify-start">
              <Star className="w-4 h-4 mr-3" />
              {expanded && <span>Starred</span>}
            </Button>
          </Link>

          <div className="pt-2 mt-auto border-t border-slate-200 dark:border-slate-800" />

          <Link href="#">
            <Button variant="ghost" className="w-full justify-start">
              <Settings className="w-4 h-4 mr-3" />
              {expanded && <span>Settings</span>}
            </Button>
          </Link>
        </nav>

        {/* Collapse/Expand toggle */}
        <button
          aria-label={expanded ? "Collapse sidebar" : "Expand sidebar"}
          onClick={() => setExpanded((v) => !v)}
          className="absolute -right-3 top-16 z-10 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-1 shadow hover:bg-slate-50 dark:hover:bg-slate-700"
        >
          {expanded ? (
            <ChevronLeft className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </button>
      </aside>

      {/* Main content */}
      <section className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-auto p-3 md:p-4">
          <div className="h-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
            <ChatInterface chatId={activeChatId} philosopher={philosopher} endpoint={endpoint} />
          </div>
        </div>
      </section>
    </div>
  );
}
