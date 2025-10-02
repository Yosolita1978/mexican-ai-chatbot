from langchain.tools import Tool, StructuredTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from typing import List, Dict, Optional
import re
import requests
from app.vector_store import search_recipes, load_vector_store
from app.config import SERPER_API_KEY, PUSHOVER_USER, PUSHOVER_TOKEN
from app.utils.recipe_parser import scale_recipe, extract_servings_from_recipe
from pydantic import BaseModel, Field

def recipe_search_function(query: str) -> str:
    try:
        results = search_recipes(query, k=3)
        
        if not results:
            return "No recipes found matching your query. Try different keywords or ask what recipes are available."
        
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
    try:
        vector_store = load_vector_store()
        results = search_recipes(recipe_type, k=20, recipe_type=recipe_type)
        
        if not results:
            return f"No {recipe_type} recipes found. Available types: chicken, soup, dessert, beef, seafood, pork, pasta, sauce, beverage, rice, beans, vegetables."
        
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
    try:
        results = search_recipes(recipe_name, k=1)
        
        if not results:
            return f"Recipe '{recipe_name}' not found. Try searching for similar recipes or list recipes by type first."
        
        result = results[0]
        recipe_name_found = result.get('recipe_name', 'Unknown Recipe')
        servings = result.get('servings')
        recipe_type = result.get('recipe_type', 'general')
        content = result['content']
        
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


class RecipeScaleInput(BaseModel):
    recipe_text: str = Field(description="The complete recipe text to scale")
    target_servings: int = Field(description="The target number of servings")

def recipe_scale_function_structured(recipe_text: str, target_servings: int) -> str:
    try:
        if not recipe_text or not recipe_text.strip():
            return "Error: No recipe provided to scale. Please provide the full recipe text first."
        
        if target_servings <= 0:
            return "Error: Target servings must be a positive number."
        
        scaled_result = scale_recipe(recipe_text, target_servings)
        return scaled_result
        
    except Exception as e:
        return f"Error scaling recipe: {str(e)}"


def ingredient_substitution_function(ingredient: str, reason: str = "") -> str:
    try:
        if not SERPER_API_KEY:
            return "Substitution lookup is not available without web search. However, common substitutions: cilantro → parsley, epazote → oregano, tomatillos → green tomatoes."
        
        search_query = f"substitute for {ingredient} in Mexican cooking"
        if reason:
            search_query += f" {reason}"
        
        search = GoogleSerperAPIWrapper(serper_api_key=SERPER_API_KEY)
        results = search.run(search_query)
        
        if not results or results.strip() == "":
            return f"Could not find substitution info for '{ingredient}'. Common Mexican ingredient substitutes: cilantro → parsley, epazote → oregano, Mexican oregano → regular oregano, tomatillos → green tomatoes + lime."
        
        return f"**Substitutes for {ingredient}:**\n\n{results}"
        
    except Exception as e:
        return f"Error finding substitutes: {str(e)}"


def cooking_technique_function(technique: str) -> str:
    try:
        if not SERPER_API_KEY:
            return f"Technique lookup requires web search. I can explain basic techniques from memory - what would you like to know about {technique}?"
        
        search_query = f"how to {technique} Mexican cooking technique"
        
        search = GoogleSerperAPIWrapper(serper_api_key=SERPER_API_KEY)
        results = search.run(search_query)
        
        if not results or results.strip() == "":
            return f"Could not find detailed info about '{technique}'. Try asking more specifically, like 'how do I toast chiles' or 'what is sofrito'."
        
        return f"**How to: {technique}**\n\n{results}"
        
    except Exception as e:
        return f"Error looking up technique: {str(e)}"


def recipe_filter_by_criteria_function(criteria: str) -> str:
    try:
        criteria_lower = criteria.lower()
        
        recipe_type = None
        types = ['chicken', 'soup', 'dessert', 'beef', 'seafood', 'pork', 'pasta', 'sauce', 'beverage', 'rice', 'beans', 'vegetables']
        for t in types:
            if t in criteria_lower:
                recipe_type = t
                break
        
        if recipe_type:
            results = search_recipes(criteria, k=10, recipe_type=recipe_type)
        else:
            results = search_recipes(criteria, k=10)
        
        if not results:
            return f"No recipes found matching criteria: {criteria}. Try broader search terms."
        
        recipe_names = []
        seen_names = set()
        for result in results:
            name = result.get('recipe_name', 'Unknown')
            if name not in seen_names:
                servings = result.get('servings', 'Unknown')
                recipe_type_found = result.get('recipe_type', 'general')
                recipe_names.append(f"• {name} ({recipe_type_found}, serves {servings})")
                seen_names.add(name)
        
        response = f"**Recipes matching '{criteria}'** (Found {len(recipe_names)}):\n\n"
        response += "\n".join(recipe_names)
        response += "\n\nWould you like the full recipe for any of these?"
        
        return response
        
    except Exception as e:
        return f"Error filtering recipes: {str(e)}"


def video_search_function(query: str) -> str:
    try:
        if not SERPER_API_KEY:
            return "Video search is not available. Serper API key is not configured."
        
        video_query = f"{query} recipe cooking tutorial how to make"
        
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'q': video_query,
            'num': 3
        }
        
        response = requests.post(
            'https://google.serper.dev/videos',
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            return "Could not fetch videos right now. Would you like me to explain the recipe steps instead?"
        
        data = response.json()
        videos = data.get('videos', [])
        
        if not videos:
            return f"No cooking videos found for: {query}. Would you like the written recipe instead?"
        
        result_lines = []
        
        video_count = 0
        for video in videos[:3]:
            link = video.get('link', '')
            
            youtube_id = None
            if 'youtube.com/watch?v=' in link:
                youtube_id = link.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in link:
                youtube_id = link.split('youtu.be/')[1].split('?')[0]
            
            if youtube_id and len(youtube_id) == 11:
                result_lines.append(f"- VIDEO:{youtube_id}")
                video_count += 1
        
        if video_count == 0:
            return f"Found some videos but couldn't embed them. Would you like the written recipe instead?"
        
        return "\n".join(result_lines)
        
    except requests.Timeout:
        return "Video search timed out. Let me give you the written recipe instead!"
    except Exception as e:
        # print(f"Video search error: {str(e)}")
        return "Having trouble finding videos right now. Would you like me to walk you through the recipe steps instead?"


def image_search_function(query: str) -> str:
    try:
        if not SERPER_API_KEY:
            return "Image search is not available. Serper API key is not configured."
        
        image_query = f"{query} Mexican food cooking"
        
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'q': image_query,
            'num': 3
        }
        
        response = requests.post(
            'https://google.serper.dev/images',
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            return "Could not fetch images right now. Try describing what you're looking for instead."
        
        data = response.json()
        images = data.get('images', [])
        
        if not images:
            return f"No images found for: {query}. Try different search terms."
        
        result_lines = []
        
        image_count = 0
        for img in images[:3]:
            image_url = img.get('imageUrl', '')
            if image_url:
                result_lines.append(f"![Image {image_count + 1}]({image_url})")
                image_count += 1
        
        if image_count == 0:
            return f"Found some images but couldn't display them. Try searching online for '{query}'."
        
        return "\n".join(result_lines)
        
    except requests.Timeout:
        return "Image search timed out. Try describing what you're looking for instead."
    except Exception as e:
        # print(f"Image search error: {str(e)}")
        return "Having trouble finding images right now. Can I help you in another way?"


def record_unknown_question_function(question: str) -> str:
    try:
        if not PUSHOVER_USER or not PUSHOVER_TOKEN:
            # print(f"⚠️ Unanswered question (Pushover not configured): {question}")
            return "Question recorded locally (notification system not configured)."
        
        payload = {
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": f"Unanswered question from SazónBot:\n\n{question}",
            "title": "SazónBot - Unanswered Question",
            "priority": 0,
        }
        
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            # print(f"✅ Pushover notification sent for question: {question}")
            return "Question recorded and notification sent successfully."
        else:
            # print(f"⚠️ Pushover failed ({response.status_code}): {question}")
            return "Question recorded but notification failed."
        
    except Exception as e:
        # print(f"❌ Error recording question: {str(e)}")
        return f"Error recording question: {str(e)}"


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

recipe_scale_tool = StructuredTool.from_function(
    func=recipe_scale_function_structured,
    name="recipe_scale_tool",
    description="""Scale a recipe to a different number of servings. 
    Use this when the user wants to adjust recipe quantities (e.g., "make this for 12 people", 
    "I only need half the recipe", "scale to 6 servings"). 
    IMPORTANT: You must provide the FULL recipe text, not just the recipe name.
    First get the full recipe using get_full_recipe_tool, then scale it.
    
    Input: recipe_text (string - the complete recipe content) and target_servings (integer - number of servings)
    Output: Scaled recipe with adjusted ingredient quantities""",
    args_schema=RecipeScaleInput,
)

ingredient_substitution_tool = Tool(
    name="ingredient_substitution_tool",
    func=ingredient_substitution_function,
    description="""Find substitutes for ingredients in Mexican cooking.
    Use when users ask about replacing ingredients due to allergies, availability, or dietary preferences
    (e.g., "can I use chicken stock instead of water?", "I'm allergic to cilantro", "no epazote available").
    
    Input: ingredient name, optional reason for substitution
    Output: Suggested substitutes with explanations"""
)

cooking_technique_tool = Tool(
    name="cooking_technique_tool",
    func=cooking_technique_function,
    description="""Explain Mexican cooking techniques and methods.
    Use when users ask HOW to do something in cooking (e.g., "how do I toast dried chiles?", 
    "what is sofrito?", "how to properly cook pozole?", "technique for making salsa").
    
    Input: Technique or method name
    Output: Detailed explanation of the technique"""
)

recipe_filter_by_criteria_tool = Tool(
    name="recipe_filter_by_criteria_tool",
    func=recipe_filter_by_criteria_function,
    description="""Filter recipes by complex criteria like cooking time, difficulty, or ingredients to avoid.
    Use for complex searches with multiple requirements (e.g., "quick recipes under 30 minutes", 
    "easy soups for beginners", "recipes without dairy", "vegetarian options").
    
    Input: Criteria description as natural language
    Output: List of recipes matching the criteria"""
)

video_search_tool = Tool(
    name="video_search_tool",
    func=video_search_function,
    description="""Search for cooking videos and video tutorials on YouTube.
    Use when users want to SEE how something is made, ask for video demonstrations,
    or use words like "show me", "video", "watch", "tutorial" (e.g., "show me a video on making pozole", 
    "video tutorial for tamales", "I want to watch how to make salsa").
    Returns YouTube video embeds that will appear directly in the chat.
    CRITICAL: Return the tool output EXACTLY as provided - DO NOT reformat VIDEO: markers.
    
    Input: Recipe or technique name
    Output: Embedded YouTube videos in format: - VIDEO:XXXXX"""
)

image_search_tool = Tool(
    name="image_search_tool",
    func=image_search_function,
    description="""Search for food and ingredient images.
    Use when users want to SEE what something looks like, ask for pictures or photos,
    or use words like "show me an image", "what does it look like", "picture of", "imagen de" 
    (e.g., "show me a picture of bistec en bola", "what does epazote look like", "image of pozole").
    Returns images that will display directly in the chat.
    CRITICAL: Return the tool output EXACTLY as provided - DO NOT reformat image markdown.
    
    Input: Food item, ingredient, or dish name
    Output: Images in markdown format: ![Image](url)"""
)

record_unknown_question_tool = Tool(
    name="record_unknown_question_tool",
    func=record_unknown_question_function,
    description="""Record questions that you cannot answer about Mexican food or cooking.
    Use this ONLY when you genuinely don't know the answer to a food/cooking question, 
    couldn't find it in recipes, and web search didn't help either.
    This sends a notification to track knowledge gaps.
    DO NOT use this for off-topic questions (politics, etc.) - only for legitimate food questions you can't answer.
    
    Input: The question that couldn't be answered
    Output: Confirmation that the question was recorded"""
)

ALL_TOOLS = [
    recipe_search_tool,
    recipe_list_by_type_tool,
    get_full_recipe_tool,
    web_search_tool,
    recipe_scale_tool,
    ingredient_substitution_tool,
    cooking_technique_tool,
    recipe_filter_by_criteria_tool,
    video_search_tool,
    image_search_tool,
    record_unknown_question_tool,
]

TIER_1_TOOLS = ALL_TOOLS

if __name__ == "__main__":
    pass