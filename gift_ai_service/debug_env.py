"""
Debug script to check if .env is being loaded correctly
Run this from gift_ai_service directory
"""
import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 60)
print("🔍 ENVIRONMENT DEBUGGING")
print("=" * 60)

# Check current directory
current_dir = Path.cwd()
print(f"\n📁 Current Directory: {current_dir}")

# Check if .env exists
env_file = current_dir / ".env"
print(f"\n📄 .env file path: {env_file}")
print(f"   Exists: {env_file.exists()}")

if env_file.exists():
    print(f"   Size: {env_file.stat().st_size} bytes")
    print("\n📝 .env file contents (first 10 lines):")
    with open(env_file, 'r') as f:
        for i, line in enumerate(f):
            if i < 10:
                # Hide sensitive values
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.split('=', 1)
                    print(f"   {key}=***{value.strip()[-10:]}")
                else:
                    print(f"   {line.rstrip()}")

# Try loading .env
print("\n" + "=" * 60)
print("🔄 Loading .env file...")
print("=" * 60)

load_dotenv(env_file, override=True)
print("✅ dotenv.load_dotenv() called")

# Check if keys are loaded
print("\n" + "=" * 60)
print("🔑 Checking API Keys")
print("=" * 60)

google_key = os.getenv("GOOGLE_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

print(f"\nGOOGLE_API_KEY:")
if google_key:
    print(f"   ✅ Found: {google_key[:15]}...{google_key[-5:]}")
else:
    print(f"   ❌ NOT FOUND")

print(f"\nGEMINI_API_KEY:")
if gemini_key:
    print(f"   ✅ Found: {gemini_key[:15]}...{gemini_key[-5:]}")
else:
    print(f"   ❌ NOT FOUND")

# Check other important vars
print("\n" + "=" * 60)
print("🔍 Other Environment Variables")
print("=" * 60)

vars_to_check = [
    "LLM_MODEL",
    "MONGO_URI",
    "QDRANT_URL",
    "PORT"
]

for var in vars_to_check:
    value = os.getenv(var)
    if value:
        # Truncate long values
        display_value = value[:50] + "..." if len(value) > 50 else value
        print(f"   ✅ {var}: {display_value}")
    else:
        print(f"   ❌ {var}: NOT FOUND")

print("\n" + "=" * 60)
print("✅ Debug complete!")
print("=" * 60)