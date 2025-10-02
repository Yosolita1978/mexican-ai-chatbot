from langchain.tools import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from typing import List, Dict, Optional
from app.vector_store import search_recipes, load_vector_store
from app.config import SERPER_API_KEY

# ============================================================================
# TIER 1: CORE TOOLS
# ============================================================================

def recipe_search_function(query: str) -> str:
    """
    Search the recipe database for relevant recipes.
    This is the wrapper function that LangChain will call.
    """
    try:
        results = search_recipes(query, k=3)
        
        if not results:
            return "No recipes found matching your query. Try different keywords or ask what recipes are available."
        
        # Format results for agent consumption
        formatted_results = []
        for i, result in enumerate(results, 1):
            recipe_name = result.get('recipe_name', 'Unknown Recipe')
            recipe_type = result.get('recipe_type', 'general')
            servings = result.get('servings')
            content_preview = result['content'][:300] + "..."
            
            formatted_results.append(
                f"{i}. **{recipe_name}** (Type: {recipe_type}, Servings: {servings})\n"
                f"   Preview: {content_preview}\n"
            )
        
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Error searching recipes: {str(e)}"


def recipe_list_by_type_function(recipe_type: str) -> str:
    """
    List all available recipes of a specific type.
    Returns just the names, not full content.
    """
    try:
        # Load vector store to access all documents
        vector_store = load_vector_store()
        
        # Get all documents with this type
        results = search_recipes(recipe_type, k=20, recipe_type=recipe_type)
        
        if not results:
            return f"No {recipe_type} recipes found. Available types: chicken, soup, dessert, beef, seafood, pork, pasta, sauce, beverage, rice, beans, vegetables."
        
        # Extract unique recipe names
        recipe_names = []
        seen_names = set()
        for result in results:
            name = result.get('recipe_name', 'Unknown')
            if name not in seen_names:
                recipe_names.append(name)
                seen_names.add(name)
        
        response = f"**{recipe_type.upper()} RECIPES** (Found {len(recipe_names)}):\n\n"
        response += "\n".join([f"• {name}" for name in recipe_names])
        
        return response
    except Exception as e:
        return f"Error listing recipes: {str(e)}"


def get_full_recipe_function(recipe_name: str) -> str:
    """
    Get the complete recipe by exact or close name match.
    """
    try:
        # Search using the recipe name
        results = search_recipes(recipe_name, k=1)
        
        if not results:
            return f"Recipe '{recipe_name}' not found. Try searching for similar recipes or list recipes by type first."
        
        result = results[0]
        recipe_name_found = result.get('recipe_name', 'Unknown Recipe')
        servings = result.get('servings')
        recipe_type = result.get('recipe_type', 'general')
        content = result['content']
        
        # Format the complete recipe
        response = f"**{recipe_name_found}**\n\n"
        response += f"*Type: {recipe_type}"
        if servings:
            response += f" | Servings: {servings}"
        response += "*\n\n"
        response += content
        
        return response
    except Exception as e:
        return f"Error retrieving recipe: {str(e)}"


def web_search_function(query: str) -> str:
    """
    Search the web for current information about Mexican food, recipes, ingredients, etc.
    """
    try:
        if not SERPER_API_KEY:
            return "Web search is not available. Serper API key is not configured."
        
        search = GoogleSerperAPIWrapper(serper_api_key=SERPER_API_KEY)
        results = search.run(query)
        
        if not results or results.strip() == "":
            return f"No web results found for: {query}"
        
        return f"**Web Search Results for '{query}':**\n\n{results}"
    except Exception as e:
        return f"Error searching the web: {str(e)}"


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

recipe_search_tool = Tool(
    name="recipe_search_tool",
    func=recipe_search_function,
    description="""Search the García family recipe database for Mexican recipes using semantic similarity. 
    Use this tool when the user asks about specific dishes (e.g., 'pozole', 'fajitas', 'chicken soup'), 
    ingredients (e.g., 'recipes with chicken', 'seafood dishes'), or general food queries (e.g., 'something spicy'). 
    Returns the top 3 most relevant recipes with previews. This is your PRIMARY tool for recipe queries.
    
    Input: A search query string (e.g., "chicken recipes", "pozole", "spicy soup")
    Output: List of matching recipes with names, types, and previews"""
)

recipe_list_by_type_tool = Tool(
    name="recipe_list_by_type_tool",
    func=recipe_list_by_type_function,
    description="""List all available recipes filtered by a specific type/category. 
    Use this when users want to browse or see all recipes in a category (e.g., "what chicken recipes do you have?", 
    "show me all desserts", "list your soups"). Returns ONLY recipe names, not full content.
    
    Available types: chicken, soup, dessert, beef, seafood, pork, pasta, sauce, beverage, rice, beans, vegetables
    
    Input: Recipe type as a string (e.g., "chicken", "soup", "dessert")
    Output: List of recipe names in that category"""
)

get_full_recipe_tool = Tool(
    name="get_full_recipe_tool",
    func=get_full_recipe_function,
    description="""Get the complete recipe with all ingredients and instructions by name. 
    Use this tool when you know the exact recipe name and need the full details, or when the user 
    explicitly asks for a specific recipe by name (e.g., "get me the pozole recipe", "show me Fajitas a la Vizcaína").
    Also use this AFTER listing recipes if the user picks one from the list.
    
    Input: Recipe name as a string (e.g., "Pozole Blanco", "Fajitas a la Vizcaína")
    Output: Complete recipe with ingredients and cooking instructions"""
)

web_search_tool = Tool(
    name="web_search_tool",
    func=web_search_function,
    description="""Search the web for current information about Mexican food, cooking, and recipes. 
    Use this tool for: recipe history and cultural context, cooking technique explanations, 
    ingredient information not in our database, food trends, nutritional information, 
    or when the user asks about topics beyond our recipe collection.
    DO NOT use this for searching our recipe database - use recipe_search_tool instead.
    
    Input: Search query string (e.g., "history of pozole", "what is piloncillo", "toasting dried chiles technique")
    Output: Web search results with relevant information"""
)

# Export all tools as a list for easy import
TIER_1_TOOLS = [
    recipe_search_tool,
    recipe_list_by_type_tool,
    get_full_recipe_tool,
    web_search_tool
]

# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_tools():
    """Test all Tier 1 tools individually"""
    print("=" * 60)
    print("TESTING TIER 1 TOOLS")
    print("=" * 60)
    
    # Test 1: Recipe Search
    print("\n1. Testing recipe_search_tool with 'chicken soup'")
    print("-" * 60)
    result = recipe_search_function("chicken soup")
    print(result)
    print()
    
    # Test 2: List by Type
    print("\n2. Testing recipe_list_by_type_tool with 'soup'")
    print("-" * 60)
    result = recipe_list_by_type_function("soup")
    print(result)
    print()
    
    # Test 3: Get Full Recipe
    print("\n3. Testing get_full_recipe_tool with 'Pozole Blanco'")
    print("-" * 60)
    result = get_full_recipe_function("Pozole Blanco")
    print(result[:500] + "...")
    print()
    
    # Test 4: Web Search
    print("\n4. Testing web_search_tool with 'history of pozole'")
    print("-" * 60)
    result = web_search_function("history of pozole")
    print(result[:500] + "...")
    print()
    
    print("=" * 60)
    print("✅ ALL TOOLS TESTED")
    print("=" * 60)


if __name__ == "__main__":
    test_tools()