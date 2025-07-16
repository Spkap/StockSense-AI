"""
StockSense ReAct Agent - Streamlit Frontend Application

This is the main frontend interface for the StockSense ReAct Agent, an AI-powered
stock market research tool that uses the ReAct pattern for autonomous analysis.
It provides a user-friendly web interface to analyze stock tickers using 
dynamic reasoning and tool selection.
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
    page_title="StockSense ReAct Agent",
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
    
    st.title("StockSense ReAct Agent")
    st.markdown("**AI-Powered Autonomous Stock Analysis with Reasoning & Action**")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Analyze a Stock")
        
        ticker = st.text_input(
            "Enter Stock Ticker Symbol:",
            placeholder="e.g., AAPL, MSFT, GOOGL, TSLA",
            help="Enter a valid stock ticker symbol (e.g., AAPL for Apple Inc.)"
        ).upper().strip()
        
        st.info("**Using ReAct Agent**: An intelligent agent that reasons about market conditions and dynamically selects the best tools for analysis.")
        
        analyze_button = st.button(
            "Analyze Stock with ReAct Agent",
            type="primary",
            use_container_width=True
        )
        
        if analyze_button:
            if not ticker:
                st.error("Please enter a stock ticker symbol before analyzing.")
                st.stop()
            
            if not ticker.isalpha() or len(ticker) < 1 or len(ticker) > 10:
                st.error("Please enter a valid stock ticker symbol (letters only, 1-10 characters).")
                st.stop()
            
            with st.spinner("Analyzing, please wait..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/analyze/{ticker}",
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success(f"Analysis for **{ticker}** has been triggered! Fetching results...")
                        
                        with st.expander("Backend Response Details"):
                            st.json(result)
                        
                        st.markdown("---")
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        max_attempts = 10
                        analysis_data = None
                        
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
                                    break
                                elif results_response.status_code == 404:
                                    if attempt < max_attempts:
                                        time.sleep(2)
                                    continue
                                else:
                                    st.error(f"Error fetching results: Status {results_response.status_code}")
                                    break
                                    
                            except requests.exceptions.RequestException as e:
                                st.error(f"Error fetching results: {str(e)}")
                                break
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        if analysis_data:
                            st.session_state.analysis_result = {
                                'ticker': ticker,
                                'data': analysis_data.get('data', analysis_data),
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            st.success(f"Analysis completed and saved for **{ticker}**!")
                            st.info("Results are now persistent - you can interact with other controls without losing data.")
                        
                        else:
                            st.error("Could not retrieve analysis results. Please try again later.")
                            st.info("The analysis might still be processing. Please wait a moment and try again.")
                        
                    else:
                        st.error(f"Error: Received status code {response.status_code} from backend.")
                        st.error(f"Response: {response.text}")
                        
                except requests.exceptions.Timeout:
                    st.error("Request timed out. The analysis is taking longer than expected. Please try again.")
                    
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to the backend server. Please ensure the FastAPI server is running on http://127.0.0.1:8000")
                    
                except requests.exceptions.RequestException as e:
                    st.error(f"Request failed: {str(e)}")
                    
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")

    if st.session_state.analysis_result:
        st.markdown("---")
        
        result_col1, result_col2 = st.columns([3, 1])
        
        with result_col1:
            ticker = st.session_state.analysis_result['ticker']
            st.header(f"Analysis Results for {ticker}")
        
        with result_col2:
            if st.button("Clear Results", type="secondary", key="clear_results"):
                st.session_state.analysis_result = None
                st.rerun()
        
        data = st.session_state.analysis_result['data']
        
        st.subheader("Analysis Summary")
        summary = data.get('summary') or data.get('analysis_summary')
        if summary:
            st.write(summary)
        else:
            st.info("No summary available.")
        
        if data.get('agent_type') == 'ReAct':
            st.subheader("ReAct Agent Information")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Reasoning Iterations",
                    value=data.get('iterations', 0),
                    help="Number of reasoning cycles the agent performed"
                )
            
            with col2:
                tools_used = data.get('tools_used', [])
                st.metric(
                    label="Tools Used",
                    value=len(set(tools_used)),
                    help="Number of different tools the agent selected"
                )
            
            with col3:
                reasoning_steps = data.get('reasoning_steps', [])
                st.metric(
                    label="Reasoning Steps",
                    value=len(reasoning_steps),
                    help="Number of reasoning steps performed"
                )
            
            if reasoning_steps:
                with st.expander("View Reasoning Steps"):
                    for i, step in enumerate(reasoning_steps, 1):
                        st.write(f"**Step {i}:** {step}")
            
            if tools_used:
                with st.expander("View Tools Used"):
                    tool_counts = {}
                    for tool in tools_used:
                        tool_counts[tool] = tool_counts.get(tool, 0) + 1
                    
                    for tool, count in tool_counts.items():
                        st.write(f"• **{tool}**: Used {count} time(s)")
        
        st.subheader("Detailed Sentiment Report")
        sentiment_report = data.get('sentiment_report')
        if sentiment_report:
            st.markdown(sentiment_report)
        else:
            st.info("No sentiment report available.")
        
        st.subheader("Data Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Price Chart with placeholder data
            st.markdown("**30-Day Price Trend**")
            
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
            st.markdown("**News Sentiment Distribution**")
            
            np.random.seed(ticker_seed)
            total_articles = 20 + (ticker_seed % 10)
            positive = max(1, int(np.random.normal(12, 3)))
            negative = max(1, int(np.random.normal(5, 2)))
            neutral = max(1, total_articles - positive - negative)
            
            sentiment_data = pd.DataFrame({
                'Count': [positive, neutral, negative]
            }, index=['Positive', 'Neutral', 'Negative'])
            
            st.bar_chart(sentiment_data)
            st.caption("News Sentiment Distribution (Placeholder Data)")
        
        st.markdown("---")
        st.markdown("**Key Metrics (Placeholder Data)**")
        
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
            st.caption(f"Analysis completed: {analysis_time}")
        with time_col2:
            st.caption(f"Cached in session: {session_time}")
        
        with st.expander("Raw Analysis Data"):
            st.json(st.session_state.analysis_result)

    with st.sidebar:
        st.header("About ReAct Agent")
        st.markdown("""
        **StockSense ReAct Agent** is an autonomous AI system that:
        
        - **Reasons**: Analyzes market conditions and data quality
        - **Acts**: Dynamically selects the best tools for each situation
        - **Adapts**: Adjusts strategy based on observations
        - **Learns**: Improves analysis through iterative reasoning
        
        **ReAct Pattern Features:**
        - Adaptive tool selection based on market context
        - Dynamic reasoning about data quality and completeness
        - Self-correction when encountering issues
        - Context-aware analysis that considers market conditions
        
        **How to use:**
        1. Enter a stock ticker symbol (e.g., AAPL)
        2. Click "Analyze Stock with ReAct Agent"
        3. Watch the agent reason and act autonomously
        4. View comprehensive analysis results
        """)
        
        st.markdown("---")
        st.markdown("**Backend Status:**")
        
        try:
            health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if health_response.status_code == 200:
                st.success("Backend Online")
            else:
                st.error("Backend Issues")
        except:
            st.error("Backend Offline")

if __name__ == "__main__":
    main()
