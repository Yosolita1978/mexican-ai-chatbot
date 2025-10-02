import re
from typing import Dict, List, Tuple, Optional
from fractions import Fraction

def parse_ingredient(ingredient_line: str) -> Optional[Dict]:
    """
    Parse an ingredient line into quantity, unit, and ingredient.
    
    Examples:
        "2 cups chicken broth" -> {quantity: 2, unit: "cups", ingredient: "chicken broth"}
        "1/2 tsp salt" -> {quantity: 0.5, unit: "tsp", ingredient: "salt"}
        "3 chicken breasts" -> {quantity: 3, unit: "", ingredient: "chicken breasts"}
    """
    # Pattern: number (or fraction) + optional unit + ingredient
    pattern = r'^([\d\s/]+)?\s*(cups?|cup|tbsp?|tsp?|oz|lb|lbs|kg|g|ml|l|cloves?|pieces?|piezas?|dientes?)?\s*(.+)$'
    
    match = re.match(pattern, ingredient_line.strip(), re.IGNORECASE)
    
    if not match:
        return None
    
    quantity_str, unit, ingredient = match.groups()
    
    # Parse quantity (handle fractions)
    quantity = 1.0
    if quantity_str:
        try:
            # Handle fractions like "1/2" or "1 1/2"
            quantity_str = quantity_str.strip()
            if '/' in quantity_str:
                parts = quantity_str.split()
                total = 0
                for part in parts:
                    if '/' in part:
                        total += float(Fraction(part))
                    else:
                        total += float(part)
                quantity = total
            else:
                quantity = float(quantity_str)
        except:
            quantity = 1.0
    
    return {
        'quantity': quantity,
        'unit': unit.lower() if unit else '',
        'ingredient': ingredient.strip()
    }


def scale_ingredient(parsed_ingredient: Dict, scale_factor: float) -> str:
    """
    Scale an ingredient by the given factor and format back to string.
    """
    new_quantity = parsed_ingredient['quantity'] * scale_factor
    
    # Format the quantity nicely (remove .0 for whole numbers)
    if new_quantity.is_integer():
        quantity_str = str(int(new_quantity))
    else:
        quantity_str = f"{new_quantity:.2f}".rstrip('0').rstrip('.')
    
    unit = parsed_ingredient['unit']
    ingredient = parsed_ingredient['ingredient']
    
    if unit:
        return f"{quantity_str} {unit} {ingredient}"
    else:
        return f"{quantity_str} {ingredient}"


def extract_servings_from_recipe(recipe_text: str) -> Optional[int]:
    """
    Extract servings/porciones from recipe text.
    """
    pattern = r'(?:Porciones?|Servings?):\s*(\d+)'
    match = re.search(pattern, recipe_text, re.IGNORECASE)
    
    if match:
        return int(match.group(1))
    
    return None


def scale_recipe(recipe_text: str, target_servings: int) -> str:
    """
    Scale an entire recipe to target servings.
    This is a utility that will be used by the recipe_scale_tool.
    """
    # Extract current servings
    current_servings = extract_servings_from_recipe(recipe_text)
    
    if not current_servings:
        return "⚠️ Cannot scale recipe: servings information not found in recipe."
    
    if current_servings == target_servings:
        return f"Recipe is already for {target_servings} servings. No scaling needed."
    
    scale_factor = target_servings / current_servings
    
    # Find ingredients section
    ingredients_match = re.search(r'Ingredientes?:(.*?)(?:Modo de preparación|Preparación|$)', 
                                  recipe_text, re.IGNORECASE | re.DOTALL)
    
    if not ingredients_match:
        return "⚠️ Cannot scale recipe: ingredients section not found."
    
    ingredients_text = ingredients_match.group(1)
    ingredient_lines = [line.strip() for line in ingredients_text.split('\n') if line.strip()]
    
    # Scale each ingredient
    scaled_ingredients = []
    for line in ingredient_lines:
        parsed = parse_ingredient(line)
        if parsed:
            scaled_line = scale_ingredient(parsed, scale_factor)
            scaled_ingredients.append(f"• {scaled_line}")
        else:
            # If we can't parse it, keep it as-is
            scaled_ingredients.append(f"• {line}")
    
    # Build scaled recipe
    scaled_recipe = f"**SCALED RECIPE** (Original: {current_servings} servings → New: {target_servings} servings)\n\n"
    scaled_recipe += f"**Scale Factor: {scale_factor:.2f}x**\n\n"
    scaled_recipe += "**Scaled Ingredients:**\n"
    scaled_recipe += "\n".join(scaled_ingredients)
    scaled_recipe += "\n\n**Note:** Preparation instructions remain the same. Adjust cooking times if needed for larger/smaller quantities."
    
    return scaled_recipe


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test ingredient parsing
    test_ingredients = [
        "2 cups chicken broth",
        "1/2 tsp salt",
        "3 chicken breasts",
        "1 1/2 cups flour",
        "2 dientes de ajo"
    ]
    
    print("Testing Ingredient Parsing:")
    print("=" * 60)
    for ing in test_ingredients:
        parsed = parse_ingredient(ing)
        print(f"Input: {ing}")
        print(f"Parsed: {parsed}")
        if parsed:
            scaled = scale_ingredient(parsed, 2.0)
            print(f"Scaled 2x: {scaled}")
        print()
    
    # Test recipe scaling
    sample_recipe = """
    Receta: Pozole Blanco
    
    Porciones: 4
    
    Ingredientes:
    2 cups chicken broth
    1/2 tsp salt
    3 chicken breasts
    1 cup hominy
    
    Modo de preparación:
    1. Cook chicken
    2. Add ingredients
    """
    
    print("\nTesting Recipe Scaling:")
    print("=" * 60)
    print("Original servings: 4")
    print("Target servings: 8")
    print()
    scaled = scale_recipe(sample_recipe, 8)
    print(scaled)