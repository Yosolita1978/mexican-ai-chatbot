const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Raised when the backend answers with an error status. `detail` holds the
// message the backend wrote for the user (rate limits, validation) and is
// safe to display; it is null when the failure has no user-facing text, so
// callers can fall back to their own translated wording.
export class ApiError extends Error {
  readonly status: number;
  readonly detail: string | null;

  constructor(status: number, detail: string | null) {
    super(detail ?? `Request failed with status ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

// Store session ID in localStorage
const getSessionId = (): string => {
  if (typeof window === 'undefined') return '';
  
  let sessionId = localStorage.getItem('sazonbot_session_id');
  if (!sessionId) {
    sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('sazonbot_session_id', sessionId);
  }
  return sessionId;
};

export const agentChat = async (message: string) => {
  const sessionId = getSessionId();
  
  const response = await fetch(`${API_URL}/agent-chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      message,
      session_id: sessionId 
    }),
  });

  if (!response.ok) {
    // The backend explains rate limits in `detail` ("¡Espérate! ..."), so show
    // that instead of a generic error. FastAPI's 422 validation errors put an
    // array in `detail`, which is why we only use it when it is a string.
    // 5xx responses also carry `detail`, but there it is str(exception) from
    // the server, which must never reach the UI - so only 4xx text is kept.
    const body: unknown = await response.json().catch(() => null);
    let detail: string | null = null;

    if (response.status < 500 && body && typeof body === 'object' && 'detail' in body) {
      const value = (body as { detail: unknown }).detail;
      if (typeof value === 'string') {
        detail = value;
      }
    }

    throw new ApiError(response.status, detail);
  }

  return response.json();
};

export const clearAgentMemory = async () => {
  const sessionId = getSessionId();
  
  const response = await fetch(`${API_URL}/clear-memory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!response.ok) {
    throw new Error('Failed to clear memory');
  }

  return response.json();
};