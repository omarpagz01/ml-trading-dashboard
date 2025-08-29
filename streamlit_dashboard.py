"""
Elite Signals Dashboard - Professional Trading Interface
Enhanced with Real-Time Price Updates and Live P&L Tracking
Fixed for Streamlit Cloud updates
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
import pytz
import os
import hashlib

# Page configuration - MUST be first Streamlit command
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

# CRITICAL: Force Streamlit to detect file changes
def get_file_hash(filepath):
    """Get hash of file to detect changes"""
    if filepath.exists():
        return hashlib.md5(open(filepath,'rb').read()).hexdigest()
    return None

def check_for_updates():
    """Check if data files have been updated"""
    version_file = Path("data_version.txt")
    if version_file.exists():
        with open(version_file, 'r') as f:
            version = f.read().strip()
            
        if 'last_version' not in st.session_state:
            st.session_state.last_version = version
        elif st.session_state.last_version != version:
            st.session_state.last_version = version
            # Force complete refresh
            st.cache_data.clear()
            for key in list(st.session_state.keys()):
                if key not in ['last_version']:
                    del st.session_state[key]

# Run update check
check_for_updates()

# Initialize session state
if 'previous_signals' not in st.session_state:
    st.session_state.previous_signals = set()
if 'counter' not in st.session_state:
    st.session_state.counter = 0
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

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

def load_json_file(filepath):
    """Load JSON file without any caching"""
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            pass
    return None

def load_trades_history():
    """Load historical trades from file"""
    data = load_json_file(Path("data/trades_history.json"))
    return data if data else []

def load_position_states():
    """Load persistent position states"""
    data = load_json_file(Path("data/position_states.json"))
    return data if data else {}

def load_realtime_prices():
    """Load real-time prices"""
    data = load_json_file(Path("realtime_prices.json"))
    return data if data else {}

def load_signals():
    """Load today's signals"""
    signal_file = Path("signals") / f"signals_{datetime.now().strftime('%Y%m%d')}.json"
    data = load_json_file(signal_file)
    return data if data else []

def load_status():
    """Load current status"""
    data = load_json_file(Path("status.json"))
    return data if data else {}

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
    """Process signals and track trades"""
    saved_positions = load_position_states()
    
    if not signals:
        latest_signals = {}
        for symbol, pos in saved_positions.items():
            if pos.get('is_open'):
                latest_signals[symbol] = {
                    'symbol': symbol,
                    'action': 'LONG',
                    'price': pos.get('entry_price', 0),
                    'timestamp': pos.get('entry_time', datetime.now().isoformat()),
                    'confidence': pos.get('last_confidence', 0),
                    'is_new_position': True
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
                'entry_price': pos.get('entry_price', 0),
                'entry_time': pos.get('entry_time'),
                'first_entry_time': pos.get('entry_time'),
                'consecutive_count': 0
            }
        else:
            position_states[symbol] = {
                'position': 'FLAT',
                'entry_price': 0,
                'entry_time': None,
                'first_entry_time': None,
                'consecutive_count': 0
            }
    
    latest_signals = {}
    unique_long_count = 0
    unique_exit_count = 0
    
    for sig in sorted_signals:
        symbol = sig['symbol']
        action = sig['action']
        timestamp = sig['timestamp']
        
        if action == 'LONG':
            if position_states[symbol]['position'] != 'LONG':
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
                position_states[symbol]['consecutive_count'] += 1
                sig['is_new_position'] = False
                sig['consecutive_count'] = position_states[symbol]['consecutive_count']
                sig['first_signal_time'] = position_states[symbol]['first_entry_time']
                
        elif action == 'EXIT' and position_states[symbol]['position'] == 'LONG':
            position_states[symbol] = {'position': 'FLAT', 'entry_price': 0, 'entry_time': None}
            unique_exit_count += 1
            sig['is_new_position'] = True
        else:
            sig['is_new_position'] = False
        
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
                    'confidence': pos.get('last_confidence', 0),
                    'is_new_position': True
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

# Elite Professional CSS
st.markdown("""
<style>
   @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
   
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
   
   * {
       margin: 0;
       padding: 0;
       box-sizing: border-box;
   }
   
   .stApp {
       background: var(--bg-primary);
       font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
   }
   
   #MainMenu, footer, header {visibility: hidden;}
   .block-container {
       padding: 2rem 2rem 0 2rem !important;
       max-width: 100% !important;
   }
   
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
   
   .signal-card {
       background: var(--bg-secondary);
       border-radius: 12px;
       padding: 14px 16px;
       margin-bottom: 10px;
       border: 1px solid var(--border-color);
   }
   
   .section-header {
       color: var(--text-primary);
       font-size: 18px;
       font-weight: 600;
       margin: 24px 0 16px 0;
       padding-bottom: 8px;
       border-bottom: 1px solid var(--border-color);
       letter-spacing: -0.3px;
   }
</style>
""", unsafe_allow_html=True)

# Main Dashboard
def main():
    # Load data fresh every time
    raw_signals = load_signals()
    status = load_status()
    trades_history = load_trades_history()
    realtime_prices = load_realtime_prices()
    
    # Get market status
    market_status, status_class = get_market_status()
    
    # Check connection
    is_connected = False
    if status and 'timestamp' in status:
        try:
            last_update = datetime.fromisoformat(status['timestamp'].replace('Z', '+00:00'))
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=pytz.UTC)
            time_diff = (datetime.now(pytz.UTC) - last_update).total_seconds()
            if time_diff < 60:
                is_connected = True
        except:
            pass
    
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
        <div style="text-align: center; padding: 80px;">
            <div style="font-size: 20px; color: var(--text-secondary);">
                Waiting for trading system data...
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(2)
        st.rerun()
        return
    
    # Process signals
    all_signals, latest_signals, unique_longs, unique_exits, last_signal_time = process_signals_for_display(raw_signals, status)
    
    # Metrics
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
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        active_positions = sum(1 for p in status.get('positions', {}).values() if p.get('is_open'))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Positions</div>
            <div class="metric-value">{active_positions}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        total_pnl = 0
        if status and 'positions' in status:
            for symbol, pos in status['positions'].items():
                if pos['is_open']:
                    current = 0
                    if 'prices' in realtime_prices and symbol in realtime_prices['prices']:
                        current = realtime_prices['prices'][symbol]
                    elif symbol in status.get('latest_prices', {}):
                        current = status['latest_prices'][symbol]
                    
                    entry = pos['entry_price']
                    if entry > 0 and current > 0:
                        pnl = ((current - entry) / entry * 100)
                        total_pnl += pnl
        
        pnl_color = "#34C759" if total_pnl > 0 else "#FF453A"
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
        </div>
        """, unsafe_allow_html=True)
    
    # Current Positions
    st.markdown('<div class="section-header">💼 Current Positions</div>', unsafe_allow_html=True)
    
    if status and 'positions' in status:
        for symbol in ASSETS:
            if symbol in status['positions']:
                pos = status['positions'][symbol]
                if pos['is_open']:
                    current = 0
                    if 'prices' in realtime_prices and symbol in realtime_prices['prices']:
                        current = realtime_prices['prices'][symbol]
                    
                    entry = pos['entry_price']
                    if entry > 0 and current > 0:
                        pnl = ((current - entry) / entry * 100)
                        pnl_color = "#34C759" if pnl > 0 else "#FF453A"
                        
                        st.markdown(f"""
                        <div class="signal-card">
                            <div style="display: flex; justify-content: space-between;">
                                <div>
                                    <strong>{symbol}</strong> - Entry: ${entry:.2f} | Current: ${current:.2f}
                                </div>
                                <div style="color: {pnl_color}; font-weight: bold;">
                                    {pnl:+.2f}%
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(1)  # Very fast refresh
    st.session_state.counter += 1
    st.rerun()

if __name__ == "__main__":
    main()
