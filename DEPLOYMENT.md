# 🚀 Deployment Guide for Streamlit Cloud

This guide will help you deploy the Cyber Baby Generator app to Streamlit Cloud.

## Prerequisites

1. **GitHub Account** - Your code needs to be in a GitHub repository
2. **Streamlit Cloud Account** - Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **API Tokens Ready** - Have your Replicate and Meshy API tokens handy

## Step 1: Push Your Code to GitHub

1. **Initialize Git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Cyber Baby Generator"
   ```

2. **Create a GitHub repository**:
   - Go to [github.com](https://github.com) and create a new repository
   - Name it something like `cyber-baby-generator`
   - **Do NOT** initialize with README, .gitignore, or license

3. **Push your code**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/cyber-baby-generator.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**:
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"

2. **Connect Your Repository**:
   - Connect your GitHub account if not already connected
   - Select your repository: `YOUR_USERNAME/cyber-baby-generator`
   - Select branch: `main`
   - Main file path: `app.py`

3. **Configure Advanced Settings**:
   - Click "Advanced settings"
   - Add the following secrets:

## Step 3: Set Environment Variables (Secrets)

In Streamlit Cloud, add these secrets in the "Secrets" section:

```toml
REPLICATE_TOKEN = "your_replicate_token_here"
MESHY_TOKEN = "your_meshy_token_here"

# Cloudinary credentials (for image hosting)
CLOUDINARY_CLOUD_NAME = "your_cloudinary_cloud_name"
CLOUDINARY_API_KEY = "your_cloudinary_api_key"
CLOUDINARY_API_SECRET = "your_cloudinary_api_secret"
CLOUDINARY_UPLOAD_FOLDER = "cyberbaby"
```

**How to add secrets:**
1. In your Streamlit Cloud app dashboard
2. Click "Settings" (⚙️ icon)
3. Scroll to "Secrets"
4. Paste the above TOML format
5. Click "Save"

## Step 4: Deploy

1. Click **"Deploy!"**
2. Wait for the app to build (usually 1-2 minutes)
3. Your app will be live at: `https://YOUR_APP_NAME.streamlit.app`

## Important Notes

### File Structure Required:
```
cyber-baby-generator/
├── app.py                    # Main Streamlit app
├── main.py                   # Core generator class
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── .gitignore               # Git ignore file
└── README.md                # (Optional) Project documentation
```

### Files Created Automatically:
- `temp/` - Temporary upload directory (created at runtime)
- `output/` - Generated files directory (created at runtime)

### Memory Considerations:
- Streamlit Cloud free tier has memory limits
- Large images may cause issues
- Consider upgrading to paid tier for production

### Timeout Considerations:
- Streamlit Cloud has a 10-minute timeout for free tier
- Step 3 (Meshy 3D generation) can take 3-10 minutes
- If you hit timeouts, consider:
  - Upgrading to paid tier
  - Using background jobs
  - Implementing async processing

## Troubleshooting

### App Won't Start:
- ✅ Check `requirements.txt` has all dependencies
- ✅ Verify `app.py` is in the root directory
- ✅ Check secrets are set correctly

### Import Errors:
- ✅ Ensure `main.py` is committed to GitHub
- ✅ Check Python version (should be 3.8+)

### API Errors:
- ✅ Verify API tokens in secrets are correct
- ✅ Check token hasn't expired
- ✅ Ensure tokens have proper permissions

### Timeout Errors:
- ✅ Step 3 takes 3-10 minutes - be patient
- ✅ Consider upgrading to paid tier
- ✅ Monitor app logs in Streamlit Cloud dashboard

## Updating Your App

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update description"
   git push
   ```
3. Streamlit Cloud will automatically redeploy!

## Support

- **Streamlit Cloud Docs**: [docs.streamlit.io/streamlit-cloud](https://docs.streamlit.io/streamlit-cloud)
- **Streamlit Community**: [discuss.streamlit.io](https://discuss.streamlit.io)

