import streamlit as st
import requests
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import yfinance as yf

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

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

BACKEND_URL = "http://127.0.0.1:8000"

POPULAR_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
    "NVDA", "META", "NFLX", "AMD", "INTC"
]

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
            AI-Powered Stock Analysis Using Reasoning & Acting
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

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Quick Select:**")
        cols = st.columns(5)
        for i, ticker in enumerate(POPULAR_TICKERS[:5]):
            with cols[i]:
                if st.button(ticker, key=f"quick_{ticker}", use_container_width=True):
                    st.session_state.selected_ticker = ticker

        cols = st.columns(5)
        for i, ticker in enumerate(POPULAR_TICKERS[5:]):
            with cols[i]:
                if st.button(ticker, key=f"quick_{ticker}", use_container_width=True):
                    st.session_state.selected_ticker = ticker

    with col2:
        st.markdown("**Or enter manually:**")
        manual_ticker = st.text_input(
            "Stock Ticker",
            value=st.session_state.selected_ticker,
            placeholder="e.g., AAPL",
            help="Enter any valid stock ticker symbol",
            label_visibility="collapsed"
        )

        if manual_ticker != st.session_state.selected_ticker:
            st.session_state.selected_ticker = manual_ticker.upper().strip()

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

            st.success(f"Analysis for **{ticker}** has been triggered! Fetching results...")

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


def display_analysis_summary(data: Dict[str, Any], ticker: str):
    """Displays the analysis summary."""
    summary = data.get('summary') or data.get('analysis_summary')

    if summary:
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
        st.info("📝 Summary not available")


def display_sentiment_analysis(data: Dict[str, Any]):
    """Displays sentiment analysis."""
    sentiment_report_raw = data.get('sentiment_report')
    sentiment_report_data = None
    sentiment_report_string = None

    if isinstance(sentiment_report_raw, str) and sentiment_report_raw.strip():
        try:
            parsed_report = json.loads(sentiment_report_raw)
            if isinstance(parsed_report, list) and parsed_report:
                sentiment_report_data = parsed_report
            else:
                sentiment_report_string = sentiment_report_raw
        except json.JSONDecodeError:
            sentiment_report_string = sentiment_report_raw
    elif isinstance(sentiment_report_raw, list) and sentiment_report_raw:
        sentiment_report_data = sentiment_report_raw

    st.markdown("### 📈 Sentiment Analysis")

    if sentiment_report_data or sentiment_report_string:
        with st.container():
            st.markdown("""
                <h4 style="color: #667eea; margin-bottom: 1rem; font-size: 1.3rem; border-bottom: 2px solid #e1e5e9; padding-bottom: 0.5rem;">
                    📊 Market Sentiment Report
                </h4>
            """, unsafe_allow_html=True)

            if sentiment_report_data:
                st.markdown("<h5>Headline Sentiment Analysis:</h5>", unsafe_allow_html=True)
                for i, item in enumerate(sentiment_report_data, 1):
                    headline = item.get('headline', 'N/A')
                    sentiment = item.get('sentiment', 'N/A')
                    justification = item.get('justification', 'N/A')

                    st.markdown(f"**{i}. {headline}**")
                    st.markdown(f"&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;**Sentiment:** {sentiment}", unsafe_allow_html=True)
                    st.markdown(f"&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;**Justification:** {justification}", unsafe_allow_html=True)
                    if i < len(sentiment_report_data):
                        st.markdown("<br>", unsafe_allow_html=True)

            elif sentiment_report_string:
                st.markdown(f"<div>{sentiment_report_string}</div>", unsafe_allow_html=True)
    else:
        st.info("📊 Sentiment analysis not available for this stock.")


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
            **ReAct Pattern (Reasoning + Acting):**

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
        if st.button("🗑️ Clear All Data", help="Clear analysis results and history"):
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

            display_analysis_summary(data, ticker)
            display_key_metrics(ticker)
            st.markdown("<br>", unsafe_allow_html=True)
            display_visualizations(ticker)
            st.markdown("<br>", unsafe_allow_html=True)
            display_sentiment_analysis(data)

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