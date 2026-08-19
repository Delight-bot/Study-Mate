"""
Quick test script to verify API keys are working
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 50)
print("Testing API Keys Configuration")
print("=" * 50)

# Check which keys are set
openai_key = os.getenv("OPENAI_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

print(f"\n✓ OpenAI Key: {'Found' if openai_key else 'MISSING'}")
if openai_key:
    print(f"  Preview: {openai_key[:20]}...")

print(f"\n✓ Gemini Key: {'Found' if gemini_key else 'MISSING'}")
if gemini_key:
    print(f"  Preview: {gemini_key[:20]}...")

print("\n" + "=" * 50)
print("Testing OpenAI Connection")
print("=" * 50)

if openai_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )

        print("✅ OpenAI API: SUCCESS")
        print(f"   Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI API: FAILED")
        print(f"   Error: {str(e)}")
else:
    print("⚠️  Skipped - No API key")

print("\n" + "=" * 50)
print("Testing Gemini Connection")
print("=" * 50)

if gemini_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)

        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Say 'test successful'")

        print("✅ Gemini API: SUCCESS")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Gemini API: FAILED")
        print(f"   Error: {str(e)}")
else:
    print("⚠️  Skipped - No API key")

print("\n" + "=" * 50)
print("Test Complete!")
print("=" * 50)
