import { NextRequest, NextResponse } from 'next/server';

// Proxy to local Ollama server for basic chat generation
// Environment variables supported:
// - OLLAMA_BASE_URL (e.g., http://localhost:11434)
// - OLLAMA_API_URL + OLLAMA_API_PORT (legacy planned vars, e.g., http://localhost + 11434)
// - OLLAMA_MODEL (default: llama3:latest)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, chatId, userId, philosopher } = body as {
      message?: string;
      chatId?: string;
      userId?: string;
      philosopher?: string;
    };

    if (!message || typeof message !== 'string' || !message.trim()) {
      return NextResponse.json(
        { error: 'Missing "message" in request body' },
        { status: 400 }
      );
    }

    const legacyUrl = process.env.OLLAMA_API_URL
      ? `${process.env.OLLAMA_API_URL}${process.env.OLLAMA_API_PORT ? `:${process.env.OLLAMA_API_PORT}` : ''}`
      : undefined;
    const baseUrl = process.env.OLLAMA_BASE_URL || legacyUrl || 'http://localhost:11434';
    const model = process.env.OLLAMA_MODEL || 'llama3:latest';
    const backendBaseUrl = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

    // Build prompt including prior conversation messages from Redis (oldest -> newest).
    // If history retrieval fails, fall back to the current message only.
    let finalPrompt: string = message;
    try {
      if (chatId && userId) {
        const histUrl = `${backendBaseUrl}/api/v1/chat/redis/${encodeURIComponent(userId)}/${encodeURIComponent(chatId)}?start=0&stop=-1`;
        const histRes = await fetch(histUrl, { method: 'GET' });
        if (histRes.ok) {
          const hist = await histRes.json();
          const items: any[] = Array.isArray(hist?.data) ? hist.data : [];
          // Sort by timestamp ascending if present; LRANGE is insertion-ordered but we ensure correctness.
          const toTime = (x: any): number => {
            const ts = x?.timestamp ? Date.parse(x.timestamp) : NaN;
            if (!Number.isNaN(ts)) return ts;
            const dt = x?.date ? Date.parse(x.date) : NaN;
            if (!Number.isNaN(dt)) return dt;
            const st = x?.state?.startTime ? Date.parse(x.state.startTime) : NaN;
            if (!Number.isNaN(st)) return st;
            const et = x?.state?.endTime ? Date.parse(x.state.endTime) : NaN;
            if (!Number.isNaN(et)) return et;
            return 0;
          };
          items.sort((a: any, b: any) => toTime(a) - toTime(b));

          // Build conversation including both user and assistant messages
          const convo: { type: string; text: string }[] = [];
          for (const it of items) {
            if ((it?.type === 'user_message' || it?.type === 'assistant_message') && typeof it?.text === 'string' && it.text.trim()) {
              convo.push({ type: it.type, text: it.text.trim() });
            } else if (!it?.type && typeof it?.message === 'string' && it.message.trim()) {
              // Back-compat: entries without a type treated as user messages
              convo.push({ type: 'user_message', text: it.message.trim() });
            } else if (!it?.type && typeof it?.text === 'string' && it.text.trim()) {
              convo.push({ type: 'user_message', text: it.text.trim() });
            }
          }

          if (convo.length > 0) {
            const currentTrim = message.trim();
            // Avoid duplicating the current user message if it's already the last in Redis history
            if (convo[convo.length - 1]?.type === 'user_message' && convo[convo.length - 1]?.text === currentTrim) {
              convo.pop();
            }
            if (convo.length > 0) {
              const historyBlock = convo
                .map((entry, idx) => `${entry.type} ${idx + 1}: ${entry.text}`)
                .join('\n');
              finalPrompt = `Prior conversation (oldest first):\n${historyBlock}\n\nCurrent user input:\n${message}`;
            }
          }
        }
      }
    } catch {
      // Ignore history errors and fall back silently
      finalPrompt = message;
    }

    const payload = {
      model,
      prompt: finalPrompt,
      stream: false,
    };

    const res = await fetch(`${baseUrl}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      return NextResponse.json(
        { error: `Ollama error: ${res.status}`, details: text },
        { status: 502 }
      );
    }

    const data = await res.json();
    const responseText: string = data?.response ?? '';

    // Fire-and-forget: push assistant response to Redis via FastAPI backend
    // Do not block the response to the UI; log on failure.
    try {
      if (chatId && userId && responseText) {
        const assistantPayload = {
          type: 'assistant_message',
          text: responseText,
          model,
          source: 'ollama',
          original: data,
          context: { philosopher },
        };
        const url = `${backendBaseUrl}/api/v1/chat/redis/${encodeURIComponent(userId)}/${encodeURIComponent(chatId)}?input=${encodeURIComponent(JSON.stringify(assistantPayload))}`;
        // Intentionally not awaited to avoid adding latency
        fetch(url, { method: 'POST' }).catch((e) => {
          console.warn('Failed to push assistant message to Redis:', e);
        });
      }
    } catch (pushErr) {
      console.warn('Error scheduling assistant message push to Redis:', pushErr);
    }

    // Normalize to { response } to be compatible with existing ChatInterface expectations
    return NextResponse.json({ response: responseText });
  } catch (err) {
    console.error('Error in /api/ollama:', err);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

