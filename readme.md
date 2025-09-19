# StockSense

**AI-Powered Stock Analysis Platform**

A modern full-stack application that combines AI analysis with real-time market data to provide comprehensive stock insights.

## Features

- **AI Stock Analysis** - Uses Google Gemini for intelligent market sentiment analysis
- **Real-time Data** - Fetches live stock prices and market news
- **User Dashboard** - Clean React interface for managing watchlists
- **Firebase Auth** - Secure user authentication and data storage
- **Django REST API** - Robust backend with comprehensive endpoints

## Tech Stack

**Frontend:**
- React + Vite
- Firebase Authentication

**Backend:**
- Django REST Framework
- Firebase Admin SDK
- SQLite database

**AI Engine:**
- Google Gemini AI
- NewsAPI integration
- Yahoo Finance data

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/HarshitR2004/StockSense-AI.git
cd StockSense
```

### 2. Setup Backend
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 3. Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

### 4. Setup AI Engine
```bash
cd stocksense
pip install -r ../requirements.txt
python main.py
```

### 5. Configure Environment
Create `.env` files with your API keys:
- Google Gemini API key
- NewsAPI key
- Firebase configuration

## API Endpoints

**Backend (Django):**
- `GET /api/watchlists/` - Get user watchlists
- `POST /api/watchlists/stocks/` - Add stock to watchlist
- `DELETE /api/watchlists/stocks/{id}/` - Remove stock

**AI Engine:**
- `GET /analyze/{ticker}` - Get AI analysis for stock
- `GET /health` - Health check

## Usage

1. **Sign Up** - Create account with Firebase auth
2. **Add Stocks** - Search and add stocks to your watchlist
3. **Get Analysis** - Click analyze to get AI-powered insights
4. **View Charts** - Interactive price charts and sentiment data

## Project Structure

```
StockSense/
├── frontend/          # React frontend
├── backend/           # Django REST API
├── stocksense/        # AI analysis engine
├── deployment/        # Docker configurations
└── requirements.txt   # Python dependencies
```

