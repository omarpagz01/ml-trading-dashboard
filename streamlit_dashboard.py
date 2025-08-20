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
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 16px;
        border: 1px solid var(--border-color);
    }
    
    [data-testid="metric-container"] label {
        font-size: 10px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        color: rgba(255,255,255,0.4) !important;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 28px !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(255,255,255,0.1) !important;
    }
    
    /* Dataframes */
    [data-testid="stDataFrame"] {
        background: rgba(255,255,255,0.02);
        border-radius: 12px;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.1);
        border-radius: 3px;
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
        return "WEEKEND", "#888"
    elif current_time < pd.Timestamp("09:30").time():
        return "PRE-MARKET", "#FF9500"
    elif current_time >= pd.Timestamp("16:00").time():
        return "AFTER-HOURS", "#FF9500"
    elif pd.Timestamp("09:30").time() <= current_time < pd.Timestamp("16:00").time():
        return "MARKET OPEN", "#34C759"
    else:
        return "CLOSED", "#FF453A"

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
    
    # Title
    st.markdown('<h1 class="main-title">SIGNALS DASHBOARD</h1>', unsafe_allow_html=True)
    
    if not status:
        st.info("⏳ Waiting for trading system data...")
        time.sleep(5)
        st.rerun()
        return
    
    # Process signals
    all_signals, latest_signals, unique_longs, unique_exits, last_signal_time = process_signals_for_display(raw_signals, status)
    
    # Get market status
    market_status, status_color = get_market_status()
    
    # Top Metrics Row
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
    
    # Performance Overview
    st.markdown("---")
    st.subheader("📈 Portfolio Performance")
    
    perf_col1, perf_col2 = st.columns([1, 5])
    with perf_col1:
        perf_filter = st.selectbox("Filter", ["ALL"] + ASSETS, key="perf_filter")
    
    metrics = calculate_performance_metrics(trades_history, perf_filter)
    
    with perf_col2:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total P&L", f"{metrics['total_pnl']:+.2f}%")
        with m2:
            st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
        with m3:
            st.metric("Profit Factor", f"{metrics['profit_factor']:.2f}")
        with m4:
            st.metric("Total Trades", metrics['total_trades'])
    
    # Main content with tabs
    tab1, tab2, tab3 = st.tabs(["📡 Live Signals", "📜 Historical Signals", "💰 Trade History"])
    
    with tab1:
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.subheader("🎯 Latest Signal Per Asset")
            
            for symbol in ASSETS:
                if symbol in latest_signals:
                    sig = latest_signals[symbol]
                    sig_time = datetime.fromisoformat(sig['timestamp'])
                    time_str = sig_time.strftime('%H:%M:%S')
                    
                    # Create signal display using columns
                    with st.container():
                        scol1, scol2, scol3 = st.columns([2, 2, 1])
                        
                        with scol1:
                            if sig['action'] == 'LONG':
                                st.success(f"🟢 {symbol} - LONG")
                            elif sig['action'] == 'EXIT':
                                st.error(f"🔴 {symbol} - EXIT")
                            else:
                                st.info(f"⚪ {symbol} - HOLD")
                        
                        with scol2:
                            st.write(f"**${sig['price']:.2f}**")
                            st.caption(time_str)
                        
                        with scol3:
                            st.write(f"**{sig['confidence']*100:.1f}%**")
                            st.caption("CONF")
                        
                        # Add consecutive indicator if needed
                        if sig.get('consecutive_count', 1) > 1 and 'first_signal_time' in sig:
                            first_time = datetime.fromisoformat(sig['first_signal_time']).strftime('%H:%M')
                            st.caption(f"📍 Opened at {first_time} • Updated at {time_str} • {sig['consecutive_count']} signals")
                else:
                    with st.container():
                        st.write(f"*{symbol} - No signals today*")
                
                st.markdown("---")
        
        with col_right:
            st.subheader("💼 Current Positions")
            
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
                                    st.write(f"**{symbol} - LONG**")
                                    pcol1, pcol2 = st.columns(2)
                                    with pcol1:
                                        st.caption(f"Entry: ${entry:.2f}")
                                        st.caption(f"Current: ${current:.2f}")
                                    with pcol2:
                                        if pnl > 0:
                                            st.success(f"P&L: {pnl:+.2f}%")
                                        else:
                                            st.error(f"P&L: {pnl:+.2f}%")
                                        st.caption(f"Conf: {pos.get('last_confidence', 0)*100:.1f}%")
                                    st.markdown("---")
                
                if not has_positions:
                    st.info("No open positions")
    
    with tab2:
        st.subheader("📜 Historical Signals")
        
        # Filter
        hist_filter = st.selectbox("Filter by Asset", ["ALL"] + ASSETS, key="hist_filter")
        
        # Display historical signals
        if hist_filter == "ALL":
            filtered_signals = [s for s in all_signals if s.get('is_new_position', True)]
        else:
            filtered_signals = [s for s in all_signals if s['symbol'] == hist_filter and s.get('is_new_position', True)]
        
        filtered_signals = sorted(filtered_signals, key=lambda x: x['timestamp'], reverse=True)
        
        if filtered_signals:
            # Create DataFrame for better display
            hist_data = []
            for sig in filtered_signals[:100]:
                sig_time = datetime.fromisoformat(sig['timestamp'])
                hist_data.append({
                    'Time': sig_time.strftime('%m/%d %H:%M:%S'),
                    'Symbol': sig['symbol'],
                    'Action': sig['action'],
                    'Price': f"${sig['price']:.2f}",
                    'Confidence': f"{sig['confidence']*100:.1f}%"
                })
            
            df_hist = pd.DataFrame(hist_data)
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info("No historical signals")
    
    with tab3:
        st.subheader("💰 Completed Trades")
        
        if trades_history:
            recent_trades = sorted(trades_history, key=lambda x: x['exit_time'], reverse=True)[:50]
            
            # Create DataFrame for trades
            trade_data = []
            for trade in recent_trades:
                exit_time = datetime.fromisoformat(trade['exit_time']).strftime('%m/%d %H:%M')
                trade_data.append({
                    'Symbol': trade['symbol'],
                    'Exit Time': exit_time,
                    'Entry': f"${trade['entry_price']:.2f}",
                    'Exit': f"${trade['exit_price']:.2f}",
                    'P&L %': f"{trade['pnl_percent']:+.2f}%",
                    'P&L $': f"${trade['pnl_dollar']:+.2f}"
                })
            
            df_trades = pd.DataFrame(trade_data)
            
            # Style the dataframe
            def style_pnl(val):
                if '+' in str(val):
                    return 'color: #34C759'
                elif '-' in str(val):
                    return 'color: #FF453A'
                return ''
            
            styled_df = df_trades.style.applymap(style_pnl, subset=['P&L %', 'P&L $'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info("No completed trades yet")
    
    # Footer
    st.markdown("---")
    fcol1, fcol2, fcol3 = st.columns([1, 2, 1])
    with fcol2:
        st.caption(f"Last Signal: {last_signal_time.strftime('%H:%M:%S') if last_signal_time else 'N/A'} • Auto-refresh: 5s • {'🟢 Connected' if is_connected else '🔴 Disconnected'}")
    
    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
