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

# Define assets
ASSETS = ['TSLA', 'HOOD', 'COIN', 'PLTR', 'AAPL']

# Set timezone
ET = pytz.timezone('US/Eastern')

# GitHub Raw URL base - CRITICAL: This fetches directly from GitHub
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/omarpagz01/ml-trading-dashboard/main"

# Initialize session state for tracking signals
if 'previous_signals' not in st.session_state:
    st.session_state.previous_signals = set()
if 'sound_played' not in st.session_state:
    st.session_state.sound_played = False
if 'counter' not in st.session_state:
   st.session_state.counter = 0
if 'last_update' not in st.session_state:
   st.session_state.last_update = datetime.now()
if 'trades_history' not in st.session_state:
   st.session_state.trades_history = []

# Helper function to play notification sound
def play_notification_sound(signal_type='LONG'):
    """Play a notification sound using JavaScript with minimal ping style"""
    if signal_type == 'LONG':
        # LONG Signal - Higher pitch (C6 with C5 octave)
        sound_script = """
        <script>
        var audioContext = new (window.AudioContext || window.webkitAudioContext)();
        var now = audioContext.currentTime;
        
        // Primary tone - C6
        var osc = audioContext.createOscillator();
        var gain = audioContext.createGain();
        var filter = audioContext.createBiquadFilter();
        
        osc.connect(filter);
        filter.connect(gain);
        gain.connect(audioContext.destination);
        
        filter.type = 'lowpass';
        filter.frequency.value = 4000;
        filter.Q.value = 0.1;
        
        osc.frequency.value = 1046.50; // C6
        osc.type = 'sine';
        
        gain.gain.setValueAtTime(0, now);
        gain.gain.linearRampToValueAtTime(0.3, now + 0.008);
        gain.gain.exponentialRampToValueAtTime(0.12, now + 0.05);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
        
        osc.start(now);
        osc.stop(now + 0.25);
        
        // Subtle octave below - C5
        var octave = audioContext.createOscillator();
        var octaveGain = audioContext.createGain();
        octave.connect(octaveGain);
        octaveGain.connect(audioContext.destination);
        octave.frequency.value = 523.25; // C5
        octave.type = 'sine';
        octaveGain.gain.setValueAtTime(0, now);
        octaveGain.gain.linearRampToValueAtTime(0.09, now + 0.01);
        octaveGain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
        octave.start(now);
        octave.stop(now + 0.2);
        </script>
        """
    else:  # EXIT signal
        # EXIT Signal - Lower pitch (F5 with F4 octave)
        sound_script = """
        <script>
        var audioContext = new (window.AudioContext || window.webkitAudioContext)();
        var now = audioContext.currentTime;
        
        // Primary tone - F5
        var osc = audioContext.createOscillator();
        var gain = audioContext.createGain();
        var filter = audioContext.createBiquadFilter();
        
        osc.connect(filter);
        filter.connect(gain);
        gain.connect(audioContext.destination);
        
        filter.type = 'lowpass';
        filter.frequency.value = 3500;
        filter.Q.value = 0.1;
        
        osc.frequency.value = 698.46; // F5
        osc.type = 'sine';
        
        gain.gain.setValueAtTime(0, now);
        gain.gain.linearRampToValueAtTime(0.3, now + 0.008);
        gain.gain.exponentialRampToValueAtTime(0.12, now + 0.06);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
        
        osc.start(now);
        osc.stop(now + 0.3);
        
        // Subtle octave below - F4
        var octave = audioContext.createOscillator();
        var octaveGain = audioContext.createGain();
        octave.connect(octaveGain);
        octaveGain.connect(audioContext.destination);
        octave.frequency.value = 349.23; // F4
        octave.type = 'sine';
        octaveGain.gain.setValueAtTime(0, now);
        octaveGain.gain.linearRampToValueAtTime(0.09, now + 0.01);
        octaveGain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
        octave.start(now);
        octave.stop(now + 0.25);
        </script>
        """
    
    st.components.v1.html(sound_script, height=0)

def check_for_new_signals(signals):
    """Check if there are new non-HOLD signals and play sound if needed"""
    if not signals:
        return
    
    # Create a set of current signal identifiers (excluding HOLD signals)
    current_signals = set()
    latest_signal_type = None
    
    for sig in signals:
        if sig['action'] != 'HOLD':
            # Create unique identifier for each signal
            sig_id = f"{sig['symbol']}_{sig['action']}_{sig['timestamp']}"
            current_signals.add(sig_id)
            
            # Track the type of the newest signal
            if sig_id not in st.session_state.previous_signals:
                latest_signal_type = sig['action']
    
    # Check if there are new signals
    new_signals = current_signals - st.session_state.previous_signals
    
    if new_signals and st.session_state.previous_signals:  # Don't play on first load
        # Play sound based on the latest signal type
        if latest_signal_type:
            play_notification_sound(signal_type=latest_signal_type)
    
    # Update the stored signals
    st.session_state.previous_signals = current_signals

# Elite Professional CSS
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
   
   /* Live Price Indicator */
   .live-price-indicator {
       display: inline-block;
       width: 6px;
       height: 6px;
       border-radius: 50%;
       background: var(--primary-green);
       animation: pulse 2s infinite;
       margin-left: 4px;
   }
   
   @keyframes pulse {
       0% { opacity: 1; box-shadow: 0 0 0 0 rgba(52, 199, 89, 0.7); }
       70% { opacity: 1; box-shadow: 0 0 0 6px rgba(52, 199, 89, 0); }
       100% { opacity: 1; box-shadow: 0 0 0 0 rgba(52, 199, 89, 0); }
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
   
   /* Live Signal Style */
   .live-signal {
       display: flex;
       justify-content: space-between;
       align-items: center;
       padding: 12px 16px;
       background: var(--bg-secondary);
       border-radius: 10px;
       margin-bottom: 10px;
       border: 1px solid var(--border-color);
       transition: all 0.15s ease;
   }
   
   .live-signal:hover {
       background: var(--bg-hover);
       transform: translateX(2px);
   }
   
   .live-signal-long {
       background: linear-gradient(90deg, rgba(52, 199, 89, 0.1), transparent);
       border-left: 3px solid var(--primary-green);
   }
   
   .live-signal-exit {
       background: linear-gradient(90deg, rgba(255, 69, 58, 0.1), transparent);
       border-left: 3px solid var(--primary-red);
   }
   
   .live-signal-hold {
       border-left: 3px solid rgba(255, 255, 255, 0.2);
   }
   
   /* Historical Signal */
   .historical-signal {
       display: flex;
       justify-content: space-between;
       align-items: center;
       padding: 10px 14px;
       background: var(--bg-secondary);
       border-radius: 8px;
       margin-bottom: 6px;
       border: 1px solid var(--border-color);
       transition: all 0.15s ease;
       font-size: 13px;
   }
   
   .historical-signal:hover {
       background: var(--bg-hover);
       transform: translateX(2px);
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
   
   /* Trade History Table */
   .trade-row {
       display: grid;
       grid-template-columns: 0.8fr 1.2fr 1fr 1fr 1fr 1fr;
       padding: 10px 14px;
       border-bottom: 1px solid var(--border-color);
       font-size: 12px;
       transition: all 0.15s ease;
   }
   
   .trade-row:hover {
       background: var(--bg-hover);
   }
   
   .trade-header {
       font-weight: 600;
       color: var(--text-secondary);
       text-transform: uppercase;
       font-size: 10px;
       letter-spacing: 0.5px;
       background: var(--bg-secondary);
   }
   
   /* Disable flicker animations */
   * {
       animation: none !important;
       transition: none !important;
   }
   
   /* Re-enable specific transitions */
   .metric-card,
   .signal-card,
   .live-signal,
   .historical-signal,
   .trade-row {
       transition: transform 0.15s ease, background 0.15s ease !important;
   }
   
   /* Re-enable pulse for live indicator */
   .live-price-indicator {
       animation: pulse 2s infinite !important;
   }
</style>
""", unsafe_allow_html=True)

# GitHub Data Loading Functions - NO CACHING, AGGRESSIVE CACHE BUSTING
def load_from_github(path):
    """Load JSON from GitHub raw URL with aggressive cache busting"""
    try:
        # Multiple cache-busting parameters
        timestamp = int(time.time() * 1000)
        random_str = random.randint(100000, 999999)
        cache_buster = hashlib.md5(f"{timestamp}{random_str}".encode()).hexdigest()[:8]
        
        url = f"{GITHUB_RAW_BASE}/{path}"
        params = {
            't': timestamp,
            'r': random_str,
            'cb': cache_buster
        }
        
        headers = {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def load_status():
    """Load current status from GitHub"""
    return load_from_github("status.json") or {}

def load_realtime_prices():
    """Load real-time prices from GitHub"""
    return load_from_github("realtime_prices.json") or {}

def load_signals():
    """Load today's signals from GitHub"""
    today = datetime.now().strftime('%Y%m%d')
    return load_from_github(f"signals/signals_{today}.json") or []

def load_position_states():
    """Load position states from GitHub"""
    return load_from_github("data/position_states.json") or {}

def load_trades_history():
    """Load trades history from GitHub"""
    return load_from_github("data/trades_history.json") or []

# Helper Functions
def convert_to_et(timestamp_str):
    """Convert ISO timestamp to ET timezone"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt.astimezone(ET)
    except:
        return datetime.now(ET)

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

def process_signals_for_display(signals, saved_positions):
    """Process signals and track trades"""
    if not signals:
        latest_signals = {}
        for symbol, pos in saved_positions.items():
            if pos.get('is_open'):
                latest_signals[symbol] = {
                    'symbol': symbol,
                    'action': 'LONG',
                    'price': pos.get('entry_price', 0),
                    'timestamp': pos.get('entry_time', datetime.now().isoformat()),
                    'confidence': pos.get('last_confidence', 0)
                }
        return [], latest_signals, 0, 0, None
    
    sorted_signals = sorted(signals, key=lambda x: x['timestamp'])
    last_signal_time = convert_to_et(sorted_signals[-1]['timestamp']) if sorted_signals else None
    
    position_states = {}
    for symbol in ASSETS:
        if symbol in saved_positions:
            pos = saved_positions[symbol]
            position_states[symbol] = {
                'position': 'LONG' if pos.get('is_open') else 'FLAT',
                'entry_price': pos.get('entry_price', 0)
            }
        else:
            position_states[symbol] = {'position': 'FLAT', 'entry_price': 0}
    
    latest_signals = {}
    unique_long_count = 0
    unique_exit_count = 0
    
    for sig in sorted_signals:
        symbol = sig['symbol']
        action = sig['action']
        
        if action == 'LONG' and position_states[symbol]['position'] != 'LONG':
            position_states[symbol] = {'position': 'LONG', 'entry_price': sig['price']}
            unique_long_count += 1
        elif action == 'EXIT' and position_states[symbol]['position'] == 'LONG':
            position_states[symbol] = {'position': 'FLAT', 'entry_price': 0}
            unique_exit_count += 1
        
        latest_signals[symbol] = sig
    
    for symbol in ASSETS:
        if symbol not in latest_signals and symbol in saved_positions:
            pos = saved_positions[symbol]
            if pos.get('is_open'):
                latest_signals[symbol] = {
                    'symbol': symbol,
                    'action': 'LONG',
                    'price': pos.get('entry_price', 0),
                    'timestamp': pos.get('entry_time', datetime.now().isoformat()),
                    'confidence': pos.get('last_confidence', 0)
                }
    
    return sorted_signals, latest_signals, unique_long_count, unique_exit_count, last_signal_time

def get_market_status():
    """Check market status"""
    now = datetime.now(ET)
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
    # Clear cache periodically
    if st.session_state.counter % 10 == 0:
        st.cache_data.clear()
    
    # Create container
    main_container = st.container()
    
    with main_container:
        # Load all data from GitHub
        status = load_status()
        raw_signals = load_signals()
        trades_history = load_trades_history()
        realtime_prices = load_realtime_prices()
        saved_positions = load_position_states()
        
        # Check for new signals
        check_for_new_signals(raw_signals)
        
        # Check connection status
        is_connected = False
        if status and 'timestamp' in status:
            try:
                last_update = datetime.fromisoformat(status['timestamp'].replace('Z', '+00:00'))
                if last_update.tzinfo is None:
                    last_update = last_update.replace(tzinfo=pytz.UTC)
                now_utc = datetime.now(pytz.UTC)
                time_diff = (now_utc - last_update).total_seconds()
                is_connected = time_diff < 90  # 90 second threshold
            except:
                is_connected = False
        
        # Title with connection status
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
            <div style="text-align: center; padding: 80px;">
                <div style="font-size: 20px; color: var(--text-secondary);">
                    Waiting for trading system data...
                </div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(3)
            st.rerun()
            return
        
        # Process signals
        all_signals, latest_signals, unique_longs, unique_exits, last_signal_time = process_signals_for_display(raw_signals, saved_positions)
        
        # Get market status
        market_status, status_class = get_market_status()
        
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
            display_time = last_signal_time.strftime('%H:%M:%S') if last_signal_time else "--:--:--"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Last Signal</div>
                <div class="metric-value" style="font-size: 22px;">{display_time}</div>
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
            # Calculate total P&L using real-time prices
            total_pnl = 0
            if status and 'positions' in status:
                for symbol, pos in status['positions'].items():
                    if pos['is_open']:
                        current = 0
                        if 'prices' in realtime_prices and symbol in realtime_prices['prices']:
                            current = realtime_prices['prices'][symbol]
                        elif 'realtime_prices' in status and symbol in status['realtime_prices']:
                            current = status['realtime_prices'][symbol]
                        elif symbol in status.get('latest_prices', {}):
                            current = status['latest_prices'][symbol]
                        
                        entry = pos['entry_price']
                        if entry > 0 and current > 0:
                            pnl = ((current - entry) / entry * 100)
                            total_pnl += pnl
            
            pnl_color = "#34C759" if total_pnl > 0 else "#FF453A" if total_pnl < 0 else "rgba(255,255,255,0.5)"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Open P&L</div>
                <div class="metric-value" style="color: {pnl_color};">
                    {total_pnl:+.2f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col6:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Closed Today</div>
                <div class="metric-value">{unique_exits}</div>
                <div class="metric-delta">trades</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Performance Overview
        st.markdown('<div class="section-header">Portfolio Performance</div>', unsafe_allow_html=True)
        
        perf_col1, perf_col2 = st.columns([1, 5])
        with perf_col1:
            perf_filter = st.selectbox("Filter", ["ALL"] + ASSETS, key="perf_filter")
        
        metrics = calculate_performance_metrics(trades_history, perf_filter)
        
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
        tab1, tab2, tab3 = st.tabs(["📡 Live Signals", "📜 Historical Signals", "💰 Trade History"])
        
        with tab1:
            col_left, col_right = st.columns([3, 2])
            
            with col_left:
                st.markdown('<div class="section-header">🎯 Latest Signal Per Asset</div>', unsafe_allow_html=True)
                
                for symbol in ASSETS:
                    if symbol in latest_signals:
                        sig = latest_signals[symbol]
                        sig_time = convert_to_et(sig['timestamp'])
                        time_str = sig_time.strftime('%H:%M:%S')
                        
                        if sig['action'] == 'LONG':
                            card_class = "live-signal-long"
                            action_color = "#34C759"
                            icon = "🟢"
                        elif sig['action'] == 'EXIT':
                            card_class = "live-signal-exit"
                            action_color = "#FF453A"
                            icon = "🔴"
                        else:
                            card_class = "live-signal-hold"
                            action_color = "rgba(255,255,255,0.6)"
                            icon = "⚪"
                        
                        st.markdown(f"""
                        <div class="live-signal {card_class}">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="color: {action_color}; font-weight: 600; font-size: 15px;">
                                        {icon} {symbol} - {sig['action']}
                                    </span>
                                    <span style="color: var(--text-secondary); font-size: 13px; margin-left: 12px;">
                                        ${sig['price']:.2f} • {time_str}
                                    </span>
                                </div>
                                <div style="color: {action_color}; font-weight: 700; font-size: 20px;">
                                    {sig.get('confidence', 0)*100:.1f}%
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="live-signal" style="opacity: 0.3;">
                            <div style="font-size: 14px; color: var(--text-tertiary);">
                                {symbol} - No signals today
                            </div>
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
                                
                                current = 0
                                price_is_live = False
                                
                                if 'prices' in realtime_prices and symbol in realtime_prices['prices']:
                                    current = realtime_prices['prices'][symbol]
                                    price_is_live = True
                                elif 'realtime_prices' in status and symbol in status['realtime_prices']:
                                    current = status['realtime_prices'][symbol]
                                    price_is_live = True
                                elif symbol in status.get('latest_prices', {}):
                                    current = status['latest_prices'][symbol]
                                
                                entry = pos['entry_price']
                                if entry > 0 and current > 0:
                                    pnl = ((current - entry) / entry * 100)
                                    pnl_color = "#34C759" if pnl > 0 else "#FF453A"
                                    
                                    price_display = f"${current:.2f}"
                                    if price_is_live:
                                        price_display += '<span class="live-price-indicator"></span>'
                                    
                                    st.markdown(f"""
                                    <div class="signal-card" style="border-left: 2px solid {pnl_color};">
                                        <div style="font-size: 14px; font-weight: 600; margin-bottom: 8px;">
                                            {symbol} - LONG
                                        </div>
                                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
                                            <div>
                                                <span style="color: var(--text-tertiary);">Entry:</span>
                                                <span style="color: var(--text-primary);"> ${entry:.2f}</span>
                                            </div>
                                            <div>
                                                <span style="color: var(--text-tertiary);">Current:</span>
                                                <span style="color: var(--text-primary);"> {price_display}</span>
                                            </div>
                                            <div>
                                                <span style="color: var(--text-tertiary);">P&L:</span>
                                                <span style="color: {pnl_color}; font-weight: 600;"> {pnl:+.2f}%</span>
                                            </div>
                                            <div>
                                                <span style="color: var(--text-tertiary);">Conf:</span>
                                                <span style="color: var(--text-primary);"> {pos.get('last_confidence', 0)*100:.1f}%</span>
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                    
                    if not has_positions:
                        st.markdown("""
                        <div style="text-align: center; padding: 40px; color: var(--text-tertiary);">
                            No open positions
                        </div>
                        """, unsafe_allow_html=True)
                
                # Price update status
                if 'last_update' in realtime_prices:
                    try:
                        price_update_time = datetime.fromisoformat(realtime_prices['last_update'])
                        if price_update_time.tzinfo is None:
                            price_update_time = price_update_time.replace(tzinfo=pytz.UTC)
                        
                        now_utc = datetime.now(pytz.UTC)
                        seconds_ago = (now_utc - price_update_time).total_seconds()
                        
                        if seconds_ago < 150:
                            update_text = f"Prices updated {int(seconds_ago)}s ago"
                            update_color = "#34C759"
                        else:
                            update_text = f"Prices updated {int(seconds_ago/60)}m ago"
                            update_color = "#FF9500"
                        
                        st.markdown(f"""
                        <div style="text-align: center; margin-top: 16px; padding: 8px; 
                                    background: var(--bg-secondary); border-radius: 8px; 
                                    font-size: 11px; color: {update_color};">
                            {update_text}
                        </div>
                        """, unsafe_allow_html=True)
                    except:
                        pass
        
        with tab2:
            st.markdown('<div class="section-header">📜 Historical Signals</div>', unsafe_allow_html=True)
            
            hist_filter = st.selectbox("Filter by Asset", ["ALL"] + ASSETS, key="hist_filter")
            
            if hist_filter == "ALL":
                filtered_signals = all_signals
            else:
                filtered_signals = [s for s in all_signals if s['symbol'] == hist_filter]
            
            filtered_signals = sorted(filtered_signals, key=lambda x: x['timestamp'], reverse=True)
            
            if filtered_signals:
                for sig in filtered_signals[:100]:
                    sig_time = convert_to_et(sig['timestamp'])
                    time_str = sig_time.strftime('%m/%d %H:%M:%S')
                    
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
                            <span style="color: var(--text-secondary);">
                                {time_str} • ${sig['price']:.2f}
                            </span>
                        </div>
                        <div style="color: {action_color}; font-weight: 600;">
                            {sig.get('confidence', 0)*100:.1f}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align: center; padding: 40px; color: var(--text-tertiary);">
                    No historical signals
                </div>
                """, unsafe_allow_html=True)
        
        with tab3:
            st.markdown('<div class="section-header">💰 Completed Trades</div>', unsafe_allow_html=True)
            
            if trades_history:
                recent_trades = sorted(trades_history, key=lambda x: x.get('exit_time', ''), reverse=True)[:50]
                
                st.markdown("""
                <div class="trade-row trade-header">
                    <div>Symbol</div>
                    <div>Exit Time</div>
                    <div>Entry</div>
                    <div>Exit</div>
                    <div>P&L %</div>
                    <div>P&L $</div>
                </div>
                """, unsafe_allow_html=True)
                
                for trade in recent_trades:
                    try:
                        exit_time = convert_to_et(trade['exit_time']).strftime('%m/%d %H:%M')
                    except:
                        exit_time = "N/A"
                    
                    pnl_color = "#34C759" if trade.get('pnl_percent', 0) > 0 else "#FF453A"
                    
                    st.markdown(f"""
                    <div class="trade-row">
                        <div style="font-weight: 600;">{trade.get('symbol', 'N/A')}</div>
                        <div style="color: var(--text-secondary);">{exit_time}</div>
                        <div>${trade.get('entry_price', 0):.2f}</div>
                        <div>${trade.get('exit_price', 0):.2f}</div>
                        <div style="color: {pnl_color}; font-weight: 600;">
                            {trade.get('pnl_percent', 0):+.2f}%
                        </div>
                        <div style="color: {pnl_color};">
                            ${trade.get('pnl_dollar', 0):+.2f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align: center; padding: 40px; color: var(--text-tertiary);">
                    No completed trades yet
                </div>
                """, unsafe_allow_html=True)
        
        # Footer
        price_status = ""
        if 'last_update' in realtime_prices:
            try:
                price_update = datetime.fromisoformat(realtime_prices['last_update'])
                if price_update.tzinfo is None:
                    price_update = price_update.replace(tzinfo=pytz.UTC)
                seconds_ago = (datetime.now(pytz.UTC) - price_update).total_seconds()
                if seconds_ago < 150:
                    price_status = " • 🟢 Real-time prices active"
            except:
                pass
        
        st.markdown(f"""
        <div style="text-align: center; color: var(--text-tertiary); font-size: 11px; 
             padding: 24px 0; border-top: 1px solid var(--border-color); margin-top: 40px;">
            Last Signal: {last_signal_time.strftime('%H:%M:%S') if last_signal_time else 'N/A'} • 
            Auto-refresh: 3 seconds{price_status} • 
            {'🟢 Connected' if is_connected else '🔴 Disconnected'} • 
            Data source: GitHub Raw URLs
        </div>
        """, unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(3)
    st.session_state.counter += 1
    st.rerun()

if __name__ == "__main__":
    main()