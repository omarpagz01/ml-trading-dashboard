"""
Elite Signals Dashboard - Professional Trading Interface
Using Native Streamlit Components for Better Rendering
"""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time
from collections import defaultdict

# Page configuration
st.set_page_config(
    page_title="Signals Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional dark theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        background: #000000;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    
    .main-title {
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin: 0 0 2rem 0;
        letter-spacing: -0.5px;
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
        background: #34C759;
        box-shadow: 0 0 8px #34C759;
    }
    
    .status-dot.disconnected {
        background: #FF453A;
        box-shadow: 0 0 8px #FF453A;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        height: 100px;
    }
    
    .performance-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 16px;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 600;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: rgba(255, 255, 255, 0.5);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        color: rgba(255,255,255,0.6);
        font-size: 13px;
        font-weight: 500;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #34C759;
        color: #000;
    }
    
    div[data-testid="column"] {
        background: transparent;
    }
    
    .stSelectbox label {
        color: rgba(255, 255, 255, 0.6);
        font-size: 12px;
    }
    
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
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
    }

def process_signals_for_display(signals, status):
    """Process signals and track trades"""
    if not signals:
        return [], {}, 0, 0, None
    
    sorted_signals = sorted(signals, key=lambda x: x['timestamp'])
    last_signal_time = datetime.fromisoformat(sorted_signals[-1]['timestamp']) if sorted_signals else None
    
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
        return "WEEKEND", "#FF453A"
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
        st.metric("MARKET STATUS", market_status)
    
    with col2:
        display_time = last_signal_time.strftime('%H:%M:%S') if last_signal_time else "--:--:--"
        st.metric("LAST SIGNAL", display_time)
    
    with col3:
        st.metric("SIGNALS TODAY", len(all_signals), f"↑ {unique_longs} longs")
    
    with col4:
        active_positions = sum(1 for p in status.get('positions', {}).values() if p.get('is_open'))
        st.metric("ACTIVE POSITIONS", f"{active_positions}/{len(ASSETS)}")
    
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
        st.metric("OPEN P&L", f"{total_pnl:+.2f}%")
    
    with col6:
        st.metric("CLOSED TODAY", f"{unique_exits} trades")
    
    # Performance Overview
    st.markdown("---")
    st.subheader("📈 Portfolio Performance")
    
    perf_col1, perf_col2, perf_col3, perf_col4, perf_col5 = st.columns([1, 1, 1, 1, 1])
    with perf_col1:
        perf_filter = st.selectbox("Filter", ["ALL"] + ASSETS, key="perf_filter")
    
    metrics = calculate_performance_metrics(trades_history, perf_filter)
    
    with perf_col2:
        st.metric("Total P&L", f"{metrics['total_pnl']:+.2f}%")
    with perf_col3:
        st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
    with perf_col4:
        st.metric("Profit Factor", f"{metrics['profit_factor']:.2f}")
    with perf_col5:
        st.metric("Total Trades", metrics['total_trades'])
    
    st.markdown("---")
    
    # Main content with tabs
    tab1, tab2, tab3 = st.tabs(["📡 Live Signals", "📜 Historical Signals", "💰 Trade History"])
    
    with tab1:
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.subheader("🎯 Latest Signal Per Asset")
            
            for symbol in ASSETS:
                with st.container():
                    if symbol in latest_signals:
                        sig = latest_signals[symbol]
                        sig_time = datetime.fromisoformat(sig['timestamp'])
                        time_str = sig_time.strftime('%H:%M:%S')
                        
                        # Create columns for signal display
                        sig_col1, sig_col2, sig_col3 = st.columns([2, 2, 1])
                        
                        with sig_col1:
                            if sig['action'] == 'LONG':
                                st.success(f"🟢 **{symbol} - LONG**")
                            elif sig['action'] == 'EXIT':
                                st.error(f"🔴 **{symbol} - EXIT**")
                            else:
                                st.info(f"⚪ **{symbol} - HOLD**")
                        
                        with sig_col2:
                            st.write(f"${sig['price']:.2f} • {time_str}")
                            
                            # Check for consecutive signals
                            if sig.get('consecutive_count', 1) > 1 and 'first_signal_time' in sig:
                                first_time = datetime.fromisoformat(sig['first_signal_time']).strftime('%H:%M')
                                st.caption(f"📍 Opened at {first_time} • {sig['consecutive_count']} signals")
                        
                        with sig_col3:
                            conf_color = "#34C759" if sig['action'] == 'LONG' else "#FF453A" if sig['action'] == 'EXIT' else "#999"
                            st.markdown(f"<div style='text-align: right; color: {conf_color}; font-size: 20px; font-weight: bold;'>{sig['confidence']*100:.1f}%</div>", unsafe_allow_html=True)
                            st.caption("CONFIDENCE")
                    else:
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
                            
                            with st.container():
                                st.write(f"**{symbol} - LONG**")
                                
                                if entry > 0 and current > 0:
                                    pnl = ((current - entry) / entry * 100)
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.caption("Entry")
                                        st.write(f"${entry:.2f}")
                                    with col2:
                                        st.caption("Current")
                                        st.write(f"${current:.2f}")
                                    
                                    col3, col4 = st.columns(2)
                                    with col3:
                                        st.caption("P&L")
                                        if pnl > 0:
                                            st.success(f"+{pnl:.2f}%")
                                        else:
                                            st.error(f"{pnl:.2f}%")
                                    with col4:
                                        st.caption("Confidence")
                                        st.write(f"{pos.get('last_confidence', 0)*100:.1f}%")
                                
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
            df_data = []
            for sig in filtered_signals[:100]:
                sig_time = datetime.fromisoformat(sig['timestamp'])
                df_data.append({
                    'Time': sig_time.strftime('%m/%d %H:%M:%S'),
                    'Symbol': sig['symbol'],
                    'Action': sig['action'],
                    'Price': f"${sig['price']:.2f}",
                    'Confidence': f"{sig['confidence']*100:.1f}%"
                })
            
            df = pd.DataFrame(df_data)
            
            # Style the dataframe
            def color_action(val):
                if 'LONG' in val:
                    return 'color: #34C759'
                elif 'EXIT' in val:
                    return 'color: #FF453A'
                return 'color: #999'
            
            styled_df = df.style.applymap(color_action, subset=['Action'])
            st.dataframe(styled_df, use_container_width=True, height=500)
        else:
            st.info("No historical signals")
    
    with tab3:
        st.subheader("💰 Completed Trades")
        
        if trades_history:
            recent_trades = sorted(trades_history, key=lambda x: x['exit_time'], reverse=True)[:50]
            
            # Create DataFrame
            df_data = []
            for trade in recent_trades:
                exit_time = datetime.fromisoformat(trade['exit_time'])
                df_data.append({
                    'Exit Time': exit_time.strftime('%m/%d %H:%M'),
                    'Symbol': trade['symbol'],
                    'Entry': f"${trade['entry_price']:.2f}",
                    'Exit': f"${trade['exit_price']:.2f}",
                    'P&L %': f"{trade['pnl_percent']:+.2f}%",
                    'P&L $': f"${trade['pnl_dollar']:+.2f}"
                })
            
            df = pd.DataFrame(df_data)
            
            # Style the dataframe
            def color_pnl(val):
                if '+' in str(val):
                    return 'color: #34C759'
                elif '-' in str(val):
                    return 'color: #FF453A'
                return ''
            
            styled_df = df.style.applymap(color_pnl, subset=['P&L %', 'P&L $'])
            st.dataframe(styled_df, use_container_width=True, height=500)
        else:
            st.info("No completed trades yet")
    
    # Footer
    st.markdown("---")
    footer_col1, footer_col2, footer_col3 = st.columns(3)
    with footer_col1:
        st.caption(f"Last Signal: {last_signal_time.strftime('%H:%M:%S') if last_signal_time else 'N/A'}")
    with footer_col2:
        st.caption("Auto-refresh: 5 seconds")
    with footer_col3:
        if is_connected:
            st.caption("🟢 Connected")
        else:
            st.caption("🔴 Disconnected")
    
    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
