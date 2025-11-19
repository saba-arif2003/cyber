"""
Quick test to verify Replicate models are working
"""
import os
import replicate

# Your token (set via environment variable)
REPLICATE_TOKEN = os.getenv("REPLICATE_TOKEN", "your_token_here")
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_TOKEN
client = replicate.Client(api_token=REPLICATE_TOKEN)

print("Testing available Replicate models...\n")

# Test models
test_models = [
    "yan-ops/face-swap:c2d783366e8d32e6e82c40682fab6b4cbc59bf4ce465eeac3900056bf84642c9",
    "logerzhu/face-swap:42a9d70bd16b5035de85349443fcfacdfc2b3455",
    "yan-ops/face_swap:latest",
    "black-forest-labs/flux-schnell:latest",
]

for model in test_models:
    try:
        print(f"✅ Testing: {model}")
        model_info = client.models.get(model.split(":")[0])
        print(f"   Model exists and accessible!")
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")

print("\n✅ Test complete!")



