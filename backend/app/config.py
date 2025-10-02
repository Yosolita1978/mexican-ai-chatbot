import os
from dotenv import load_dotenv

load_dotenv()

# App metadata
APP_NAME = "SazónBot"
APP_VERSION = "1.0.0"

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Serper API Key (for web search)
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Pushover credentials (for notifications)
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")

# Sentry DSN (for error tracking)
SENTRY_DSN = os.getenv("SENTRY_DSN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Vector store path
VECTOR_STORE_PATH = "data/vector_store"

# Recipe data path
RECIPE_DATA_PATH = "data/recipes"

# print("✅ Configuration loaded")
# print(f"   - OpenAI API Key: {'Set' if OPENAI_API_KEY else 'Missing'}")
# print(f"   - Serper API Key: {'Set' if SERPER_API_KEY else 'Missing'}")
# print(f"   - Pushover User: {'Set' if PUSHOVER_USER else 'Missing'}")
# print(f"   - Pushover Token: {'Set' if PUSHOVER_TOKEN else 'Missing'}")
# print(f"   - Sentry DSN: {'Set' if SENTRY_DSN else 'Missing'}")
# print(f"   - Environment: {ENVIRONMENT}")