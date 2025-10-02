from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.agent import get_agent
from app.config import APP_NAME, APP_VERSION, OPENAI_API_KEY, SENTRY_DSN, ENVIRONMENT
import os
from typing import Optional
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

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

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
def agent_chat(request: ChatRequest):
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