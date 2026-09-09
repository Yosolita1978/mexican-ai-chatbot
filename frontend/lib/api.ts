const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
    const body: unknown = await response.json().catch(() => null);
    let detail: string | null = null;

    if (body && typeof body === 'object' && 'detail' in body) {
      const value = (body as { detail: unknown }).detail;
      if (typeof value === 'string') {
        detail = value;
      }
    }

    throw new Error(detail ?? 'Failed to chat with agent');
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