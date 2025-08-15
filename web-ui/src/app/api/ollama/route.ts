import { NextRequest, NextResponse } from 'next/server';

// Proxy to local Ollama server for basic chat generation
// Environment variables supported:
// - OLLAMA_BASE_URL (e.g., http://localhost:11434)
// - OLLAMA_API_URL + OLLAMA_API_PORT (legacy planned vars, e.g., http://localhost + 11434)
// - OLLAMA_MODEL (default: llama3:latest)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message } = body as { message?: string };

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
    // Normalize to { response } to be compatible with existing ChatInterface expectations
    return NextResponse.json({ response: data?.response ?? '' });
  } catch (err) {
    console.error('Error in /api/ollama:', err);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
