import { NextRequest, NextResponse } from 'next/server';

const MANAGER_API = process.env.MANAGER_API_URL || 'http://localhost:8002/xiaozhi';

export async function GET(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return proxy(request, await params);
}
export async function POST(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return proxy(request, await params);
}
export async function PUT(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return proxy(request, await params);
}
export async function DELETE(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return proxy(request, await params);
}

async function proxy(request: NextRequest, { path }: { path: string[] }) {
  const targetPath = path.join('/');
  const target = `${MANAGER_API}/${targetPath}${request.nextUrl.search}`;

  const headers: Record<string, string> = {};
  request.headers.forEach((value, key) => {
    if (!['host', 'connection', 'transfer-encoding'].includes(key.toLowerCase())) {
      headers[key] = value;
    }
  });

  const init: RequestInit = {
    method: request.method,
    headers,
  };

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    const contentType = request.headers.get('content-type') || '';
    if (contentType.includes('multipart/form-data')) {
      init.body = await request.arrayBuffer();
    } else {
      try {
        init.body = await request.text();
      } catch {
        // empty body
      }
    }
  }

  try {
    const res = await fetch(target, init);
    const body = await res.arrayBuffer();

    const responseHeaders = new Headers();
    res.headers.forEach((value, key) => {
      if (!['transfer-encoding', 'content-encoding'].includes(key.toLowerCase())) {
        responseHeaders.set(key, value);
      }
    });

    return new NextResponse(body, {
      status: res.status,
      headers: responseHeaders,
    });
  } catch (err: any) {
    return NextResponse.json(
      { code: -1, msg: `Không thể kết nối Manager API (${MANAGER_API}): ${err.message}` },
      { status: 502 }
    );
  }
}
