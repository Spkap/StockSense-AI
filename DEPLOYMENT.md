# Deployment Guide for StockSense Agent

## Backend Deployment (Render)

1. **Fork/Clone Repository** to your GitHub account

2. **Create Render Account** and connect your GitHub

3. **Create Web Service**:

   - Select your forked repository
   - Environment: Python
   - Build Command: `pip install --no-cache-dir -r requirements-backend.txt`
   - Start Command: `uvicorn stocksense.main:app --host 0.0.0.0 --port $PORT`

4. **Set Environment Variables**:

   - `GOOGLE_API_KEY`: Your Google Gemini API key
   - `NEWSAPI_KEY`: Your NewsAPI key
   - `STOCKSENSE_DB_PATH`: `/var/data/stocksense.db`
   - `LOG_LEVEL`: `info`

5. **Configure Disk Storage**:

   - Add persistent disk at `/var/data` (1GB)

6. **Deploy**: Render will automatically deploy your backend

## Frontend Deployment (Streamlit Cloud)

1. **Update Backend URL**:

   - After backend deployment, copy your Render URL
   - Edit `.streamlit/secrets.toml`
   - Replace `https://your-app-name.onrender.com` with your actual Render URL

2. **Deploy to Streamlit Cloud**:

   - Go to https://share.streamlit.io/
   - Connect your GitHub account
   - Select your repository
   - Set main file path: `app.py`
   - Add secrets in Streamlit Cloud dashboard:
     ```
     BACKEND_URL = "https://your-actual-render-url.onrender.com"
     ```

3. **Deploy**: Streamlit will automatically deploy your frontend

## Verification

1. Check backend health: `https://your-render-url.onrender.com/health`
2. Check frontend: Your Streamlit Cloud URL
3. Test stock analysis functionality

## Important Notes

- Use the `requirements-streamlit.txt` file for Streamlit Cloud deployment
- Backend uses `requirements-backend.txt` for Render deployment
- Ensure environment variables are properly set in both platforms
- Database persistence is handled by Render's disk storage
