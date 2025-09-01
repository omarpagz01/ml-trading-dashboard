"""
Elite Signals Dashboard - Professional Trading Interface
Fetching directly from GitHub Raw URLs for real-time updates
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
import requests

# Page configuration
st.set_page_config(
   page_title="Signals Dashboard",
   page_icon="📊",
   layout="wide",
   initial_sidebar_state="collapsed"
)

# GitHub raw content base URL - fetches directly from GitHub
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/omarpagz01/ml-trading-dashboard/main"

# Define assets
ASSETS = ['TSLA', 'HOOD', 'COIN', 'PLTR', 'AAPL']

# Set timezone
ET = pytz.timezone('US/Eastern')

# Initialize session state
if 'previous_signals' not in st.session_state:
    st.session_state.previous_signals = set()
if 'counter' not in st.session_state:
   st.session_state.counter = 0

# GitHub fetching functions with no caching
def load_from_github(path):
    """Load JSON from GitHub raw URL - always fresh"""
    try:
        url = f"{GITHUB_RAW_BASE}/{path}"
        # Add cache-busting parameter to force fresh fetch
        cache_buster = f"?cb={int(time.time())}"
        response = requests.get(url + cache_buster, headers={'Cache-Control': 'no-cache'}, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
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
            'losing_trades': 0
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
        'losing_trades': len(losses)
    }

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

# CSS Styling
st.markdown("""
<style>
   @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
   
   :root {
       --primary-green: #34C759;
       --primary-red: #FF453A;
       --primary-orange: #FF9500;
       --bg-primary: #000000;
       --bg-secondary: rgba(255,255,255,0.03);
       --border-color: rgba(255,255,255,0.08);
       --text-primary: #ffffff;
       --text-secondary: rgba(255,255,255,0.6);
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
       text-transform: uppercase;
   }
   
   .metric-card {
       background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
       border-radius: 16px;
       padding: 20px;
       border: 1px solid var(--border-color);
       height: 100px;
       display: flex;
       flex-direction: column;
       justify-content: space-between;
   }
   
   .metric-label {
       color: rgba(255,255,255,0.4);
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
   }
   
   .signal-card {
       background: var(--bg-secondary);
       border-radius: 12px;
       padding: 14px 16px;
       margin-bottom: 10px;
       border: 1px solid var(--border-color);
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
</style>
""", unsafe_allow_html=True)

# Main Dashboard
def main():
    # Load all data from GitHub
    status = load_status()
    raw_signals = load_signals()
    trades_history = load_trades_history()
    realtime_prices = load_realtime_prices()
    saved_positions = load_position_states()
    
    # Check connection
    is_connected = False
    if status and 'timestamp' in status:
        try:
            last_update = datetime.fromisoformat(status['timestamp'].replace('Z', '+00:00'))
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=pytz.UTC)
            time_diff = (datetime.now(pytz.UTC) - last_update).total_seconds()
            is_connected = time_diff < 60
        except:
            pass
    
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
        st.warning("Waiting for trading system data...")
        time.sleep(3)
        st.rerun()
        return
    
    # Get market status
    market_status, status_class = get_market_status()
    
    # Top Metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Market Status</div>
            <div class="metric-value" style="font-size: 16px;">{market_status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        last_signal_time = None
        if raw_signals:
            sorted_signals = sorted(raw_signals, key=lambda x: x['timestamp'])
            if sorted_signals:
                last_signal_time = convert_to_et(sorted_signals[-1]['timestamp'])
        
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
            <div class="metric-value">{len(raw_signals)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        active_positions = sum(1 for p in status.get('positions', {}).values() if p.get('is_open'))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Positions</div>
            <div class="metric-value">{active_positions}</div>
            <div style="font-size: 12px; color: var(--text-secondary);">of {len(ASSETS)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        # Calculate total P&L
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
        metrics = calculate_performance_metrics(trades_history)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Win Rate</div>
            <div class="metric-value">{metrics['win_rate']:.1f}%</div>
            <div style="font-size: 12px; color: var(--text-secondary);">{metrics['total_trades']} trades</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📡 Live Positions", "📜 Recent Signals", "💰 Trade History"])
    
    with tab1:
        st.markdown("### Current Positions")
        if status and 'positions' in status:
            for symbol in ASSETS:
                if symbol in status['positions']:
                    pos = status['positions'][symbol]
                    if pos['is_open']:
                        current = 0
                        if 'prices' in realtime_prices and symbol in realtime_prices['prices']:
                            current = realtime_prices['prices'][symbol]
                        elif symbol in status.get('latest_prices', {}):
                            current = status['latest_prices'][symbol]
                        
                        entry = pos['entry_price']
                        if entry > 0 and current > 0:
                            pnl = ((current - entry) / entry * 100)
                            pnl_color = "#34C759" if pnl > 0 else "#FF453A"
                            
                            st.markdown(f"""
                            <div class="signal-card">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong style="font-size: 16px;">{symbol}</strong><br>
                                        Entry: ${entry:.2f} | Current: ${current:.2f}
                                    </div>
                                    <div style="text-align: right;">
                                        <span style="color: {pnl_color}; font-size: 20px; font-weight: 600;">
                                            {pnl:+.2f}%
                                        </span>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Recent Signals")
        if raw_signals:
            sorted_signals = sorted(raw_signals, key=lambda x: x['timestamp'], reverse=True)
            for sig in sorted_signals[:10]:
                sig_time = convert_to_et(sig['timestamp'])
                action_color = "#34C759" if sig['action'] == 'LONG' else "#FF453A" if sig['action'] == 'EXIT' else "rgba(255,255,255,0.5)"
                
                st.markdown(f"""
                <div class="signal-card">
                    <span style="color: {action_color}; font-weight: 600;">
                        {sig['symbol']} - {sig['action']}
                    </span>
                    @ ${sig['price']:.2f} | {sig_time.strftime('%H:%M:%S')} | 
                    Confidence: {sig.get('confidence', 0)*100:.1f}%
                </div>
                """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### Trade History")
        if trades_history:
            recent_trades = sorted(trades_history, key=lambda x: x.get('exit_time', ''), reverse=True)[:20]
            for trade in recent_trades:
                pnl_color = "#34C759" if trade['pnl_percent'] > 0 else "#FF453A"
                st.markdown(f"""
                <div class="signal-card">
                    <strong>{trade['symbol']}</strong> | 
                    Entry: ${trade['entry_price']:.2f} → Exit: ${trade['exit_price']:.2f} | 
                    <span style="color: {pnl_color}; font-weight: 600;">
                        P&L: {trade['pnl_percent']:+.2f}%
                    </span>
                </div>
                """, unsafe_allow_html=True)
    
    # Footer
    st.markdown(f"""
    <div style="text-align: center; color: var(--text-secondary); font-size: 11px; 
         padding: 24px 0; border-top: 1px solid var(--border-color); margin-top: 40px;">
        Auto-refresh: 3 seconds | Data source: GitHub Raw URLs | 
        {'🟢 Connected' if is_connected else '🔴 Disconnected'}
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(3)
    st.session_state.counter += 1
    st.rerun()

if __name__ == "__main__":
    main()
