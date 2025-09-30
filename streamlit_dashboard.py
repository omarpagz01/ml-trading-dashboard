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

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0 2rem 0;
        font-size: 2rem;
        font-weight: bold;
        color: #ffffff;
    }
    
    .connection-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        margin-left: 1rem;
        font-weight: 600;
    }
    
    .connected {
        background-color: #00d632;
        color: #000000;
    }
    
    .disconnected {
        background-color: #ff3838;
        color: #ffffff;
    }
    
    .metric-card {
        background: #1e1e2e;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        color: #8b8b9a;
        font-size: 0.75rem;
        margin-bottom: 0.25rem;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 1.5rem;
        font-weight: bold;
    }
    
    .positive {
        color: #00d632;
    }
    
    .negative {
        color: #ff3838;
    }
    
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #2e2e3e;
    }
    
    .signal-card {
        background: #1e1e2e;
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
    }
    
    .watchlist-card {
        background: #1e1e2e;
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin: 0.5rem;
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
        params = {
            't': timestamp,
            'r': random_val
        }
        headers = {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error loading {path}: {str(e)}")
    return None

def load_status():
    """Load system status"""
    return load_from_github("status.json") or {}

def load_realtime_prices():
    """Load real-time prices"""
    return load_from_github("realtime_prices.json") or {}

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
        return "WEEKEND"
    elif current_time < datetime.strptime("09:30", "%H:%M").time():
        return "PRE-MARKET"
    elif current_time >= datetime.strptime("16:00", "%H:%M").time():
        return "AFTER-HOURS"
    elif datetime.strptime("09:30", "%H:%M").time() <= current_time < datetime.strptime("16:00", "%H:%M").time():
        return "MARKET OPEN"
    else:
        return "CLOSED"

def format_criteria(signal):
    """Format entry criteria from signal"""
    criteria_parts = []
    
    if 'features_snapshot' in signal and signal['features_snapshot']:
        features = signal['features_snapshot']
        
        if 'rsi' in features:
            rsi = features['rsi']
            criteria_parts.append(f"RSI:{rsi:.1f}")
        
        if 'macd' in features:
            macd = features['macd']
            criteria_parts.append(f"MACD:{macd:.2f}")
        
        if 'bb_position' in features:
            bb = features['bb_position']
            criteria_parts.append(f"BB:{bb:.2f}")
        
        if 'volume_ratio' in features:
            vol = features['volume_ratio']
            criteria_parts.append(f"Vol:{vol:.1f}x")
    
    if 'ml_scores' in signal and signal['ml_scores']:
        scores = signal['ml_scores']
        if 'rf_long' in scores:
            criteria_parts.append(f"RF:{scores['rf_long']*100:.0f}%")
        if 'gb_long' in scores:
            criteria_parts.append(f"GB:{scores['gb_long']*100:.0f}%")
    
    return " | ".join(criteria_parts) if criteria_parts else "Standard"

def calculate_metrics(trades):
    """Calculate trading metrics"""
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

def check_new_signals(signals):
    """Check for new signals and play sound"""
    if not signals:
        return
    
    current_signals = set()
    
    for sig in signals:
        if sig.get('action') not in ['HOLD', None]:
            sig_id = f"{sig['symbol']}_{sig['action']}_{sig['timestamp']}"
            current_signals.add(sig_id)
    
    new_signals = current_signals - st.session_state.previous_signals
    
    if new_signals and st.session_state.previous_signals:
        # Play notification sound
        st.balloons()
    
    st.session_state.previous_signals = current_signals

# Main application
def main():
    # Clear cache periodically
    if st.session_state.counter % 10 == 0:
        st.cache_data.clear()
    
    # Load all data
    status = load_status()
    signals = load_signals()
    positions = load_positions()
    trades = load_trades()
    prices = load_realtime_prices()
    
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
    connection_status = "LIVE" if is_connected else "OFFLINE"
    connection_class = "connected" if is_connected else "disconnected"
    
    st.markdown(f"""
        <div class="main-header">
            SIGNALS DASHBOARD
            <span class="connection-badge {connection_class}">{connection_status}</span>
        </div>
    """, unsafe_allow_html=True)
    
    if not status:
        st.info("Waiting for trading system data...")
        time.sleep(5)
        st.session_state.counter += 1
        st.rerun()
        return
    
    # Calculate metrics
    market_status = get_market_status()
    metrics = calculate_metrics(trades)
    
    # Top metrics row
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    with col1:
        st.metric("Market", market_status)
    
    with col2:
        active_positions = sum(1 for p in positions.values() if p.get('is_open'))
        st.metric("Positions", f"{active_positions}/{len(ASSETS)}")
    
    with col3:
        # Calculate open PnL
        open_pnl = 0
        if positions and prices.get('prices'):
            for symbol, pos in positions.items():
                if pos.get('is_open'):
                    current = prices['prices'].get(symbol, 0)
                    entry = pos.get('entry_price', 0)
                    if current > 0 and entry > 0:
                        open_pnl += ((current - entry) / entry * 100)
        
        st.metric("Open P&L", f"{open_pnl:+.2f}%", 
                 delta=None if open_pnl == 0 else f"{'↑' if open_pnl > 0 else '↓'}")
    
    with col4:
        st.metric("Total P&L", f"{metrics['total_pnl']:+.2f}%",
                 delta=None if metrics['total_pnl'] == 0 else f"{'↑' if metrics['total_pnl'] > 0 else '↓'}")
    
    with col5:
        st.metric("Win Rate", f"{metrics['win_rate']:.0f}%")
    
    with col6:
        st.metric("Profit Factor", f"{metrics['profit_factor']:.2f}")
    
    with col7:
        st.metric("Signals Today", len(signals) if signals else 0)
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Positions & Signals", "👁 Watchlist", "📈 Performance", "💰 Trades"])
    
    with tab1:
        # Active Positions Section
        st.subheader("🎯 Active Positions")
        
        # Build positions data
        positions_list = []
        latest_signals = {}
        
        # Get latest signal for each symbol
        for sig in signals:
            sym = sig.get('symbol')
            if sym and (sym not in latest_signals or sig['timestamp'] > latest_signals[sym]['timestamp']):
                latest_signals[sym] = sig
        
        for symbol in ASSETS:
            if symbol in positions and positions[symbol].get('is_open'):
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
                
                criteria = "Standard"
                if symbol in latest_signals:
                    criteria = format_criteria(latest_signals[symbol])
                
                positions_list.append({
                    'Symbol': symbol,
                    'Status': 'LONG',
                    'Entry': f"${entry_price:.2f}",
                    'Entry Time': entry_time,
                    'Current': f"${current_price:.2f}",
                    'Criteria': criteria,
                    'P&L (%)': f"{pnl_pct:+.2f}%",
                    'P&L ($)': f"${pnl_usd:+.2f}"
                })
        
        if positions_list:
            df = pd.DataFrame(positions_list)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No active positions")
        
        # Recent Signals Section
        st.subheader("📡 Recent Signals")
        
        if signals:
            recent = sorted(signals, key=lambda x: x['timestamp'], reverse=True)[:10]
            
            for sig in recent:
                sig_time = convert_to_et(sig['timestamp'])
                
                col1, col2, col3 = st.columns([2, 3, 2])
                
                with col1:
                    action_color = "🟢" if sig['action'] == 'LONG' else "🔴" if sig['action'] == 'EXIT' else "⚪"
                    st.write(f"{action_color} **{sig['symbol']}** - {sig['action']}")
                
                with col2:
                    st.write(f"${sig['price']:.2f} @ {sig_time.strftime('%H:%M:%S')}")
                
                with col3:
                    criteria = format_criteria(sig)
                    st.write(f"{criteria[:30]}..." if len(criteria) > 30 else criteria)
        else:
            st.info("No signals today")
    
    with tab2:
        st.subheader("👁 Watchlist - Monitoring Only")
        
        cols = st.columns(len(WATCHLIST))
        
        for idx, symbol in enumerate(WATCHLIST):
            with cols[idx]:
                price = prices.get('prices', {}).get(symbol, 0)
                
                st.markdown(f"**{symbol}**")
                st.write(f"${price:.2f}" if price > 0 else "N/A")
                st.caption("Monitoring")
                
                # Mock reasons for demo
                reasons = ["RSI: Neutral", "Volume: Low", "No trend"]
                st.caption(" | ".join(reasons[:2]))
    
    with tab3:
        st.subheader("📈 Performance Analysis")
        
        if trades:
            df_trades = pd.DataFrame(trades)
            
            # P&L Distribution
            col1, col2 = st.columns(2)
            
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=df_trades['pnl_percent'],
                    nbinsx=20,
                    marker_color='green'
                ))
                fig.update_layout(
                    title="P&L Distribution",
                    xaxis_title="P&L (%)",
                    yaxis_title="Count",
                    height=400
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
                        line=dict(color='green', width=2)
                    ))
                    fig.update_layout(
                        title="Cumulative P&L",
                        xaxis_title="Date",
                        yaxis_title="Cumulative P&L (%)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trades to display")
    
    with tab4:
        st.subheader("💰 Trade History")
        
        if trades:
            df_trades = pd.DataFrame(trades)
            df_trades = df_trades.sort_values('exit_time', ascending=False).head(20)
            
            # Format columns
            display_df = df_trades[['symbol', 'exit_time', 'entry_price', 'exit_price', 'pnl_percent', 'pnl_dollar']].copy()
            display_df.columns = ['Symbol', 'Exit Time', 'Entry', 'Exit', 'P&L (%)', 'P&L ($)']
            
            # Format values
            display_df['Exit Time'] = pd.to_datetime(display_df['Exit Time']).dt.strftime('%m/%d %H:%M')
            display_df['Entry'] = display_df['Entry'].apply(lambda x: f"${x:.2f}")
            display_df['Exit'] = display_df['Exit'].apply(lambda x: f"${x:.2f}")
            display_df['P&L (%)'] = display_df['P&L (%)'].apply(lambda x: f"{x:+.2f}%")
            display_df['P&L ($)'] = display_df['P&L ($)'].apply(lambda x: f"${x:+.2f}")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No completed trades")
    
    # Footer
    st.markdown("---")
    st.caption(f"Auto-refresh: 5 seconds | Last update: {datetime.now().strftime('%H:%M:%S')} | Data: GitHub")
    
    # Auto refresh
    time.sleep(5)
    st.session_state.counter += 1
    st.rerun()

if __name__ == "__main__":
    main()
