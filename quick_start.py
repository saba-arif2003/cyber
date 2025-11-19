"""
Quick Start Script - Already configured with your API tokens
Just add your parent photos and run!
"""

import os
from main import CyberBabyGenerator

# Your API tokens (set via environment variables or replace placeholders)
REPLICATE_TOKEN = os.getenv("REPLICATE_TOKEN", "your_token_here")
MESHY_TOKEN = os.getenv("MESHY_TOKEN", "your_token_here")

def main():
    print("🎯 Cyber Baby Generator - Quick Start\n")
    
    # Initialize generator with your tokens
    generator = CyberBabyGenerator(REPLICATE_TOKEN, MESHY_TOKEN)
    
    # Paths to parent photos - UPDATE THESE with your actual photo paths
    parent1 = "parent1.jpg"
    parent2 = "parent2.jpg"
    
    # Check if files exist
    if not os.path.exists(parent1):
        print(f"❌ Parent 1 photo not found: {parent1}")
        print("   Please add your first parent photo as 'parent1.jpg'")
        return
    
    if not os.path.exists(parent2):
        print(f"❌ Parent 2 photo not found: {parent2}")
        print("   Please add your second parent photo as 'parent2.jpg'")
        return
    
    # Generate complete 3D baby
    print("🚀 Starting complete baby generation workflow...\n")
    print("📸 Parent 1:", parent1)
    print("📸 Parent 2:", parent2)
    print("📁 Output directory: output/\n")
    
    try:
        outputs = generator.generate_complete_baby(
            parent1_path=parent1,
            parent2_path=parent2,
            output_dir="output"
        )
        
        print("\n" + "="*50)
        print("✅ SUCCESS! Generated files:")
        print("="*50)
        for key, path in outputs.items():
            print(f"  • {key}: {path}")
        print("\n🎉 Your 3D baby model is ready!")
            
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        print("\n💡 Tips:")
        print("  - Make sure parent photos are clear, front-facing portraits")
        print("  - Check your API tokens are valid")
        print("  - Ensure you have active Replicate and Meshy Pro subscriptions")

if __name__ == "__main__":
    main()


