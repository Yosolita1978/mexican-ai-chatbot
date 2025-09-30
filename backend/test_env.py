import os
from dotenv import load_dotenv

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
serper_key = os.getenv("SERPER_API_KEY")

print("🔑 Environment Variable Check:")
print(f"OpenAI Key: {'✅ Found' if openai_key else '❌ Missing'}")
print(f"Serper Key: {'✅ Found' if serper_key else '⏳ Not needed yet (Day 2)'}")

if openai_key:
    print(f"OpenAI Key starts with: {openai_key[:10]}...")