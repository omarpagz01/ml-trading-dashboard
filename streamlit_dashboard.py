import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np
import pytz
import requests
import random
import hashlib

# Page configuration
st.set_page_config(
    page_title="Signals Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constants
ASSETS = ['TSLA', 'HOOD', 'COIN', 'PLTR', 'AAPL']
WATCHLIST = ['NVDA', 'AMD', 'META', 'GOOGL', 'MSFT']
ET = pytz.timezone('US/Eastern')
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/omarpagz01/ml-trading-dashboard/main"

# Initialize session state
if 'counter' not in st.session_state:
    st.session_state.counter = 0
if 'previous_signals' not in st.session_state:
    st.session_state.previous_signals = set()

# Apple-inspired CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@200;300;400;500;600;700;800;900&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(180deg, #000000 0%, #0a0a0a 100%);
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    
    /* Main Header */
    .main-header {
        text-align: center;
        padding: 2rem 0 3rem 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 100%);
        border-radius: 24px;
        margin-bottom: 2rem;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
    
    .header-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff 0%, #8b8b9a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }
    
    .connection-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 100px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-top: 1rem;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    .connected .status-dot {
        background: #30d158;
        box-shadow: 0 0 10px rgba(48, 209, 88, 0.5);
    }
    
    .disconnected .status-dot {
        background: #ff453a;
        box-shadow: 0 0 10px rgba(255, 69, 58, 0.5);
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(1.1); }
    }
    
    /* Metric Cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.25rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%);
        box-shadow: 0 20px 40px rgba(0,0,0,0.5);
    }
    
    .metric-label {
        font-size: 11px;
        font-weight: 600;
        color: #8e8e93;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.02em;
    }
    
    .metric-delta {
        font-size: 12px;
        font-weight: 500;
        margin-top: 4px;
        color: #8e8e93;
    }
    
    .positive { color: #30d158; }
    .negative { color: #ff453a; }
    .neutral { color: #8e8e93; }
    
    /* Glass Cards */
    .glass-card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(40px) saturate(180%);
        -webkit-backdrop-filter: blur(40px) saturate(180%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        background: rgba(255,255,255,0.07);
        transform: scale(1.01);
    }
    
    /* Section Headers */
    .section-header {
        font-size: 18px;
        font-weight: 600;
        color: #ffffff;
        margin: 2rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .section-header::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(255,255,255,0.2) 0%, transparent 100%);
    }
    
    /* Position Row */
    .position-row {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, transparent 100%);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border: 1px solid rgba(255,255,255,0.08);
        transition: all 0.2s ease;
    }
    
    .position-row:hover {
        background: rgba(255,255,255,0.08);
        transform: translateX(4px);
    }
    
    /* Signal Card */
    .signal-card {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid;
        transition: all 0.2s ease;
    }
    
    .signal-long { border-color: #30d158; }
    .signal-exit { border-color: #ff453a; }
    .signal-hold { border-color: #8e8e93; }
    
    /* Watchlist Grid */
    .watchlist-container {
        background: rgba(255,255,255,0.02);
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(255,255,255,0.08);
    }
    
    .watchlist-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .watchlist-item {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, transparent 100%);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.2s ease;
    }
    
    .watchlist-item:hover {
        background: rgba(255,255,255,0.08);
        transform: translateY(-2px);
    }
    
    .watchlist-symbol {
        font-size: 16px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 4px;
    }
    
    .watchlist-price {
        font-size: 20px;
        font-weight: 700;
        color: #8e8e93;
        margin-bottom: 8px;
    }
    
    .watchlist-status {
        font-size: 11px;
        color: #ff9f0a;
        font-weight: 500;
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 12px;
        color: white;
        font-weight: 500;
        padding: 0.5rem 1.5rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.08) 100%);
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    
    /* Tab Styles */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #8e8e93;
        font-weight: 500;
        padding: 8px 16px;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(255,255,255,0.1);
        color: white;
    }
    
    /* Dataframe Styles */
    .dataframe {
        background: transparent !important;
    }
    
    .dataframe th {
        background: rgba(255,255,255,0.05) !important;
        color: #8e8e93 !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        font-size: 11px !important;
        letter-spacing: 0.5px !important;
    }
    
    .dataframe td {
        background: transparent !important;
        color: #ffffff !important;
        border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    }
</style>
""", unsafe_allow_html=True)

# Data loading functions
def load_from_github(path):
    """Load JSON data from GitHub"""
    try:
        timestamp = int(time.time() * 1000)
        random_val = random.randint(100000, 999999)
        
        url = f"{GITHUB_RAW_BASE}/{path}"
        params = {'t': timestamp, 'r': random_val}
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def load_status():
    return load_from_github("status.json") or {}

def load_realtime_prices():
    return load_from_github("realtime_prices.json") or {}

def load_signals():
    today = datetime.now().strftime('%Y%m%d')
    return load_from_github(f"signals/signals_{today}.json") or []

def load_positions():
    return load_from_github("data/position_states.json") or {}

def load_trades():
    return load_from_github("data/trades_history.json") or []

def convert_to_et(timestamp_str):
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt.astimezone(ET)
    except:
        return datetime.now(ET)

def get_market_status():
    now = datetime.now(ET)
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday >= 5:
        return "WEEKEND", "#ff9f0a"
    elif current_time < datetime.strptime("09:30", "%H:%M").time():
        return "PRE-MARKET", "#ff9f0a"
    elif current_time >= datetime.strptime("16:00", "%H:%M").time():
        return "AFTER-HOURS", "#8e8e93"
    elif datetime.strptime("09:30", "%H:%M").time() <= current_time < datetime.strptime("16:00", "%H:%M").time():
        return "OPEN", "#30d158"
    else:
        return "CLOSED", "#8e8e93"

def format_criteria(signal):
    criteria_parts = []
    
    if 'features_snapshot' in signal and signal['features_snapshot']:
        features = signal['features_snapshot']
        
        if 'rsi' in features:
            criteria_parts.append(f"RSI:{features['rsi']:.0f}")
        if 'macd' in features:
            criteria_parts.append(f"MACD:{features['macd']:.1f}")
        if 'bb_position' in features:
            criteria_parts.append(f"BB:{features['bb_position']:.1f}")
        if 'volume_ratio' in features:
            criteria_parts.append(f"Vol:{features['volume_ratio']:.1f}x")
    
    if 'ml_scores' in signal and signal['ml_scores']:
        scores = signal['ml_scores']
        if 'rf_long' in scores:
            criteria_parts.append(f"RF:{scores['rf_long']*100:.0f}%")
        if 'gb_long' in scores:
            criteria_parts.append(f"GB:{scores['gb_long']*100:.0f}%")
    
    return " • ".join(criteria_parts) if criteria_parts else "Standard"

def calculate_metrics(trades):
    if not trades:
        return {'total_pnl': 0, 'win_rate': 0, 'profit_factor': 0, 'total_trades': 0}
    
    wins = [t for t in trades if t.get('pnl_percent', 0) > 0]
    losses = [t for t in trades if t.get('pnl_percent', 0) < 0]
    
    total_wins = sum(abs(t.get('pnl_percent', 0)) for t in wins)
    total_losses = sum(abs(t.get('pnl_percent', 0)) for t in losses)
    
    return {
        'total_pnl': sum(t.get('pnl_percent', 0) for t in trades),
        'win_rate': (len(wins) / len(trades) * 100) if trades else 0,
        'profit_factor': (total_wins / total_losses) if total_losses > 0 else 0,
        'total_trades': len(trades)
    }

# Main application
def main():
    if st.session_state.counter % 10 == 0:
        st.cache_data.clear()
    
    # Load all data
    status = load_status()
    signals = load_signals()
    positions = load_positions()
    trades = load_trades()
    prices = load_realtime_prices()
    
    # Check connection
    is_connected = False
    if status and 'timestamp' in status:
        try:
            last_update = datetime.fromisoformat(status['timestamp'].replace('Z', '+00:00'))
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=pytz.UTC)
            time_diff = (datetime.now(pytz.UTC) - last_update).total_seconds()
            is_connected = time_diff < 120
        except:
            is_connected = False
    
    # Header
    st.markdown(f"""
        <div class="main-header">
            <div class="header-title">Signals Dashboard</div>
            <div class="connection-pill {'connected' if is_connected else 'disconnected'}">
                <div class="status-dot"></div>
                {'LIVE' if is_connected else 'OFFLINE'}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if not status:
        st.info("Waiting for trading system data...")
        time.sleep(5)
        st.session_state.counter += 1
        st.rerun()
        return
    
    # Calculate metrics
    market_status, market_color = get_market_status()
    metrics = calculate_metrics(trades)
    
    # Calculate open PnL
    open_pnl = 0
    if positions and prices.get('prices'):
        for symbol, pos in positions.items():
            if pos.get('is_open'):
                current = prices['prices'].get(symbol, 0)
                entry = pos.get('entry_price', 0)
                if current > 0 and entry > 0:
                    open_pnl += ((current - entry) / entry * 100)
    
    # Metrics Grid
    st.markdown("""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Market</div>
                <div class="metric-value" style="color: """ + market_color + """;">""" + market_status + """</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Positions</div>
                <div class="metric-value">""" + str(sum(1 for p in positions.values() if p.get('is_open'))) + """/""" + str(len(ASSETS)) + """</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Open P&L</div>
                <div class="metric-value """ + ('class="positive"' if open_pnl > 0 else 'class="negative"' if open_pnl < 0 else '') + """>""" + f"{open_pnl:+.1f}%" + """</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total P&L</div>
                <div class="metric-value """ + ('class="positive"' if metrics['total_pnl'] > 0 else 'class="negative"' if metrics['total_pnl'] < 0 else '') + """>""" + f"{metrics['total_pnl']:+.1f}%" + """</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Win Rate</div>
                <div class="metric-value">""" + f"{metrics['win_rate']:.0f}%" + """</div>
                <div class="metric-delta">""" + f"{metrics['total_trades']} trades" + """</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Profit Factor</div>
                <div class="metric-value">""" + f"{metrics['profit_factor']:.2f}" + """</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Today's Signals</div>
                <div class="metric-value">""" + str(len(signals) if signals else 0) + """</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Main content with two columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Positions Section
        st.markdown('<div class="section-header">📊 Active Positions</div>', unsafe_allow_html=True)
        
        positions_html = '<div class="glass-card">'
        latest_signals = {}
        
        for sig in signals:
            sym = sig.get('symbol')
            if sym and (sym not in latest_signals or sig['timestamp'] > latest_signals[sym]['timestamp']):
                latest_signals[sym] = sig
        
        active_count = 0
        for symbol in ASSETS:
            if symbol in positions and positions[symbol].get('is_open'):
                active_count += 1
                pos = positions[symbol]
                
                current_price = prices.get('prices', {}).get(symbol, 0)
                entry_price = pos.get('entry_price', 0)
                
                pnl_pct = 0
                pnl_usd = 0
                if current_price > 0 and entry_price > 0:
                    pnl_pct = ((current_price - entry_price) / entry_price * 100)
                    pnl_usd = (current_price - entry_price) * 100
                
                entry_time = ""
                if pos.get('entry_time'):
                    try:
                        et = convert_to_et(pos['entry_time'])
                        entry_time = et.strftime('%m/%d %H:%M')
                    except:
                        pass
                
                criteria = format_criteria(latest_signals[symbol]) if symbol in latest_signals else "Standard"
                pnl_color = "positive" if pnl_pct > 0 else "negative"
                
                positions_html += f"""
                    <div class="position-row">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 16px; font-weight: 600; color: white; margin-bottom: 4px;">{symbol}</div>
                                <div style="font-size: 12px; color: #8e8e93;">Entry: ${entry_price:.2f} • {entry_time}</div>
                                <div style="font-size: 11px; color: #636366; margin-top: 4px;">{criteria}</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 18px; font-weight: 700; color: white;">${current_price:.2f}</div>
                                <div class="{pnl_color}" style="font-size: 14px; font-weight: 600;">{pnl_pct:+.1f}% • ${pnl_usd:+.0f}</div>
                            </div>
                        </div>
                    </div>
                """
        
        if active_count == 0:
            positions_html += '<div style="text-align: center; color: #8e8e93; padding: 2rem;">No active positions</div>'
        
        positions_html += '</div>'
        st.markdown(positions_html, unsafe_allow_html=True)
        
        # Recent Signals
        st.markdown('<div class="section-header">📡 Recent Signals</div>', unsafe_allow_html=True)
        
        if signals:
            recent = sorted(signals, key=lambda x: x['timestamp'], reverse=True)[:5]
            signals_html = ""
            
            for sig in recent:
                sig_time = convert_to_et(sig['timestamp'])
                action_class = "signal-long" if sig['action'] == 'LONG' else "signal-exit" if sig['action'] == 'EXIT' else "signal-hold"
                action_emoji = "🟢" if sig['action'] == 'LONG' else "🔴" if sig['action'] == 'EXIT' else "⚪"
                
                signals_html += f"""
                    <div class="signal-card {action_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 14px; font-weight: 600;">{action_emoji} {sig['symbol']} • {sig['action']}</span>
                                <span style="font-size: 12px; color: #8e8e93; margin-left: 12px;">${sig['price']:.2f}</span>
                            </div>
                            <div style="font-size: 11px; color: #636366;">{sig_time.strftime('%H:%M:%S')}</div>
                        </div>
                    </div>
                """
            
            
            if signals:
                recent = sorted(signals, key=lambda x: x['timestamp'], reverse=True)[:5]
                for sig in recent:
                    sig_time = convert_to_et(sig['timestamp'])
                    action_class = "signal-long" if sig['action'] == 'LONG' else "signal-exit" if sig['action'] == 'EXIT' else "signal-hold"
                    action_emoji = "🟢" if sig['action'] == 'LONG' else "🔴" if sig['action'] == 'EXIT' else "⚪"
                    
                    signals_html += f"""
                        <div class="signal-card {action_class}">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-size: 14px; font-weight: 600;">{action_emoji} {sig['symbol']} • {sig['action']}</span>
                                    <span style="font-size: 12px; color: #8e8e93; margin-left: 12px;">${sig['price']:.2f}</span>
                                </div>
                                <div style="font-size: 11px; color: #636366;">{sig_time.strftime('%H:%M:%S')}</div>
                            </div>
                        </div>
                    """
                
                st.markdown(signals_html, unsafe_allow_html=True)
            else:
                st.markdown('<div class="glass-card" style="text-align: center; color: #8e8e93;">No signals today</div>', unsafe_allow_html=True)
    
    with col2:
        # Watchlist Section
        st.markdown('<div class="section-header">👁 Watchlist</div>', unsafe_allow_html=True)
        
        watchlist_html = '<div class="watchlist-container"><div class="watchlist-grid">'
        
        for symbol in WATCHLIST:
            price = prices.get('prices', {}).get(symbol, 0)
            price_display = f"${price:.2f}" if price > 0 else "---"
            
            watchlist_html += f"""
                <div class="watchlist-item">
                    <div class="watchlist-symbol">{symbol}</div>
                    <div class="watchlist-price">{price_display}</div>
                    <div class="watchlist-status">MONITORING</div>
                </div>
            """
        
        watchlist_html += '</div></div>'
        st.markdown(watchlist_html, unsafe_allow_html=True)
    
    # Tabs for additional content
    tab1, tab2 = st.tabs(["📈 Performance", "💰 Trade History"])
    
    with tab1:
        if trades:
            df_trades = pd.DataFrame(trades)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=df_trades['pnl_percent'],
                    nbinsx=20,
                    marker=dict(
                        color='rgba(48, 209, 88, 0.7)',
                        line=dict(color='rgba(48, 209, 88, 1)', width=1)
                    )
                ))
                fig.update_layout(
                    title="P&L Distribution",
                    xaxis_title="P&L (%)",
                    yaxis_title="Frequency",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'exit_time' in df_trades.columns:
                    df_trades['exit_time'] = pd.to_datetime(df_trades['exit_time'])
                    df_trades = df_trades.sort_values('exit_time')
                    df_trades['cumulative'] = df_trades['pnl_percent'].cumsum()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_trades['exit_time'],
                        y=df_trades['cumulative'],
                        mode='lines',
                        line=dict(color='rgba(48, 209, 88, 0.9)', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(48, 209, 88, 0.1)'
                    ))
                    fig.update_layout(
                        title="Cumulative P&L",
                        xaxis_title="Date",
                        yaxis_title="Cumulative (%)",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white'),
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available")
    
    with tab2:
        if trades:
            df_display = pd.DataFrame(trades).sort_values('exit_time', ascending=False).head(15)
            df_display['exit_time'] = pd.to_datetime(df_display['exit_time']).dt.strftime('%m/%d %H:%M')
            df_display = df_display[['symbol', 'exit_time', 'entry_price', 'exit_price', 'pnl_percent', 'pnl_dollar']]
            df_display.columns = ['Symbol', 'Exit Time', 'Entry', 'Exit', 'P&L (%)', 'P&L ($)']
            
            for col in ['Entry', 'Exit']:
                df_display[col] = df_display[col].apply(lambda x: f"${x:.2f}")
            df_display['P&L (%)'] = df_display['P&L (%)'].apply(lambda x: f"{x:+.1f}%")
            df_display['P&L ($)'] = df_display['P&L ($)'].apply(lambda x: f"${x:+.0f}")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No completed trades")
    
    # Footer
    st.markdown("---")
    st.caption(f"Auto-refresh: 5 seconds • Last update: {datetime.now().strftime('%H:%M:%S')}")
    
    # Auto refresh
    time.sleep(5)
    st.session_state.counter += 1
    st.rerun()

if __name__ == "__main__":
    main()
