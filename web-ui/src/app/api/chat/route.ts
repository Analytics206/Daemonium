import { NextRequest, NextResponse } from 'next/server';

// Proxy to backend API for chat operations
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const backendUrl = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';
    const userId = (body?.userId ?? '').toString() || 'anonymous';
    const authHeader = request.headers.get('authorization') || undefined;

    // Ensure backend receives expected field name
    const forwardBody = {
      ...body,
      // Backend expects `author`; preserve if provided, else map from `philosopher`
      author: body?.author ?? body?.philosopher ?? undefined,
    };

    // Forward request to backend chat API (correct endpoint is /message)
    const backendResponse = await fetch(`${backendUrl}/api/v1/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Add user context for backend (Firebase uid/email preferred)
        'X-User-ID': userId,
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      body: JSON.stringify(forwardBody),
    });

    if (!backendResponse.ok) {
      const errText = await backendResponse.text().catch(() => '');
      console.error('Backend API error', backendResponse.status, errText);
      return NextResponse.json(
        { error: 'Backend API error', status: backendResponse.status, details: errText },
        { status: 502 }
      );
    }

    const data: any = await backendResponse.json();

    // Extract response text for UI and for persistence
    const responseText: string = typeof data?.response === 'string' ? data.response : '';

    // Fire-and-forget: push assistant response to Redis via FastAPI backend (do not block UI)
    try {
      const chatId: string | undefined = (body?.chatId ?? '').toString() || undefined;
      const uid: string | undefined = (body?.userId ?? '').toString() || undefined;
      if (chatId && uid && responseText && responseText.trim()) {
        // Try to derive model from backend sources array like ["MCP ollama.chat", "model=llama3.1:latest"]
        let model: string | undefined;
        try {
          const sources = Array.isArray(data?.sources) ? data.sources : [];
          for (const s of sources) {
            if (typeof s === 'string' && s.startsWith('model=')) {
              model = s.slice('model='.length);
              break;
            }
          }
        } catch {}

        const assistantPayload = {
          type: 'assistant_message',
          text: responseText,
          model,
          source: 'mcp',
          original: data,
          context: { philosopher: forwardBody.author },
        } as Record<string, any>;

        const url = `${backendUrl}/api/v1/chat/redis/${encodeURIComponent(uid)}/${encodeURIComponent(chatId)}`;
        const headers: Record<string, string> = { 'Content-Type': 'application/json' };
        if (authHeader) headers['Authorization'] = authHeader;
        fetch(url, { method: 'POST', headers, body: JSON.stringify(assistantPayload) })
          .then(async (r) => {
            if (!r.ok) {
              const t = await r.text().catch(() => '');
              console.warn('[api/chat] failed to push assistant message to Redis', { status: r.status, details: t.slice(0, 300) });
            }
          })
          .catch((e) => {
            console.warn('[api/chat] failed to push assistant message to Redis', e);
          });
      }
    } catch (pushErr) {
      console.warn('[api/chat] error scheduling assistant message push to Redis', pushErr);
    }

    // Return backend JSON directly (includes { response, ... })
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in chat API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
