from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
import os
import re
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

VECTOR_STORE_PATH = os.path.join(PROJECT_ROOT, "data", "recipe_vectors")
RECIPE_PDF_PATH = os.path.join(PROJECT_ROOT, "data", "recipes.pdf")

# The loaded FAISS index, kept in memory so every search does not re-read it
_vector_store_cache = None

def load_pdf_recipes(file_path: str = RECIPE_PDF_PATH):
    """Load recipes from PDF file using LangChain's PyPDFLoader"""
    #print(f"📄 Loading recipes from {file_path}...")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Recipe PDF not found at {file_path}")
    
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    
    #print(f"✅ Loaded {len(documents)} pages from PDF")
    
    return documents

# Recipe types are decided by the recipe NAME first, in most-specific-first
# order, and only fall back to the ingredient text when the name says nothing.
# The old version checked content early, so "caldo de pollo" appearing in the
# ingredients of a vegetable dish was enough to file it under chicken, and
# broad words like "carne" claimed pork and tuna dishes before their own
# rules ever ran.
RECIPE_TYPE_NAME_RULES = [
    ("dessert",    ["postre", "dulce", "pastel", "flan", "galleta", "pay", "gelatina"]),
    ("beverage",   ["bebida", "agua", "licuado", "atole", "té"]),
    # "sopa de pasta" is a soup, so soup is checked before pasta.
    ("soup",       ["sopa", "caldo", "pozole", "consomé", "mole de olla"]),
    ("rice",       ["arroz"]),
    ("beans",      ["enfrijoladas", "frijol"]),
    ("pasta",      ["pasta", "spaghetti", "spaguetti", "fusilli", "codito", "tornillo"]),
    # Proteins before "carne"/"picadillo", which would otherwise claim them.
    ("seafood",    ["pescado", "atún", "atun", "ceviche", "bacalao"]),
    ("pork",       ["puerco", "cerdo"]),
    ("chicken",    ["pollo", "pollito", "pechuga", "tinga", "fajitas"]),
    ("beef",       ["bistec", "carne", "albondigas", "picadillo"]),
    ("vegetables", ["acelgas", "verduras", "nopales", "verdolagas"]),
    # A dish "en salsa verde" is named after its sauce but is not one, so this
    # runs last and only catches recipes no protein rule claimed.
    ("sauce",      ["salsa", "guacamole", "pico de gallo"]),
]

RECIPE_TYPE_CONTENT_RULES = [
    ("chicken", ["pollo", "pechuga"]),
    ("pork",    ["carne de puerco", "maciza"]),
    ("seafood", ["pescado", "atún", "filete"]),
    ("beef",    ["carne de res", "molida de res"]),
]


def classify_recipe_type(recipe_name: str, text: str) -> str:
    """Work out a recipe's type from its name, falling back to its contents."""
    name_lower = recipe_name.lower()
    for recipe_type, keywords in RECIPE_TYPE_NAME_RULES:
        if any(word in name_lower for word in keywords):
            return recipe_type

    content_lower = text.lower()
    for recipe_type, keywords in RECIPE_TYPE_CONTENT_RULES:
        if any(word in content_lower for word in keywords):
            return recipe_type

    return "general"


def extract_recipe_metadata(text: str) -> Dict:
    """Extract structured metadata from recipe text"""
    metadata = {
        "recipe_name": "Unknown Recipe",
        "servings": None,
        "has_ingredients": False,
        "has_instructions": False,
        "recipe_type": "general"
    }
    
    recipe_name = None
    
    receta_pattern = r'Receta:\s*([A-ZÁÉÍÓÚÑ\(\)\s]+?)(?:\n|Porciones)'
    receta_match = re.search(receta_pattern, text, re.IGNORECASE)
    if receta_match:
        recipe_name = receta_match.group(1).strip()
    
    if not recipe_name or recipe_name == "":
        lines = text.split('\n')
        for line in lines[:10]:
            cleaned_line = line.strip()
            if cleaned_line.startswith('Receta:'):
                recipe_name = cleaned_line.replace('Receta:', '').strip()
                break
    
    if recipe_name:
        recipe_name = ' '.join(recipe_name.split())
        recipe_name = recipe_name.replace('*', '').strip()
        recipe_name = re.sub(r'^[^\w\s\(\)]+|[^\w\s\(\)]+$', '', recipe_name)
        
        if recipe_name and len(recipe_name) > 2:
            metadata["recipe_name"] = recipe_name
    
    servings_pattern = r'Porciones?:\s*(\d+)'
    servings_match = re.search(servings_pattern, text, re.IGNORECASE)
    if servings_match:
        metadata["servings"] = int(servings_match.group(1))
    
    if re.search(r'Ingredientes?:', text, re.IGNORECASE):
        metadata["has_ingredients"] = True
    
    if re.search(r'Modo de preparaci[oó]n|Preparaci[oó]n|Instrucciones', text, re.IGNORECASE):
        metadata["has_instructions"] = True
    
    metadata["recipe_type"] = classify_recipe_type(metadata["recipe_name"], text)
    
    return metadata

def debug_recipe_extraction():
    """Debug which recipes are failing to extract names"""
    documents = load_pdf_recipes()
    
    all_text = "\n".join([doc.page_content for doc in documents])
    
    recipe_pattern = r'Receta:\s*[A-ZÁÉÍÓÚÑ\(\)\s]+'
    
    matches = list(re.finditer(recipe_pattern, all_text, re.IGNORECASE))
    
    print(f"\n🔍 Found {len(matches)} 'Receta:' occurrences")
    print("\nFirst 15 recipe name extractions:")
    print("=" * 60)
    
    for i, match in enumerate(matches[:15]):
        start = match.start()
        end = min(match.end() + 150, len(all_text))
        context = all_text[start:end]
        
        receta_pattern = r'Receta:\s*([A-ZÁÉÍÓÚÑ\(\)\s]+?)(?:\n|Porciones)'
        name_match = re.search(receta_pattern, context, re.IGNORECASE)
        
        if name_match:
            name = name_match.group(1).strip()
            print(f"\n{i+1}. ✅ Extracted: '{name}'")
        else:
            print(f"\n{i+1}. ❌ FAILED to extract")
            print(f"   Context: {context}")
    
    print("\n" + "=" * 60)
    
    print("\n\nNow testing full recipe parsing:")
    recipes = parse_recipes_from_pdf(documents)
    
    unknown = [r for r in recipes if r["metadata"]["recipe_name"] == "Unknown Recipe"]
    if unknown:
        print(f"\n⚠️  Found {len(unknown)} recipes with 'Unknown Recipe'")
        print("\nFirst unknown recipe full text:")
        print("=" * 60)
        print(unknown[0]["text"][:500])
        print("=" * 60)

def parse_recipes_from_pdf(documents):
    """Parse PDF documents and extract individual recipes with metadata"""
    #print("🔍 Parsing recipes and extracting metadata...")
    
    all_text = "\n".join([doc.page_content for doc in documents])
    
    recipe_pattern = r'Receta:\s*[A-ZÁÉÍÓÚÑ\(\)\s]+'
    
    recipe_starts = []
    for match in re.finditer(recipe_pattern, all_text, re.IGNORECASE):
        recipe_starts.append(match.start())
    
    recipes = []
    
    if len(recipe_starts) > 1:
        for i in range(len(recipe_starts)):
            start = recipe_starts[i]
            end = recipe_starts[i + 1] if i + 1 < len(recipe_starts) else len(all_text)
            recipe_text = all_text[start:end].strip()
            
            if len(recipe_text) > 150 and "Ingredientes" in recipe_text:
                metadata = extract_recipe_metadata(recipe_text)
                recipes.append({
                    "text": recipe_text,
                    "metadata": metadata
                })
    else:
        for i, doc in enumerate(documents):
            if i == 0:
                continue
            metadata = extract_recipe_metadata(doc.page_content)
            metadata["page"] = doc.metadata.get("page", i)
            recipes.append({
                "text": doc.page_content,
                "metadata": metadata
            })
    
    #print(f"✅ Extracted {len(recipes)} recipes with metadata")
    
    unknown_count = sum(1 for r in recipes if r["metadata"]["recipe_name"] == "Unknown Recipe")
    if unknown_count > 0:
        print(f"⚠️  Warning: {unknown_count} recipes still have 'Unknown Recipe' as name")
    else:
        print(f"🎉 All recipe names extracted successfully!")
    
    # if recipes:
    #     #print(f"\n📋 Sample recipe metadata:")
    #     sample = recipes[0]["metadata"]
    #     for key, value in sample.items():
    #         #print(f"   - {key}: {value}")
    
    return recipes

def create_recipe_chunks(recipes: List[Dict]):
    """Split recipes into optimal chunks while preserving metadata and cleaning text"""
    #print("✂️  Splitting recipes into chunks...")
    
    cleaned_recipes = []
    for recipe in recipes:
        text = recipe["text"]
        text = ' '.join(text.split())
        text = text.replace(' Ingredientes: ', '\n\nIngredientes:\n')
        text = text.replace(' Modo de preparación ', '\n\nModo de preparación:\n')
        text = text.replace(' Porciones: ', '\n\nPorciones: ')
        text = text.replace(' Receta: ', '\n\nReceta: ')
        
        cleaned_recipes.append({
            "text": text,
            "metadata": recipe["metadata"]
        })
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    all_chunks = []
    
    for recipe in cleaned_recipes:
        chunks = text_splitter.split_text(recipe["text"])
        
        for i, chunk in enumerate(chunks):
            metadata = recipe["metadata"].copy()
            metadata["chunk_index"] = i
            metadata["total_chunks"] = len(chunks)
            
            doc = Document(
                page_content=chunk,
                metadata=metadata
            )
            all_chunks.append(doc)
    
    #print(f"✅ Created {len(all_chunks)} chunks with metadata")
    
    return all_chunks

def create_vector_store():
    """Create and save FAISS vector store from recipe PDF"""
    #print("=" * 50)
    #print("🚀 Creating Enhanced Vector Store from PDF")
    #print("=" * 50)
    
    documents = load_pdf_recipes()
    recipes = parse_recipes_from_pdf(documents)
    chunks = create_recipe_chunks(recipes)
    
    #print("🧠 Creating embeddings and building vector store...")
    #print("   (This may take a minute...)")
    
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    os.makedirs(os.path.dirname(VECTOR_STORE_PATH), exist_ok=True)
    vector_store.save_local(VECTOR_STORE_PATH)
    
    # Rebuilding replaces whatever load_vector_store() may already be holding
    global _vector_store_cache
    _vector_store_cache = vector_store
    
    #print(f"💾 Vector store saved to {VECTOR_STORE_PATH}/")
    #print("=" * 50)
    
    return vector_store

def load_vector_store():
    """Load the FAISS vector store, reusing it after the first load.

    This used to read the index off disk and rebuild the embeddings client on
    every single recipe search. The index does not change while the app is
    running, so we keep one copy in memory - the same way get_agent() keeps
    one agent.
    """
    global _vector_store_cache

    if _vector_store_cache is not None:
        return _vector_store_cache

    embeddings = OpenAIEmbeddings()

    if os.path.exists(VECTOR_STORE_PATH):
        #print(f"📂 Loading existing vector store from {VECTOR_STORE_PATH}/")
        _vector_store_cache = FAISS.load_local(
            VECTOR_STORE_PATH, 
            embeddings,
            allow_dangerous_deserialization=True
        )
        #print("✅ Vector store loaded successfully")
    else:
        #print(f"⚠️  No existing vector store found at {VECTOR_STORE_PATH}/")
        #print("🔨 Creating new vector store...")
        _vector_store_cache = create_vector_store()

    return _vector_store_cache

def get_available_recipe_types() -> List[str]:
    """
    List the recipe types actually present in the index.

    The tools used to advertise a hardcoded list that included types no
    recipe had, so asking for desserts produced "No dessert recipes found.
    Available types: ... dessert ...". Reading the real values keeps the
    two from drifting apart again.
    """
    vector_store = load_vector_store()
    types = {
        doc.metadata.get("recipe_type", "general")
        for doc in vector_store.docstore._dict.values()
    }
    types.discard("general")
    return sorted(types)


def search_recipes(query: str, k: int = 1, recipe_type: str = None):
    """Search for recipes using similarity search - returns only best match"""
    vector_store = load_vector_store()
    
    if recipe_type:
        # FAISS applies `filter` AFTER retrieving `fetch_k` chunks, and fetch_k
        # defaults to 20 - so without this, asking for k=20 of a given type only
        # ever sees the 20 nearest chunks overall. The index holds ~70 chunks,
        # so fetching well past that makes the type filter exact.
        results = vector_store.similarity_search_with_score(
            query, 
            k=k,
            filter={"recipe_type": recipe_type},
            fetch_k=max(k * 10, 200)
        )
    else:
        results = vector_store.similarity_search_with_score(query, k=k)
    
    formatted_results = []
    for doc, score in results:
        formatted_results.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "similarity_score": float(score),
            "recipe_name": doc.metadata.get("recipe_name", "Unknown Recipe"),
            "servings": doc.metadata.get("servings"),
            "recipe_type": doc.metadata.get("recipe_type", "general")
        })
    
    return formatted_results

def format_search_results_for_chat(results: List[dict]):
    """Format search results for chat response - returns ONE complete recipe"""
    if not results:
        return "No recipes found for your query. Try asking about different ingredients or dishes!"
    
    result = results[0]
    recipe_name = result.get('recipe_name', 'Unknown Recipe')
    servings = result.get('servings')
    recipe_type = result.get('recipe_type', 'general')
    content = result['content']
    
    formatted = f"**{recipe_name}**\n\n"
    if servings:
        formatted += f"*Servings: {servings} | Type: {recipe_type}*\n\n"
    else:
        formatted += f"*Type: {recipe_type}*\n\n"
    
    formatted += content
    
    return formatted

# def test_vector_store():
#     """Test the vector store with sample queries"""
#     print("=" * 50)
#     print("🧪 Testing Enhanced Vector Store")
#     print("=" * 50)
    
#     test_queries = [
#         ("fajitas", None),
#         ("chicken", "chicken"),
#         ("pozole", None),
#         ("soup", "soup"),
#         ("atun", "seafood"),
#     ]
    
#     for query, filter_type in test_queries:
#         filter_msg = f" (filtered by: {filter_type})" if filter_type else ""
#         print(f"\n🔍 Testing query: '{query}'{filter_msg}")
        
#         results = search_recipes(query, k=1, recipe_type=filter_type)
        
#         if results:
#             print(f"✅ Found {len(results)} results")
#             top = results[0]
#             print(f"   Top result: {top['recipe_name']}")
#             print(f"   Type: {top['recipe_type']}")
#             if top['servings']:
#                 print(f"   Servings: {top['servings']}")
#             print(f"   Preview: {top['content'][:100]}...")
#         else:
#             print("❌ No results found")
    
#     print("\n" + "=" * 50)
#     print("✅ Vector store testing complete!")
#     print("=" * 50)

def get_vector_store_info():
    """Get information about the current vector store"""
    if not os.path.exists(VECTOR_STORE_PATH):
        return {
            "exists": False,
            "message": "No vector store found. Run setup to create one."
        }
    
    vector_store = load_vector_store()
    
    return {
        "exists": True,
        "path": VECTOR_STORE_PATH,
        "message": "Enhanced vector store is ready with metadata!"
    }

if __name__ == "__main__":
    #print("🔧 Enhanced Vector Store Setup & Testing")
    #print("=" * 50)
    
    choice = input("\nWhat would you like to do?\n1. Create new vector store\n4. Debug recipe extraction\n\nChoice (1/4): ")
    
    if choice == "1":
        create_vector_store()
    elif choice == "4":
        debug_recipe_extraction()
    else:
        print("Invalid choice. Exiting.")