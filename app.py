"""
Cyber Baby Generator - Web Frontend
Upload two parent photos and generate a 3D baby model
"""

import streamlit as st
import os
from pathlib import Path
from main import CyberBabyGenerator
import time

# Page configuration
st.set_page_config(
    page_title="Cyber Baby Generator",
    page_icon="👶",
    layout="wide"
)

# API tokens from environment variables (set in Streamlit Cloud secrets)
REPLICATE_TOKEN = os.getenv("REPLICATE_TOKEN", "")
MESHY_TOKEN = os.getenv("MESHY_TOKEN", "")

# Initialize generator (cache it)
@st.cache_resource
def get_generator():
    return CyberBabyGenerator(REPLICATE_TOKEN, MESHY_TOKEN)

# Clear cache when needed (add ?clear_cache=true to URL)
if st.query_params.get("clear_cache"):
    st.cache_resource.clear()
    st.rerun()

def main():
    st.title("👶 Cyber Baby Generator")
    st.markdown("### Upload two parent photos to generate a realistic 3D baby model")
    
    st.markdown("---")
    
    # Create two columns for file uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📸 Parent 1 Photo")
        parent1_file = st.file_uploader(
            "Upload first parent photo",
            type=['jpg', 'jpeg', 'png'],
            key="parent1"
        )
        if parent1_file:
            st.image(parent1_file, use_container_width=True, caption="Parent 1")
    
    with col2:
        st.subheader("📸 Parent 2 Photo")
        parent2_file = st.file_uploader(
            "Upload second parent photo",
            type=['jpg', 'jpeg', 'png'],
            key="parent2"
        )
        if parent2_file:
            st.image(parent2_file, use_container_width=True, caption="Parent 2")
    
    st.markdown("---")
    
    # Generate button
    if parent1_file and parent2_file:
        if st.button("🚀 Generate 3D Baby Model", type="primary", use_container_width=True):
            # Create temporary files
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            parent1_path = temp_dir / "parent1.jpg"
            parent2_path = temp_dir / "parent2.jpg"
            
            # Save uploaded files
            with open(parent1_path, "wb") as f:
                f.write(parent1_file.getbuffer())
            with open(parent2_path, "wb") as f:
                f.write(parent2_file.getbuffer())
            
            # Create output directory
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # Initialize generator
            generator = get_generator()
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Generate baby face
                status_text.text("🔄 Step 1/3: Generating baby face from parent photos (~30-60 seconds)...")
                progress_bar.progress(10)
                
                baby_face_path = generator.step1_generate_baby_face(
                    str(parent1_path),
                    str(parent2_path),
                    output_path=str(output_dir / "baby_face.jpg")
                )
                
                progress_bar.progress(35)
                status_text.text("✅ Step 1 complete! Moving to Step 2...")
                
                # Step 2: Attach face to body
                status_text.text("🔄 Step 2/3: Attaching face to full baby body (~30-60 seconds)...")
                progress_bar.progress(40)
                
                full_baby_path = generator.step2_attach_face_to_body(
                    baby_face_path,
                    output_path=str(output_dir / "full_baby.jpg")
                )
                
                progress_bar.progress(70)
                status_text.text("✅ Step 2 complete! Moving to Step 3...")
                
                # Step 3: Convert to 3D
                status_text.text("⏳ Step 3/3: Converting to 3D model (~3-10 minutes)...\n⚠️ This is the longest step - please be patient!")
                progress_bar.progress(75)
                
                model_3d_path = generator.step3_convert_to_3d(
                    full_baby_path,
                    output_3d_path=str(output_dir / "baby_3d_model.glb")
                )
                
                progress_bar.progress(100)
                status_text.text("✅ Complete! Your 3D baby model is ready!")
                
                # Display results
                st.success("🎉 Baby generation complete!")
                st.markdown("---")
                
                # Show results in columns
                result_col1, result_col2, result_col3 = st.columns(3)
                
                with result_col1:
                    st.subheader("👶 Baby Face")
                    if os.path.exists(baby_face_path):
                        st.image(baby_face_path, use_container_width=True)
                        with open(baby_face_path, "rb") as f:
                            st.download_button(
                                "📥 Download Baby Face",
                                f.read(),
                                "baby_face.jpg",
                                "image/jpeg"
                            )
                
                with result_col2:
                    st.subheader("👶 Full Baby")
                    if os.path.exists(full_baby_path):
                        st.image(full_baby_path, use_container_width=True)
                        with open(full_baby_path, "rb") as f:
                            st.download_button(
                                "📥 Download Full Baby",
                                f.read(),
                                "full_baby.jpg",
                                "image/jpeg"
                            )
                
                with result_col3:
                    st.subheader("🎨 3D Model")
                    if os.path.exists(model_3d_path):
                        st.info("3D Model Generated!")
                        with open(model_3d_path, "rb") as f:
                            st.download_button(
                                "📥 Download 3D Model (.glb)",
                                f.read(),
                                "baby_3d_model.glb",
                                "model/gltf-binary"
                            )
                        st.markdown("""
                        **To view the 3D model:**
                        - Use online viewers like [Sketchfab](https://sketchfab.com)
                        - Use Blender (File → Import → glTF)
                        - Use Windows 3D Viewer (Windows 10/11)
                        """)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
                progress_bar.progress(0)
    
    else:
        st.info("👆 Please upload both parent photos to begin")
    
    # Sidebar information
    with st.sidebar:
        st.header("ℹ️ How It Works")
        st.markdown("""
        **Step 1:** Blend two parent photos into a realistic 4-month-old baby face
        
        **Step 2:** Attach the baby face to a full neutral baby body
        
        **Step 3:** Convert the full baby image into a 3D model
        
        **Time:** ~5-10 minutes (Step 3 takes the longest)
        """)
        
        st.header("📋 Requirements")
        st.markdown("""
        - Clear, front-facing parent photos
        - Good lighting
        - Face clearly visible
        """)
        
        st.header("🔧 Models Used")
        st.markdown("""
        - **Step 1:** Replicate (modelscope-facefusion)
        - **Step 2:** Replicate (instant-id)
        - **Step 3:** Meshy Pro (Image-to-3D)
        """)

if __name__ == "__main__":
    main()

