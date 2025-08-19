import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
// Proxy to local Ollama server for basic chat generation
// Environment variables supported:
// - OLLAMA_BASE_URL (e.g., http://localhost:11434)
// - OLLAMA_API_URL + OLLAMA_API_PORT (legacy planned vars, e.g., http://localhost + 11434)
// - OLLAMA_MODEL (default: llama3.1:latest)
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
    const baseUrlRaw = process.env.OLLAMA_BASE_URL || legacyUrl || 'http://localhost:11434';
    // Prefer IPv4 loopback to avoid IPv6 localhost resolution issues on some Windows setups (only for explicit localhost)
    const baseUrl = baseUrlRaw.replace('://localhost', '://127.0.0.1');
    const model = process.env.OLLAMA_MODEL || 'llama3.1:latest';
    const backendBaseUrl = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';
    const authHeader = request.headers.get('authorization') || undefined;

    // Lightweight request tracing (no message content)
    try {
      console.debug('[api/ollama] request', {
        chatId: chatId || null,
        userId: userId || null,
        model,
        baseUrl,
        hasAuth: !!authHeader,
      });
    } catch {}

    // Build prompt including prior conversation messages from Redis (oldest -> newest).
    // If history retrieval fails, fall back to the current message only.
    let finalPrompt: string = message;
    try {
      if (chatId && userId) {
        const histUrl = `${backendBaseUrl}/api/v1/chat/redis/${encodeURIComponent(userId)}/${encodeURIComponent(chatId)}?start=0&stop=-1`;
        const histHeaders: Record<string, string> = {};
        if (authHeader) histHeaders['Authorization'] = authHeader;
        const histRes = await fetch(histUrl, { method: 'GET', headers: histHeaders });
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

    let res;
    try {
      res = await fetch(`${baseUrl}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch (e: any) {
      // If initial attempt used a loopback address, try host.docker.internal as a fallback regardless of env flags
      if (baseUrl.includes('127.0.0.1') || baseUrl.includes('localhost')) {
        const alt = 'http://host.docker.internal:11434';
        try {
          res = await fetch(`${alt}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
        } catch (e2: any) {
          console.error('Failed to reach Ollama at', `${baseUrl}/api/generate`, 'and fallback', `${alt}/api/generate`, e2);
          return NextResponse.json(
            { error: 'Failed to reach Ollama', details: String(e2), target: `${baseUrl}/api/generate`, fallback: `${alt}/api/generate` },
            { status: 502 }
          );
        }
      } else {
        console.error('Failed to reach Ollama at', `${baseUrl}/api/generate`, e);
        return NextResponse.json(
          { error: 'Failed to reach Ollama', details: String(e), target: `${baseUrl}/api/generate` },
          { status: 502 }
        );
      }
    }

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      console.warn('[api/ollama] non-OK from Ollama', { status: res.status, details: text.slice(0, 300) });
      return NextResponse.json(
        { error: `Ollama error: ${res.status}`, details: text },
        { status: 502 }
      );
    }

    // Guard JSON parsing and unexpected payloads
    let data: any = null;
    let responseText: string = '';
    try {
      const ct = (res.headers.get('content-type') || '').toLowerCase();
      if (ct.includes('application/json')) {
        data = await res.json();
      } else {
        const raw = await res.text();
        try {
          data = JSON.parse(raw);
        } catch {
          // Some misconfigured servers could return plain text; surface as response
          data = { response: raw };
        }
      }
      const candidate = (data?.response ?? data?.text ?? data?.message);
      responseText = typeof candidate === 'string' ? candidate : '';
    } catch (parseErr) {
      console.error('[api/ollama] failed to parse Ollama response', parseErr);
      return NextResponse.json(
        { error: 'Malformed response from Ollama' },
        { status: 502 }
      );
    }

    if (!responseText || !responseText.trim()) {
      console.warn('[api/ollama] empty response from Ollama', { model });
    }

    // Fire-and-forget: push assistant response to Redis via FastAPI backend
    // Do not block the response to the UI; log on failure.
    try {
      if (chatId && userId && responseText && responseText.trim()) {
        const assistantPayload = {
          type: 'assistant_message',
          text: responseText,
          model,
          source: 'ollama',
          original: data,
          context: { philosopher },
        };
        const url = `${backendBaseUrl}/api/v1/chat/redis/${encodeURIComponent(userId)}/${encodeURIComponent(chatId)}`;
        const headers: Record<string, string> = { 'Content-Type': 'application/json' };
        if (authHeader) headers['Authorization'] = authHeader;
        // Intentionally not awaited to avoid adding latency
        fetch(url, { method: 'POST', headers, body: JSON.stringify(assistantPayload) }).then(async (r) => {
          if (!r.ok) {
            const t = await r.text().catch(() => '');
            console.warn('[api/ollama] failed to push assistant message to Redis', { status: r.status, details: t.slice(0, 300) });
          }
        }).catch((e) => {
          console.warn('[api/ollama] failed to push assistant message to Redis', e);
        });
      }
    } catch (pushErr) {
      console.warn('[api/ollama] error scheduling assistant message push to Redis', pushErr);
    }

    // Normalize to { response } to be compatible with existing ChatInterface expectations
    return NextResponse.json({ response: responseText });
  } catch (err) {
    console.error('Error in /api/ollama:', err);
    return NextResponse.json(
      { error: 'Internal server error', details: String(err) },
      { status: 500 }
    );
  }
}

