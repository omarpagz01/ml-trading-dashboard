"""
Elite Signals Dashboard - Professional Trading Interface
Complete with Historical Signals, P&L Tracking, and Performance Analytics
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

# Page configuration
st.set_page_config(
    page_title="Signals Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Elite Professional CSS - Keeping ALL original styling
st.markdown("""
<style>
    /* Premium Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Root Variables */
    :root {
        --primary-green: #34C759;
        --primary-red: #FF453A;
        --primary-orange: #FF9500;
        --bg-primary: #000000;
        --bg-secondary: rgba(255,255,255,0.03);
        --bg-hover: rgba(255,255,255,0.05);
        --border-color: rgba(255,255,255,0.08);
        --text-primary: #ffffff;
        --text-secondary: rgba(255,255,255,0.6);
        --text-tertiary: rgba(255,255,255,0.4);
    }
    
    /* Reset */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* Base */
    .stApp {
        background: var(--bg-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {
        padding: 2rem 2rem 0 2rem !important;
        max-width: 100% !important;
    }
    
    /* Main Title */
    .main-title {
        font-size: 32px;
        font-weight: 700;
        color: var(--text-primary);
        text-align: center;
        margin: 0 0 2rem 0;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    
    /* Connection Status */
    .connection-status {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        background: rgba(52, 199, 89, 0.1);
        border: 1px solid rgba(52, 199, 89, 0.3);
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--primary-green);
        box-shadow: 0 0 8px var(--primary-green);
    }
    
    .status-dot.disconnected {
        background: var(--primary-red);
        box-shadow: 0 0 8px var(--primary-red);
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid var(--border-color);
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255,255,255,0.12);
    }
    
    .metric-label {
        color: var(--text-tertiary);
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-value {
        color: var(--text-primary);
        font-size: 28px;
        font-weight: 600;
        line-height: 1;
        letter-spacing: -0.5px;
    }
    
    .metric-delta {
        font-size: 12px;
        font-weight: 500;
        color: var(--text-secondary);
    }
    
    .metric-delta-positive {
        color: var(--primary-green);
    }
    
    .metric-delta-negative {
        color: var(--primary-red);
    }
    
    /* Override Streamlit metrics to match elite style */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid var(--border-color);
        height: 100px;
        transition: all 0.2s ease;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        border-color: rgba(255,255,255,0.12);
    }
    
    [data-testid="metric-container"] label {
        color: var(--text-tertiary) !important;
        font-size: 10px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: var(--text-primary) !important;
        font-size: 28px !important;
        font-weight: 600 !important;
        line-height: 1 !important;
        letter-spacing: -0.5px !important;
    }
    
    [data-testid="metric-container"] [data-testid="metric-delta"] {
        font-size: 12px !important;
        font-weight: 500 !important;
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    
    .status-open {
        background: linear-gradient(135deg, #34C759, #30D158);
        color: #000;
    }
    
    .status-closed {
        background: linear-gradient(135deg, #FF453A, #FF6961);
        color: #fff;
    }
    
    .status-after-hours {
        background: linear-gradient(135deg, #FF9500, #FFAB00);
        color: #000;
    }
    
    /* Section Headers */
    .section-header {
        color: var(--text-primary);
        font-size: 18px;
        font-weight: 600;
        margin: 24px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border-color);
        letter-spacing: -0.3px;
    }
    
    /* Signal Cards */
    .signal-card {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        border: 1px solid var(--border-color);
        transition: all 0.15s ease;
    }
    
    .signal-card:hover {
        background: var(--bg-hover);
        transform: translateX(2px);
    }
    
    .signal-long {
        background: linear-gradient(90deg, rgba(52, 199, 89, 0.1), transparent);
        border-left: 2px solid var(--primary-green);
    }
    
    .signal-exit {
        background: linear-gradient(90deg, rgba(255, 69, 58, 0.1), transparent);
        border-left: 2px solid var(--primary-red);
    }
    
    .signal-hold {
        border-left: 2px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Performance Card */
    .performance-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid var(--border-color);
        margin-bottom: 16px;
    }
    
    .performance-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-top: 16px;
    }
    
    .performance-metric {
        text-align: center;
    }
    
    .performance-metric-value {
        font-size: 24px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 4px;
    }
    
    .performance-metric-label {
        font-size: 10px;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Custom container styles */
    .stContainer > div {
        background: linear-gradient(90deg, rgba(52, 199, 89, 0.1), transparent);
        border-left: 2px solid var(--primary-green);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    
    /* Success/Error/Info boxes as signal cards */
    .stSuccess, .stError, .stInfo {
        background: var(--bg-secondary) !important;
        border-radius: 12px !important;
        padding: 14px 16px !important;
        margin-bottom: 10px !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
    }
    
    .stSuccess {
        background: linear-gradient(90deg, rgba(52, 199, 89, 0.1), transparent) !important;
        border-left: 2px solid var(--primary-green) !important;
    }
    
    .stError {
        background: linear-gradient(90deg, rgba(255, 69, 58, 0.1), transparent) !important;
        border-left: 2px solid var(--primary-red) !important;
    }
    
    .stInfo {
        border-left: 2px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        border: 1px solid var(--border-color);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: rgba(255,255,255,0.6);
        font-weight: 500;
        font-size: 14px;
        letter-spacing: 0.3px;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(255,255,255,0.1) !important;
        color: #ffffff !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 4px;
        height: 4px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.1);
        border-radius: 2px;
    }
    
    /* Consecutive indicator */
    .consecutive-indicator {
        display: inline-block;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 10px;
        color: var(--text-secondary);
        margin-top: 6px;
    }
    
    /* Position card styling */
    .position-card {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        border: 1px solid var(--border-color);
    }
    
    /* Make sure captions are styled properly */
    .caption {
        font-size: 11px !important;
        color: var(--text-tertiary) !important;
        letter-spacing: 0.3px !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'trades_history' not in st.session_state:
    st.session_state.trades_history = []

# Define assets
ASSETS = ['TSLA', 'HOOD', 'COIN', 'PLTR', 'AAPL']

# Helper Functions
def load_trades_history():
    """Load historical trades from file"""
    trades_file = Path("data/trades_history.json")
    if trades_file.exists():
        try:
            with open(trades_file, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_trade(trade_data):
    """Save a completed trade"""
    trades_file = Path("data/trades_history.json")
    trades_file.parent.mkdir(exist_ok=True)
    
    trades = load_trades_history()
    trades.append(trade_data)
    
    with open(trades_file, 'w') as f:
        json.dump(trades, f, indent=2)

def calculate_performance_metrics(trades, symbol_filter=None):
    """Calculate performance metrics from trades"""
    if symbol_filter and symbol_filter != "ALL":
        trades = [t for t in trades if t.get('symbol') == symbol_filter]
    
    if not trades:
        return {
            'total_pnl': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_win': 0,
            'avg_loss': 0
        }
    
    wins = [t for t in trades if t.get('pnl_percent', 0) > 0]
    losses = [t for t in trades if t.get('pnl_percent', 0) < 0]
    
    total_wins = sum(t.get('pnl_percent', 0) for t in wins)
    total_losses = abs(sum(t.get('pnl_percent', 0) for t in losses))
    
    return {
        'total_pnl': sum(t.get('pnl_percent', 0) for t in trades),
        'win_rate': (len(wins) / len(trades) * 100) if trades else 0,
        'profit_factor': (total_wins / total_losses) if total_losses > 0 else total_wins,
        'total_trades': len(trades),
        'winning_trades': len(wins),
        'losing_trades': len(losses),
        'avg_win': (total_wins / len(wins)) if wins else 0,
        'avg_loss': (total_losses / len(losses)) if losses else 0
    }

def process_signals_for_display(signals, status):
    """Process signals and track trades with consecutive signal detection"""
    if not signals:
        return [], {}, 0, 0, None
    
    sorted_signals = sorted(signals, key=lambda x: x['timestamp'])
    last_signal_time = datetime.fromisoformat(sorted_signals[-1]['timestamp']) if sorted_signals else None
    
    # Track positions and trades
    latest_signals = {}
    position_states = {}
    unique_long_count = 0
    unique_exit_count = 0
    
    for sig in sorted_signals:
        symbol = sig['symbol']
        action = sig['action']
        timestamp = sig['timestamp']
        
        if symbol not in position_states:
            position_states[symbol] = {
                'position': 'FLAT', 
                'entry_price': 0, 
                'entry_time': None,
                'first_entry_time': None,
                'consecutive_count': 0
            }
        
        if action == 'LONG':
            if position_states[symbol]['position'] != 'LONG':
                # New position
                position_states[symbol] = {
                    'position': 'LONG',
                    'entry_price': sig['price'],
                    'entry_time': timestamp,
                    'first_entry_time': timestamp,
                    'consecutive_count': 1
                }
                unique_long_count += 1
                sig['is_new_position'] = True
                sig['consecutive_count'] = 1
            else:
                # Consecutive signal
                position_states[symbol]['consecutive_count'] += 1
                sig['is_new_position'] = False
                sig['consecutive_count'] = position_states[symbol]['consecutive_count']
                sig['first_signal_time'] = position_states[symbol]['first_entry_time']
                
        elif action == 'EXIT' and position_states[symbol]['position'] == 'LONG':
            # Calculate and save trade
            entry_price = position_states[symbol]['entry_price']
            exit_price = sig['price']
            pnl_percent = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            trade_data = {
                'symbol': symbol,
                'entry_time': position_states[symbol]['entry_time'],
                'exit_time': timestamp,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl_percent': pnl_percent,
                'pnl_dollar': (exit_price - entry_price) * 100
            }
            
            # Check if trade already exists
            existing_trades = load_trades_history()
            if not any(t['exit_time'] == timestamp and t['symbol'] == symbol for t in existing_trades):
                save_trade(trade_data)
            
            position_states[symbol] = {'position': 'FLAT', 'entry_price': 0, 'entry_time': None}
            unique_exit_count += 1
            sig['is_new_position'] = True
        else:
            sig['is_new_position'] = False
        
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
        except:
            pass
    return []

@st.cache_data(ttl=2)
def load_status():
    """Load current status"""
    status_file = Path("status.json")
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def get_market_status():
    """Check market status"""
    now = datetime.now(timezone(timedelta(hours=-4)))
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday >= 5:
        return "WEEKEND", "status-closed"
    elif current_time < pd.Timestamp("09:30").time():
        return "PRE-MARKET", "status-closed"
    elif current_time >= pd.Timestamp("16:00").time():
        return "AFTER-HOURS", "status-after-hours"
    elif pd.Timestamp("09:30").time() <= current_time < pd.Timestamp("16:00").time():
        return "MARKET OPEN", "status-open"
    else:
        return "CLOSED", "status-closed"

# Main Dashboard
def main():
    # Load data
    raw_signals = load_signals()
    status = load_status()
    trades_history = load_trades_history()
    
    # Check connection status
    is_connected = bool(status and 'timestamp' in status)
    if is_connected:
        last_update = datetime.fromisoformat(status['timestamp'])
        time_diff = (datetime.now() - last_update).total_seconds()
        is_connected = time_diff < 120
    
    # Title with connection status
    connection_badge = "LIVE" if is_connected else "OFFLINE"
    connection_color = "#34C759" if is_connected else "#FF453A"
    
    st.markdown(f"""
    <h1 class="main-title">
        SIGNALS DASHBOARD
        <span class="connection-status" style="background: rgba({'52, 199, 89' if is_connected else '255, 69, 58'}, 0.1); 
              border: 1px solid {connection_color};">
            <span class="status-dot {'connected' if is_connected else 'disconnected'}"></span>
            {connection_badge}
        </span>
    </h1>
    """, unsafe_allow_html=True)
    
    if not status:
        with st.container():
            st.markdown("""
            <div style="text-align: center; padding: 80px; color: var(--text-secondary);">
                <div style="font-size: 20px;">Waiting for trading system data...</div>
            </div>
            """, unsafe_allow_html=True)
        time.sleep(5)
        st.rerun()
        return
    
    # Process signals
    all_signals, latest_signals, unique_longs, unique_exits, last_signal_time = process_signals_for_display(raw_signals, status)
    
    # Get market status
    market_status, status_class = get_market_status()
    
    # Top Metrics Row - Using Streamlit metrics with custom styling
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Market Status", market_status)
    
    with col2:
        display_time = last_signal_time.strftime('%H:%M:%S') if last_signal_time else "--:--:--"
        st.metric("Last Signal", display_time)
    
    with col3:
        st.metric("Signals Today", len(all_signals), f"↑ {unique_longs} longs")
    
    with col4:
        active_positions = sum(1 for p in status.get('positions', {}).values() if p.get('is_open'))
        st.metric("Active Positions", f"{active_positions}/{len(ASSETS)}")
    
    with col5:
        total_pnl = 0
        if status and 'positions' in status:
            for symbol, pos in status['positions'].items():
                if pos['is_open'] and symbol in status.get('latest_prices', {}):
                    current = status['latest_prices'][symbol]
                    entry = pos['entry_price']
                    if entry > 0:
                        pnl = ((current - entry) / entry * 100)
                        total_pnl += pnl
        st.metric("Open P&L", f"{total_pnl:+.2f}%")
    
    with col6:
        st.metric("Closed Today", unique_exits, "trades")
    
    # Performance Overview Section
    st.markdown('<div class="section-header">📈 Portfolio Performance</div>', unsafe_allow_html=True)
    
    perf_col1, perf_col2 = st.columns([1, 5])
    with perf_col1:
        perf_filter = st.selectbox("Filter", ["ALL"] + ASSETS, key="perf_filter")
    
    metrics = calculate_performance_metrics(trades_history, perf_filter)
    
    # Performance metrics in a card
    st.markdown(f"""
    <div class="performance-card">
        <div class="performance-grid">
            <div class="performance-metric">
                <div class="performance-metric-value" style="color: {'#34C759' if metrics['total_pnl'] > 0 else '#FF453A'};">
                    {metrics['total_pnl']:+.2f}%
                </div>
                <div class="performance-metric-label">Total P&L</div>
            </div>
            <div class="performance-metric">
                <div class="performance-metric-value">
                    {metrics['win_rate']:.1f}%
                </div>
                <div class="performance-metric-label">Win Rate</div>
            </div>
            <div class="performance-metric">
                <div class="performance-metric-value">
                    {metrics['profit_factor']:.2f}
                </div>
                <div class="performance-metric-label">Profit Factor</div>
            </div>
            <div class="performance-metric">
                <div class="performance-metric-value">
                    {metrics['total_trades']}
                </div>
                <div class="performance-metric-label">Total Trades</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content with tabs
    tab1, tab2, tab3 = st.tabs(["�� Live Signals", "📜 Historical Signals", "💰 Trade History"])
    
    with tab1:
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.markdown('<div class="section-header">🎯 Latest Signal Per Asset</div>', unsafe_allow_html=True)
            
            for symbol in ASSETS:
                if symbol in latest_signals:
                    sig = latest_signals[symbol]
                    sig_time = datetime.fromisoformat(sig['timestamp'])
                    time_str = sig_time.strftime('%H:%M:%S')
                    
                    # Create signal box using columns
                    with st.container():
                        c1, c2, c3 = st.columns([2, 2, 1])
                        
                        with c1:
                            if sig['action'] == 'LONG':
                                st.success(f"🟢 {symbol} - LONG")
                            elif sig['action'] == 'EXIT':
                                st.error(f"🔴 {symbol} - EXIT")
                            else:
                                st.info(f"⚪ {symbol} - HOLD")
                        
                        with c2:
                            st.markdown(f"**${sig['price']:.2f}**")
                            st.caption(time_str)
                        
                        with c3:
                            st.markdown(f"**{sig['confidence']*100:.1f}%**")
                            st.caption("CONF")
                    
                    # Add consecutive indicator if needed
                    if sig.get('consecutive_count', 1) > 1 and 'first_signal_time' in sig:
                        first_time = datetime.fromisoformat(sig['first_signal_time']).strftime('%H:%M')
                        st.caption(f"📍 Opened at {first_time} • Updated at {time_str} • {sig['consecutive_count']} signals")
                    
                    st.markdown("---")
                else:
                    with st.container():
                        st.markdown(f"""
                        <div style="color: var(--text-tertiary); padding: 14px;">
                            {symbol} - No signals today
                        </div>
                        """, unsafe_allow_html=True)
        
        with col_right:
            st.markdown('<div class="section-header">💼 Current Positions</div>', unsafe_allow_html=True)
            
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
                                
                                with st.container():
                                    st.markdown(f"**{symbol} - LONG**")
                                    
                                    pc1, pc2 = st.columns(2)
                                    with pc1:
                                        st.caption(f"Entry: ${entry:.2f}")
                                        st.caption(f"Current: ${current:.2f}")
                                    with pc2:
                                        pnl_color = "#34C759" if pnl > 0 else "#FF453A"
                                        st.markdown(f"<span style='color: {pnl_color}; font-weight: 600;'>P&L: {pnl:+.2f}%</span>", unsafe_allow_html=True)
                                        st.caption(f"Conf: {pos.get('last_confidence', 0)*100:.1f}%")
                                    
                                    st.markdown("---")
                
                if not has_positions:
                    st.markdown("""
                    <div style="text-align: center; padding: 40px; color: var(--text-tertiary);">
                        No open positions
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="section-header">📜 Historical Signals</div>', unsafe_allow_html=True)
        
        # Filter
        hist_filter = st.selectbox("Filter by Asset", ["ALL"] + ASSETS, key="hist_filter")
        
        # Display historical signals
        if hist_filter == "ALL":
            filtered_signals = [s for s in all_signals if s.get('is_new_position', True)]
        else:
            filtered_signals = [s for s in all_signals if s['symbol'] == hist_filter and s.get('is_new_position', True)]
        
        filtered_signals = sorted(filtered_signals, key=lambda x: x['timestamp'], reverse=True)
        
        if filtered_signals:
            for sig in filtered_signals[:100]:
                sig_time = datetime.fromisoformat(sig['timestamp'])
                time_str = sig_time.strftime('%m/%d %H:%M:%S')
                
                with st.container():
                    hc1, hc2, hc3 = st.columns([2, 3, 1])
                    
                    with hc1:
                        if sig['action'] == 'LONG':
                            st.markdown(f"🟢 **{sig['symbol']} - LONG**")
                        elif sig['action'] == 'EXIT':
                            st.markdown(f"🔴 **{sig['symbol']} - EXIT**")
                        else:
                            st.markdown(f"⚪ **{sig['symbol']} - HOLD**")
                    
                    with hc2:
                        st.caption(f"{time_str} • ${sig['price']:.2f}")
                    
                    with hc3:
                        action_color = "#34C759" if sig['action'] == 'LONG' else "#FF453A" if sig['action'] == 'EXIT' else "#888"
                        st.markdown(f"<span style='color: {action_color}; font-weight: 600;'>{sig['confidence']*100:.1f}%</span>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 40px; color: var(--text-tertiary);">
                No historical signals
            </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="section-header">💰 Completed Trades</div>', unsafe_allow_html=True)
        
        if trades_history:
            recent_trades = sorted(trades_history, key=lambda x: x['exit_time'], reverse=True)[:50]
            
            # Create DataFrame for better display
            trade_data = []
            for trade in recent_trades:
                exit_time = datetime.fromisoformat(trade['exit_time']).strftime('%m/%d %H:%M')
                trade_data.append({
                    'Symbol': trade['symbol'],
                    'Exit Time': exit_time,
                    'Entry': f"${trade['entry_price']:.2f}",
                    'Exit': f"${trade['exit_price']:.2f}",
                    'P&L %': trade['pnl_percent'],
                    'P&L $': trade['pnl_dollar']
                })
            
            df_trades = pd.DataFrame(trade_data)
            
            # Custom styling for P&L columns
            def style_pnl(val):
                if isinstance(val, (int, float)):
                    if val > 0:
                        return f'color: #34C759; font-weight: 600;'
                    elif val < 0:
                        return f'color: #FF453A; font-weight: 600;'
                return ''
            
            # Format P&L columns for display
            df_trades['P&L %'] = df_trades['P&L %'].apply(lambda x: f"{x:+.2f}%")
            df_trades['P&L $'] = df_trades['P&L $'].apply(lambda x: f"${x:+.2f}")
            
            st.dataframe(df_trades, use_container_width=True, hide_index=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 40px; color: var(--text-tertiary);">
                No completed trades yet
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown(f"""
    <div style="text-align: center; color: var(--text-tertiary); font-size: 11px; 
         padding: 24px 0; border-top: 1px solid var(--border-color); margin-top: 40px;">
        Last Signal: {last_signal_time.strftime('%H:%M:%S') if last_signal_time else 'N/A'} • 
        Auto-refresh: 5 seconds • 
        {'🟢 Connected' if is_connected else '🔴 Disconnected'}
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
