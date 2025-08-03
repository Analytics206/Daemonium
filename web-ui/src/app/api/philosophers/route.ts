import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../../lib/auth';

// Proxy to backend API
export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';
    
    // Forward request to backend API
    const backendResponse = await fetch(`${backendUrl}/api/v1/philosophers?${searchParams.toString()}`, {
      headers: {
        'Content-Type': 'application/json',
        // Add any auth headers if needed for backend
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
