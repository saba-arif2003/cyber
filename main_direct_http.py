"""
Alternative: Using Direct HTTP Requests to Replicate API
This shows what the "API" tab on model pages is actually doing
"""

import os
import requests
import time
from pathlib import Path


class CyberBabyGeneratorDirectHTTP:
    """
    Using DIRECT HTTP requests to Replicate API
    (Instead of Python client - same endpoint, more control)
    """
    
    def __init__(self, replicate_api_token: str, meshy_api_token: str):
        self.replicate_api_token = replicate_api_token
        self.meshy_api_token = meshy_api_token
        self.base_url = "https://api.replicate.com/v1"
        self.headers = {
            "Authorization": f"Token {replicate_api_token}",
            "Content-Type": "application/json"
        }
    
    def _upload_file(self, file_path: str) -> str:
        """Upload file to Replicate and get URL"""
        upload_url = "https://api.replicate.com/v1/files"
        
        with open(file_path, "rb") as f:
            files = {"file": f}
            headers = {"Authorization": f"Token {self.replicate_api_token}"}
            response = requests.post(upload_url, files=files, headers=headers)
            response.raise_for_status()
            return response.json()["urls"]["get"]
    
    def _run_model_direct(self, model_name: str, input_data: dict) -> str:
        """
        Run model using DIRECT HTTP API (what the "API" tab shows)
        This is exactly what Replicate's "API" tab demonstrates
        """
        # Step 1: Upload files if needed
        processed_input = {}
        for key, value in input_data.items():
            if isinstance(value, str) and os.path.exists(value):
                # Upload local file
                file_url = self._upload_file(value)
                processed_input[key] = file_url
            elif hasattr(value, 'read'):
                # File object - upload it
                # For simplicity, save to temp first
                temp_path = f"temp_{key}.jpg"
                with open(temp_path, "wb") as f:
                    f.write(value.read())
                file_url = self._upload_file(temp_path)
                processed_input[key] = file_url
            else:
                processed_input[key] = value
        
        # Step 2: Create prediction (what the API tab shows)
        prediction_url = f"{self.base_url}/predictions"
        
        # Get model version first
        model_info = requests.get(
            f"{self.base_url}/models/{model_name}/versions",
            headers=self.headers
        ).json()
        
        version = model_info["results"][0]["id"]  # Latest version
        
        prediction_data = {
            "version": version,
            "input": processed_input
        }
        
        response = requests.post(
            prediction_url,
            json=prediction_data,
            headers=self.headers
        )
        response.raise_for_status()
        prediction = response.json()
        
        prediction_id = prediction["id"]
        status_url = f"{self.base_url}/predictions/{prediction_id}"
        
        # Step 3: Poll for completion (same as Python client does)
        print(f"   Prediction ID: {prediction_id}")
        print(f"   Status: {prediction['status']}")
        
        while True:
            response = requests.get(status_url, headers=self.headers)
            response.raise_for_status()
            prediction = response.json()
            
            status = prediction["status"]
            
            if status == "succeeded":
                output = prediction["output"]
                # Handle list or string output
                if isinstance(output, list):
                    return output[0] if output else None
                return output
            elif status == "failed":
                error = prediction.get("error", "Unknown error")
                raise Exception(f"Prediction failed: {error}")
            elif status in ["starting", "processing"]:
                print(f"   ⏳ Status: {status}...")
                time.sleep(2)
            else:
                raise Exception(f"Unknown status: {status}")
    
    def step1_generate_baby_face(self, parent1_path: str, parent2_path: str, output_path: str = "baby_face.jpg"):
        """Step 1 using DIRECT HTTP API"""
        print("🔄 Step 1: Generating baby face (using DIRECT HTTP API)...")
        
        # This is what the "API" tab on model page shows!
        models_to_try = [
            ("cdingram/face-swap", {"source_image": parent1_path, "target_image": parent2_path}),
            ("codeplugtech/face-swap", {"source": parent1_path, "target": parent2_path}),
        ]
        
        for model_name, inputs in models_to_try:
            try:
                print(f"   Trying model: {model_name}...")
                output_url = self._run_model_direct(model_name, inputs)
                
                # Download result
                response = requests.get(output_url)
                response.raise_for_status()
                
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                print(f"✅ Step 1 complete! Baby face saved to: {output_path}")
                return output_path
            except Exception as e:
                print(f"   ⚠️ {model_name} failed: {str(e)[:100]}...")
                continue
        
        raise Exception("All models failed")


# Example usage
if __name__ == "__main__":
REPLICATE_TOKEN = os.getenv("REPLICATE_TOKEN", "your_token_here")
MESHY_TOKEN = os.getenv("MESHY_TOKEN", "your_token_here")
    
    generator = CyberBabyGeneratorDirectHTTP(REPLICATE_TOKEN, MESHY_TOKEN)
    print("✅ Direct HTTP API generator ready!")
    print("This is what the 'API' tab on model pages shows!")


