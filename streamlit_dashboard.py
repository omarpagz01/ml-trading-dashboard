"""
Signals Dashboard - iOS-Inspired Design
With Historical Signals and Latest Signal Tracking
"""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time
import numpy as np
from collections import defaultdict, OrderedDict

# Page configuration - MUST BE FIRST
st.set_page_config(
    page_title="Signals Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# iOS-Inspired CSS with SF Pro Display font
st.markdown("""
<style>
    /* Import SF Pro Display-like font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Main App Background - iOS dark mode style */
    .stApp {
        background: #000000;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .css-1y4p8pa {padding-top: 0rem;}
    
    /* Main Title - iOS style */
    .main-title {
        font-size: 34px;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 32px;
        letter-spacing: -0.5px;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    }
    
    /* Metric Cards - iOS style with subtle glass effect */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 20px 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        background: linear-gradient(135deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.06) 100%);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    .metric-label {
        color: rgba(255, 255, 255, 0.6);
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 32px;
        font-weight: 600;
        line-height: 1;
        margin-bottom: 8px;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        letter-spacing: -1px;
    }
    
    .metric-delta {
        font-size: 13px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.7);
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    }
    
    .metric-delta-positive {
        color: #34C759;
    }
    
    .metric-delta-negative {
        color: #FF453A;
    }
    
    /* Status Badge - iOS pill style */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 8px 16px;
        border-radius: 100px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: -0.2px;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    }
    
    .status-open {
        background: linear-gradient(135deg, #34C759 0%, #30D158 100%);
        color: #000000;
    }
    
    .status-closed {
        background: linear-gradient(135deg, #FF453A 0%, #FF6961 100%);
        color: #ffffff;
    }
    
    .status-after-hours {
        background: linear-gradient(135deg, #FF9500 0%, #FFAB40 100%);
        color: #000000;
    }
    
    /* Section Headers - Clean iOS style */
    .section-header {
        color: #ffffff;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        letter-spacing: -0.5px;
    }
    
    /* Signal Cards - iOS notification style */
    .signal-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.04) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 16px 20px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .signal-card:hover {
        transform: translateX(4px);
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
    }
    
    .signal-long {
        border-left: 3px solid #34C759;
        background: linear-gradient(135deg, rgba(52, 199, 89, 0.1) 0%, rgba(52, 199, 89, 0.02) 100%);
    }
    
    .signal-exit {
        border-left: 3px solid #FF453A;
        background: linear-gradient(135deg, rgba(255, 69, 58, 0.1) 0%, rgba(255, 69, 58, 0.02) 100%);
    }
    
    .signal-hold {
        border-left: 3px solid rgba(255, 255, 255, 0.3);
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
    }
    
    /* Latest Signal Card */
    .latest-signal-card {
        background: linear-gradient(135deg, rgba(52, 199, 89, 0.15) 0%, rgba(52, 199, 89, 0.05) 100%);
        border: 1px solid rgba(52, 199, 89, 0.3);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 16px;
        transition: all 0.3s ease;
    }
    
    .consecutive-indicator {
        display: inline-block;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 4px 12px;
        font-size: 11px;
        color: rgba(255, 255, 255, 0.7);
        margin-top: 8px;
    }
    
    /* Filter Pills */
    .filter-pill {
        display: inline-block;
        padding: 8px 16px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        margin-right: 8px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 13px;
        font-weight: 500;
    }
    
    .filter-pill:hover {
        background: rgba(255, 255, 255, 0.15);
        border-color: rgba(255, 255, 255, 0.3);
    }
    
    .filter-pill.active {
        background: #34C759;
        border-color: #34C759;
        color: #000;
    }
    
    /* Tables - iOS style */
    .dataframe {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif !important;
    }
    
    .stDataFrame {
        background: rgba(255,255,255,0.05);
        border-radius: 20px;
        padding: 4px;
    }
    
    /* Custom Scrollbar - iOS style */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }
    
    /* Loading dot - iOS style */
    @keyframes pulse {
        0%, 80%, 100% { 
            opacity: 0.3;
            transform: scale(0.8);
        }
        40% { 
            opacity: 1;
            transform: scale(1);
        }
    }
    
    .loading-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        background: #34C759;
        border-radius: 50%;
        animation: pulse 1.4s infinite ease-in-out;
        margin-left: 4px;
    }
    
    /* Smooth animations */
    * {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'selected_filter' not in st.session_state:
    st.session_state.selected_filter = 'ALL'

# Define your assets
ASSETS = ['TSLA', 'HOOD', 'COIN', 'PLTR', 'AAPL']

# Helper functions
def process_signals_for_display(signals):
    """Process signals to identify unique trades and consecutive signals"""
    if not signals:
        return [], {}, 0, 0
    
    # Sort signals by timestamp
    sorted_signals = sorted(signals, key=lambda x: x['timestamp'])
    
    # Track latest signal per symbol
    latest_signals = {}
    signal_history = defaultdict(list)
    position_states = {}
    unique_long_count = 0
    unique_exit_count = 0
    
    for sig in sorted_signals:
        symbol = sig['symbol']
        action = sig['action']
        timestamp = sig['timestamp']
        
        # Initialize position if needed
        if symbol not in position_states:
            position_states[symbol] = {'position': 'FLAT', 'first_entry_time': None}
        
        # Track signal history
        signal_history[symbol].append(sig)
        
        # Process based on action
        if action == 'LONG':
            if position_states[symbol]['position'] != 'LONG':
                # New long position
                position_states[symbol]['position'] = 'LONG'
                position_states[symbol]['first_entry_time'] = timestamp
                unique_long_count += 1
                sig['is_new_position'] = True
                sig['consecutive_count'] = 1
            else:
                # Consecutive long signal
                sig['is_new_position'] = False
                if symbol in latest_signals and latest_signals[symbol]['action'] == 'LONG':
                    sig['consecutive_count'] = latest_signals[symbol].get('consecutive_count', 1) + 1
                    sig['first_signal_time'] = position_states[symbol]['first_entry_time']
                else:
                    sig['consecutive_count'] = 1
        
        elif action == 'EXIT':
            if position_states[symbol]['position'] == 'LONG':
                position_states[symbol]['position'] = 'FLAT'
                position_states[symbol]['first_entry_time'] = None
                unique_exit_count += 1
                sig['is_new_position'] = True
            else:
                sig['is_new_position'] = False
        
        else:  # HOLD
            sig['is_new_position'] = False
        
        # Update latest signal for symbol
        latest_signals[symbol] = sig
    
    return sorted_signals, latest_signals, unique_long_count, unique_exit_count

@st.cache_data(ttl=2)
def load_signals():
    """Load today's signals"""
    signal_file = Path("signals") / f"signals_{datetime.now().strftime('%Y%m%d')}.json"
    if signal_file.exists():
        try:
            with open(signal_file, 'r') as f:
                content = f.read()
                if content.strip():
                    return json.loads(content)
        except Exception as e:
            st.error(f"Error loading signals: {e}")
    return []

@st.cache_data(ttl=2)
def load_status():
    """Load current status"""
    status_file = Path("status.json")
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading status: {e}")
    return {}

@st.cache_data(ttl=5)
def load_historical_data(symbol):
    """Load historical price data for a symbol"""
    today = datetime.now().strftime('%Y%m%d')
    data_file = Path("realtime_data") / f"{symbol}_realtime_{today}.parquet"
    if data_file.exists():
        try:
            df = pd.read_parquet(data_file)
            return df
        except:
            pass
    return None

def get_market_status():
    """Check if market is open with styled output"""
    now = datetime.now(timezone(timedelta(hours=-4)))  # ET
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday >= 5:  # Weekend
        return "WEEKEND", "status-closed", "🔴"
    elif current_time < pd.Timestamp("09:30").time():
        return "PRE-MARKET", "status-closed", "🟡"
    elif current_time >= pd.Timestamp("16:00").time():
        return "AFTER-HOURS", "status-after-hours", "🟠"
    elif pd.Timestamp("09:30").time() <= current_time < pd.Timestamp("16:00").time():
        return "MARKET OPEN", "status-open", "🟢"
    else:
        return "CLOSED", "status-closed", "🔴"

def format_currency(value):
    """Format currency values"""
    if value == 0 or value is None:
        return "-"
    return f"${value:,.2f}"

# Main Dashboard
def main():
    # Clean title
    st.markdown('<h1 class="main-title">SIGNALS DASHBOARD</h1>', unsafe_allow_html=True)
    
    # Load data
    raw_signals = load_signals()
    status = load_status()
    
    # Process signals
    all_signals, latest_signals, unique_longs, unique_exits = process_signals_for_display(raw_signals)
    
    if not status:
        st.markdown("""
        <div style="text-align: center; padding: 60px;">
            <div style="font-size: 48px; margin-bottom: 20px;">⏳</div>
            <div style="color: rgba(255,255,255,0.8); font-size: 18px; font-weight: 500;">
                Waiting for trading system data...
            </div>
            <div class="loading-dot" style="margin-top: 20px;"></div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(5)
        st.rerun()
        return
    
    # Get market status
    market_status, status_class, status_icon = get_market_status()
    
    # Top Metrics Row
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Market Status</div>
            <div class="status-badge {status_class}">{market_status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        last_update = datetime.fromisoformat(status['timestamp']) if 'timestamp' in status else datetime.now()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Last Update</div>
            <div class="metric-value">{last_update.strftime('%H:%M:%S')}</div>
            <div class="loading-dot"></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Signals Today</div>
            <div class="metric-value">{len(all_signals)}</div>
            <div class="metric-delta metric-delta-positive">↑ {unique_longs} longs</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        active_positions = sum(1 for p in status.get('positions', {}).values() if p.get('is_open'))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Positions</div>
            <div class="metric-value">{active_positions}</div>
            <div class="metric-delta">of {len(ASSETS)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        # Calculate total P&L
        total_pnl = 0
        if status and 'positions' in status:
            for symbol, pos in status['positions'].items():
                if pos['is_open'] and symbol in status.get('latest_prices', {}):
                    current = status['latest_prices'][symbol]
                    entry = pos['entry_price']
                    if entry > 0:
                        pnl = ((current - entry) / entry * 100)
                        total_pnl += pnl
        
        pnl_color = "#34C759" if total_pnl > 0 else "#FF453A" if total_pnl < 0 else "rgba(255,255,255,0.5)"
        pnl_text = f"{total_pnl:+.2f}%" if total_pnl != 0 else "-"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Open P&L</div>
            <div class="metric-value" style="font-size: 28px; color: {pnl_color};">{pnl_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Trades Today</div>
            <div class="metric-value">{unique_exits}</div>
            <div class="metric-delta">exits</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main Content Area
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        # Latest Signals Section
        st.markdown('<div class="section-header">🎯 Latest Signal Per Asset</div>', unsafe_allow_html=True)
        
        latest_container = st.container()
        with latest_container:
            for symbol in ASSETS:
                if symbol in latest_signals:
                    sig = latest_signals[symbol]
                    sig_time = datetime.fromisoformat(sig['timestamp'])
                    time_str = sig_time.strftime('%H:%M:%S')
                    
                    # Check for consecutive signals
                    consecutive_html = ""
                    if sig.get('consecutive_count', 1) > 1 and 'first_signal_time' in sig:
                        first_time = datetime.fromisoformat(sig['first_signal_time']).strftime('%H:%M')
                        consecutive_html = f"""
                        <div class="consecutive-indicator">
                            📍 Position opened at {first_time} • Updated at {time_str} ({sig['consecutive_count']} signals)
                        </div>
                        """
                    
                    if sig['action'] == 'LONG':
                        card_class = "signal-long"
                        color = "#34C759"
                        icon = "🟢"
                    elif sig['action'] == 'EXIT':
                        card_class = "signal-exit"
                        color = "#FF453A"
                        icon = "🔴"
                    else:
                        card_class = "signal-hold"
                        color = "rgba(255,255,255,0.6)"
                        icon = "⚪"
                    
                    st.markdown(f"""
                    <div class="signal-card {card_class}" style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <div style="font-size: 18px; font-weight: 600; color: {color}; margin-bottom: 4px;">
                                    {icon} {symbol} - {sig['action']}
                                </div>
                                <div style="color: rgba(255,255,255,0.5); font-size: 13px;">
                                    ${sig['price']:.2f} • {time_str}
                                </div>
                                {consecutive_html}
                            </div>
                            <div style="text-align: right;">
                                <div style="color: rgba(255,255,255,0.4); font-size: 11px; text-transform: uppercase;">Confidence</div>
                                <div style="color: {color}; font-size: 24px; font-weight: 700;">
                                    {sig['confidence']*100:.1f}%
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="signal-card" style="margin-bottom: 12px; opacity: 0.5;">
                        <div style="font-size: 16px; color: rgba(255,255,255,0.4);">
                            {symbol} - No signals today
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Historical Signals Section
        st.markdown('<div class="section-header">📜 Historical Signals</div>', unsafe_allow_html=True)
        
        # Filter Pills
        col_filter1, col_filter2 = st.columns([3, 1])
        with col_filter1:
            # Create filter buttons
            filter_html = '<div style="margin-bottom: 20px;">'
            filter_html += f'<span class="filter-pill {"active" if st.session_state.selected_filter == "ALL" else ""}">ALL</span>'
            for asset in ASSETS:
                filter_html += f'<span class="filter-pill {"active" if st.session_state.selected_filter == asset else ""}">{asset}</span>'
            filter_html += '</div>'
            st.markdown(filter_html, unsafe_allow_html=True)
            
            # Asset filter selector
            selected_asset = st.selectbox(
                "Filter by Asset",
                ["ALL"] + ASSETS,
                key="asset_filter",
                label_visibility="collapsed"
            )
        
        # Display filtered historical signals
        historical_container = st.container(height=400)
        with historical_container:
            # Filter signals based on selection
            if selected_asset == "ALL":
                filtered_signals = [s for s in all_signals if s.get('is_new_position', True)]
            else:
                filtered_signals = [s for s in all_signals if s['symbol'] == selected_asset and s.get('is_new_position', True)]
            
            # Sort by time descending
            filtered_signals = sorted(filtered_signals, key=lambda x: x['timestamp'], reverse=True)
            
            if filtered_signals:
                for sig in filtered_signals[:50]:  # Show last 50 signals
                    sig_time = datetime.fromisoformat(sig['timestamp'])
                    time_str = sig_time.strftime('%H:%M:%S')
                    
                    if sig['action'] == 'LONG':
                        st.markdown(f"""
                        <div class="signal-card signal-long">
                            <div style="display: flex; justify-content: space-between;">
                                <div>
                                    <span style="color: #34C759; font-weight: 600;">🟢 {sig['symbol']} - LONG</span>
                                    <span style="color: rgba(255,255,255,0.4); margin-left: 12px; font-size: 12px;">
                                        {time_str} • ${sig['price']:.2f}
                                    </span>
                                </div>
                                <div style="color: #34C759; font-weight: 600;">
                                    {sig['confidence']*100:.1f}%
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif sig['action'] == 'EXIT':
                        st.markdown(f"""
                        <div class="signal-card signal-exit">
                            <div style="display: flex; justify-content: space-between;">
                                <div>
                                    <span style="color: #FF453A; font-weight: 600;">🔴 {sig['symbol']} - EXIT</span>
                                    <span style="color: rgba(255,255,255,0.4); margin-left: 12px; font-size: 12px;">
                                        {time_str} • ${sig['price']:.2f}
                                    </span>
                                </div>
                                <div style="color: #FF453A; font-weight: 600;">
                                    {sig['confidence']*100:.1f}%
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align: center; padding: 40px; color: rgba(255,255,255,0.4);">
                    No signals to display
                </div>
                """, unsafe_allow_html=True)
    
    with col_right:
        # Current Positions
        st.markdown('<div class="section-header">📊 Current Positions</div>', unsafe_allow_html=True)
        
        if status and 'positions' in status:
            for symbol in ASSETS:
                if symbol in status['positions']:
                    pos = status['positions'][symbol]
                    
                    if pos['is_open']:
                        current = status.get('latest_prices', {}).get(symbol, 0)
                        entry = pos['entry_price']
                        if entry > 0 and current > 0:
                            pnl = ((current - entry) / entry * 100)
                            pnl_color = "#34C759" if pnl > 0 else "#FF453A"
                            
                            st.markdown(f"""
                            <div class="signal-card" style="border-left: 3px solid {pnl_color};">
                                <div style="font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 8px;">
                                    {symbol} - LONG
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 13px;">
                                    <div>
                                        <div style="color: rgba(255,255,255,0.5);">Entry</div>
                                        <div style="color: #fff; font-weight: 500;">${entry:.2f}</div>
                                    </div>
                                    <div>
                                        <div style="color: rgba(255,255,255,0.5);">Current</div>
                                        <div style="color: #fff; font-weight: 500;">${current:.2f}</div>
                                    </div>
                                    <div>
                                        <div style="color: rgba(255,255,255,0.5);">P&L</div>
                                        <div style="color: {pnl_color}; font-weight: 600;">{pnl:+.2f}%</div>
                                    </div>
                                    <div>
                                        <div style="color: rgba(255,255,255,0.5);">Confidence</div>
                                        <div style="color: #fff; font-weight: 500;">{pos.get('last_confidence', 0)*100:.1f}%</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
        
        # Price Action
        st.markdown('<div class="section-header">💹 Price Action</div>', unsafe_allow_html=True)
        
        if status and 'latest_prices' in status:
            tabs = st.tabs(ASSETS)
            
            for tab, symbol in zip(tabs, ASSETS):
                with tab:
                    hist_data = load_historical_data(symbol)
                    
                    if hist_data is not None and not hist_data.empty:
                        # Create mini chart
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=pd.to_datetime(hist_data['timestamp']),
                            y=hist_data['close'],
                            mode='lines',
                            name=symbol,
                            line=dict(color='#34C759', width=2)
                        ))
                        
                        # Add signal markers
                        symbol_signals = [s for s in all_signals if s['symbol'] == symbol and s.get('is_new_position')]
                        if symbol_signals:
                            long_sigs = [s for s in symbol_signals if s['action'] == 'LONG']
                            exit_sigs = [s for s in symbol_signals if s['action'] == 'EXIT']
                            
                            if long_sigs:
                                fig.add_trace(go.Scatter(
                                    x=[datetime.fromisoformat(s['timestamp']) for s in long_sigs],
                                    y=[s['price'] for s in long_sigs],
                                    mode='markers',
                                    marker=dict(size=8, color='#34C759', symbol='circle'),
                                    name='Long'
                                ))
                            
                            if exit_sigs:
                                fig.add_trace(go.Scatter(
                                    x=[datetime.fromisoformat(s['timestamp']) for s in exit_sigs],
                                    y=[s['price'] for s in exit_sigs],
                                    mode='markers',
                                    marker=dict(size=8, color='#FF453A', symbol='circle'),
                                    name='Exit'
                                ))
                        
                        fig.update_layout(
                            height=200,
                            showlegend=False,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(255,255,255,0.02)',
                            xaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=False),
                            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=True),
                            margin=dict(l=0, r=0, t=0, b=0),
                            font=dict(color='rgba(255,255,255,0.8)', size=10)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        if symbol in status.get('latest_prices', {}):
                            st.metric(label="Current Price", value=format_currency(status['latest_prices'][symbol]))
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: rgba(255,255,255,0.3); font-size: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;">
        Last Update: {datetime.now().strftime('%H:%M:%S')} • Auto-refresh: 5 seconds • Data: Polygon + Alpaca APIs
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
