"""
Signals Dashboard - Professional iOS-Inspired Design
Clean, aligned, and polished interface
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

# Professional CSS with proper alignment
st.markdown("""
<style>
    /* Import premium font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Reset and base styles */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* Main App Background */
    .stApp {
        background: #000000;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'SF Pro Display', 'Segoe UI', sans-serif;
    }
    
    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* Main Title */
    .main-title {
        font-size: 36px;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin: 0 0 2rem 0;
        letter-spacing: -1px;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    }
    
    /* Metric Cards - Uniform height and alignment */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.04) 100%);
        border-color: rgba(255, 255, 255, 0.12);
    }
    
    .metric-label {
        color: rgba(255, 255, 255, 0.5);
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin: 0;
        line-height: 1;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 32px;
        font-weight: 600;
        line-height: 1;
        margin: 8px 0;
        letter-spacing: -1px;
    }
    
    .metric-delta {
        font-size: 13px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.6);
        line-height: 1;
    }
    
    .metric-delta-positive {
        color: #34C759;
    }
    
    .metric-delta-negative {
        color: #FF453A;
    }
    
    /* Status Badge - Consistent sizing */
    .status-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 6px 14px;
        border-radius: 100px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.2px;
        margin-top: 8px;
        white-space: nowrap;
    }
    
    .status-open {
        background: linear-gradient(135deg, #34C759, #30D158);
        color: #000000;
    }
    
    .status-closed {
        background: linear-gradient(135deg, #FF453A, #FF6961);
        color: #ffffff;
    }
    
    .status-after-hours {
        background: linear-gradient(135deg, #FF9500, #FFAB00);
        color: #000000;
    }
    
    /* Section Headers */
    .section-header {
        color: #ffffff;
        font-size: 20px;
        font-weight: 600;
        margin: 24px 0 16px 0;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        letter-spacing: -0.5px;
    }
    
    /* Signal Cards - Consistent styling */
    .signal-card {
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        transition: all 0.2s ease;
    }
    
    .signal-card:hover {
        background: rgba(255,255,255,0.06);
        transform: translateX(2px);
    }
    
    .signal-long {
        background: linear-gradient(90deg, rgba(52, 199, 89, 0.15), rgba(52, 199, 89, 0.05));
        border-left: 3px solid #34C759;
    }
    
    .signal-exit {
        background: linear-gradient(90deg, rgba(255, 69, 58, 0.15), rgba(255, 69, 58, 0.05));
        border-left: 3px solid #FF453A;
    }
    
    .signal-hold {
        border-left: 3px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Latest signal specific */
    .latest-signal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    
    .latest-signal-symbol {
        font-size: 18px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .latest-signal-details {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: rgba(255, 255, 255, 0.6);
        font-size: 13px;
    }
    
    .confidence-display {
        text-align: right;
    }
    
    .confidence-label {
        color: rgba(255, 255, 255, 0.4);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    
    .confidence-value {
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Consecutive indicator */
    .consecutive-indicator {
        display: inline-block;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 4px 10px;
        font-size: 11px;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 8px;
    }
    
    /* Position card styling */
    .position-card {
        background: rgba(255,255,255,0.04);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    .position-header {
        font-size: 16px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .position-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
    }
    
    .position-metric {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    
    .position-metric-label {
        color: rgba(255, 255, 255, 0.5);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    
    .position-metric-value {
        color: #ffffff;
        font-size: 14px;
        font-weight: 500;
    }
    
    /* Filter styling */
    .filter-container {
        display: flex;
        gap: 8px;
        margin-bottom: 16px;
        flex-wrap: wrap;
    }
    
    .filter-pill {
        padding: 6px 14px;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        color: rgba(255, 255, 255, 0.7);
        font-size: 12px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .filter-pill:hover {
        background: rgba(255, 255, 255, 0.12);
        color: #ffffff;
    }
    
    .filter-pill.active {
        background: #34C759;
        border-color: #34C759;
        color: #000000;
    }
    
    /* Historical signal styling */
    .historical-signal {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        margin-bottom: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        transition: all 0.15s ease;
    }
    
    .historical-signal:hover {
        background: rgba(255,255,255,0.05);
    }
    
    .historical-signal-info {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .historical-signal-symbol {
        font-weight: 600;
        font-size: 14px;
    }
    
    .historical-signal-time {
        color: rgba(255, 255, 255, 0.5);
        font-size: 12px;
    }
    
    .historical-signal-confidence {
        font-weight: 600;
        font-size: 14px;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
    }
    
    /* Loading animation */
    @keyframes pulse {
        0%, 100% { opacity: 0.4; }
        50% { opacity: 1; }
    }
    
    .loading-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        background: #34C759;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .metric-card {
            height: auto;
            min-height: 100px;
        }
        
        .metric-value {
            font-size: 24px;
        }
    }
    
    /* Remove Streamlit default margins */
    .element-container {
        margin: 0 !important;
    }
    
    .stMetric {
        background: transparent !important;
    }
    
    [data-testid="metric-container"] {
        background: transparent !important;
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
        return [], {}, 0, 0, None
    
    # Sort signals by timestamp
    sorted_signals = sorted(signals, key=lambda x: x['timestamp'])
    
    # Get last signal time
    last_signal_time = datetime.fromisoformat(sorted_signals[-1]['timestamp']) if sorted_signals else None
    
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
    
    return sorted_signals, latest_signals, unique_long_count, unique_exit_count, last_signal_time

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
    # Title
    st.markdown('<h1 class="main-title">SIGNALS DASHBOARD</h1>', unsafe_allow_html=True)
    
    # Load data
    raw_signals = load_signals()
    status = load_status()
    
    # Process signals
    all_signals, latest_signals, unique_longs, unique_exits, last_signal_time = process_signals_for_display(raw_signals)
    
    if not status:
        st.markdown("""
        <div style="text-align: center; padding: 80px 20px;">
            <div style="font-size: 48px; margin-bottom: 20px;">⏳</div>
            <div style="color: rgba(255,255,255,0.7); font-size: 18px; font-weight: 500;">
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
    
    # Top Metrics Row - Properly aligned
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Market Status</div>
            <div class="status-badge {status_class}">{market_status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Use last signal time instead of status timestamp
        if last_signal_time:
            display_time = last_signal_time.strftime('%H:%M:%S')
        else:
            display_time = "--:--:--"
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Last Signal</div>
            <div class="metric-value" style="font-size: 24px;">{display_time}</div>
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
            <div class="metric-value" style="font-size: 26px; color: {pnl_color};">{pnl_text}</div>
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
    
    # Main Content Area
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        # Latest Signals Section
        st.markdown('<div class="section-header">🎯 Latest Signal Per Asset</div>', unsafe_allow_html=True)
        
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
                        📍 Opened at {first_time} • Updated at {time_str} • {sig['consecutive_count']} signals
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
                <div class="signal-card {card_class}">
                    <div class="latest-signal-header">
                        <div class="latest-signal-symbol">
                            {icon} {symbol} - {sig['action']}
                        </div>
                        <div class="confidence-display">
                            <div class="confidence-label">Confidence</div>
                            <div class="confidence-value" style="color: {color};">
                                {sig['confidence']*100:.1f}%
                            </div>
                        </div>
                    </div>
                    <div class="latest-signal-details">
                        <div>${sig['price']:.2f} • {time_str}</div>
                    </div>
                    {consecutive_html}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="signal-card" style="opacity: 0.3;">
                    <div style="font-size: 14px; color: rgba(255,255,255,0.4);">
                        {symbol} - No signals today
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Historical Signals Section
        st.markdown('<div class="section-header">📜 Historical Signals</div>', unsafe_allow_html=True)
        
        # Filter selector
        selected_asset = st.selectbox(
            "Filter by Asset",
            ["ALL"] + ASSETS,
            key="asset_filter",
            label_visibility="collapsed"
        )
        
        # Display filtered historical signals
        historical_container = st.container(height=350)
        with historical_container:
            # Filter signals
            if selected_asset == "ALL":
                filtered_signals = [s for s in all_signals if s.get('is_new_position', True)]
            else:
                filtered_signals = [s for s in all_signals if s['symbol'] == selected_asset and s.get('is_new_position', True)]
            
            # Sort by time descending
            filtered_signals = sorted(filtered_signals, key=lambda x: x['timestamp'], reverse=True)
            
            if filtered_signals:
                for sig in filtered_signals[:50]:
                    sig_time = datetime.fromisoformat(sig['timestamp'])
                    time_str = sig_time.strftime('%H:%M:%S')
                    
                    if sig['action'] == 'LONG':
                        action_color = "#34C759"
                        icon = "🟢"
                    elif sig['action'] == 'EXIT':
                        action_color = "#FF453A"
                        icon = "🔴"
                    else:
                        action_color = "rgba(255,255,255,0.5)"
                        icon = "⚪"
                    
                    st.markdown(f"""
                    <div class="historical-signal">
                        <div class="historical-signal-info">
                            <span style="color: {action_color}; font-weight: 600;">
                                {icon} {sig['symbol']} - {sig['action']}
                            </span>
                            <span class="historical-signal-time">
                                {time_str} • ${sig['price']:.2f}
                            </span>
                        </div>
                        <div class="historical-signal-confidence" style="color: {action_color};">
                            {sig['confidence']*100:.1f}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align: center; padding: 40px; color: rgba(255,255,255,0.3);">
                    No signals to display
                </div>
                """, unsafe_allow_html=True)
    
    with col_right:
        # Current Positions
        st.markdown('<div class="section-header">📊 Current Positions</div>', unsafe_allow_html=True)
        
        if status and 'positions' in status:
            has_positions = False
            for symbol in ASSETS:
                if symbol in status['positions']:
                    pos = status['positions'][symbol]
                    
                    if pos['is_open']:
                        has_positions = True
                        current = status.get('latest_prices', {}).get(symbol, 0)
                        entry = pos['entry_price']
                        if entry > 0 and current > 0:
                            pnl = ((current - entry) / entry * 100)
                            pnl_color = "#34C759" if pnl > 0 else "#FF453A"
                            
                            st.markdown(f"""
                            <div class="position-card" style="border-left: 3px solid {pnl_color};">
                                <div class="position-header">
                                    🟢 {symbol} - LONG
                                </div>
                                <div class="position-grid">
                                    <div class="position-metric">
                                        <div class="position-metric-label">Entry</div>
                                        <div class="position-metric-value">${entry:.2f}</div>
                                    </div>
                                    <div class="position-metric">
                                        <div class="position-metric-label">Current</div>
                                        <div class="position-metric-value">${current:.2f}</div>
                                    </div>
                                    <div class="position-metric">
                                        <div class="position-metric-label">P&L</div>
                                        <div class="position-metric-value" style="color: {pnl_color}; font-weight: 600;">
                                            {pnl:+.2f}%
                                        </div>
                                    </div>
                                    <div class="position-metric">
                                        <div class="position-metric-label">Confidence</div>
                                        <div class="position-metric-value">
                                            {pos.get('last_confidence', 0)*100:.1f}%
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            
            if not has_positions:
                st.markdown("""
                <div style="text-align: center; padding: 40px; color: rgba(255,255,255,0.3);">
                    No open positions
                </div>
                """, unsafe_allow_html=True)
        
        # Price Action
        st.markdown('<div class="section-header">💹 Price Action</div>', unsafe_allow_html=True)
        
        if status and 'latest_prices' in status:
            for symbol in ASSETS:
                if symbol in status.get('latest_prices', {}):
                    price = status['latest_prices'][symbol]
                    
                    # Check if we have a position
                    has_position = False
                    pnl = 0
                    if symbol in status.get('positions', {}):
                        pos = status['positions'][symbol]
                        if pos['is_open'] and pos['entry_price'] > 0:
                            has_position = True
                            pnl = ((price - pos['entry_price']) / pos['entry_price'] * 100)
                    
                    color = "#34C759" if pnl > 0 else "#FF453A" if pnl < 0 else "rgba(255,255,255,0.7)"
                    
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; 
                         padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <div style="font-size: 14px; font-weight: 500; color: rgba(255,255,255,0.9);">
                            {symbol}
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 16px; font-weight: 600; color: #ffffff;">
                                ${price:.2f}
                            </div>
                            {f'<div style="font-size: 12px; color: {color};">{pnl:+.2f}%</div>' if has_position else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: rgba(255,255,255,0.3); font-size: 12px; 
         font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif; padding: 20px 0;">
        Last Signal: {last_signal_time.strftime('%H:%M:%S') if last_signal_time else 'N/A'} • 
        Auto-refresh: 5 seconds • 
        Data: Polygon + Alpaca APIs
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
