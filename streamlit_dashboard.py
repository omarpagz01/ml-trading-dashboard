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

# Define assets - Main trading assets
ASSETS = ['TSLA', 'HOOD', 'COIN', 'PLTR', 'AAPL']

# Watchlist assets (not currently traded but monitored)
WATCHLIST = ['NVDA', 'AMD', 'META', 'GOOGL', 'MSFT']

# Set timezone
ET = pytz.timezone('US/Eastern')

# GitHub Raw URL base
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/omarpagz01/ml-trading-dashboard/main"

# Initialize session state
if 'previous_signals' not in st.session_state:
    st.session_state.previous_signals = set()
if 'sound_played' not in st.session_state:
    st.session_state.sound_played = False
if 'counter' not in st.session_state:
   st.session_state.counter = 0
if 'last_update' not in st.session_state:
   st.session_state.last_update = datetime.now()

# Helper function to play notification sound
def play_notification_sound(signal_type='LONG'):
    """Play a notification sound using JavaScript"""
    if signal_type == 'LONG':
        frequency = 1046.50  # C6
    else:
        frequency = 698.46   # F5
    
    sound_script = f"""
    <script>
    var audioContext = new (window.AudioContext || window.webkitAudioContext)();
    var osc = audioContext.createOscillator();
    var gain = audioContext.createGain();
    
    osc.connect(gain);
    gain.connect(audioContext.destination);
    osc.frequency.value = {frequency};
    osc.type = 'sine';
    
    gain.gain.setValueAtTime(0, audioContext.currentTime);
    gain.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.008);
    gain.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.2);
    
    osc.start(audioContext.currentTime);
    osc.stop(audioContext.currentTime + 0.25);
    </script>
    """
    st.components.v1.html(sound_script, height=0)

def check_for_new_signals(signals):
    """Check if there are new non-HOLD signals and play sound if needed"""
    if not signals:
        return
    
    current_signals = set()
    latest_signal_type = None
    
    for sig in signals:
        if sig['action'] != 'HOLD':
            sig_id = f"{sig['symbol']}_{sig['action']}_{sig['timestamp']}"
            current_signals.add(sig_id)
            if sig_id not in st.session_state.previous_signals:
                latest_signal_type = sig['action']
    
    new_signals = current_signals - st.session_state.previous_signals
    
    if new_signals and st.session_state.previous_signals:
        if latest_signal_type:
            play_notification_sound(signal_type=latest_signal_type)
    
    st.session_state.previous_signals = current_signals

# Professional CSS
st.markdown("""
<style>
   @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
   
   :root {
       --primary-green: #00d632;
       --primary-red: #ff3838;
       --primary-orange: #FF9500;
       --bg-primary: #0e1117;
       --bg-secondary: #1e1e2e;
       --bg-hover: #252535;
       --border-color: #2e2e3e;
       --text-primary: #ffffff;
       --text-secondary: #8b8b9a;
       --text-tertiary: #5a5a6a;
   }
   
   .stApp {
       background: var(--bg-primary);
       font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
   }
   
   #MainMenu, footer, header {visibility: hidden;}
   .block-container {
       padding: 1.5rem 2rem 0 2rem !important;
       max-width: 100% !important;
   }
   
   /* Main Title */
   .main-title {
       font-size: 28px;
       font-weight: 700;
       color: var(--text-primary);
       text-align: center;
       margin: 0 0 1.5rem 0;
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
       background: rgba(0, 214, 50, 0.1);
       border: 1px solid rgba(0, 214, 50, 0.3);
       border-radius: 20px;
       font-size: 11px;
       font-weight: 600;
       text-transform: uppercase;
   }
   
   .status-dot {
       width: 8px;
       height: 8px;
       border-radius: 50%;
       background: var(--primary-green);
       animation: pulse 2s infinite;
   }
   
   .status-dot.disconnected {
       background: var(--primary-red);
   }
   
   @keyframes pulse {
       0%, 100% { opacity: 1; }
       50% { opacity: 0.5; }
   }
   
   /* Metric Cards */
   .metric-card {
       background: var(--bg-secondary);
       border-radius: 12px;
       padding: 16px;
       border: 1px solid var(--border-color);
       height: 85px;
   }
   
   .metric-label {
       color: var(--text-tertiary);
       font-size: 10px;
       font-weight: 600;
       text-transform: uppercase;
       letter-spacing: 0.5px;
       margin-bottom: 8px;
   }
   
   .metric-value {
       color: var(--text-primary);
       font-size: 24px;
       font-weight: 600;
       line-height: 1;
   }
   
   .metric-delta {
       font-size: 11px;
       color: var(--text-secondary);
       margin-top: 4px;
   }
   
   /* Section Headers */
   .section-header {
       color: var(--text-primary);
       font-size: 14px;
       font-weight: 600;
       margin: 20px 0 12px 0;
       padding-bottom: 6px;
       border-bottom: 1px solid var(--border-color);
   }
   
   /* Position Table */
   .position-table {
       background: var(--bg-secondary);
       border-radius: 10px;
       overflow: hidden;
       margin-bottom: 16px;
   }
   
   .position-header {
       display: grid;
       grid-template-columns: 0.8fr 1fr 1fr 1fr 1.2fr 1fr 1fr;
       padding: 10px 14px;
       background: #161620;
       font-size: 10px;
       font-weight: 600;
       text-transform: uppercase;
       color: var(--text-secondary);
       letter-spacing: 0.5px;
   }
   
   .position-row {
       display: grid;
       grid-template-columns: 0.8fr 1fr 1fr 1fr 1.2fr 1fr 1fr;
       padding: 12px 14px;
       border-bottom: 1px solid var(--border-color);
       font-size: 12px;
       align-items: center;
   }
   
   .position-row:last-child {
       border-bottom: none;
   }
   
   .position-row:hover {
       background: var(--bg-hover);
   }
   
   .symbol-cell {
       font-weight: 600;
       color: var(--text-primary);
   }
   
   .status-long {
       color: var(--primary-green);
       font-weight: 600;
   }
   
   .pnl-positive {
       color: var(--primary-green);
       font-weight: 600;
   }
   
   .pnl-negative {
       color: var(--primary-red);
       font-weight: 600;
   }
   
   /* Entry Criteria */
   .criteria-text {
       font-size: 10px;
       color: var(--text-secondary);
       line-height: 1.3;
   }
   
   /* Watchlist */
   .watchlist-grid {
       display: grid;
       grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
       gap: 12px;
       margin-top: 12px;
   }
   
   .watchlist-card {
       background: var(--bg-secondary);
       border-radius: 8px;
       padding: 12px;
       border: 1px solid var(--border-color);
   }
   
   .watchlist-header {
       display: flex;
       justify-content: space-between;
       align-items: center;
       margin-bottom: 8px;
   }
   
   .watchlist-symbol {
       font-weight: 600;
       font-size: 14px;
       color: var(--text-primary);
   }
   
   .watchlist-price {
       font-size: 13px;
       color: var(--text-primary);
   }
   
   .watchlist-details {
       font-size: 10px;
       color: var(--text-secondary);
       line-height: 1.4;
   }
   
   .no-entry-reason {
       color: var(--text-tertiary);
       font-style: italic;
       margin-top: 4px;
   }
   
   /* Signal Analysis */
   .signal-analysis {
       background: var(--bg-secondary);
       border-radius: 8px;
       padding: 12px;
       margin-bottom: 8px;
       border: 1px solid var(--border-color);
   }
   
   .signal-header {
       display: flex;
       justify-content: space-between;
       align-items: center;
       margin-bottom: 8px;
   }
   
   .signal-symbol {
       font-weight: 600;
       font-size: 13px;
   }
   
   .signal-action {
       padding: 2px 8px;
       border-radius: 4px;
       font-size: 11px;
       font-weight: 600;
   }
   
   .action-long {
       background: rgba(0, 214, 50, 0.2);
       color: var(--primary-green);
   }
   
   .action-exit {
       background: rgba(255, 56, 56, 0.2);
       color: var(--primary-red);
   }
   
   .action-hold {
       background: rgba(139, 139, 154, 0.2);
       color: var(--text-secondary);
   }
   
   /* Technical Indicators */
   .indicators-grid {
       display: grid;
       grid-template-columns: repeat(4, 1fr);
       gap: 8px;
       margin-top: 8px;
       padding-top: 8px;
       border-top: 1px solid var(--border-color);
   }
   
   .indicator-item {
       font-size: 10px;
   }
   
   .indicator-label {
       color: var(--text-tertiary);
       margin-bottom: 2px;
   }
   
   .indicator-value {
       color: var(--text-primary);
       font-weight: 500;
   }
   
   /* Compact Mode */
   .compact-grid {
       display: grid;
       grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
       gap: 10px;
   }
</style>
""", unsafe_allow_html=True)

# Data loading functions
def load_from_github(path):
    """Load JSON from GitHub with cache busting"""
    try:
        timestamp = int(time.time() * 1000)
        random_str = random.randint(100000, 999999)
        cache_buster = hashlib.md5(f"{timestamp}{random_str}".encode()).hexdigest()[:8]
        
        url = f"{GITHUB_RAW_BASE}/{path}"
        params = {'t': timestamp, 'r': random_str, 'cb': cache_buster}
        headers = {'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache'}
        
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

def load_position_states():
    return load_from_github("data/position_states.json") or {}

def load_trades_history():
    return load_from_github("data/trades_history.json") or []

def convert_to_et(timestamp_str):
    """Convert ISO timestamp to ET timezone"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt.astimezone(ET)
    except:
        return datetime.now(ET)

def format_entry_criteria(signal):
    """Extract and format entry criteria from signal"""
    criteria = []
    
    if 'features_snapshot' in signal and signal['features_snapshot']:
        features = signal['features_snapshot']
        
        # RSI
        if 'rsi' in features:
            rsi_val = features['rsi']
            if rsi_val < 30:
                criteria.append(f"RSI: {rsi_val:.1f} (oversold)")
            elif rsi_val > 70:
                criteria.append(f"RSI: {rsi_val:.1f} (overbought)")
            else:
                criteria.append(f"RSI: {rsi_val:.1f}")
        
        # MACD
        if 'macd' in features:
            macd_val = features['macd']
            criteria.append(f"MACD: {macd_val:.2f}")
        
        # Bollinger Bands
        if 'bb_position' in features:
            bb_pos = features['bb_position']
            if bb_pos < 0.2:
                criteria.append(f"BB: {bb_pos:.2f} (near lower)")
            elif bb_pos > 0.8:
                criteria.append(f"BB: {bb_pos:.2f} (near upper)")
            else:
                criteria.append(f"BB: {bb_pos:.2f}")
        
        # Volume
        if 'volume_ratio' in features:
            vol_ratio = features['volume_ratio']
            if vol_ratio > 1.5:
                criteria.append(f"Vol: {vol_ratio:.1f}x avg")
    
    # ML Scores
    if 'ml_scores' in signal and signal['ml_scores']:
        scores = signal['ml_scores']
        if 'rf_long' in scores:
            criteria.append(f"RF: {scores['rf_long']*100:.0f}%")
        if 'gb_long' in scores:
            criteria.append(f"GB: {scores['gb_long']*100:.0f}%")
        if 'lstm_long' in scores:
            criteria.append(f"LSTM: {scores['lstm_long']*100:.0f}%")
    
    return " | ".join(criteria) if criteria else "Standard criteria met"

def calculate_performance_metrics(trades, symbol_filter=None):
    """Calculate performance metrics"""
    if symbol_filter and symbol_filter != "ALL":
        trades = [t for t in trades if t.get('symbol') == symbol_filter]
    
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

def get_market_status():
    """Check market status"""
    now = datetime.now(ET)
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday >= 5:
        return "WEEKEND", "closed"
    elif current_time < pd.Timestamp("09:30").time():
        return "PRE-MARKET", "premarket"
    elif current_time >= pd.Timestamp("16:00").time():
        return "AFTER-HOURS", "closed"
    elif pd.Timestamp("09:30").time() <= current_time < pd.Timestamp("16:00").time():
        return "MARKET OPEN", "open"
    else:
        return "CLOSED", "closed"

# Main Dashboard
def main():
    if st.session_state.counter % 10 == 0:
        st.cache_data.clear()
    
    # Load data
    status = load_status()
    raw_signals = load_signals()
    trades_history = load_trades_history()
    realtime_prices = load_realtime_prices()
    saved_positions = load_position_states()
    
    check_for_new_signals(raw_signals)
    
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
    
    # Title
    st.markdown(f"""
    <h1 class="main-title">
        SIGNALS DASHBOARD
        <div class="connection-status">
            <div class="status-dot {'connected' if is_connected else 'disconnected'}"></div>
            {'LIVE' if is_connected else 'OFFLINE'}
        </div>
    </h1>
    """, unsafe_allow_html=True)
    
    if not status:
        st.markdown("""
        <div style="text-align: center; padding: 60px;">
            <div style="font-size: 18px; color: var(--text-secondary);">
                Waiting for trading system data...
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(5)
        st.rerun()
        return
    
    market_status, status_class = get_market_status()
    
    # Top Metrics
    metrics = calculate_performance_metrics(trades_history)
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Market</div>
            <div class="metric-value" style="font-size: 14px; color: {'#00d632' if status_class == 'open' else '#ff9500' if status_class == 'premarket' else '#8b8b9a'};">
                {market_status}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        active = sum(1 for p in saved_positions.values() if p.get('is_open'))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Positions</div>
            <div class="metric-value">{active}/{len(ASSETS)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_pnl = 0
        if saved_positions and realtime_prices.get('prices'):
            for symbol, pos in saved_positions.items():
                if pos.get('is_open'):
                    current = realtime_prices['prices'].get(symbol, 0)
                    entry = pos.get('entry_price', 0)
                    if current > 0 and entry > 0:
                        total_pnl += ((current - entry) / entry * 100)
        
        pnl_color = "#00d632" if total_pnl > 0 else "#ff3838" if total_pnl < 0 else "#8b8b9a"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Open P&L</div>
            <div class="metric-value" style="color: {pnl_color};">
                {total_pnl:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        pnl_color = "#00d632" if metrics['total_pnl'] > 0 else "#ff3838" if metrics['total_pnl'] < 0 else "#8b8b9a"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total P&L</div>
            <div class="metric-value" style="color: {pnl_color};">
                {metrics['total_pnl']:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Win Rate</div>
            <div class="metric-value">{metrics['win_rate']:.0f}%</div>
            <div class="metric-delta">{metrics['total_trades']} trades</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Profit Factor</div>
            <div class="metric-value">{metrics['profit_factor']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col7:
        signals_today = len(raw_signals) if raw_signals else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Signals Today</div>
            <div class="metric-value">{signals_today}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Positions & Signals", "👁 Watchlist", "📈 Performance", "💰 Trade History"])
    
    with tab1:
        # Current Positions
        st.markdown('<div class="section-header">🎯 Active Positions</div>', unsafe_allow_html=True)
        
        positions_html = """
        <div class="position-table">
            <div class="position-header">
                <div>Symbol</div>
                <div>Status</div>
                <div>Entry Price</div>
                <div>Current</div>
                <div>Entry Criteria</div>
                <div>P&L %</div>
                <div>P&L $</div>
            </div>
        """
        
        # Get latest signals for entry criteria
        latest_signals = {}
        for sig in raw_signals:
            if sig['symbol'] not in latest_signals or sig['timestamp'] > latest_signals[sig['symbol']]['timestamp']:
                latest_signals[sig['symbol']] = sig
        
        has_positions = False
        for symbol in ASSETS:
            if symbol in saved_positions and saved_positions[symbol].get('is_open'):
                has_positions = True
                pos = saved_positions[symbol]
                
                current = 0
                if realtime_prices.get('prices') and symbol in realtime_prices['prices']:
                    current = realtime_prices['prices'][symbol]
                
                entry = pos.get('entry_price', 0)
                entry_time = convert_to_et(pos.get('entry_time', '')) if pos.get('entry_time') else None
                
                pnl_pct = 0
                pnl_dollar = 0
                if current > 0 and entry > 0:
                    pnl_pct = ((current - entry) / entry * 100)
                    pnl_dollar = (current - entry) * 100
                
                pnl_class = "pnl-positive" if pnl_pct > 0 else "pnl-negative"
                
                # Get entry criteria
                criteria = "N/A"
                if symbol in latest_signals:
                    criteria = format_entry_criteria(latest_signals[symbol])
                
                positions_html += f"""
                <div class="position-row">
                    <div class="symbol-cell">{symbol}</div>
                    <div class="status-long">LONG</div>
                    <div>${entry:.2f}<br><span style="font-size: 9px; color: #5a5a6a;">{entry_time.strftime('%m/%d %H:%M') if entry_time else ''}</span></div>
                    <div>${current:.2f}</div>
                    <div class="criteria-text">{criteria}</div>
                    <div class="{pnl_class}">{pnl_pct:+.2f}%</div>
                    <div class="{pnl_class}">${pnl_dollar:+.2f}</div>
                </div>
                """
        
        if not has_positions:
            positions_html += """
            <div style="padding: 20px; text-align: center; color: #5a5a6a;">
                No active positions
            </div>
            """
        
        positions_html += "</div>"
        st.markdown(positions_html, unsafe_allow_html=True)
        
        # Recent Signals
        st.markdown('<div class="section-header">📡 Recent Signals & Analysis</div>', unsafe_allow_html=True)
        
        if raw_signals:
            recent_signals = sorted(raw_signals, key=lambda x: x['timestamp'], reverse=True)[:10]
            
            for sig in recent_signals:
                sig_time = convert_to_et(sig['timestamp'])
                
                action_class = ""
                if sig['action'] == 'LONG':
                    action_class = "action-long"
                elif sig['action'] == 'EXIT':
                    action_class = "action-exit"
                else:
                    action_class = "action-hold"
                
                criteria = format_entry_criteria(sig)
                
                st.markdown(f"""
                <div class="signal-analysis">
                    <div class="signal-header">
                        <div>
                            <span class="signal-symbol">{sig['symbol']}</span>
                            <span style="margin-left: 8px; font-size: 11px; color: #8b8b9a;">
                                {sig_time.strftime('%m/%d %H:%M:%S')} • ${sig['price']:.2f}
                            </span>
                        </div>
                        <div class="signal-action {action_class}">{sig['action']}</div>
                    </div>
                    <div style="font-size: 11px; color: #8b8b9a;">
                        {criteria}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No signals generated today")
    
    with tab2:
        st.markdown('<div class="section-header">👁 Asset Watchlist - Not Trading</div>', unsafe_allow_html=True)
        
        watchlist_html = '<div class="watchlist-grid">'
        
        for symbol in WATCHLIST:
            # Get price if available
            price = 0
            if realtime_prices.get('prices') and symbol in realtime_prices['prices']:
                price = realtime_prices['prices'][symbol]
            
            # Generate mock reasons for not entering (in real system, this would come from actual analysis)
            no_entry_reasons = [
                f"RSI: 45 (neutral)",
                f"Volume: 0.8x avg",
                f"No clear trend",
                f"Waiting for breakout"
            ]
            
            watchlist_html += f"""
            <div class="watchlist-card">
                <div class="watchlist-header">
                    <div class="watchlist-symbol">{symbol}</div>
                    <div class="watchlist-price">${price:.2f if price > 0 else 'N/A'}</div>
                </div>
                <div class="watchlist-details">
                    <div>Status: <span style="color: #ff9500;">Monitoring</span></div>
                    <div class="no-entry-reason">
                        {' | '.join(no_entry_reasons[:2])}
                    </div>
                </div>
            </div>
            """
        
        watchlist_html += '</div>'
        st.markdown(watchlist_html, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="margin-top: 16px; padding: 12px; background: #1e1e2e; border-radius: 8px; font-size: 11px; color: #8b8b9a;">
            <strong>Note:</strong> Watchlist assets are monitored but not actively traded. Entry signals require multiple criteria alignment including technical indicators, ML predictions, and market conditions.
        </div>
        """, unsafe_allow_html=True)
    
    with tab3:
        # Performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="section-header">P&L Distribution</div>', unsafe_allow_html=True)
            
            if trades_history:
                df_trades = pd.DataFrame(trades_history)
                
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=df_trades['pnl_percent'],
                    nbinsx=20,
                    name='P&L Distribution',
                    marker_color='#00d632'
                ))
                
                fig.update_layout(
                    xaxis_title="P&L %",
                    yaxis_title="Frequency",
                    template="plotly_dark",
                    height=300,
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown('<div class="section-header">Cumulative P&L</div>', unsafe_allow_html=True)
            
            if trades_history:
                df_trades = pd.DataFrame(trades_history)
                if 'exit_time' in df_trades.columns:
                    df_trades['exit_time'] = pd.to_datetime(df_trades['exit_time'])
                    df_trades = df_trades.sort_values('exit_time')
                    df_trades['cumulative_pnl'] = df_trades['pnl_percent'].cumsum()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_trades['exit_time'],
                        y=df_trades['cumulative_pnl'],
                        mode='lines',
                        name='Cumulative P&L',
                        line=dict(color='#00d632', width=2)
                    ))
                    
                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Cumulative P&L (%)",
                        template="plotly_dark",
                        height=300,
                        margin=dict(l=40, r=40, t=40, b=40)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown('<div class="section-header">Recent Trades</div>', unsafe_allow_html=True)
        
        if trades_history:
            df_trades = pd.DataFrame(trades_history)
            df_trades = df_trades.sort_values('exit_time', ascending=False).head(20)
            
            # Format for display
            df_display = df_trades[['symbol', 'exit_time', 'entry_price', 'exit_price', 'pnl_percent', 'pnl_dollar']].copy()
            df_display['exit_time'] = pd.to_datetime(df_display['exit_time']).dt.strftime('%m/%d %H:%M')
            df_display['entry_price'] = df_display['entry_price'].apply(lambda x: f"${x:.2f}")
            df_display['exit_price'] = df_display['exit_price'].apply(lambda x: f"${x:.2f}")
            df_display['pnl_percent'] = df_display['pnl_percent'].apply(lambda x: f"{x:+.2f}%")
            df_display['pnl_dollar'] = df_display['pnl_dollar'].apply(lambda x: f"${x:+.2f}")
            
            df_display.columns = ['Symbol', 'Exit Time', 'Entry', 'Exit', 'P&L %', 'P&L $']
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                height=400
            )
        else:
            st.info("No completed trades yet")
    
    # Footer
    st.markdown(f"""
    <div style="text-align: center; color: #5a5a6a; font-size: 11px; 
         padding: 20px 0; border-top: 1px solid #2e2e3e; margin-top: 30px;">
        Auto-refresh: 5 seconds • 
        {'🟢 Connected' if is_connected else '🔴 Disconnected'} • 
        Data: GitHub
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(5)
    st.session_state.counter += 1
    st.rerun()

if __name__ == "__main__":
    main()
