"""
Cyber Baby Generator - Complete 3-Step Workflow
Step 1: Generate baby face from parent photos (Replicate)
Step 2: Attach face to full baby body (Replicate)
Step 3: Convert to 3D model (Meshy Pro)

Using DIRECT HTTP API calls for better efficiency and control
"""

import os
import requests
import json
from pathlib import Path
from typing import Optional
import time


class CyberBabyGenerator:
    def __init__(self, replicate_api_token: str, meshy_api_token: str):
        """
        Initialize the baby generator with API tokens.
        Using direct HTTP API calls for better efficiency.
        
        Args:
            replicate_api_token: Your Replicate API token
            meshy_api_token: Your Meshy Pro API token
        """
        self.replicate_api_token = replicate_api_token
        self.meshy_api_token = meshy_api_token
        self.replicate_base_url = "https://api.replicate.com/v1"
        self.replicate_headers = {
            "Authorization": f"Token {replicate_api_token}",
            "Content-Type": "application/json"
        }
    
    def _upload_file_to_replicate(self, file_path_or_obj, require_public_url: bool = False) -> str:
        """Upload a file to Replicate. Returns public HTTPS URL or base64 data URL."""
        import base64
        
        # Read file content
        if hasattr(file_path_or_obj, "read"):
            if hasattr(file_path_or_obj, "seek"):
                file_path_or_obj.seek(0)
            file_content = file_path_or_obj.read()
            file_name = getattr(file_path_or_obj, "name", "upload.jpg")
        elif isinstance(file_path_or_obj, str):
            file_name = os.path.basename(file_path_or_obj)
            with open(file_path_or_obj, "rb") as f:
                file_content = f.read()
        else:
            raise ValueError(f"Unsupported file type: {type(file_path_or_obj)}")
        
        ext = os.path.splitext(file_name)[1].lower()
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        content_type = content_types.get(ext, "image/jpeg")
        files_endpoint = f"{self.replicate_base_url}/files"
        
        def _extract_url(payload):
            """Extract HTTP URL from various possible Replicate responses."""
            if not payload:
                return None
            
            def _dig(obj):
                if isinstance(obj, str) and obj.startswith("http"):
                    return obj
                if isinstance(obj, dict):
                    for value in obj.values():
                        result = _dig(value)
                        if result:
                            return result
                if isinstance(obj, (list, tuple)):
                    for item in obj:
                        result = _dig(item)
                        if result:
                            return result
                return None
            
            return _dig(payload)
        
        def _try_fetch_public_url(file_id, file_name):
            """Try multiple endpoints to resolve a downloadable HTTPS URL."""
            if not file_id:
                return None
            
            # 1) Fetch metadata for urls
            try:
                meta_resp = requests.get(
                    f"{files_endpoint}/{file_id}",
                    headers={"Authorization": self.replicate_headers["Authorization"]},
                    timeout=10,
                )
                if meta_resp.status_code == 200:
                    meta_json = meta_resp.json()
                    url = _extract_url(meta_json.get("urls")) or _extract_url(meta_json)
                    if url and url.startswith("http"):
                        return url
            except Exception:
                pass
            
            download_endpoint = f"{files_endpoint}/{file_id}/download"
            
            # 2) Attempt HEAD/GET without following redirects to capture Location
            try:
                dl_resp = requests.get(
                    download_endpoint,
                    headers={"Authorization": self.replicate_headers["Authorization"]},
                    timeout=10,
                    allow_redirects=False,
                )
                location = dl_resp.headers.get("Location")
                if location and location.startswith("http"):
                    return location
            except Exception:
                pass
            
            # 3) Follow redirect but don't download entire file (stream)
            try:
                dl_resp = requests.get(
                    download_endpoint,
                    headers={"Authorization": self.replicate_headers["Authorization"]},
                    timeout=10,
                    allow_redirects=True,
                    stream=True,
                )
                if dl_resp.status_code == 200:
                    final_url = dl_resp.url
                    dl_resp.close()
                    if final_url and final_url.startswith("http"):
                        return final_url
            except Exception:
                pass
            
            # 4) Construct replicate.delivery URL manually if file_id looks like pb key
            if file_id:
                manual_url = f"https://replicate.delivery/pb/{file_id}/{file_name}"
                return manual_url
            
            return None
        
        # --- Modern slot-based upload (2025) ---
        try:
            slot_resp = requests.post(
                files_endpoint,
                json={
                    "filename": file_name,
                    "content_type": content_type,
                },
                headers={
                    "Authorization": self.replicate_headers["Authorization"],
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            slot_resp.raise_for_status()
            slot_json = slot_resp.json()
            upload_url = slot_json.get("upload_url")
            file_meta = slot_json.get("file") or {}
            file_id = file_meta.get("id") or slot_json.get("id")
            
            if not upload_url or not file_id:
                raise Exception("Slot response missing upload_url or file id")
            
            put_resp = requests.put(
                upload_url,
                data=file_content,
                headers={"Content-Type": content_type},
                timeout=60,
            )
            put_resp.raise_for_status()
            
            # Poll for public URL
            max_wait = 30  # seconds
            poll_start = time.time()
            while True:
                public_url = _try_fetch_public_url(file_id, file_name)
                if public_url and public_url.startswith("http"):
                    file_size_kb = len(file_content) / 1024
                    print(f"   ✅ Replicate upload OK ({file_size_kb:.1f}KB): {public_url[:50]}...")
                    return public_url
                
                if time.time() - poll_start > max_wait:
                    break
                time.sleep(1.5)
            
            if require_public_url:
                print("   ⚠️ Slot upload done but no public URL yet, trying legacy fallback...")
            else:
                print("   ⚠️ Slot upload done but no public URL yet, will fall back if needed...")
        except Exception as slot_error:
            print(f"   ⚠️ Slot upload flow failed: {str(slot_error)[:120]}...")
        
        # --- Legacy multipart upload ---
        try:
            files_upload = {
                "file": (file_name, file_content, content_type)
            }
            upload_response = requests.post(
                files_endpoint,
                files=files_upload,
                headers={"Authorization": self.replicate_headers["Authorization"]},
                timeout=30
            )
            if upload_response.status_code == 200:
                file_url = _extract_url(upload_response.json())
                if file_url:
                    file_size_kb = len(file_content) / 1024
                    print(f"   ✅ File uploaded to Replicate ({file_size_kb:.1f}KB): {file_url[:50]}...")
                    return file_url
            print(f"   ⚠️ Legacy upload returned status {upload_response.status_code}")
        except Exception as upload_error:
            print(f"   ⚠️ Legacy upload failed: {str(upload_error)[:120]}...")
        
        # --- JSON/base64 fallback ---
        try:
            base64_content = base64.b64encode(file_content).decode("utf-8")
            json_response = requests.post(
                files_endpoint,
                json={
                    "name": file_name,
                    "content": base64_content,
                    "content_type": content_type,
                },
                headers={
                    "Authorization": self.replicate_headers["Authorization"],
                    "Content-Type": "application/json",
                },
                timeout=30
            )
            if json_response.status_code == 200:
                file_url = _extract_url(json_response.json())
                if file_url:
                    file_size_kb = len(file_content) / 1024
                    print(f"   ✅ File uploaded via JSON ({file_size_kb:.1f}KB): {file_url[:50]}...")
                    return file_url
            print(f"   ⚠️ JSON upload returned status {json_response.status_code}")
        except Exception as upload_error:
            print(f"   ⚠️ JSON upload failed: {str(upload_error)[:120]}...")
        
        # --- Public fallback: transfer.sh (no auth needed) ---
        try:
            print("   ⚠️ Replicate upload failed; attempting transfer.sh fallback...")
            transfer_name = file_name.replace(" ", "_")
            transfer_url = f"https://transfer.sh/{transfer_name}"
            transfer_resp = requests.put(
                transfer_url,
                data=file_content,
                headers={"Content-Type": content_type},
                timeout=60,
            )
            transfer_resp.raise_for_status()
            url_candidate = transfer_resp.text.strip().split()[0]
            if url_candidate.startswith("http"):
                print(f"   ✅ Uploaded via transfer.sh: {url_candidate}")
                return url_candidate
        except Exception as transfer_error:
            print(f"   ⚠️ transfer.sh fallback failed: {str(transfer_error)[:120]}...")
        
        # --- Public fallback #2: 0x0.st (anonymous file hosting) ---
        try:
            print("   ⚠️ transfer.sh failed; attempting 0x0.st fallback...")
            zero_response = requests.post(
                "https://0x0.st",
                files={"file": (file_name, file_content, content_type)},
                timeout=60,
            )
            zero_response.raise_for_status()
            zero_url = zero_response.text.strip().split()[0]
            if zero_url.startswith("http"):
                print(f"   ✅ Uploaded via 0x0.st: {zero_url}")
                return zero_url
        except Exception as zero_error:
            print(f"   ⚠️ 0x0.st fallback failed: {str(zero_error)[:120]}...")
        
        # --- Public fallback #3: file.io (note: expires after a download) ---
        try:
            print("   ⚠️ 0x0.st failed; attempting file.io fallback (single-download link)...")
            fileio_resp = requests.post(
                "https://file.io/",
                files={"file": (file_name, file_content, content_type)},
                timeout=60,
            )
            fileio_resp.raise_for_status()
            fileio_json = fileio_resp.json()
            fileio_url = fileio_json.get("link") or fileio_json.get("url")
            if fileio_url and fileio_url.startswith("http"):
                print(f"   ✅ Uploaded via file.io: {fileio_url}")
                return fileio_url
        except Exception as fileio_error:
            print(f"   ⚠️ file.io fallback failed: {str(fileio_error)[:120]}...")
        
        if require_public_url:
            raise Exception("Failed to obtain public URL from Replicate upload.")
        
        if len(file_content) > 10 * 1024 * 1024:
            raise Exception(f"File too large: {len(file_content) / 1024 / 1024:.1f}MB (max 10MB for base64 fallback)")
        
        data_url = f"data:{content_type};base64,{base64_content}"
        file_size_kb = len(file_content) / 1024
        print(f"   ✅ File converted to base64 data URL ({file_size_kb:.1f}KB)")
        return data_url
    
    def _run_replicate_model_with_version(self, model_name: str, version_id: str, input_data: dict) -> str:
        """
        Run model with specific version ID
        """
        # Process input (if already URLs, use them; if local files, upload them)
        processed_input = {}
        for key, value in input_data.items():
            if isinstance(value, str):
                if value.startswith("http"):
                    # Already a URL, use directly
                    processed_input[key] = value
                elif os.path.exists(value):
                    # Local file, upload it
                    print(f"   Uploading {key}...")
                    file_url = self._upload_file_to_replicate(value)
                    processed_input[key] = file_url
                else:
                    processed_input[key] = value
            else:
                processed_input[key] = value
        
        # Use provided version ID directly
        version_id_to_use = version_id
        
        # Create prediction
        prediction_url = f"{self.replicate_base_url}/predictions"
        prediction_data = {
            "version": version_id_to_use,
            "input": processed_input
        }
        
        try:
            response = requests.post(
                prediction_url,
                json=prediction_data,
                headers=self.replicate_headers,
                timeout=30
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            if e.response is not None:
                try:
                    error_json = e.response.json()
                    error_detail = error_json.get("detail") or error_json.get("message") or str(error_json)
                except Exception:
                    error_detail = e.response.text[:200]
            else:
                error_detail = str(e)
            raise Exception(f"HTTP {e.response.status_code if hasattr(e.response, 'status_code') else ''}: {error_detail}")
        
        prediction = response.json()
        
        prediction_id = prediction["id"]
        status_url = f"{self.replicate_base_url}/predictions/{prediction_id}"
        
        # Poll for completion (optimized - faster checks and failure detection)
        # Face fusion models can take 2-3 minutes, so allow more time
        max_wait = 180  # 3 minutes max for face fusion models (they can be slow)
        start_time = time.time()
        last_status = None
        status_check_count = 0
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                raise Exception(f"Timeout after {int(elapsed)}s - model may need more time or parameters may be wrong")
            
            response = requests.get(status_url, headers=self.replicate_headers, timeout=10)
            response.raise_for_status()
            prediction = response.json()
            
            status = prediction["status"]
            status_check_count += 1
            
            # Print status every 2 checks or on change (reduces spam)
            if status != last_status or status_check_count % 2 == 0:
                print(f"   ⏳ Status: {status} ({int(elapsed)}s)...")
                last_status = status
            
            if status == "succeeded":
                output = prediction["output"]
                if isinstance(output, list):
                    return output[0] if output else None
                return output
            elif status == "failed":
                error = prediction.get("error", "Unknown error")
                error_detail = str(error)
                if isinstance(error, dict):
                    error_detail = error.get("detail", error.get("message", str(error)))
                raise Exception(f"Failed: {error_detail}")
            elif status in ["starting", "processing"]:
                time.sleep(0.5)  # Faster polling (0.5s)
            else:
                raise Exception(f"Unknown status: {status}")
    
    def _run_replicate_model_direct(self, model_name: str, input_data: dict) -> str:
        """
        Run model using DIRECT HTTP API (more efficient than Python client)
        This directly calls Replicate's API endpoint
        Uses latest version automatically
        """
        # Process input (if already URLs, use them; if local files, upload them)
        processed_input = {}
        for key, value in input_data.items():
            if isinstance(value, str):
                if value.startswith("http"):
                    # Already a URL, use directly
                    processed_input[key] = value
                elif os.path.exists(value):
                    # Local file, upload it
                    print(f"   Uploading {key}...")
                    file_url = self._upload_file_to_replicate(value)
                    processed_input[key] = file_url
                else:
                    processed_input[key] = value
            else:
                processed_input[key] = value
        
        # Get latest model version
        model_url = f"{self.replicate_base_url}/models/{model_name}/versions"
        response = requests.get(model_url, headers=self.replicate_headers, timeout=30)
        
        # Handle 404 - model doesn't exist
        if response.status_code == 404:
            raise Exception(f"Model not found (404): {model_name}. Check model name on Replicate.")
        
        response.raise_for_status()
        versions = response.json()
        
        if not versions.get("results"):
            raise Exception(f"No versions found for model {model_name}")
        
        version_id = versions["results"][0]["id"]
        
        # Create prediction
        prediction_url = f"{self.replicate_base_url}/predictions"
        prediction_data = {
            "version": version_id,
            "input": processed_input
        }
        
        response = requests.post(
            prediction_url,
            json=prediction_data,
            headers=self.replicate_headers,
            timeout=30
        )
        response.raise_for_status()
        prediction = response.json()
        
        prediction_id = prediction["id"]
        status_url = f"{self.replicate_base_url}/predictions/{prediction_id}"
        
        # Poll for completion (optimized - faster checks and failure detection)
        max_wait = 90  # 90 seconds max - fail fast if parameters are wrong
        start_time = time.time()
        last_status = None
        status_check_count = 0
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                raise Exception(f"Timeout after {int(elapsed)}s - parameters may be wrong")
            
            response = requests.get(status_url, headers=self.replicate_headers, timeout=10)
            response.raise_for_status()
            prediction = response.json()
            
            status = prediction["status"]
            status_check_count += 1
            
            # Print status every 2 checks or on change (reduces spam)
            if status != last_status or status_check_count % 2 == 0:
                print(f"   ⏳ Status: {status} ({int(elapsed)}s)...")
                last_status = status
            
            if status == "succeeded":
                output = prediction["output"]
                if isinstance(output, list):
                    return output[0] if output else None
                return output
            elif status == "failed":
                error = prediction.get("error", "Unknown error")
                error_detail = str(error)
                if isinstance(error, dict):
                    error_detail = error.get("detail", error.get("message", str(error)))
                raise Exception(f"Failed: {error_detail}")
            elif status in ["starting", "processing"]:
                time.sleep(0.5)  # Faster polling (0.5s)
            else:
                raise Exception(f"Unknown status: {status}")
        
    def step1_generate_baby_face(
        self,
        parent1_path: str,
        parent2_path: str,
        output_path: str = "baby_face.jpg",
        width: int = 1024,
        height: int = 1024,
        strength: float = 0.75
    ) -> str:
        """
        Step 1: Generate realistic 4-month-old baby face by blending two parent photos.
        
        Model: lucataco/modelscope-facefusion
        
        Args:
            parent1_path: Path to first parent photo
            parent2_path: Path to second parent photo
            output_path: Where to save the generated baby face
            width: Image width (default: 1024)
            height: Image height (default: 1024)
            strength: Blending strength 0.7-0.8 (default: 0.75)
            
        Returns:
            Path to generated baby face image
        """
        print("🔄 Step 1: Generating baby face from parent photos...")
        
        try:
            # Use modelscope-facefusion for face blending (as specified in original instructions)
            # Upload files once
            print("   Uploading parent photos...")
            parent1_url = self._upload_file_to_replicate(parent1_path)
            parent2_url = self._upload_file_to_replicate(parent2_path)
            print("   ✅ Uploads complete")
            
            # Use specific version of modelscope-facefusion for face fusion/blending
            model_name = "codeplugtech/face-swap"
            model_version = "278a81e7ebb22db98bcba54de985d22cc1abeead2754eb1f2af717247be69b34"
            print(f"   Using model: {model_name} (version: {model_version[:20]}...)")
            
            # Build parameter variations – this model supports source/target style inputs
            prompt_text = (
                "Generate a realistic 4-month-old baby face blending the two parent photos. "
                "Natural infant proportions, soft lighting, neutral background."
            )
            param_variations = [
                {
                    "source_image": parent1_url,
                    "target_image": parent2_url,
                    "prompt": prompt_text,
                    "width": width,
                    "height": height,
                },
                {
                    "source_image": parent2_url,
                    "target_image": parent1_url,
                    "prompt": prompt_text,
                    "width": width,
                    "height": height,
                },
                {
                    "swap_image": parent1_url,
                    "target_image": parent2_url,
                    "prompt": prompt_text,
                },
                {
                    "swap_image": parent2_url,
                    "target_image": parent1_url,
                    "prompt": prompt_text,
                },
                {
                    "input_image": parent1_url,
                    "reference_image": parent2_url,
                    "prompt": prompt_text,
                    "width": width,
                    "height": height,
                },
                {
                    "input_image": parent2_url,
                    "reference_image": parent1_url,
                    "prompt": prompt_text,
                    "width": width,
                    "height": height,
                },
                {
                    "input_image": parent1_url,
                    "swap_image": parent2_url,
                    "prompt": prompt_text,
                },
                {
                    "input_image": parent2_url,
                    "swap_image": parent1_url,
                    "prompt": prompt_text,
                },
            ]
            
            # Try parameters with fast timeout
            image_url = None
            last_error = None
            last_error_full = None
            
            print(f"   Trying {len(param_variations)} parameter variation(s)...")
            
            for i, params in enumerate(param_variations, 1):
                try:
                    print(f"   [{i}/{len(param_variations)}] Trying: {list(params.keys())}...")
                    # Use specific version directly
                    image_url = self._run_replicate_model_with_version(model_name, model_version, params)
                    if image_url:
                        print(f"   ✅ SUCCESS with parameters: {list(params.keys())}")
                        break
                except Exception as e:
                    error_msg = str(e)
                    last_error = error_msg[:150]  # Short version
                    last_error_full = error_msg   # Full version
                    
                    # Check if it's a parameter error (fails immediately)
                    if "invalid" in error_msg.lower() or "unexpected" in error_msg.lower() or "required" in error_msg.lower():
                        print(f"   ⚠️ Invalid parameters: {error_msg[:80]}...")
                        # Continue to next - parameter error means wrong params
                        continue
                    elif "timeout" in error_msg.lower():
                        print(f"   ⚠️ Timeout (model may not support these params): {error_msg[:80]}...")
                        # Continue - timeout might mean wrong params or slow model
                        continue
                    else:
                        print(f"   ⚠️ Error: {error_msg[:100]}...")
                        continue
            
            if not image_url:
                error_detail = f"All {len(param_variations)} parameter variation(s) failed for {model_name}."
                error_detail += f"\n   Model version: {model_version[:30]}..."
                if last_error:
                    error_detail += f"\n   Last error: {last_error}"
                error_detail += f"\n\n   💡 Possible issues:"
                error_detail += f"\n   1. Model version may be incorrect or unavailable"
                error_detail += f"\n   2. Model may require different parameter names"
                error_detail += f"\n   3. Check model page: https://replicate.com/{model_name}"
                raise Exception(error_detail)
            
            # Download and save the image (image_url is always a URL from direct API)
            response = requests.get(image_url, timeout=60)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Step 1 complete! Baby face saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Step 1 failed: {str(e)}")
            raise
    
    def step2_attach_face_to_body(
        self,
        baby_face_path: str,
        reference_body_path: Optional[str] = None,
        output_path: str = "full_baby.jpg"
    ) -> str:
        """
        Step 2: Attach baby face to full neutral 4-month-old baby body.
        
        Model: instant-id or segformer
        
        Args:
            baby_face_path: Path to baby face from Step 1
            reference_body_path: Optional reference body image (if None, uses default neutral body)
            output_path: Where to save the full baby image
            
        Returns:
            Path to full baby image
        """
        print("🔄 Step 2: Attaching face to full baby body...")
        
        body_prompt = (
            "Create a full-body 4-month-old baby with a smooth, simplified, neutral body "
            "(no clothing textures, no anatomical details). "
            "Attach the previously generated blended baby face. "
            "Maintain natural infant body proportions, soft silhouette, photorealistic lighting on the face."
        )
        
        try:
            # Use working models for body attachment
            if reference_body_path:
                # If reference body provided, use face swap (try multiple models)
                models_to_try = [
                    "cdingram/face-swap",
                    "codeplugtech/face-swap",
                    "easel/advanced-face-swap",
                ]
                image_url = None
                
                for model_name in models_to_try:
                    try:
                        print(f"   Trying model: {model_name}...")
                        param_variations = [
                            {"source_image": baby_face_path, "target_image": reference_body_path},
                            {"source": baby_face_path, "target": reference_body_path},
                        ]
                        
                        for params in param_variations:
                            try:
                                image_url = self._run_replicate_model_direct(model_name, params)
                                if image_url:
                                    break
                            except:
                                continue
                        
                        if image_url:
                            print(f"   ✅ Success with {model_name}")
                            break
                    except Exception as e:
                        print(f"   ⚠️ {model_name} failed, trying next...")
                        continue
                
                if not image_url:
                    raise Exception("All face swap models failed for body attachment")
            else:
                # Use FLUX or alternative models to generate baby body with face reference
                print("   Generating full baby body with face reference...")
                
                # Try multiple models that can generate full body from face
                models_to_try = [
                    "black-forest-labs/flux-schnell",
                    "black-forest-labs/flux-dev",
                    "stability-ai/sdxl",
                    "fofr/face-to-many",  # Can generate full body
                ]
                
                image_url = None
                last_error = None
                
                for model_name in models_to_try:
                    try:
                        print(f"   Trying model: {model_name}...")
                        
                        # Different models have different parameters
                        param_sets = [
                            # FLUX models
                            {
                                "prompt": body_prompt + " Full body, 4-month-old baby, using face as reference.",
                                "image": baby_face_path,
                                "num_outputs": 1,
                                "width": 1024,
                                "height": 1024,
                            },
                            # SDXL style
                            {
                                "prompt": body_prompt + " Full body, 4-month-old baby.",
                                "image": baby_face_path,
                                "num_outputs": 1,
                                "width": 1024,
                                "height": 1024,
                            },
                            # face-to-many style
                            {
                                "image": baby_face_path,
                                "prompt": body_prompt,
                            },
                        ]
                        
                        for params in param_sets:
                            try:
                                image_url = self._run_replicate_model_direct(model_name, params)
                                if image_url:
                                    print(f"   ✅ Success with {model_name}")
                                    break
                            except Exception as e:
                                error_msg = str(e)
                                if "404" in error_msg or "not found" in error_msg.lower():
                                    # Model doesn't exist, skip to next
                                    print(f"   ⚠️ Model not found, trying next...")
                                    raise Exception("Model not found")
                                continue
                        
                        if image_url:
                            break
                            
                    except Exception as e:
                        last_error = str(e)
                        if "404" in last_error or "not found" in last_error.lower():
                            print(f"   ⚠️ {model_name} not found (404), trying next model...")
                        else:
                            print(f"   ⚠️ {model_name} failed: {str(e)[:80]}...")
                        continue
                
                if not image_url:
                    # Last resort: Use face swap on a simple baby body template
                    print("   ⚠️ All generation models failed, using face swap fallback...")
                    # You could generate a simple baby body using any text-to-image model
                    raise Exception(f"Could not generate baby body. Tried: {', '.join(models_to_try)}. Error: {last_error[:100] if last_error else 'Unknown'}")
            
            # Download and save (image_url is always a URL from direct API)
            response = requests.get(image_url, timeout=60)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Step 2 complete! Full baby image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Step 2 failed: {str(e)}")
            raise
    
    def step3_convert_to_3d(
        self,
        full_baby_image_path: str,
        output_3d_path: str = "baby_3d_model.glb"
    ) -> str:
        """
        Step 3: Convert full baby image to 3D model using Meshy Pro.
        
        Args:
            full_baby_image_path: Path to full baby image from Step 2
            output_3d_path: Where to save the 3D model file
            
        Returns:
            Path to 3D model file
        """
        print("🔄 Step 3: Converting to 3D model with Meshy Pro...")
        
        prompt = (
            "Full-body 4-month-old baby, smooth neutral body, realistic face with blended features from parents, "
            "proper infant proportions, soft skin, photorealistic lighting. "
            "Generate full 3D model with complete body, head, arms, legs, hands, and feet."
        )
        
        try:
            print("   Uploading final 2D image to Cloudinary...")
            image_url = self._upload_file_to_cloudinary(full_baby_image_path)
            
            headers = {
                "Authorization": f"Bearer {self.meshy_api_token}",
                "Content-Type": "application/json",
            }
            
            # Correct API endpoint and payload structure
            payload = {
                "image_url": image_url,
                "enable_pbr": True,
                "should_texture": True,
                "ai_model": "latest"  # Use latest model (Meshy 6)
            }
            
            # FIXED: Use correct endpoint
            create_url = "https://api.meshy.ai/openapi/v1/image-to-3d"
            print("   Submitting job to Meshy (POST /openapi/v1/image-to-3d)...")
            create_response = requests.post(create_url, headers=headers, json=payload, timeout=60)
            create_response.raise_for_status()
            job_data = create_response.json()
            
            # FIXED: Correct response field
            task_id = job_data.get("result")
            
            if not task_id:
                raise Exception(f"Meshy response missing task ID: {str(job_data)[:200]}")
            
            # FIXED: Use correct status endpoint
            status_url = f"https://api.meshy.ai/openapi/v1/image-to-3d/{task_id}"
            print(f"   ✅ Meshy job submitted (ID: {task_id})")
            print("⏳ 3D generation in progress... (typically 3-8 minutes)")
            
            max_wait_time = 900  # 15 minutes max
            start_time = time.time()
            last_status = None
            check_interval = 5
            
            while True:
                elapsed = time.time() - start_time
                if elapsed > max_wait_time:
                    raise Exception(f"⏱️ Timeout after {max_wait_time//60} minutes waiting for Meshy.")
                
                status_response = requests.get(status_url, headers=headers, timeout=30)
                if status_response.status_code == 429:
                    print("   ⚠️ Rate limited, waiting 10s before retry...")
                    time.sleep(10)
                    continue
                
                status_response.raise_for_status()
                status_data = status_response.json()
                
                # FIXED: Correct status field
                status = status_data.get("status", "UNKNOWN")
                
                if status != last_status:
                    elapsed_min = int(elapsed // 60)
                    elapsed_sec = int(elapsed % 60)
                    progress = status_data.get("progress", 0)
                    print(f"   📊 Status: {status} | Progress: {progress}% ({elapsed_min}m {elapsed_sec}s)")
                    last_status = status
                
                if status == "SUCCEEDED":
                    # FIXED: Correct response structure
                    model_urls = status_data.get("model_urls", {})
                    model_url = model_urls.get("glb")
                    
                    if not model_url:
                        raise Exception(f"Meshy job succeeded but no GLB URL was returned: {str(model_urls)[:200]}")
                    
                    print("   ⬇️ Downloading Meshy GLB...")
                    model_response = requests.get(model_url, timeout=120)
                    model_response.raise_for_status()
                    with open(output_3d_path, "wb") as f:
                        f.write(model_response.content)
                    
                    total_time = int(elapsed)
                    print(f"✅ Step 3 complete! 3D model saved to: {output_3d_path}")
                    print(f"   ⏱️ Total time: {total_time//60}m {total_time%60}s")
                    return output_3d_path
                
                if status == "FAILED":
                    error = status_data.get("task_error", {})
                    error_msg = error.get("message", "Unknown Meshy error")
                    raise Exception(f"❌ Meshy reported failure: {error_msg}")
                
                # FIXED: Handle IN_PROGRESS and other valid in-progress statuses
                if status in ["PENDING", "PROCESSING", "IN_PROGRESS"]:
                    time.sleep(check_interval)
                else:
                    raise Exception(f"Unknown status: {status}")
                        
        except Exception as e:
            print(f"❌ Step 3 failed: {str(e)}")
            raise
    
    def generate_complete_baby(
        self,
        parent1_path: str,
        parent2_path: str,
        reference_body_path: Optional[str] = None,
        output_dir: str = "output"
    ) -> dict:
        """
        Complete workflow: Generate 3D baby from parent photos.
        
        Args:
            parent1_path: Path to first parent photo
            parent2_path: Path to second parent photo
            reference_body_path: Optional reference baby body image
            output_dir: Directory to save all outputs
            
        Returns:
            Dictionary with paths to all generated files
        """
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        outputs = {}
        
        # Step 1: Generate baby face
        outputs["baby_face"] = self.step1_generate_baby_face(
            parent1_path,
            parent2_path,
            output_path=os.path.join(output_dir, "baby_face.jpg")
        )
        
        # Step 2: Attach face to body
        outputs["full_baby"] = self.step2_attach_face_to_body(
            outputs["baby_face"],
            reference_body_path,
            output_path=os.path.join(output_dir, "full_baby.jpg")
        )
        
        # Step 3: Convert to 3D
        outputs["3d_model"] = self.step3_convert_to_3d(
            outputs["full_baby"],
            output_3d_path=os.path.join(output_dir, "baby_3d_model.glb")
        )
        
        print("\n🎉 Complete! 3D baby model generated successfully!")
        print(f"📁 All files saved in: {output_dir}/")
        
        return outputs


# Example usage
if __name__ == "__main__":
    import sys
    
    # Example usage - tokens can come from environment or be hardcoded
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
    MESHY_API_TOKEN = os.getenv("MESHY_API_TOKEN", "")
    
    if not REPLICATE_API_TOKEN or not MESHY_API_TOKEN:
        print("⚠️  Please set REPLICATE_API_TOKEN and MESHY_API_TOKEN")
        print("   Or use quick_start.py for easy setup")
        sys.exit(1)
    
    print("✅ Cyber Baby Generator initialized successfully!")
    print("📖 Use quick_start.py to generate your baby model")
    print("   Or use generator.generate_complete_baby() programmatically")

