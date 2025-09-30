from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

class RecipeSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for recipes", min_length=1)
    limit: Optional[int] = Field(3, description="Number of results to return", ge=1, le=10)

class RecipeSearchResult(BaseModel):
    content: str
    recipe_name: str
    similarity_score: float
    metadata: Dict[str, Any]

class RecipeSearchResponse(BaseModel):
    results: List[RecipeSearchResult]
    query: str
    total_results: int

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to the chatbot", min_length=1)

class ChatResponse(BaseModel):
    response: str
    sources_used: List[str]