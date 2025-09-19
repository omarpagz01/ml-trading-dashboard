import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time
import numpy as np
from collections import defaultdict
import pytz
import requests
import random
import hashlib

# Page configuration
st.set_page_config(
    page_title="ML Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuration
ASSETS = ['TSLA', 'HOOD', 'COIN', 'PLTR', 'AAPL']
ET = pytz.timezone('US/Eastern')

# GitHub repository configuration - UPDATE THIS WITH YOUR REPO
GITHUB_USER = "YOUR_GITHUB_USERNAME"  # Replace with your GitHub username
GITHUB_REPO = "YOUR_REPO_NAME"  # Replace with your repo name
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main"

# Initialize session state
if 'previous_signals' not in st.session_state:
    st.session_state.previous_signals = set()
if 'counter' not in st.session_state:
    st.session_state.counter = 0
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# Custom CSS for dark theme
st.markdown("""
<style>
    /* Dark theme styling */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Container styling */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    
    /* Main header */
    .main-header {
        text-align: center;
        padding: 1rem 0 2rem 0;
        border-bottom: 2px solid #262730;
        margin-bottom: 2rem;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #252535 100%);
        border-radius: 10px;
        padding: 1.5rem;
        border: 1px solid #262730;
        height: 100%;
    }
    
    .metric-label {
        color: #8b8b9a;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        color: #fafafa;
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
    }
    
    .metric-delta {
        color: #8b8b9a;
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }
    
    /* Status indicators */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-open {
        background-color: #00d632;
        color: #000;
    }
    
    .status-closed {
        background-color: #ff3838;
        color: #fff;
    }
    
    .status-premarket {
        background-color: #ff9500;
        color: #000;
    }
    
    /* Signal cards */
    .signal-card {
        background: #1e1e2e;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border-left: 3px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .signal-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    
    .signal-long {
        border-left-color: #00d632;
        background: linear-gradient(90deg, rgba(0, 214, 50, 0.1), transparent);
    }
    
    .signal-exit {
        border-left-color: #ff3838;
        background: linear-gradient(90deg, rgba(255, 56, 56, 0.1), transparent);
    }
    
    .signal-hold {
        border-left-color: #8b8b9a;
    }
    
    /* Position cards */
    .position-card {
        background: #1e1e2e;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border: 1px solid #262730;
    }
    
    .position-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .position-symbol {
        font-size: 1.1rem;
        font-weight: bold;
        color: #fafafa;
    }
    
    .position-pnl {
        font-size: 1.1rem;
        font-weight: bold;
    }
    
    .pnl-positive {
        color: #00d632;
    }
    
    .pnl-negative {
        color: #ff3838;
    }
    
    /* Trade table */
    .trade-table {
        background: #1e1e2e;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .trade-row {
        display: grid;
        grid-template-columns: 1fr 2fr 1fr 1fr 1fr 1fr;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #262730;
        align-items: center;
    }
    
    .trade-header {
        background: #252535;
        font-weight: bold;
        color: #8b8b9a;
    }
    
    /* Connection status */
    .connection-status {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0.75rem;
        background: rgba(0, 214, 50, 0.1);
        border: 1px solid rgba(0, 214, 50, 0.3);
        border-radius: 15px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #00d632;
    }
    
    .connection-status.offline {
        background: rgba(255, 56, 56, 0.1);
        border-color: rgba(255, 56, 56, 0.3);
        color: #ff3838;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 currentColor;
        }
        70% {
            box-shadow: 0 0 0 6px rgba(0, 214, 50, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(0, 214, 50, 0);
        }
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def load_from_github(path):
    """Load JSON data from GitHub with cache busting"""
    try:
        # Cache busting parameters
        timestamp = int(time.time() * 1000)
        random_str = random.randint(100000, 999999)
        
        url = f"{GITHUB_RAW_BASE}/{path}"
        params = {
            't': timestamp,
            'r': random_str
        }
        
        headers = {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error loading {path}: {str(e)}")
    return None

def load_status():
    """Load current status"""
    return load_from_github("status.json") or {}

def load_signals():
    """Load today's signals"""
    today = datetime.now().strftime('%Y%m%d')
    return load_from_github(f"signals/signals_{today}.json") or []

def load_positions():
    """Load position states"""
    return load_from_github("data/position_states.json") or {}

def load_trades():
    """Load trade history"""
    return load_from_github("data/trades_history.json") or []

def load_realtime_prices():
    """Load real-time prices"""
    return load_from_github("realtime_prices.json") or {}

def convert_to_et(timestamp_str):
    """Convert timestamp to ET"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt.astimezone(ET)
    except:
        return datetime.now(ET)

def get_market_status():
    """Get current market status"""
    now = datetime.now(ET)
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday >= 5:
        return "WEEKEND", "status-closed"
    elif current_time < pd.Timestamp("09:30").time():
        return "PRE-MARKET", "status-premarket"
    elif current_time >= pd.Timestamp("16:00").time():
        return "AFTER-HOURS", "status-closed"
    elif pd.Timestamp("09:30").time() <= current_time < pd.Timestamp("16:00").time():
        return "MARKET OPEN", "status-open"
    else:
        return "CLOSED", "status-closed"

def calculate_metrics(trades, symbol_filter=None):
    """Calculate performance metrics"""
    if symbol_filter and symbol_filter != "ALL":
        trades = [t for t in trades if t.get('symbol') == symbol_filter]
    
    if not trades:
        return {
            'total_pnl': 0,
            'win_rate': 0,
            'total_trades': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0
        }
    
    wins = [t for t in trades if t.get('pnl_percent', 0) > 0]
    losses = [t for t in trades if t.get('pnl_percent', 0) < 0]
    
    total_wins = sum(abs(t.get('pnl_percent', 0)) for t in wins)
    total_losses = sum(abs(t.get('pnl_percent', 0)) for t in losses)
    
    return {
        'total_pnl': sum(t.get('pnl_percent', 0) for t in trades),
        'win_rate': (len(wins) / len(trades) * 100) if trades else 0,
        'total_trades': len(trades),
        'avg_win': (total_wins / len(wins)) if wins else 0,
        'avg_loss': (total_losses / len(losses)) if losses else 0,
        'profit_factor': (total_wins / total_losses) if total_losses > 0 else total_wins
    }

def play_notification_sound(signal_type='LONG'):
    """Play notification sound for new signals"""
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
    gain.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.3);
    
    osc.start(audioContext.currentTime);
    osc.stop(audioContext.currentTime + 0.3);
    </script>
    """
    
    st.components.v1.html(sound_script, height=0)

def check_new_signals(signals):
    """Check for new signals and play sound"""
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
            play_notification_sound(latest_signal_type)
    
    st.session_state.previous_signals = current_signals

# Main app
def main():
    # Load all data
    status = load_status()
    signals = load_signals()
    positions = load_positions()
    trades = load_trades()
    realtime_prices = load_realtime_prices()
    
    # Check for new signals
    check_new_signals(signals)
    
    # Check connection status
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
        <h1 class="main-title">ML Trading Dashboard</h1>
        <div class="connection-status {'offline' if not is_connected else ''}">
            <span class="status-dot"></span>
            {'LIVE' if is_connected else 'OFFLINE'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Get market status
    market_status, status_class = get_market_status()
    
    # Top metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Market Status</div>
            <div class="status-badge {status_class}">{market_status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        active_positions = sum(1 for p in positions.values() if p.get('is_open'))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Positions</div>
            <div class="metric-value">{active_positions}</div>
            <div class="metric-delta">of {len(ASSETS)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        unique_longs = len([s for s in signals if s['action'] == 'LONG'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Signals Today</div>
            <div class="metric-value">{len(signals)}</div>
            <div class="metric-delta">{unique_longs} longs</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Calculate open P&L
        total_pnl = 0
        if positions and realtime_prices.get('prices'):
            for symbol, pos in positions.items():
                if pos.get('is_open'):
                    current = realtime_prices['prices'].get(symbol, 0)
                    entry = pos.get('entry_price', 0)
                    if current > 0 and entry > 0:
                        pnl = ((current - entry) / entry) * 100
                        total_pnl += pnl
        
        pnl_class = "pnl-positive" if total_pnl > 0 else "pnl-negative" if total_pnl < 0 else ""
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Open P&L</div>
            <div class="metric-value {pnl_class}">{total_pnl:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        metrics = calculate_metrics(trades)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Win Rate</div>
            <div class="metric-value">{metrics['win_rate']:.1f}%</div>
            <div class="metric-delta">{metrics['total_trades']} trades</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        pnl_class = "pnl-positive" if metrics['total_pnl'] > 0 else "pnl-negative" if metrics['total_pnl'] < 0 else ""
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total P&L</div>
            <div class="metric-value {pnl_class}">{metrics['total_pnl']:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📡 Live Signals", "💼 Positions", "📊 Performance", "💰 Trade History"])
    
    with tab1:
        st.markdown("### Latest Signals")
        
        # Get latest signal for each asset
        latest_signals = {}
        for sig in signals:
            symbol = sig['symbol']
            if symbol not in latest_signals or sig['timestamp'] > latest_signals[symbol]['timestamp']:
                latest_signals[symbol] = sig
        
        # Display signals
        for symbol in ASSETS:
            if symbol in latest_signals:
                sig = latest_signals[symbol]
                sig_time = convert_to_et(sig['timestamp'])
                
                action_class = ""
                if sig['action'] == 'LONG':
                    action_class = "signal-long"
                    icon = "🟢"
                elif sig['action'] == 'EXIT':
                    action_class = "signal-exit"
                    icon = "🔴"
                else:
                    action_class = "signal-hold"
                    icon = "⚪"
                
                st.markdown(f"""
                <div class="signal-card {action_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 1.2rem; font-weight: bold;">
                                {icon} {symbol} - {sig['action']}
                            </span>
                            <span style="margin-left: 1rem; color: #8b8b9a;">
                                ${sig['price']:.2f} • {sig_time.strftime('%H:%M:%S')}
                            </span>
                        </div>
                        <div style="font-size: 1.5rem; font-weight: bold;">
                            {sig.get('confidence', 0)*100:.1f}%
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="signal-card" style="opacity: 0.5;">
                    <div>{symbol} - No signals today</div>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Current Positions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Open Positions")
            
            has_positions = False
            if positions and realtime_prices.get('prices'):
                for symbol, pos in positions.items():
                    if pos.get('is_open'):
                        has_positions = True
                        current = realtime_prices['prices'].get(symbol, 0)
                        entry = pos.get('entry_price', 0)
                        
                        if current > 0 and entry > 0:
                            pnl = ((current - entry) / entry) * 100
                            pnl_class = "pnl-positive" if pnl > 0 else "pnl-negative"
                            
                            st.markdown(f"""
                            <div class="position-card">
                                <div class="position-header">
                                    <span class="position-symbol">{symbol}</span>
                                    <span class="position-pnl {pnl_class}">{pnl:+.2f}%</span>
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.9rem;">
                                    <div>Entry: ${entry:.2f}</div>
                                    <div>Current: ${current:.2f}</div>
                                    <div>Confidence: {pos.get('last_confidence', 0)*100:.1f}%</div>
                                    <div>P&L: ${(current - entry) * 100:+.2f}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            
            if not has_positions:
                st.info("No open positions")
        
        with col2:
            st.markdown("#### Position Summary")
            
            summary_data = []
            for symbol in ASSETS:
                pos = positions.get(symbol, {})
                status = "LONG" if pos.get('is_open') else "FLAT"
                summary_data.append({
                    'Symbol': symbol,
                    'Status': status,
                    'Entry': f"${pos.get('entry_price', 0):.2f}" if pos.get('is_open') else "-",
                    'Confidence': f"{pos.get('last_confidence', 0)*100:.1f}%" if pos.get('last_confidence') else "-"
                })
            
            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tab3:
        st.markdown("### Performance Metrics")
        
        # Performance filter
        perf_filter = st.selectbox("Filter by Symbol", ["ALL"] + ASSETS, key="perf_filter")
        
        # Calculate metrics
        metrics = calculate_metrics(trades, perf_filter)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total P&L", f"{metrics['total_pnl']:+.2f}%")
        
        with col2:
            st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
        
        with col3:
            st.metric("Profit Factor", f"{metrics['profit_factor']:.2f}")
        
        with col4:
            st.metric("Total Trades", metrics['total_trades'])
        
        # P&L Chart
        if trades:
            df_trades = pd.DataFrame(trades)
            if 'exit_time' in df_trades.columns:
                df_trades['exit_time'] = pd.to_datetime(df_trades['exit_time'])
                df_trades = df_trades.sort_values('exit_time')
                df_trades['cumulative_pnl'] = df_trades['pnl_percent'].cumsum()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_trades['exit_time'],
                    y=df_trades['cumulative_pnl'],
                    mode='lines+markers',
                    name='Cumulative P&L',
                    line=dict(color='#667eea', width=2),
                    marker=dict(size=6)
                ))
                
                fig.update_layout(
                    title="Cumulative P&L Over Time",
                    xaxis_title="Date",
                    yaxis_title="P&L (%)",
                    template="plotly_dark",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown("### Trade History")
        
        if trades:
            # Convert to DataFrame for easier manipulation
            df_trades = pd.DataFrame(trades)
            
            # Sort by exit time
            if 'exit_time' in df_trades.columns:
                df_trades['exit_time'] = pd.to_datetime(df_trades['exit_time'])
                df_trades = df_trades.sort_values('exit_time', ascending=False)
            
            # Display recent trades
            st.markdown("""
            <div class="trade-table">
                <div class="trade-row trade-header">
                    <div>Symbol</div>
                    <div>Exit Time</div>
                    <div>Entry</div>
                    <div>Exit</div>
                    <div>P&L %</div>
                    <div>P&L $</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            for _, trade in df_trades.head(20).iterrows():
                pnl_class = "pnl-positive" if trade.get('pnl_percent', 0) > 0 else "pnl-negative"
                
                try:
                    exit_time = trade['exit_time'].strftime('%m/%d %H:%M')
                except:
                    exit_time = "N/A"
                
                st.markdown(f"""
                <div class="trade-row">
                    <div style="font-weight: bold;">{trade.get('symbol', 'N/A')}</div>
                    <div>{exit_time}</div>
                    <div>${trade.get('entry_price', 0):.2f}</div>
                    <div>${trade.get('exit_price', 0):.2f}</div>
                    <div class="{pnl_class}" style="font-weight: bold;">
                        {trade.get('pnl_percent', 0):+.2f}%
                    </div>
                    <div class="{pnl_class}">
                        ${trade.get('pnl_dollar', 0):+.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No completed trades yet")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding-top: 2rem; 
         border-top: 1px solid #262730; color: #8b8b9a; font-size: 0.85rem;">
        Auto-refresh: 5 seconds • 
        Data Source: GitHub • 
        Last Update: """ + datetime.now().strftime('%H:%M:%S') + """
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(5)
    st.session_state.counter += 1
    st.rerun()

if __name__ == "__main__":
    main()
