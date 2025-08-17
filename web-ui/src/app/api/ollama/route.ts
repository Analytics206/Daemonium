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

    const payload = {
      model,
      prompt: message,
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

