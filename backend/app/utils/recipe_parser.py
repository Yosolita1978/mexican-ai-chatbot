import re
from typing import Dict, List, Tuple, Optional
from fractions import Fraction

# Spanish number words used in the recipe PDF. Values are floats so that
# fractions like "medio" work the same way as whole numbers.
SPANISH_NUMBERS = {
    'medio': 0.5, 'media': 0.5,
    'un': 1.0, 'una': 1.0, 'uno': 1.0,
    'dos': 2.0, 'tres': 3.0, 'cuatro': 4.0, 'cinco': 5.0,
    'seis': 6.0, 'siete': 7.0, 'ocho': 8.0, 'nueve': 9.0,
    'diez': 10.0, 'once': 11.0, 'doce': 12.0, 'docena': 12.0,
    'trece': 13.0, 'catorce': 14.0, 'quince': 15.0,
    'veinte': 20.0,
}

UNIT_PATTERN = (
    r'cups?|tbsp?|tsp|oz|lb|lbs|kg|g|ml|l|'
    r'cucharadas?|cucharaditas?|tazas?|gramos?|kilos?|litros?|'
    r'cloves?|pieces?|piezas?|dientes?|latas?|manojos?|pizcas?'
)


def parse_ingredient(ingredient_line: str) -> Optional[Dict]:
    """
    Parse an ingredient line into quantity, unit, and ingredient.

    Handles digits ("2 cups broth"), fractions ("1/2 tsp salt") and the
    Spanish number words used in this recipe collection ("Una pechuga",
    "Cuatro o cinco tomates").

    When no quantity is present at all ("Sal y pimienta al gusto"),
    'quantity' is None. Those lines must not be scaled.

    Returns None only if the line is empty.
    """
    line = ingredient_line.strip()
    if not line:
        return None

    quantity, rest = _extract_quantity(line)

    # Pull off a unit if one directly follows the quantity.
    unit = ''
    unit_match = re.match(rf'^({UNIT_PATTERN})\b\.?\s+(.*)$', rest, re.IGNORECASE)
    if unit_match:
        unit = unit_match.group(1).lower()
        rest = unit_match.group(2)

    return {
        'quantity': quantity,
        'unit': unit,
        'ingredient': rest.strip(),
    }


def _extract_quantity(line: str) -> Tuple[Optional[float], str]:
    """
    Read a leading quantity off an ingredient line.

    Returns (quantity, remaining_text). quantity is None when the line does
    not start with a number in digits or in Spanish words.

    A range like "cuatro o cinco tomates" is reduced to its lower bound so
    the result stays a single scalable number.
    """
    # Digits and fractions: "2", "1/2", "1 1/2"
    digit_match = re.match(r'^(\d+(?:\s+\d+)?\s*/\s*\d+|\d+(?:[.,]\d+)?)\s*(.*)$', line)
    if digit_match:
        quantity_str, rest = digit_match.group(1), digit_match.group(2)
        try:
            if '/' in quantity_str:
                total = 0.0
                for part in quantity_str.split():
                    total += float(Fraction(part)) if '/' in part else float(part)
                return total, rest
            return float(quantity_str.replace(',', '.')), rest
        except (ValueError, ZeroDivisionError):
            return None, line

    # Spanish number words, optionally a range: "cuatro o cinco"
    word_match = re.match(r'^(\w+)(?:\s+o\s+(\w+))?\s+(.*)$', line, re.UNICODE)
    if word_match:
        first = word_match.group(1).lower()
        if first in SPANISH_NUMBERS:
            rest = word_match.group(3)
            second = word_match.group(2)
            # "cuatro o cinco" -> keep the lower bound, drop the alternative
            if second and second.lower() in SPANISH_NUMBERS:
                return SPANISH_NUMBERS[first], rest
            # The second word was not a number, so "o ..." belongs to the text
            if second:
                rest = f"o {second} {rest}"
            return SPANISH_NUMBERS[first], rest

    return None, line


def scale_ingredient(parsed_ingredient: Dict, scale_factor: float) -> str:
    """
    Scale an ingredient by the given factor and format back to string.

    Ingredients with no quantity ("al gusto") are returned untouched.
    """
    quantity = parsed_ingredient['quantity']
    unit = parsed_ingredient['unit']
    ingredient = parsed_ingredient['ingredient']

    if quantity is None:
        return " ".join(part for part in (unit, ingredient) if part)

    new_quantity = quantity * scale_factor

    if float(new_quantity).is_integer():
        quantity_str = str(int(new_quantity))
    else:
        quantity_str = f"{new_quantity:.2f}".rstrip('0').rstrip('.')

    parts = [quantity_str]
    if unit:
        parts.append(unit)
    if ingredient:
        parts.append(ingredient)
    return " ".join(parts)


def split_ingredients(ingredients_text: str) -> List[str]:
    """
    Split an ingredients block into one entry per ingredient.

    The recipe PDF separates ingredients with "-" bullets rather than line
    breaks, and the stored chunks collapse whitespace, so splitting on "\\n"
    alone yields a single giant ingredient. Split on bullets and newlines.
    """
    parts = re.split(r'(?:^|\s)[-•*]\s+|\n', ingredients_text)
    return [part.strip(' -•*\t') for part in parts if part and part.strip(' -•*\t')]


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

    ingredient_lines = split_ingredients(ingredients_match.group(1))

    # Scale each ingredient
    scaled_ingredients = []
    unscaled_count = 0
    for line in ingredient_lines:
        parsed = parse_ingredient(line)
        if parsed:
            if parsed['quantity'] is None:
                unscaled_count += 1
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
    if unscaled_count:
        scaled_recipe += f"\n\n**Heads up:** {unscaled_count} ingredient(s) had no stated amount (e.g. \"al gusto\") and were left unchanged."

    return scaled_recipe
