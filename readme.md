# StockSense

**AI-Powered Stock Analysis Platform**

A modern full-stack application that combines AI analysis with real-time market data to provide comprehensive stock insights.

## Features

- **AI Stock Analysis** - Uses Google Gemini for intelligent stock analysis
- **Real-time Data** - Fetches live stock prices and market news
- **User Dashboard** - Clean React interface for managing watchlists
- **Firebase Auth** - Secure user authentication and data storage
- **Django REST API** - Robust backend with comprehensive endpoints
- **CI/CD Pipeline** - Automated testing and deployment with GitHub Actions

## Tech Stack

**Frontend:**
- React + Vite
- Firebase Authentication

**Backend:**
- Django REST Framework
- Firebase Admin SDK
- PostgreSQL database

**AI Engine:**
- Google Gemini AI
- NewsAPI integration
- Yahoo Finance data

**DevOps:**
- GitHub Actions (CI/CD)
- Docker containerization
- Render platform deployment

## CI/CD Pipeline

This project uses **GitHub Actions** for CI/CD:

### Backend CI/CD Pipeline
- **Automated Testing**: Runs on every push/PR to `main` branch affecting `backend/**`
- **Environment Setup**: Configures Python 3.11 and PostgreSQL test database
- **Dependency Management**: Installs requirements and runs database migrations
- **Test Execution**: Runs Django test suite with coverage reporting
- **Firebase Integration**: Handles Firebase configuration for test environments
- **EC2 Deployment**: Automatically deploys to AWS EC2 instances after successful testing

### Frontend CI/CD Pipeline
- **Automated Deployment**: Deploys on every push to `main` branch affecting `frontend/**`
- **Build Process**: Uses Vite for optimized production builds with asset bundling
- **Environment Configuration**: Manages Firebase and API keys through Render environment variables
- **Static Site Hosting**: Serves React SPA with proper routing fallbacks on Render


## Usage

1. **Authentication** - Sign in with Firebase authentication
2. **Stock Management** - Add stocks to your personalized watchlist
3. **AI Analysis** - Get comprehensive AI-powered stock analysis and insights
4. **Real-time Updates** - Monitor live market data and news sentiment

