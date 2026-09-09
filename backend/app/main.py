from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.agent import get_agent
from app.config import APP_NAME, APP_VERSION, OPENAI_API_KEY, SENTRY_DSN, ENVIRONMENT
import os
import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Optional
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

# Initialize Sentry
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        traces_sample_rate=1.0 if ENVIRONMENT == "development" else 0.1,
        profiles_sample_rate=1.0 if ENVIRONMENT == "development" else 0.1,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        release=f"{APP_NAME}@{APP_VERSION}",
        # Set custom tags
        before_send=lambda event, hint: event,
    )


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="SazónBot - Mexican Recipe Assistant with Session Support"
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://sazonbot.vercel.app",  # Update after deploying
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate limiting ----------------------------------------------------
# Every chat message costs OpenAI credits, so cap how many any single
# caller can send. This lives in memory: it resets whenever Render
# restarts or spins the instance down, and each instance counts on its
# own. Good enough to stop casual abuse, not a hard security boundary.
MAX_REQUESTS_PER_MINUTE = 10
MAX_REQUESTS_PER_DAY = 100
MAX_MESSAGE_LENGTH = 1000

_request_log: Dict[str, List[float]] = defaultdict(list)
_rate_limit_lock = Lock()


def get_client_ip(request: Request) -> str:
    """Find the real caller's IP.

    Render puts a proxy in front of the app, so request.client.host is the
    proxy, not the user. The original IP is the first entry of
    X-Forwarded-For.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(client_ip: str) -> None:
    """Raise 429 if this IP has sent too many messages. Call before any work."""
    now = time.time()
    one_minute_ago = now - 60
    one_day_ago = now - 86400

    with _rate_limit_lock:
        # Forget anything older than a day so the log cannot grow forever
        for ip in list(_request_log.keys()):
            _request_log[ip] = [t for t in _request_log[ip] if t > one_day_ago]
            if not _request_log[ip]:
                del _request_log[ip]

        timestamps = _request_log[client_ip]
        recent = [t for t in timestamps if t > one_minute_ago]

        if len(recent) >= MAX_REQUESTS_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail="¡Espérate! You are sending messages too fast. Please wait a minute."
            )

        if len(timestamps) >= MAX_REQUESTS_PER_DAY:
            raise HTTPException(
                status_code=429,
                detail="¡Ay! You have reached the daily limit. Come back tomorrow, cariño."
            )

        timestamps.append(now)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    session_id: Optional[str] = Field(default=None, max_length=100)

class ChatResponse(BaseModel):
    response: str
    tools_used: list = []
    session_id: str

class ClearMemoryRequest(BaseModel):
    session_id: str

@app.get("/")
def read_root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "openai_configured": bool(OPENAI_API_KEY),
        "session_support": True,
        "sentry_enabled": bool(SENTRY_DSN),
        "environment": ENVIRONMENT
    }

@app.post("/agent-chat", response_model=ChatResponse)
def agent_chat(request: ChatRequest, http_request: Request):
    # Checked before the try block on purpose: the except below turns every
    # exception into a 500, which would swallow this 429.
    check_rate_limit(get_client_ip(http_request))

    try:
        # Add context to Sentry
        if SENTRY_DSN:
            sentry_sdk.set_context("chat_request", {
                "message_length": len(request.message),
                "has_session_id": bool(request.session_id)
            })
        
        agent = get_agent()
        result = agent.chat(request.message, session_id=request.session_id)
        
        # Clean up old sessions periodically
        agent.cleanup_old_sessions(max_sessions=100)
        
        return ChatResponse(
            response=result["response"],
            tools_used=result.get("tools_used", []),
            session_id=result["session_id"]
        )
    except Exception as e:
        # Sentry will automatically capture this
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clear-memory")
def clear_memory(request: ClearMemoryRequest):
    try:
        agent = get_agent()
        success = agent.clear_memory(request.session_id)
        
        if success:
            return {"status": "success", "message": "Conversation memory cleared"}
        else:
            return {"status": "not_found", "message": "Session not found"}
    except Exception as e:
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/sentry-test")
def sentry_test():
    """Test endpoint to verify Sentry is working"""
    if not SENTRY_DSN:
        return {"error": "Sentry not configured"}
    
    try:
        # Intentionally cause an error
        1 / 0
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return {"message": "Error sent to Sentry! Check your Sentry dashboard."}

@app.middleware("http")
async def add_sentry_context(request: Request, call_next):
    """Add request context to all Sentry events"""
    if SENTRY_DSN:
        sentry_sdk.set_context("request", {
            "url": str(request.url),
            "method": request.method,
            "headers": dict(request.headers),
        })
    
    response = await call_next(request)
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)