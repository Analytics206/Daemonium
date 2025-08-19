import { NextRequest, NextResponse } from 'next/server';

// Proxy to backend API
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const backendUrl = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';
    const userId = searchParams.get('userId') || 'anonymous';
    
    // Forward request to backend API
    const backendResponse = await fetch(`${backendUrl}/api/v1/philosophers?${searchParams.toString()}`, {
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userId,
      },
    });

    if (!backendResponse.ok) {
      throw new Error(`Backend API error: ${backendResponse.status}`);
    }

    const data = await backendResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching philosophers:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
