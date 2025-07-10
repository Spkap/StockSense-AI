"""
StockSense Agent - Streamlit Frontend Application

This is the main frontend interface for the StockSense Agent, an AI-powered
stock market research tool. It provides a user-friendly web interface to
analyze stock tickers using sentiment analysis and market data.
"""

import streamlit as st
import requests
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional

# Configure the Streamlit page
st.set_page_config(
    page_title="StockSense Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state for persistent data storage
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# Backend API configuration
BACKEND_URL = "http://127.0.0.1:8000"

def main():
    """
    Main function that creates the Streamlit UI and handles user interactions.
    """
    
    # Page header
    st.title("📈 StockSense Agent")
    st.markdown("**AI-Powered Stock Market Research & Sentiment Analysis**")
    st.markdown("---")
    
    # Create columns for better layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # User input section
        st.subheader("🔍 Analyze a Stock")
        
        # Stock ticker input
        ticker = st.text_input(
            "Enter Stock Ticker Symbol:",
            placeholder="e.g., AAPL, MSFT, GOOGL, TSLA",
            help="Enter a valid stock ticker symbol (e.g., AAPL for Apple Inc.)"
        ).upper().strip()
        
        # Analyze button
        analyze_button = st.button(
            "🚀 Analyze Stock",
            type="primary",
            use_container_width=True
        )
        
        # Handle button click
        if analyze_button:
            # Validate ticker input
            if not ticker:
                st.error("⚠️ Please enter a stock ticker symbol before analyzing.")
                st.stop()
            
            # Validate ticker format (basic validation)
            if not ticker.isalpha() or len(ticker) < 1 or len(ticker) > 10:
                st.error("⚠️ Please enter a valid stock ticker symbol (letters only, 1-10 characters).")
                st.stop()
            
            # Show loading spinner and trigger analysis
            with st.spinner("🔄 Analyzing, please wait..."):
                try:
                    # Make POST request to backend to trigger analysis
                    response = requests.post(
                        f"{BACKEND_URL}/analyze/{ticker}",
                        timeout=60  # 60 second timeout for analysis
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display success message
                        st.success(f"✅ Analysis for **{ticker}** has been triggered! Fetching results...")
                        
                        # Show the backend response for debugging (optional)
                        with st.expander("📋 Backend Response Details"):
                            st.json(result)
                        
                        # Polling logic to fetch results
                        st.markdown("---")
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        max_attempts = 10
                        analysis_data = None
                        
                        for attempt in range(1, max_attempts + 1):
                            status_text.text(f"🔍 Fetching results... (Attempt {attempt}/{max_attempts})")
                            progress_bar.progress(attempt / max_attempts)
                            
                            try:
                                # Make GET request to fetch results
                                results_response = requests.get(
                                    f"{BACKEND_URL}/results/{ticker}",
                                    timeout=10
                                )
                                
                                if results_response.status_code == 200:
                                    analysis_data = results_response.json()
                                    status_text.text("✅ Results retrieved successfully!")
                                    progress_bar.progress(1.0)
                                    break
                                elif results_response.status_code == 404:
                                    # Analysis not ready yet, continue polling
                                    if attempt < max_attempts:
                                        time.sleep(2)  # Wait 2 seconds before next attempt
                                    continue
                                else:
                                    st.error(f"❌ Error fetching results: Status {results_response.status_code}")
                                    break
                                    
                            except requests.exceptions.RequestException as e:
                                st.error(f"🚨 Error fetching results: {str(e)}")
                                break
                        
                        # Clear progress indicators
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Display results or error
                        if analysis_data:
                            # Store result in session state for persistence
                            st.session_state.analysis_result = {
                                'ticker': ticker,
                                'data': analysis_data.get('data', analysis_data),
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            st.success(f"✅ Analysis completed and saved for **{ticker}**!")
                            st.info("📌 Results are now persistent - you can interact with other controls without losing data.")
                        
                        else:
                            st.error("❌ Could not retrieve analysis results. Please try again later.")
                            st.info("💡 The analysis might still be processing. Please wait a moment and try again.")
                        
                    else:
                        st.error(f"❌ Error: Received status code {response.status_code} from backend.")
                        st.error(f"Response: {response.text}")
                        
                except requests.exceptions.Timeout:
                    st.error("⏰ Request timed out. The analysis is taking longer than expected. Please try again.")
                    
                except requests.exceptions.ConnectionError:
                    st.error("🔌 Cannot connect to the backend server. Please ensure the FastAPI server is running on http://127.0.0.1:8000")
                    
                except requests.exceptions.RequestException as e:
                    st.error(f"🚨 Request failed: {str(e)}")
                    
                except Exception as e:
                    st.error(f"🚨 Unexpected error: {str(e)}")

    # Persistent Results Display Section
    if st.session_state.analysis_result:
        st.markdown("---")
        
        # Create header with clear button
        result_col1, result_col2 = st.columns([3, 1])
        
        with result_col1:
            ticker = st.session_state.analysis_result['ticker']
            st.header(f"📊 Analysis Results for {ticker}")
        
        with result_col2:
            if st.button("🗑️ Clear Results", type="secondary", key="clear_results"):
                st.session_state.analysis_result = None
                st.rerun()
        
        # Extract data from session state
        data = st.session_state.analysis_result['data']
        
        # Display Analysis Summary
        st.subheader("📝 Analysis Summary")
        summary = data.get('summary') or data.get('analysis_summary')
        if summary:
            st.write(summary)
        else:
            st.info("No summary available.")
        
        # Display Detailed Sentiment Report
        st.subheader("🧠 Detailed Sentiment Report")
        sentiment_report = data.get('sentiment_report')
        if sentiment_report:
            st.markdown(sentiment_report)
        else:
            st.info("No sentiment report available.")
        
        # Data Visualizations Section
        st.subheader("📊 Data Visualizations")
        
        # Create two columns for side-by-side charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Price Chart with placeholder data
            st.markdown("**📈 30-Day Price Trend**")
            
            # Generate placeholder price data (random walk) - consistent for same ticker
            ticker_seed = sum(ord(c) for c in ticker)  # Create consistent seed from ticker
            np.random.seed(ticker_seed)
            days = 30
            dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
            
            # Create realistic stock price movement (random walk)
            initial_price = 100.0 + (ticker_seed % 200)  # Vary initial price by ticker
            daily_returns = np.random.normal(0.001, 0.02, days)  # Small daily returns with volatility
            price_multipliers = np.exp(np.cumsum(daily_returns))
            prices = initial_price * price_multipliers
            
            # Create DataFrame for price data
            price_df = pd.DataFrame({
                'Price': prices
            }, index=dates)
            
            # Display line chart
            st.line_chart(price_df)
            st.caption("30-Day Price Trend (Placeholder Data)")
        
        with col2:
            # Sentiment Distribution Chart
            st.markdown("**🧠 News Sentiment Distribution**")
            
            # Generate placeholder sentiment data based on ticker
            np.random.seed(ticker_seed)
            total_articles = 20 + (ticker_seed % 10)
            positive = max(1, int(np.random.normal(12, 3)))
            negative = max(1, int(np.random.normal(5, 2)))
            neutral = max(1, total_articles - positive - negative)
            
            sentiment_data = pd.DataFrame({
                'Count': [positive, neutral, negative]
            }, index=['Positive', 'Neutral', 'Negative'])
            
            # Display bar chart
            st.bar_chart(sentiment_data)
            st.caption("News Sentiment Distribution (Placeholder Data)")
        
        # Additional metrics in a single row
        st.markdown("---")
        st.markdown("**📊 Key Metrics (Placeholder Data)**")
        
        # Create metrics columns
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.metric(
                label="Current Price", 
                value=f"${prices[-1]:.2f}",
                delta=f"{((prices[-1] - prices[-2]) / prices[-2] * 100):+.1f}%"
            )
        
        with metric_col2:
            st.metric(
                label="30-Day High", 
                value=f"${prices.max():.2f}",
                delta=None
            )
        
        with metric_col3:
            st.metric(
                label="30-Day Low", 
                value=f"${prices.min():.2f}",
                delta=None
            )
        
        with metric_col4:
            volatility = np.std(daily_returns) * 100
            st.metric(
                label="Volatility", 
                value=f"{volatility:.1f}%",
                delta=None
            )
        
        # Display timestamps
        st.markdown("---")
        analysis_time = data.get('timestamp', 'Unknown')
        session_time = st.session_state.analysis_result['timestamp']
        
        time_col1, time_col2 = st.columns(2)
        with time_col1:
            st.caption(f"📅 Analysis completed: {analysis_time}")
        with time_col2:
            st.caption(f"💾 Cached in session: {session_time}")
        
        # Option to show raw data
        with st.expander("📋 Raw Analysis Data"):
            st.json(st.session_state.analysis_result)

    # Sidebar information
    with st.sidebar:
        st.header("ℹ️ About StockSense Agent")
        st.markdown("""
        **StockSense Agent** is an AI-powered tool that provides:
        
        - 📰 **News Analysis**: Fetches recent news headlines
        - 🧠 **AI Sentiment**: Uses Google Gemini for sentiment analysis  
        - 📊 **Market Insights**: Generates comprehensive reports
        - 💾 **Smart Caching**: Stores results for quick retrieval
        
        **How to use:**
        1. Enter a stock ticker symbol (e.g., AAPL)
        2. Click "Analyze Stock" 
        3. Wait for AI analysis to complete
        4. View detailed sentiment report
        """)
        
        st.markdown("---")
        st.markdown("**Backend Status:**")
        
        # Check backend health
        try:
            health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if health_response.status_code == 200:
                st.success("🟢 Backend Online")
            else:
                st.error("🔴 Backend Issues")
        except:
            st.error("🔴 Backend Offline")

if __name__ == "__main__":
    main()
