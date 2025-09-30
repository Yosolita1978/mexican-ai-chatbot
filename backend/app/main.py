from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from app.config import APP_NAME, APP_VERSION, OPENAI_API_KEY
from app.models import HealthResponse, RecipeSearchRequest, RecipeSearchResponse, ChatRequest
from app.vector_store import search_recipes, format_search_results_for_chat, get_vector_store_info

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print(f"🚀 Starting {APP_NAME} v{APP_VERSION}")
    print("=" * 50)
    print(f"✅ OpenAI API Key: {'Configured' if OPENAI_API_KEY else 'Missing'}")
    
    vector_info = get_vector_store_info()
    if vector_info["exists"]:
        print(f"✅ Vector Store: {vector_info['message']}")
    else:
        print(f"⚠️  Vector Store: {vector_info['message']}")
    
    print(f"📚 Server running at: http://localhost:8000")
    print(f"📖 API Documentation: http://localhost:8000/docs")
    print(f"🔍 Alternative Docs: http://localhost:8000/redoc")
    print("=" * 50)
    
    yield
    
    print("=" * 50)
    print(f"👋 Shutting down {APP_NAME}")
    print("=" * 50)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered Mexican recipe chatbot with grandmother's authentic recipes",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(
        status="healthy",
        message=f"Welcome to {APP_NAME}! Visit /docs for API documentation.",
        version=APP_VERSION
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="Server is running and ready to serve recipes!",
        version=APP_VERSION
    )

@app.get("/test/config")
async def test_config():
    vector_info = get_vector_store_info()
    
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "openai_configured": bool(OPENAI_API_KEY),
        "vector_store_ready": vector_info["exists"],
        "vector_store_path": vector_info.get("path", "Not created yet"),
        "endpoints_available": [
            "/health",
            "/docs",
            "/test/config",
            "/search-recipes",
            "/chat-search/{query}"
        ]
    }

@app.post("/search-recipes", response_model=RecipeSearchResponse)
async def search_recipes_endpoint(request: RecipeSearchRequest):
    """
    Search for recipes using semantic similarity search
    
    - **query**: Search query (e.g., "chicken soup", "fajitas", "dessert")
    - **limit**: Number of results to return (1-10, default: 3)
    """
    try:
        results = search_recipes(request.query, k=request.limit)
        
        return RecipeSearchResponse(
            results=results,
            query=request.query,
            total_results=len(results)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching recipes: {str(e)}"
        )

@app.get("/chat-search/{query}")
async def chat_search_endpoint(query: str, limit: int = 3):
    """
    Simple endpoint for chat interface - returns formatted text response
    
    - **query**: Search query
    - **limit**: Number of results (optional, default: 3)
    """
    try:
        results = search_recipes(query, k=limit)
        formatted_response = format_search_results_for_chat(results)
        
        return {
            "query": query,
            "response": formatted_response,
            "total_results": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching recipes: {str(e)}"
        )

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint for conversational recipe queries
    Returns formatted response ready for display
    """
    try:
        results = search_recipes(request.message, k=3)
        formatted_response = format_search_results_for_chat(results)
        
        sources = [r.get("recipe_name", "Unknown") for r in results]
        
        return {
            "response": formatted_response,
            "sources_used": sources
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )

@app.get("/recipes/types")
async def get_recipe_types():
    """Get available recipe types for filtering"""
    return {
        "types": [
            "chicken",
            "meat",
            "seafood",
            "soup",
            "dessert",
            "sauce",
            "beverage",
            "general"
        ]
    }

@app.get("/recipes/search-by-type/{recipe_type}")
async def search_by_type(recipe_type: str, query: str = "", limit: int = 5):
    """
    Search recipes filtered by type
    
    - **recipe_type**: Type of recipe (chicken, soup, dessert, etc.)
    - **query**: Optional search query within that type
    - **limit**: Number of results
    """
    try:
        if query:
            results = search_recipes(query, k=limit, recipe_type=recipe_type)
        else:
            results = search_recipes(recipe_type, k=limit, recipe_type=recipe_type)
        
        formatted_response = format_search_results_for_chat(results)
        
        return {
            "recipe_type": recipe_type,
            "query": query,
            "response": formatted_response,
            "total_results": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching by type: {str(e)}"
        )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "The requested endpoint does not exist. Visit /docs for available endpoints."
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Something went wrong. Please try again later."
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )