"""
Example usage of Cyber Baby Generator
"""

import os
from main import CyberBabyGenerator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Get API tokens from environment
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    meshy_token = os.getenv("MESHY_API_TOKEN")
    
    if not replicate_token or not meshy_token:
        print("❌ Please set REPLICATE_API_TOKEN and MESHY_API_TOKEN in .env file")
        return
    
    # Initialize generator
    generator = CyberBabyGenerator(replicate_token, meshy_token)
    
    # Paths to parent photos
    parent1 = "parent1.jpg"  # Update with your parent photo paths
    parent2 = "parent2.jpg"  # Update with your parent photo paths
    
    # Check if files exist
    if not os.path.exists(parent1) or not os.path.exists(parent2):
        print(f"❌ Parent photos not found. Please add {parent1} and {parent2}")
        return
    
    # Generate complete 3D baby
    print("🚀 Starting complete baby generation workflow...\n")
    
    try:
        outputs = generator.generate_complete_baby(
            parent1_path=parent1,
            parent2_path=parent2,
            output_dir="output"
        )
        
        print("\n📊 Generated files:")
        for key, path in outputs.items():
            print(f"  - {key}: {path}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()



