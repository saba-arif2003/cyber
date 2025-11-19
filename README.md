# Cyber Baby Generator

Complete 3-step workflow to generate a realistic 3D baby model from two parent photos.

## Workflow Overview

1. **Step 1**: Generate 4-month-old baby face from parent photos using Replicate (`codeplugtech/face-swap`)
2. **Step 2**: Attach face to full neutral baby body using Replicate (`instant-id`)
3. **Step 3**: Convert full baby image to 3D model using Meshy Pro API

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note:** This project uses **direct HTTP API calls** to Replicate (more efficient than Python client). No `replicate` package needed!

2. Set API tokens:
```bash
export REPLICATE_API_TOKEN="your_replicate_token"
export MESHY_API_TOKEN="your_meshy_pro_token"
```

Or create a `.env` file:
```
REPLICATE_API_TOKEN=your_token_here
MESHY_API_TOKEN=your_token_here
```

## Usage

### Web Frontend (Recommended)

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser at `http://localhost:8501`
3. Upload two parent photos
4. Click "Generate 3D Baby Model"
5. Download the results!

### Command Line

```python
from main import CyberBabyGenerator

# Initialize
generator = CyberBabyGenerator(
    replicate_api_token="your_token",
    meshy_api_token="your_token"
)

# Generate complete 3D baby
outputs = generator.generate_complete_baby(
    parent1_path="parent1.jpg",
    parent2_path="parent2.jpg",
    output_dir="output"
)

# Or run steps individually
baby_face = generator.step1_generate_baby_face("parent1.jpg", "parent2.jpg")
full_baby = generator.step2_attach_face_to_body(baby_face)
model_3d = generator.step3_convert_to_3d(full_baby)
```

### Quick Start Script

```bash
python quick_start.py
```

## Output Files

- `baby_face.jpg` - Blended baby face from parents
- `full_baby.jpg` - Full-body baby image with attached face
- `baby_3d_model.glb` - Final 3D model

## Models Used

| Step | Tool | Model | Purpose |
|------|------|-------|---------|
| 1 | Replicate | `codeplugtech/face-swap` | Blend parent photos into baby face |
| 2 | Replicate | `instant-id` / face swap | Attach face to neutral baby body |
| 3 | Meshy Pro | Image-to-3D | Convert 2D image to 3D model |

## Performance & Speed Improvements

**What was fixed:**
- ✅ **Using Direct HTTP API** - More efficient, faster than Python client
- ✅ Fixed incorrect model names (now uses working face-swap models)
- ✅ Added automatic fallback to multiple models
- ✅ Reduced polling interval from 10s to 5s for Step 3
- ✅ Added proper timeout handling
- ✅ Better error messages for debugging

**Expected Times:**
- Step 1 (Face Blend): ~30-60 seconds
- Step 2 (Body Attachment): ~30-60 seconds  
- Step 3 (3D Conversion): ~3-10 minutes (Meshy Pro processing)

**Total Time: ~5-12 minutes** (mostly Step 3)

## Notes

- Ensure parent photos are clear, front-facing portraits
- Step 3 (3D conversion) takes the longest time (~3-10 min)
- Meshy Pro API requires active subscription
- If a model fails, the code automatically tries alternatives

