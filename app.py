import streamlit as st
import requests
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import os
PLOTLY_AVAILABLE = True

st.set_page_config(
    page_title="StockSense AI Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/Spkap/StockSense-AI',
        'Report a bug': 'https://github.com/Spkap/StockSense-AI/issues',
        'About': "# StockSense ReAct Agent\nAI-powered autonomous stock analysis using ReAct pattern"
    }
)

st.markdown("""
<style>
    /* Main container styling */
    .main > div {
        padding-top: 2rem;
    }

    /* Hero section styling */
    .hero-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }

    /* Card styling */
    .analysis-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #e1e5e9;
        margin-bottom: 1rem;
        color: #333333;
    }

    .metric-card {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #dee2e6;
        color: #333333;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    /* Status indicators */
    .status-online {
        color: #28a745;
        font-weight: bold;
    }

    .status-offline {
        color: #dc3545;
        font-weight: bold;
    }

    /* Input styling */
    .stTextInput input {
        border-radius: 8px;
        border: 2px solid #e1e5e9;
        padding: 0.75rem;
        font-size: 16px;
    }

    .stTextInput input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* Button styling */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    /* Progress bar styling */
    .stProgress .st-bo {
        background-color: #667eea;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }

    /* Success/Error message styling */
    .stSuccess {
        border-radius: 8px;
    }

    .stError {
        border-radius: 8px;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    if 'backend_status' not in st.session_state:
        st.session_state.backend_status = None
    if 'selected_ticker' not in st.session_state:
        st.session_state.selected_ticker = ""

initialize_session_state()

@st.cache_data
def load_company_ticker_mapping():
    """Load company name to ticker mapping from CSV file."""
    csv_path = Path("nasdaq_screener.csv")
    
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            if 'Symbol' in df.columns and 'Name' in df.columns:
                # Create a mapping from company name to ticker
                mapping = dict(zip(df['Name'], df['Symbol']))
                return mapping, df
        except Exception as e:
            st.warning(f"Error loading CSV file: {e}")
    
    # Fallback to popular stocks if CSV not available
    fallback_mapping = {
        "Apple Inc.": "AAPL",
        "Microsoft Corporation": "MSFT", 
        "Alphabet Inc.": "GOOGL",
        "Amazon.com Inc.": "AMZN",
        "Tesla Inc.": "TSLA",
        "NVIDIA Corporation": "NVDA",
        "Meta Platforms Inc.": "META",
        "Netflix Inc.": "NFLX",
        "Advanced Micro Devices Inc.": "AMD",
        "Intel Corporation": "INTC"
    }
    
    return fallback_mapping, None

def create_candlestick_chart(price_data: list) -> go.Figure:
    """Create an interactive candlestick chart with moving averages."""
    if not price_data:
        return None
        
    # Convert to DataFrame
    df = pd.DataFrame(price_data)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    # Calculate moving averages
    df['SMA_20'] = df['Close'].rolling(window=20, min_periods=1).mean()
    df['SMA_50'] = df['Close'].rolling(window=50, min_periods=1).mean()
    
    # Create candlestick chart
    fig = go.Figure()
    
    # Add candlestick
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="Price",
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ))
    
    # Add moving averages
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['SMA_20'],
        mode='lines',
        name='SMA 20',
        line=dict(color='orange', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['SMA_50'],
        mode='lines',
        name='SMA 50',
        line=dict(color='blue', width=2)
    ))
    
    # Update layout
    fig.update_layout(
        title="Stock Price with Moving Averages",
        yaxis_title="Price ($)",
        xaxis_title="Date",
        template="plotly_white",
        height=500,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    return fig

# Get backend URL from Streamlit secrets first, then environment, then default
try:
    BACKEND_URL = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", "http://127.0.0.1:8000"))
except:
    BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

def check_backend_status() -> bool:
    """Check if the backend is online."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        status = response.status_code == 200
        st.session_state.backend_status = status
        return status
    except:
        st.session_state.backend_status = False
        return False


def create_styled_header():
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                padding: 2rem 1rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; text-align: center; margin: 0;
                   text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
            📈 StockSense AI Agent
        </h1>
        <p style="color: #f0f0f0; text-align: center; margin: 0.5rem 0 0 0;
                  font-size: 1.1rem; opacity: 0.9;">
            AI-Powered Stock Analysis Using Reasoning & Action
        </p>
    </div>
    """, unsafe_allow_html=True)


def display_hero_section():
    create_styled_header()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if check_backend_status():
            st.success("🟢 Backend Connected & Ready", icon="✅")
        else:
            st.error("🔴 Backend Connection Failed", icon="❌")

    st.markdown("<br>", unsafe_allow_html=True)


def display_ticker_input():
    st.markdown("### Select Stock to Analyze")

    # Load company mapping
    company_mapping, df = load_company_ticker_mapping()
    company_names = list(company_mapping.keys())

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Select Company:**")
        
        # Company selectbox
        selected_company = st.selectbox(
            "Choose a company",
            options=[""] + company_names,
            index=0,
            help="Select a company from the dropdown",
            label_visibility="collapsed"
        )
        
        if selected_company:
            ticker = company_mapping[selected_company]
            st.session_state.selected_ticker = ticker
            st.info(f"Selected: **{selected_company}** → **{ticker}**")

    with col2:
        st.markdown("**Or enter manually:**")
        manual_ticker = st.text_input(
            "Stock Ticker",
            value=st.session_state.selected_ticker if not selected_company else "",
            placeholder="e.g., AAPL",
            help="Enter any valid stock ticker symbol",
            label_visibility="collapsed"
        )

        if manual_ticker and manual_ticker != st.session_state.selected_ticker:
            st.session_state.selected_ticker = manual_ticker.upper().strip()

    # Quick select buttons for popular stocks
    st.markdown("**Quick Select Popular Stocks:**")
    cols = st.columns(5)
    popular_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    
    for i, ticker in enumerate(popular_tickers):
        with cols[i]:
            if st.button(ticker, key=f"quick_{ticker}", use_container_width=True):
                st.session_state.selected_ticker = ticker

    cols = st.columns(5)
    more_tickers = ["NVDA", "META", "NFLX", "AMD", "INTC"]
    
    for i, ticker in enumerate(more_tickers):
        with cols[i]:
            if st.button(ticker, key=f"quick_{ticker}", use_container_width=True):
                st.session_state.selected_ticker = ticker

    return st.session_state.selected_ticker


def validate_ticker(ticker: str) -> tuple[bool, str]:
    """Validate ticker input."""
    if not ticker:
        return False, "Please select or enter a stock ticker symbol"

    if not ticker.replace('.', '').isalpha() or len(ticker) < 1 or len(ticker) > 10:
        return False, "Please enter a valid ticker (1-10 letters, dots allowed)"

    return True, ""


def trigger_analysis(ticker: str) -> Optional[Dict[str, Any]]:
    """Triggers stock analysis via backend API."""
    try:
        if not check_backend_status():
            st.error("🔌 Backend server is offline. Please start the FastAPI server.")
            return None

        with st.spinner("🤖 ReAct Agent is analyzing..."):
            response = requests.post(
                f"{BACKEND_URL}/analyze/{ticker}",
                timeout=60
            )

        if response.status_code == 200:
            result = response.json()

            st.success(f"Analysis for **{ticker}** has been triggered!")

            # Check if this is a fresh analysis or cached result
            analysis_data = result.get('data', {})
            if analysis_data.get('source') == 'react_analysis':
                # Fresh analysis - use the data directly from /analyze response
                st.success("✅ Fresh analysis completed!")
                
                result_obj = {
                    'ticker': ticker,
                    'data': analysis_data,
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }

                st.session_state.analysis_result = result_obj
                st.session_state.analysis_history.insert(0, result_obj)
                if len(st.session_state.analysis_history) > 10:
                    st.session_state.analysis_history.pop()

                return result_obj
                
            elif analysis_data.get('source') == 'cache':
                # Cached result - data is already complete
                st.info("📚 Retrieved from cache")
                
                result_obj = {
                    'ticker': ticker,
                    'data': analysis_data,
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }

                st.session_state.analysis_result = result_obj
                st.session_state.analysis_history.insert(0, result_obj)
                if len(st.session_state.analysis_history) > 10:
                    st.session_state.analysis_history.pop()

                return result_obj
            
            else:
                # Fallback to old behavior for backward compatibility
                with st.expander("Backend Response Details"):
                    st.json(result)

                st.markdown("---")
                progress_bar = st.progress(0)
                status_text = st.empty()

                max_attempts = 10
                for attempt in range(1, max_attempts + 1):
                    status_text.text(f"Fetching results... (Attempt {attempt}/{max_attempts})")
                    progress_bar.progress(attempt / max_attempts)

                    try:
                        results_response = requests.get(
                            f"{BACKEND_URL}/results/{ticker}",
                            timeout=10
                        )

                        if results_response.status_code == 200:
                            analysis_data = results_response.json()
                            status_text.text("Results retrieved successfully!")
                            progress_bar.progress(1.0)

                            result_obj = {
                                'ticker': ticker,
                                'data': analysis_data.get('data', analysis_data),
                                'timestamp': datetime.now().isoformat(),
                                'success': True
                            }

                            st.session_state.analysis_result = result_obj

                            st.session_state.analysis_history.insert(0, result_obj)
                            if len(st.session_state.analysis_history) > 10:
                                st.session_state.analysis_history.pop()

                            progress_bar.empty()
                            status_text.empty()
                            return result_obj

                        elif results_response.status_code == 404:
                            if attempt < max_attempts:
                                time.sleep(2)
                                continue
                        else:
                            st.error(f"❌ Error fetching results: Status {results_response.status_code}")
                            break

                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Network error: {str(e)}")
                        break

                progress_bar.empty()
                status_text.empty()
                st.error("⏱️ Analysis timed out. Please try again.")
            return None

        else:
            st.error(f"❌ Analysis failed: Status {response.status_code}")
            if response.text:
                st.error(f"Details: {response.text}")
            return None

    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Analysis may still be processing.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to backend. Please ensure the server is running.")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None


def display_enhanced_analysis_results(data: Dict[str, Any], ticker: str):
    """Display enhanced analysis results with tabbed interface."""
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Analysis Dashboard", "📰 News & Sentiment", "⚙️ Agent Reasoning"])
    
    with tab1:
        st.markdown("### 📊 Analysis Dashboard")
        
        # Display analysis summary
        summary = (data.get('summary') or 
                  data.get('analysis_summary') or
                  data.get('analysis') or
                  "Analysis completed successfully")
        
        if summary and summary != "Analysis completed successfully":
            st.markdown(f"""
            <div class="analysis-card fade-in">
                <h4 style="color: #667eea; margin-bottom: 1rem; font-size: 1.3rem; border-bottom: 2px solid #e1e5e9; padding-bottom: 0.5rem;">
                    📊 Analysis Summary
                </h4>
                <p><strong>Stock:</strong> {ticker}</p>
                <div>{summary}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("📊 Detailed analysis summary not available for this request")
        
        # Display interactive candlestick chart
        price_data = data.get('price_data', [])
        if not price_data:
            # Try alternative key names
            price_data = (data.get('historical_data') or 
                         data.get('price_history') or
                         data.get('ohlcv_data') or [])
        
        if price_data and len(price_data) > 0:
            st.markdown("#### 📈 Interactive Price Chart with Moving Averages")
            
            try:
                fig = create_candlestick_chart(price_data)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    st.success(f"📊 Displaying {len(price_data)} days of price data with technical indicators")
                else:
                    st.warning("Unable to create candlestick chart - trying fallback visualization")
                    # Fallback to simple line chart
                    try:
                        df = pd.DataFrame(price_data)
                        df['Date'] = pd.to_datetime(df['Date'])
                        df = df.sort_values('Date').set_index('Date')
                        st.line_chart(df[['Close']], use_container_width=True)
                    except Exception as fallback_error:
                        st.error(f"Chart creation failed: {str(fallback_error)}")
            except Exception as e:
                st.error(f"Error creating chart: {str(e)}")
                # Show raw data for debugging
                with st.expander("🔍 Debug: Raw Price Data"):
                    st.json(price_data[:3])  # Show first 3 records
        else:
            # Show more helpful message
            available_keys = list(data.keys())
            st.info(f"📈 No historical price data available in this analysis. Available data: {', '.join(available_keys)}")
            
            # Try to get real-time price data as fallback
            if st.button("🔄 Fetch Current Price Data", key="fetch_price_fallback"):
                with st.spinner("Fetching current market data..."):
                    try:
                        from stocksense.data_collectors import get_price_history
                        df = get_price_history(ticker, period="1mo")
                        if df is not None and not df.empty:
                            # Convert to our format
                            df_reset = df.reset_index()
                            df_reset['Date'] = df_reset['Date'].dt.strftime('%Y-%m-%d')
                            fallback_data = df_reset.to_dict(orient='records')
                            
                            fig = create_candlestick_chart(fallback_data)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                                st.success("📊 Showing current market data (not from AI analysis)")
                    except Exception as e:
                        st.error(f"Failed to fetch fallback data: {str(e)}")
        
        # Display key metrics
        display_key_metrics(ticker)
    
    with tab2:
        st.markdown("### 📰 News & Sentiment Analysis")
        
        # Display detailed sentiment report
        sentiment_report_raw = data.get('sentiment_report')
        
        if sentiment_report_raw:
            st.markdown("""
                <h4 style="color: #667eea; margin-bottom: 1rem; font-size: 1.3rem; border-bottom: 2px solid #e1e5e9; padding-bottom: 0.5rem;">
                    📊 Market Sentiment Report
                </h4>
            """, unsafe_allow_html=True)
            
            # Try to parse as JSON first
            if isinstance(sentiment_report_raw, str):
                try:
                    sentiment_data = json.loads(sentiment_report_raw)
                    if isinstance(sentiment_data, list):
                        # Display structured sentiment data
                        for i, item in enumerate(sentiment_data, 1):
                            headline = item.get('headline', 'N/A')
                            sentiment = item.get('sentiment', 'N/A')
                            justification = item.get('justification', 'N/A')
                            
                            with st.expander(f"📰 Article {i}: {headline[:80]}..."):
                                st.markdown(f"**Headline:** {headline}")
                                st.markdown(f"**Sentiment:** {sentiment}")
                                st.markdown(f"**Analysis:** {justification}")
                    else:
                        st.markdown(sentiment_report_raw)
                except json.JSONDecodeError:
                    st.markdown(sentiment_report_raw)
            elif isinstance(sentiment_report_raw, list):
                # Already structured data
                for i, item in enumerate(sentiment_report_raw, 1):
                    headline = item.get('headline', 'N/A')
                    sentiment = item.get('sentiment', 'N/A')
                    justification = item.get('justification', 'N/A')
                    
                    with st.expander(f"� Article {i}: {headline[:80]}..."):
                        st.markdown(f"**Headline:** {headline}")
                        st.markdown(f"**Sentiment:** {sentiment}")
                        st.markdown(f"**Analysis:** {justification}")
            else:
                st.markdown(str(sentiment_report_raw))
        else:
            # Try to show any related sentiment data
            sentiment_info = []
            if data.get('headlines_count'):
                sentiment_info.append(f"Analyzed {data['headlines_count']} headlines")
            if data.get('sentiment'):
                sentiment_info.append(f"Overall sentiment: {data['sentiment']}")
                
            if sentiment_info:
                st.info("Sentiment analysis completed. " + " | ".join(sentiment_info))
            else:
                st.info("No detailed sentiment analysis data available")
    
    with tab3:
        st.markdown("### ⚙️ Agent Reasoning Process")
        
        # Check if we have any reasoning data - be more specific about what constitutes "available"
        reasoning_steps = data.get('reasoning_steps') or []
        has_reasoning_steps = len(reasoning_steps) > 0
        has_tools_used = data.get('tools_used') and len(data.get('tools_used', [])) > 0
        has_iterations = data.get('iterations') and data.get('iterations', 0) > 0
        has_source_info = data.get('source') == 'react_analysis'  # Fresh analysis vs cached
        
        # For cached data, don't show reasoning even if it has generic cache steps
        is_cached = data.get('source') == 'cache'
        has_meaningful_reasoning = has_reasoning_steps and not is_cached
        
        if has_meaningful_reasoning or (has_tools_used and not is_cached) or (has_iterations and not is_cached):
            st.markdown("""
                <h4 style="color: #667eea; margin-bottom: 1rem; font-size: 1.3rem; border-bottom: 2px solid #e1e5e9; padding-bottom: 0.5rem;">
                    🧠 ReAct Agent Decision Process
                </h4>
            """, unsafe_allow_html=True)
            
            # Show reasoning steps if available
            if has_meaningful_reasoning:
                reasoning_data = reasoning_steps  # Use the cleaned version
                st.markdown("**📋 Agent Reasoning Steps:**")
                if isinstance(reasoning_data, str):
                    st.markdown(reasoning_data)
                elif isinstance(reasoning_data, list):
                    for i, step in enumerate(reasoning_data, 1):
                        st.markdown(f"**Step {i}:** {step}")
                else:
                    st.markdown(str(reasoning_data))
            
            # Show tools used if available (but not for cached data)
            if has_tools_used and not is_cached:
                st.markdown("**🔧 Tools Used:**")
                tools = data['tools_used']
                if isinstance(tools, list):
                    for tool in set(tools):  # Remove duplicates
                        st.markdown(f"• {tool}")
                else:
                    st.markdown(str(tools))
            
            # Show iteration count if available (but not for cached data)
            if has_iterations and not is_cached:
                st.markdown(f"**🔄 Analysis Iterations:** {data['iterations']}")
                
            # Show analysis type
            if has_source_info and not is_cached:
                st.info(f"✅ Fresh ReAct analysis completed with {data.get('iterations', 0)} reasoning iterations")
                
        else:
            # Determine why no reasoning data is available
            source = data.get('source', 'unknown')
            if source == 'cache':
                st.info("📚 This is a cached result from a previous analysis. Detailed reasoning steps are not available for cached results.")
            elif not has_source_info:
                st.warning("⚠️ No detailed reasoning information available. This may be an incomplete analysis or cached result.")
            else:
                # This shouldn't happen for fresh analyses
                st.error("❌ No reasoning data available despite being a fresh analysis. This may indicate an issue with the ReAct agent.")
        
        # Display raw data for debugging
        with st.expander("🔍 Raw Analysis Data (Debug)"):
            st.json(data)


def display_visualizations(ticker: str):
    """Displays data visualizations for price trends and sentiment distribution."""
    st.markdown("### 📊 Market Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📈 30-Day Price Trend**")

        from stocksense.data_collectors import get_price_history

        with st.spinner("Fetching real market data..."):
            price_data = get_price_history(ticker, period="1mo")

        if price_data is not None and not price_data.empty:
            price_df = pd.DataFrame({'Price': price_data['Close']})
            st.line_chart(price_df, use_container_width=True)

            current_price = price_data['Close'].iloc[-1]
            prev_price = price_data['Close'].iloc[-2] if len(price_data) > 1 else current_price
            change_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price != 0 else 0
            trend_icon = "📈" if change_pct > 0 else "📉"

            st.markdown(f"""
            <div class="metric-card">
                <h4>{trend_icon} Current Price (Real Data)</h4>
                <h2>${current_price:.2f}</h2>
                <p style="color: {'green' if change_pct > 0 else 'red'};">
                    {change_pct:+.2f}% from previous day
                </p>
                <small style="color: #666;">Source: Yahoo Finance</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error(f"❌ Unable to fetch real price data for {ticker}")
            st.info("Please check if the ticker symbol is valid and try again.")

    with col2:
        st.markdown("**📊 Sentiment Distribution**")

        from stocksense.database import get_latest_analysis

        try:
            cached_result = get_latest_analysis(ticker)
            if cached_result and cached_result.get('sentiment_report'):
                sentiment_data = cached_result['sentiment_report']

                if isinstance(sentiment_data, str) and sentiment_data.strip():
                    sentiment_counts = {'Positive': 0, 'Negative': 0, 'Neutral': 0}

                    text_lower = sentiment_data.lower()

                    lines = sentiment_data.split('\n')
                    for line in lines:
                        line_lower = line.lower()
                        if 'sentiment:' in line_lower or 'sentiment is' in line_lower:
                            if 'positive' in line_lower:
                                sentiment_counts['Positive'] += 1
                            elif 'negative' in line_lower:
                                sentiment_counts['Negative'] += 1
                            elif 'neutral' in line_lower:
                                sentiment_counts['Neutral'] += 1

                    if sum(sentiment_counts.values()) == 0:
                        positive_words = ['positive', 'bullish', 'optimistic', 'strong', 'good', 'gains', 'up', 'growth', 'beat', 'exceeds']
                        negative_words = ['negative', 'bearish', 'pessimistic', 'weak', 'bad', 'losses', 'down', 'decline', 'miss', 'disappoints']
                        neutral_words = ['neutral', 'mixed', 'stable', 'unchanged', 'moderate']

                        for word in positive_words:
                            sentiment_counts['Positive'] += text_lower.count(word)
                        for word in negative_words:
                            sentiment_counts['Negative'] += text_lower.count(word)
                        for word in neutral_words:
                            sentiment_counts['Neutral'] += text_lower.count(word)

                        max_count = max(sentiment_counts.values())
                        if max_count > 10:
                            for key in sentiment_counts:
                                sentiment_counts[key] = min(sentiment_counts[key], 10)

                    if sum(sentiment_counts.values()) == 0:
                        sentiment_counts['Neutral'] = 1

                    sentiment_df = pd.DataFrame(
                        list(sentiment_counts.items()),
                        columns=['Sentiment', 'Count']
                    )

                    if PLOTLY_AVAILABLE:
                        colors = {
                            'Positive': '#28a745',
                            'Negative': '#dc3545',
                            'Neutral': '#6c757d'
                        }

                        fig = go.Figure(data=[
                            go.Bar(
                                x=sentiment_df['Sentiment'],
                                y=sentiment_df['Count'],
                                marker_color=[colors.get(sent, '#6c757d') for sent in sentiment_df['Sentiment']],
                                text=sentiment_df['Count'],
                                textposition='auto',
                            )
                        ])

                        fig.update_layout(
                            title="Sentiment Distribution",
                            xaxis_title="Sentiment",
                            yaxis_title="Count",
                            showlegend=False,
                            height=300,
                            margin=dict(l=20, r=20, t=40, b=20)
                        )

                        st.plotly_chart(fig, use_container_width=True)

                    else:
                        st.bar_chart(sentiment_df.set_index('Sentiment'), use_container_width=True)

                    total_headlines = sum(sentiment_counts.values())
                    dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get) if total_headlines > 0 else "Neutral"

                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>📊 Sentiment Summary</h4>
                        <p><strong>Analysis Available:</strong> ✅</p>
                        <p><strong>Dominant:</strong> {dominant_sentiment}</p>
                        <small style="color: #666;">From real market data</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No sentiment analysis available. Run a new analysis to see sentiment data.")
                    placeholder_df = pd.DataFrame({
                        'Sentiment': ['Positive', 'Negative', 'Neutral'],
                        'Count': [0, 0, 0]
                    })
                    st.bar_chart(placeholder_df.set_index('Sentiment'), use_container_width=True)
            else:
                st.info("No recent sentiment analysis available. Run a new analysis to see sentiment data.")
                placeholder_df = pd.DataFrame({
                    'Sentiment': ['Positive', 'Negative', 'Neutral'],
                    'Count': [0, 0, 0]
                })
                st.bar_chart(placeholder_df.set_index('Sentiment'), use_container_width=True)
        except Exception as e:
            st.warning("Unable to load sentiment data. Run a new analysis to generate sentiment insights.")
            placeholder_df = pd.DataFrame({
                'Sentiment': ['Positive', 'Negative', 'Neutral'],
                'Count': [0, 0, 0]
            })
            st.bar_chart(placeholder_df.set_index('Sentiment'), use_container_width=True)


def display_key_metrics(ticker: str):
    """Displays key financial metrics."""
    st.markdown("### 💰 Key Metrics")

    from stocksense.data_collectors import get_price_history

    with st.spinner("Loading real market metrics..."):
        price_data = get_price_history(ticker, period="1mo")

    if price_data is not None and not price_data.empty:
        current_price = price_data['Close'].iloc[-1]
        prev_price = price_data['Close'].iloc[-2] if len(price_data) > 1 else current_price
        high_30d = price_data['High'].max()
        low_30d = price_data['Low'].min()

        returns = price_data['Close'].pct_change().dropna()
        volatility = returns.std() * 100 if len(returns) > 1 else 0

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            change_pct = ((current_price - prev_price) / prev_price * 100) if prev_price != 0 else 0
            st.metric(
                "💵 Current Price",
                f"${current_price:.2f}",
                f"{change_pct:+.2f}%"
            )

        with col2:
            st.metric(
                "📊 30D High",
                f"${high_30d:.2f}",
                help="Highest price in the last 30 days"
            )

        with col3:
            st.metric(
                "📉 30D Low",
                f"${low_30d:.2f}",
                help="Lowest price in the last 30 days"
            )

        with col4:
            st.metric(
                "📈 Volatility",
                f"{volatility:.1f}%",
                help="Price volatility over the period"
            )

        st.caption("📊 All metrics sourced from Yahoo Finance real-time data")
    else:
        st.error(f"❌ Unable to fetch real market data for {ticker}")
        st.info("Please verify the ticker symbol and try again.")


def clear_database_cache() -> tuple[bool, int | str]:
    """Clear all cached analysis results from the database.

    Returns (success, rows_deleted_or_error_message)
    """
    try:
        import sqlite3
        from stocksense.database import _resolve_db_path  # type: ignore
        db_path = _resolve_db_path()
        
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM analysis_cache')
                rows_deleted = cursor.rowcount
                conn.commit()
            return True, rows_deleted
        else:
            return True, 0  # No database file, so "cleared"
            
    except Exception as e:
        return False, str(e)


def get_cache_stats() -> dict:
    """Get statistics about cached analysis results."""
    try:
        import sqlite3
        import os
        from stocksense.database import _resolve_db_path  # type: ignore
        db_path = _resolve_db_path()
        
        # Debug info for troubleshooting
        debug_info = {
            "db_path": db_path,
            "path_exists": os.path.exists(db_path),
            "file_size_bytes": os.path.getsize(db_path) if os.path.exists(db_path) else 0
        }
        
        if not os.path.exists(db_path):
            return {"total_analyses": 0, "unique_tickers": 0, "db_size_mb": 0, "debug": debug_info}
        
        # Get file size
        db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_cache'")
            if not cursor.fetchone():
                return {"total_analyses": 0, "unique_tickers": 0, "db_size_mb": db_size_mb}
            
            # Get total analyses
            cursor.execute('SELECT COUNT(*) FROM analysis_cache')
            total_analyses = cursor.fetchone()[0]
            
            # Get unique tickers
            cursor.execute('SELECT COUNT(DISTINCT ticker) FROM analysis_cache')
            unique_tickers = cursor.fetchone()[0]
            
            return {
                "total_analyses": total_analyses,
                "unique_tickers": unique_tickers,
                "db_size_mb": db_size_mb,
                "debug": debug_info
            }
            
    except Exception as e:
        return {"total_analyses": 0, "unique_tickers": 0, "db_size_mb": 0, "error": str(e), "debug": {"db_path": "unknown", "path_exists": False, "file_size_bytes": 0}}


def get_cached_tickers() -> list:
    """Get list of all cached ticker symbols."""
    try:
        import sqlite3
        from stocksense.database import _resolve_db_path  # type: ignore
        db_path = _resolve_db_path()
        
        if not os.path.exists(db_path):
            return []
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_cache'")
            if not cursor.fetchone():
                return []
            
            cursor.execute('''
                SELECT DISTINCT ticker, MAX(timestamp) as latest_timestamp, COUNT(*) as analysis_count
                FROM analysis_cache 
                GROUP BY ticker 
                ORDER BY latest_timestamp DESC
            ''')
            
            results = cursor.fetchall()
            return [{"ticker": result[0], "latest": result[1], "count": result[2]} for result in results]
            
    except Exception as e:
        return []


def display_analysis_history():
    """Displays analysis history in sidebar."""
    if st.session_state.analysis_history:
        st.markdown("### 📚 Recent Analyses")

        for i, analysis in enumerate(st.session_state.analysis_history[:5]):
            ticker = analysis['ticker']
            timestamp = analysis['timestamp']
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%m/%d %H:%M")

            if st.button(f"📊 {ticker} - {time_str}", key=f"history_{i}"):
                st.session_state.analysis_result = analysis
                st.rerun()


def display_sidebar():
    with st.sidebar:
        st.markdown("### 🔧 System Status")

        status = check_backend_status()
        if status:
            st.markdown('<p class="status-online">🟢 Backend Online</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-offline">🔴 Backend Offline</p>', unsafe_allow_html=True)
            st.warning("Start the FastAPI server to enable analysis")

        display_analysis_history()

        st.markdown("---")

        st.markdown("### ℹ️ About ReAct Agent")

        with st.expander("How it works"):
            st.markdown("""
            **ReAct Pattern (Reasoning + Action):**

            1. 🧠 **Reasons** about market conditions
            2. 🔧 **Acts** by selecting appropriate tools
            3. 📊 **Observes** the results
            4. 🔄 **Adapts** strategy based on findings
            5. ✅ **Concludes** with comprehensive analysis

            **Features:**
            - Autonomous decision making
            - Dynamic tool selection
            - Real-time sentiment analysis
            - Market trend identification
            """)

        with st.expander("Data Sources"):
            st.markdown("""
            - 📰 **NewsAPI**: Latest market news
            - 📈 **Yahoo Finance**: Price data
            - 🤖 **Google Gemini**: AI analysis
            - 💾 **SQLite**: Result caching
            """)

        st.markdown("---")
        
        # Cache Management Section
        st.markdown("### 💾 Cache Management")
        
        # Force refresh cache stats (no @st.cache_data to ensure fresh data)
        if st.button("🔄 Refresh Cache Stats", help="Force refresh cache statistics"):
            st.rerun()
        
        # Get cache statistics
        cache_stats = get_cache_stats()
        
        if cache_stats.get("error"):
            st.error(f"❌ Cache error: {cache_stats['error']}")
        else:
            # Display cache statistics in a nice format
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📊 Total Analyses", cache_stats["total_analyses"])
            with col2:
                st.metric("🎯 Unique Stocks", cache_stats["unique_tickers"])
            
            if cache_stats["db_size_mb"] > 0:
                st.metric("💾 Database Size", f"{cache_stats['db_size_mb']} MB")
            
            # Show debug info in expandable section
            debug_info = cache_stats.get("debug", {})
            with st.expander("🔍 Debug Info", expanded=False):
                st.code(f"""
Database Path: {debug_info.get('db_path', 'unknown')}
Path Exists: {debug_info.get('path_exists', False)}
File Size: {debug_info.get('file_size_bytes', 0)} bytes
                """.strip())
            
            # Clear cache section
            if cache_stats["total_analyses"] > 0:
                with st.expander("🗑️ Clear Cache", expanded=False):
                    st.markdown(f"""
                    **Current Cache Status:**
                    - {cache_stats['total_analyses']} cached analyses
                    - {cache_stats['unique_tickers']} different stocks
                    - {cache_stats['db_size_mb']} MB database size
                    """)
                    
                    # Show cached tickers
                    cached_tickers = get_cached_tickers()
                    if cached_tickers:
                        st.markdown("**Cached Stocks:**")
                        ticker_display = ", ".join([f"`{item['ticker']}`" for item in cached_tickers[:10]])
                        if len(cached_tickers) > 10:
                            ticker_display += f" *(+{len(cached_tickers)-10} more)*"
                        st.markdown(ticker_display)
                    
                    st.markdown("""
                    ⚠️ **Warning:** This will permanently delete all cached analysis results.
                    Fresh analyses will take longer but will use the latest data.
                    """)
                    
                    # Confirmation checkbox
                    confirm_clear = st.checkbox("I understand this action cannot be undone", key="confirm_cache_clear")
                    
                    # Clear button (only enabled when confirmed)
                    if st.button(
                        "🗑️ Clear All Cached Results", 
                        type="secondary",
                        disabled=not confirm_clear,
                        help="Permanently delete all cached analysis results",
                        use_container_width=True
                    ):
                        with st.spinner("Clearing cache..."):
                            success, result = clear_database_cache()
                            
                        if success:
                            st.success(f"✅ Successfully cleared {result} cached analyses!")
                            # Also clear session state
                            st.session_state.analysis_result = None
                            st.session_state.analysis_history = []
                            time.sleep(1)  # Brief pause to show success message
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to clear cache: {result}")
            else:
                st.info("📭 No cached results to clear")

        st.markdown("---")
        
        if st.button("🗑️ Clear Session Data", help="Clear current analysis results and history from this session only"):
            st.session_state.analysis_result = None
            st.session_state.analysis_history = []
            st.rerun()

def main():
    """Main function for the Streamlit application."""
    display_hero_section()
    display_sidebar()

    main_container = st.container()

    with main_container:
        ticker = display_ticker_input()

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            is_valid, error_msg = validate_ticker(ticker)

            if not is_valid and ticker:
                st.error(f"❌ {error_msg}")

            analyze_button = st.button(
                "🚀 Analyze with ReAct Agent",
                type="primary",
                use_container_width=True,
                disabled=not is_valid,
                help="Trigger autonomous AI analysis using the ReAct pattern"
            )

            if analyze_button and is_valid:
                result = trigger_analysis(ticker)
                if result and result.get('success'):
                    st.success(f"✅ Analysis completed for **{ticker}**!")

        st.markdown("---")

        if st.session_state.analysis_result:
            result_data = st.session_state.analysis_result
            ticker = result_data['ticker']
            data = result_data['data']

            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"## 📊 Analysis Results: {ticker}")

            with col2:
                if st.button("🗑️ Clear", help="Clear current results"):
                    st.session_state.analysis_result = None
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            # Use the enhanced tabbed display
            display_enhanced_analysis_results(data, ticker)

        else:
            st.markdown("""
            <div class="analysis-card fade-in" style="text-align: center; padding: 3rem;">
                <h3>👋 Welcome to StockSense AI Agent</h3>
                <p style="font-size: 1.1rem; color: #666;">
                    Select a stock ticker above to begin your AI-powered market analysis
                </p>
                <p style="color: #888;">
                    Our ReAct agent will autonomously reason about market conditions
                    and select the best tools for comprehensive analysis
                </p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()