import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Validate required keys
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please add it to your .env file.")

# Serper not required for Day 1, but we'll check for it
if not SERPER_API_KEY:
    print("⚠️  SERPER_API_KEY not found - will be needed for Day 2 web search functionality")

# Application settings
APP_NAME = "Mexican Recipe Chatbot"
APP_VERSION = "1.0.0"
DEBUG = True

print(f"✅ Configuration loaded successfully")
print(f"📦 {APP_NAME} v{APP_VERSION}")