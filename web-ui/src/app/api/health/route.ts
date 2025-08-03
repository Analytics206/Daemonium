import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Check if the application is healthy
    const healthStatus = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: 'daemonium-web-ui',
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      uptime: process.uptime(),
    };

    return NextResponse.json(healthStatus, { status: 200 });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        service: 'daemonium-web-ui',
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
