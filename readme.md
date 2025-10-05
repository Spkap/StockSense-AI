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


## CI/CD Pipeline

This project uses **GitHub Actions** for automated CI/CD with comprehensive testing and deployment:

### Backend CI/CD Pipeline
- **Automated Testing**: Runs on every push/PR to `main` branch affecting `backend/**`
- **Environment Setup**: Configures Python 3.11 and PostgreSQL test database
- **Dependency Management**: Installs requirements and runs database migrations
- **Test Execution**: Runs Django test suite with coverage reporting
- **Docker Containerization**: Builds Docker images and pushes to Amazon ECR
- **EC2 Deployment**: Automatically deploys containerized backend to AWS EC2 instances
- **Health Checks**: Validates deployment with automated health endpoint testing
- **HTTPS Security**: Uses nginx reverse proxy to convert HTTP to HTTPS traffic
- **Environment Configuration**: Manages Firebase and database secrets through GitHub Actions

### Frontend CI/CD Pipeline
- **Automated Deployment**: Deploys on every push to `main` branch affecting `frontend/**`
- **Build Process**: Uses Vite for optimized production builds with asset bundling
- **Deploy Hook Automation**: GitHub Actions workflow automatically triggers Render deployment using secure deploy hooks
- **Environment Configuration**: Manages Firebase and API keys through Render environment variables

### AI-Service CI/CD Pipeline
- **Automated Deployment**: Triggers on changes to `stocksense/**` directory structure
- **FastAPI Integration**: Deploys Python-based AI microservice
- **EC2 Deployment**: Automatically deploys to AWS EC2 instance for AI processing workloads

### Infrastructure & Security
- **nginx Reverse Proxy**: Converts HTTP traffic to HTTPS for secure communication
- **Docker Images**: All services run as containerized applications for consistency
- **AWS Integration**: Uses ECR for image storage and EC2 for compute resources
- **Secrets Management**: Secure handling of API keys and credentials via GitHub Secrets

## AI Agent Architecture

The StockSense AI Agent is built using the **ReAct (Reasoning + Acting) pattern** with **LangGraph** for sophisticated stock analysis workflows.

### Core Components

**ReAct Agent Engine**
- **LangGraph State Management**: Maintains conversation state and tool execution history
- **Google Gemini 2.5 Flash**: Primary LLM for reasoning and analysis
- **Tool Orchestration**: Systematically executes analysis tools in logical sequence
- **Iterative Reasoning**: Up to 8 reasoning cycles for comprehensive analysis

**Data Collection Tools**
- **News Headlines Fetcher**: Retrieves recent news articles using NewsAPI
- **Price Data Collector**: Fetches historical stock prices via Yahoo Finance
- **Sentiment Analyzer**: AI-powered sentiment analysis of news headlines

**Analysis Workflow**
1. **News Collection**: Fetches recent headlines (7-day lookback)
2. **Price Data Retrieval**: Gathers historical price movements
3. **Sentiment Analysis**: Analyzes news sentiment with detailed justifications
4. **Comprehensive Summary**: Generates final investment recommendation


### Analysis Output

Each AI analysis provides:
- **Investment Recommendation**: Clear BUY/SELL/HOLD decision
- **Sentiment Report**: Detailed news sentiment breakdown
- **Price Trend Analysis**: Historical price movement insights
- **Reasoning Steps**: Transparent decision-making process
- **Tool Usage Tracking**: Complete audit trail of analysis steps
- **Confidence Metrics**: Analysis quality indicators


## Usage

1. **Authentication** - Sign in with Firebase authentication
2. **Stock Management** - Add stocks to your personalized watchlist
3. **AI Analysis** - Get comprehensive AI-powered stock analysis and insights
4. **Real-time Updates** - Monitor live market data and news sentiment

