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

    const data = await backendResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in chat API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
