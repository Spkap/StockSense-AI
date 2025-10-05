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

##  Architecture

StockSense follows a **microservices architecture** with three main services working together to deliver comprehensive stock analysis capabilities.

### System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   AI Service    │
│   (React)       │◄──►│   (Django)      │◄──►│   (FastAPI)     │
│                 │    │                 │    │                 │
│ • React 18      │    │ • Django REST   │    │ • Google Gemini │
│ • Vite          │    │ • PostgreSQL    │    │ • LangGraph     │
│ • TailwindCSS   │    │ • Firebase Auth │    │ • NewsAPI       │
│ • Axios         │    │ • CORS          │    │ • Yahoo Finance │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Render        │    │   AWS EC2       │    │   AWS EC2       │
│   (Frontend)    │    │   (Backend)     │    │   (AI Agent)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Architecture Components

**Frontend Layer (React + Vite)**
- **User Interface**: Modern React 18 application with responsive design
- **State Management**: Context API for global state and user authentication
- **Routing**: React Router for single-page application navigation
- **Styling**: TailwindCSS for utility-first styling and dark/light themes
- **API Communication**: Axios for HTTP requests to backend services
- **Authentication**: Firebase SDK for user management and session handling

**Backend API Layer (Django REST Framework)**
- **RESTful API**: Comprehensive endpoints for user data, watchlists, and stock management
- **Database**: PostgreSQL for reliable data persistence and ACID compliance
- **Authentication**: Firebase Admin SDK for token verification and user validation
- **CORS Configuration**: Cross-origin resource sharing for frontend communication
- **Data Models**: User profiles, watchlists, stock symbols, and analysis history
- **Business Logic**: Portfolio management, user preferences, and data aggregation

**AI Service Layer (FastAPI + LangGraph)**
- **ReAct Agent**: Sophisticated reasoning and acting pattern for stock analysis
- **LLM Integration**: Google Gemini 2.5 Flash for natural language processing
- **Data Sources**: 
  - NewsAPI for real-time financial news
  - Yahoo Finance for historical stock data
  - Sentiment analysis for market sentiment
- **Workflow Engine**: LangGraph for managing complex analysis workflows
- **Tool Orchestration**: Coordinated execution of data collection and analysis tools


### Deployment Architecture

**Multi-Environment Deployment**
- **Frontend**: Deployed on Render with automatic GitHub integration
- **Backend**: Containerized Django app on AWS EC2 with nginx reverse proxy
- **AI Service**: Containerized FastAPI app on separate AWS EC2 instance
- **Database**: AWS RDS PostgreSQL for production data storage
- **Storage**: AWS ECR for Docker image management

**Infrastructure Features**
- **Load Balancing**: nginx for HTTPS termination and request routing
- **Containerization**: Docker for consistent deployment environments
- **CI/CD Integration**: GitHub Actions for automated testing and deployment
- **Security**: Environment variables and secrets management via GitHub Actions
- **Monitoring**: Health checks and logging across all services



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

