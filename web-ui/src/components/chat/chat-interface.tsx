'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Send, Bot, User } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

interface SessionState {
  userId: string;
  chatId: string;
  date: string;        // YYYY-MM-DD
  startTime: string;   // ISO string
  endTime: string | null; // ISO string or null until session ends
}

interface ChatInterfaceProps {
  chatId: string;
  philosopher?: string;
  endpoint?: string;
}

export default function ChatInterface({ chatId, philosopher, endpoint = '/api/chat' }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Placeholder user identity until auth is wired
  const userId = 'analytics206@gmail';
  const backendBaseUrl = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

  const [sessionChatId, setSessionChatId] = useState<string>('');
  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [sessionInitSent, setSessionInitSent] = useState<boolean>(false);

  const generateId = () => {
    try {
      // Prefer crypto.randomUUID when available
      return (crypto as any)?.randomUUID ? (crypto as any).randomUUID() : `chat-${Math.random().toString(36).slice(2)}-${Date.now()}`;
    } catch {
      return `chat-${Math.random().toString(36).slice(2)}-${Date.now()}`;
    }
  };

  const pushToRedis = async (payload: string) => {
    if (!sessionChatId) return;
    const url = `${backendBaseUrl}/api/v1/chat/redis/${encodeURIComponent(userId)}/${encodeURIComponent(sessionChatId)}?input=${encodeURIComponent(payload)}`;
    try {
      await fetch(url, { method: 'POST' });
    } catch (err) {
      console.error('Failed to push to Redis:', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize session (generate ChatID, set session state, push session_start to Redis)
  useEffect(() => {
    // Only initialize once per mount
    if (!sessionChatId) {
      const now = new Date();
      const newChatId = generateId();
      setSessionChatId(newChatId);
      try { console.log('[Chat] New session ChatID:', newChatId); } catch {}

      const state: SessionState = {
        userId,
        chatId: newChatId,
        date: now.toISOString().slice(0, 10),
        startTime: now.toISOString(),
        endTime: null,
      };
      setSessionState(state);
    }
  }, [sessionChatId, userId]);

  // Once sessionState is ready and not yet sent, push to Redis as session_start
  useEffect(() => {
    const sendInit = async () => {
      if (sessionState && !sessionInitSent) {
        const payload = JSON.stringify({ type: 'session_start', state: sessionState });
        await pushToRedis(payload);
        setSessionInitSent(true);
      }
    };
    sendInit();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionState, sessionInitSent]);

  // On unmount, set endTime and push session_end
  useEffect(() => {
    return () => {
      if (sessionState) {
        const ended = { ...sessionState, endTime: new Date().toISOString() };
        const payload = JSON.stringify({ type: 'session_end', state: ended });
        // Fire and forget
        pushToRedis(payload);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionState]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      // Push the user's input to Redis (do not block chat flow on failure)
      void pushToRedis(JSON.stringify({ type: 'user_message', text: currentInput }));

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentInput,
          chatId: sessionChatId || chatId,
          philosopher,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: data.response,
          role: 'assistant',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        console.error('Chat API error:', response.statusText);
      }
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-h-[600px]">
      {/* Chat Header */}
      <div className="flex items-center p-4 border-b border-slate-200 dark:border-slate-700">
        <Bot className="w-6 h-6 mr-2 text-blue-600" />
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          {philosopher ? `Chat with ${philosopher}` : 'Philosopher Chat'}
        </h2>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-slate-500 dark:text-slate-400 py-8">
            <Bot className="w-12 h-12 mx-auto mb-4 text-slate-400" />
            <p>Start a conversation with {philosopher || 'a philosopher'}!</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex items-start space-x-3 ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0">
                <Bot className="w-8 h-8 text-blue-600" />
              </div>
            )}
            
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-slate-100'
              }`}
            >
              <p className="text-sm">{message.content}</p>
              <p className="text-xs opacity-70 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0">
                <User className="w-8 h-8 text-slate-600" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-start space-x-3">
            <Bot className="w-8 h-8 text-blue-600" />
            <div className="bg-slate-100 dark:bg-slate-700 px-4 py-2 rounded-lg">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:100ms]"></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:200ms]"></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-slate-200 dark:border-slate-700">
        <div className="flex space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask ${philosopher || 'a philosopher'} anything...`}
            disabled={isLoading}
            className="flex-1"
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </form>
    </div>
  );
}
