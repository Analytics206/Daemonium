"use client";

import React, { useState } from "react";
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
          <Link href="#">
            <Button variant="ghost" className="w-full justify-start">
              <Plus className="w-4 h-4 mr-3" />
              {expanded && <span>New chat</span>}
            </Button>
          </Link>

          <Link href="#">
            <Button variant="ghost" className="w-full justify-start">
              <History className="w-4 h-4 mr-3" />
              {expanded && <span>Recent</span>}
            </Button>
          </Link>

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
            <ChatInterface chatId={chatId} philosopher={philosopher} endpoint={endpoint} />
          </div>
        </div>
      </section>
    </div>
  );
}
