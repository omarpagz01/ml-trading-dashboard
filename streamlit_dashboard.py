"""
Signals Dashboard - iOS-Inspired Design
Clean, minimalist, and beautiful interface
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
from collections import defaultdict

# Page configuration - MUST BE FIRST
st.set_page_config(
    page_title="Signals Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# iOS-Inspired CSS with SF Pro Display font
st.markdown("""
<style>
    /* Import SF Pro Display-like font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Main App Background - iOS dark mode style */
    .stApp {
        background: #000000;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .css-1y4p8pa {padding-top: 0rem;}
    
    /* Main Title - iOS style */
    .main-title {
        font-size: 34px;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 32px;
        letter-spacing: -0.5px;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    }
    
    /* Metric Cards - iOS style with subtle glass effect */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 20px 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        background: linear-gradient(135deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.06) 100%);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    .metric-label {
        color: rgba(255, 255, 255, 0.6);
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 32px;
        font-weight: 600;
        line-height: 1;
        margin-bottom: 8px;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        letter-spacing: -1px;
    }
    
    .metric-delta {
        font-size: 13px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.7);
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    }
    
    .metric-delta-positive {
        color: #34C759;
    }
    
    .metric-delta-negative {
        color: #FF453A;
    }
    
    /* Status Badge - iOS pill style */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 8px 16px;
        border-radius: 100px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: -0.2px;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    }
    
    .status-open {
        background: linear-gradient(135deg, #34C759 0%, #30D158 100%);
        color: #000000;
    }
    
    .status-closed {
        background: linear-gradient(135deg, #FF453A 0%, #FF6961 100%);
        color: #ffffff;
    }
    
    .status-after-hours {
        background: linear-gradient(135deg, #FF9500 0%, #FFAB40 100%);
        color: #000000;
    }
    
    /* Section Headers - Clean iOS style */
    .section-header {
        color: #ffffff;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        letter-spacing: -0.5px;
    }
    
    /* Signal Cards - iOS notification style */
    .signal-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.04) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 16px 20px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .signal-card:hover {
        transform: translateX(4px);
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
    }
    
    .signal-long {
        border-left: 3px solid #34C759;
        background: linear-gradient(135deg, rgba(52, 199, 89, 0.1) 0%, rgba(52, 199, 89, 0.02) 100%);
    }
    
    .signal-exit {
        border-left: 3px solid #FF453A;
        background: linear-gradient(135deg, rgba(255, 69, 58, 0.1) 0%, rgba(255, 69, 58, 0.02) 100%);
    }
    
    .signal-hold {
        border-left: 3px solid rgba(255, 255, 255, 0.3);
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
    }
    
    /* Tables - iOS style */
    .dataframe {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif !important;
    }
    
    .stDataFrame {
        background: rgba(255,255,255,0.05);
        border-radius: 20px;
        padding: 4px;
    }
    
    /* Charts Container */
    .chart-container {
        background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
        border-radius: 24px;
        padding: 20px;
        margin-top: 20px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Custom Scrollbar - iOS style */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }
    
    /* Loading dot - iOS style */
    @keyframes pulse {
        0%, 80%, 100% { 
            opacity: 0.3;
            transform: scale(0.8);
        }
        40% { 
            opacity: 1;
            transform: scale(1);
        }
    }
    
    .loading-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        background: #34C759;
        border-radius: 50%;
        animation: pulse 1.4s infinite ease-in-out;
        margin-left: 4px;
    }
    
    /* Smooth animations */
    * {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* Hide Streamlit expander arrows */
    .css-1x8cf1d {
        visibility: hidden;
    }
    
    /* Metric value styling override */
    [data-testid="metric-container"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    [data-testid="metric-container"] > div {
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# Define your assets
ASSETS = ['TSLA', 'HOOD', 'COIN', 'PLTR', 'AAPL']

# Helper functions
def process_signals_with_proper_counting(signals):
    """Process signals with proper counting logic"""
    if not signals:
        return [], 0, 0, 0
    
    # Sort signals by timestamp
    sorted_signals = sorted(signals, key=lambda x: x['timestamp'])
    
    # Track positions and unique trades
    position_states = {}  # symbol -> current_position
    processed_signals = []
    unique_long_trades = set()
    unique_exit_trades = set()
    last_signal_per_symbol = {}
    
    for sig in sorted_signals:
        symbol = sig['symbol']
        action = sig['action']
        timestamp = sig['timestamp']
        
        # Initialize position state
        if symbol not in position_states:
            position_states[symbol] = 'FLAT'
        
        current_position = position_states[symbol]
        
        # Check if this is a new signal or duplicate
        is_duplicate = False
        if symbol in last_signal_per_symbol:
            last_action = last_signal_per_symbol[symbol]['action']
            if action == 'HOLD' and last_action == 'HOLD':
                is_duplicate = True
            elif action == 'LONG' and current_position == 'LONG':
                is_duplicate = True
        
        # Process signal
        if action == 'LONG' and current_position != 'LONG':
            position_states[symbol] = 'LONG'
            unique_long_trades.add(symbol)
            sig['is_new_trade'] = True
            sig['is_duplicate'] = False
        elif action == 'EXIT' and current_position == 'LONG':
            position_states[symbol] = 'FLAT'
            unique_exit_trades.add(symbol)
            sig['is_new_trade'] = True
            sig['is_duplicate'] = False
        else:
            sig['is_new_trade'] = False
            sig['is_duplicate'] = is_duplicate
        
        last_signal_per_symbol[symbol] = sig
        processed_signals.append(sig)
    
    # Count unique trades
    unique_longs = len(unique_long_trades)
    unique_exits = len(unique_exit_trades)
    
    # Filter out duplicate HOLD signals for display
    display_signals = [s for s in processed_signals if not s.get('is_duplicate', False)]
    
    return display_signals, unique_longs, unique_exits, len(processed_signals)

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
        except Exception as e:
            st.error(f"Error loading signals: {e}")
    return []

@st.cache_data(ttl=2)
def load_status():
    """Load current status"""
    status_file = Path("status.json")
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading status: {e}")
    return {}

@st.cache_data(ttl=5)
def load_historical_data(symbol):
    """Load historical price data for a symbol"""
    today = datetime.now().strftime('%Y%m%d')
    data_file = Path("realtime_data") / f"{symbol}_realtime_{today}.parquet"
    if data_file.exists():
        try:
            df = pd.read_parquet(data_file)
            return df
        except:
            pass
    return None

def get_market_status():
    """Check if market is open with styled output"""
    now = datetime.now(timezone(timedelta(hours=-4)))  # ET
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday >= 5:  # Weekend
        return "WEEKEND", "status-closed", "🔴"
    elif current_time < pd.Timestamp("09:30").time():
        return "PRE-MARKET", "status-closed", "🟡"
    elif current_time >= pd.Timestamp("16:00").time():
        return "AFTER-HOURS", "status-after-hours", "🟠"
    elif pd.Timestamp("09:30").time() <= current_time < pd.Timestamp("16:00").time():
        return "MARKET OPEN", "status-open", "🟢"
    else:
        return "CLOSED", "status-closed", "🔴"

def format_currency(value):
    """Format currency values"""
    if value == 0 or value is None:
        return "-"
    return f"${value:,.2f}"

def format_percentage(value):
    """Format percentage values"""
    if value == 0 or value is None:
        return "-"
    color = "#34C759" if value > 0 else "#FF453A"
    return f'<span style="color: {color}; font-weight: 600;">{value:+.2f}%</span>'

# Main Dashboard
def main():
    # Clean title without icon
    st.markdown('<h1 class="main-title">SIGNALS DASHBOARD</h1>', unsafe_allow_html=True)
    
    # Load data
    raw_signals = load_signals()
    status = load_status()
    
    # Process signals with proper counting
    signals, unique_longs, unique_exits, total_signals = process_signals_with_proper_counting(raw_signals)
    
    if not status:
        st.markdown("""
        <div style="text-align: center; padding: 60px;">
            <div style="font-size: 48px; margin-bottom: 20px;">⏳</div>
            <div style="color: rgba(255,255,255,0.8); font-size: 18px; font-weight: 500;">
                Waiting for trading system data...
            </div>
            <div class="loading-dot" style="margin-top: 20px;"></div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(5)
        st.rerun()
        return
    
    # Get market status
    market_status, status_class, status_icon = get_market_status()
    
    # Top Metrics Row - iOS style cards
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Market Status</div>
            <div class="status-badge {status_class}">{market_status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        last_update = datetime.fromisoformat(status['timestamp']) if 'timestamp' in status else datetime.now()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Last Update</div>
            <div class="metric-value">{last_update.strftime('%H:%M:%S')}</div>
            <div class="loading-dot"></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Signals Today</div>
            <div class="metric-value">{total_signals}</div>
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
        # Calculate total P&L
        total_pnl = 0
        if status and 'positions' in status:
            for symbol, pos in status['positions'].items():
                if pos['is_open'] and symbol in status.get('latest_prices', {}):
                    current = status['latest_prices'][symbol]
                    entry = pos['entry_price']
                    if entry > 0:
                        pnl = ((current - entry) / entry * 100)
                        total_pnl += pnl
        
        pnl_html = format_percentage(total_pnl) if total_pnl != 0 else '<span style="color: rgba(255,255,255,0.5);">-</span>'
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Open P&L</div>
            <div class="metric-value" style="font-size: 28px;">{pnl_html}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Trades Today</div>
            <div class="metric-value">{unique_exits}</div>
            <div class="metric-delta">exits</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main Content Area
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        # Positions Section
        st.markdown('<div class="section-header">📊 Current Positions</div>', unsafe_allow_html=True)
        
        if status and 'positions' in status:
            positions_data = []
            
            for symbol in ASSETS:
                if symbol in status['positions']:
                    pos = status['positions'][symbol]
                    
                    # Determine position status icon
                    if pos['is_open']:
                        status_icon = '🟢'
                        position_text = 'LONG'
                    else:
                        status_icon = '⚪'
                        position_text = 'FLAT'
                    
                    row_data = {
                        'Symbol': symbol,
                        'Status': status_icon,
                        'Position': position_text,
                        'Entry': format_currency(pos['entry_price']) if pos['entry_price'] > 0 else '-',
                    }
                    
                    if pos['is_open'] and symbol in status.get('latest_prices', {}):
                        current = status['latest_prices'][symbol]
                        entry = pos['entry_price']
                        if entry > 0:
                            pnl_pct = ((current - entry) / entry * 100)
                            pnl_dollar = (current - entry) * 100
                            
                            row_data['Current'] = format_currency(current)
                            row_data['P&L %'] = f"{pnl_pct:+.2f}%"
                            row_data['P&L $'] = format_currency(pnl_dollar)
                        else:
                            row_data['Current'] = format_currency(current)
                            row_data['P&L %'] = '-'
                            row_data['P&L $'] = '-'
                    else:
                        row_data['Current'] = '-'
                        row_data['P&L %'] = '-'
                        row_data['P&L $'] = '-'
                    
                    row_data['Confidence'] = f"{pos.get('last_confidence', 0):.1%}" if pos.get('last_confidence', 0) > 0 else '-'
                    
                    positions_data.append(row_data)
            
            if positions_data:
                df_positions = pd.DataFrame(positions_data)
                
                # Style the dataframe
                def style_pnl(val):
                    if isinstance(val, str):
                        if '+' in val and '%' in val:
                            return 'color: #34C759; font-weight: 600;'
                        elif '-' in val and '%' in val and val != '-':
                            return 'color: #FF453A; font-weight: 600;'
                    return 'color: rgba(255,255,255,0.9);'
                
                styled_df = df_positions.style.applymap(style_pnl, subset=['P&L %', 'P&L $'])
                styled_df = styled_df.set_properties(**{
                    'background-color': 'transparent',
                    'color': 'rgba(255,255,255,0.9)',
                    'font-family': '-apple-system, BlinkMacSystemFont, Inter, sans-serif',
                    'font-size': '14px'
                })
                
                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    hide_index=True,
                    height=250
                )
        
        # Price Charts
        st.markdown('<div class="section-header">💹 Price Action</div>', unsafe_allow_html=True)
        
        if status and 'latest_prices' in status:
            tabs = st.tabs(ASSETS)
            
            for tab, symbol in zip(tabs, ASSETS):
                with tab:
                    hist_data = load_historical_data(symbol)
                    
                    if hist_data is not None and not hist_data.empty:
                        # Create iOS-style chart
                        fig = go.Figure()
                        
                        # Candlestick with iOS colors
                        fig.add_trace(go.Candlestick(
                            x=pd.to_datetime(hist_data['timestamp']),
                            open=hist_data['open'],
                            high=hist_data['high'],
                            low=hist_data['low'],
                            close=hist_data['close'],
                            name=symbol,
                            increasing=dict(line=dict(color='#34C759', width=1), fillcolor='#34C759'),
                            decreasing=dict(line=dict(color='#FF453A', width=1), fillcolor='#FF453A')
                        ))
                        
                        # Volume bars with transparency
                        fig.add_trace(go.Bar(
                            x=pd.to_datetime(hist_data['timestamp']),
                            y=hist_data['volume'],
                            name='Volume',
                            yaxis='y2',
                            marker=dict(color='rgba(52, 199, 89, 0.2)')
                        ))
                        
                        # Add trade signals
                        symbol_signals = [s for s in signals if s['symbol'] == symbol and s.get('is_new_trade')]
                        if symbol_signals:
                            long_signals = [s for s in symbol_signals if s['action'] == 'LONG']
                            exit_signals = [s for s in symbol_signals if s['action'] == 'EXIT']
                            
                            if long_signals:
                                fig.add_trace(go.Scatter(
                                    x=[datetime.fromisoformat(s['timestamp']) for s in long_signals],
                                    y=[s['price'] for s in long_signals],
                                    mode='markers',
                                    name='BUY',
                                    marker=dict(
                                        symbol='circle',
                                        size=12,
                                        color='#34C759',
                                        line=dict(width=2, color='rgba(52, 199, 89, 0.3)')
                                    )
                                ))
                            
                            if exit_signals:
                                fig.add_trace(go.Scatter(
                                    x=[datetime.fromisoformat(s['timestamp']) for s in exit_signals],
                                    y=[s['price'] for s in exit_signals],
                                    mode='markers',
                                    name='SELL',
                                    marker=dict(
                                        symbol='circle',
                                        size=12,
                                        color='#FF453A',
                                        line=dict(width=2, color='rgba(255, 69, 58, 0.3)')
                                    )
                                ))
                        
                        # iOS-style layout
                        fig.update_layout(
                            template='plotly_dark',
                            height=400,
                            showlegend=False,
                            xaxis=dict(
                                rangeslider=dict(visible=False),
                                gridcolor='rgba(255,255,255,0.05)',
                                showgrid=True,
                                zeroline=False
                            ),
                            yaxis=dict(
                                title='',
                                side='right',
                                gridcolor='rgba(255,255,255,0.05)',
                                showgrid=True,
                                zeroline=False
                            ),
                            yaxis2=dict(
                                title='',
                                overlaying='y',
                                side='left',
                                showgrid=False,
                                zeroline=False
                            ),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(255,255,255,0.02)',
                            font=dict(
                                color='rgba(255,255,255,0.8)',
                                family='-apple-system, BlinkMacSystemFont, Inter, sans-serif',
                                size=12
                            ),
                            margin=dict(l=0, r=0, t=0, b=0),
                            hoverlabel=dict(
                                bgcolor='rgba(0,0,0,0.8)',
                                font=dict(size=13, family='-apple-system, BlinkMacSystemFont, Inter')
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        if symbol in status.get('latest_prices', {}):
                            current = status['latest_prices'][symbol]
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">{symbol} Price</div>
                                <div class="metric-value">{format_currency(current)}</div>
                            </div>
                            """, unsafe_allow_html=True)
    
    with col_right:
        # Live Signal Feed
        st.markdown('<div class="section-header">📈 Live Signal Feed</div>', unsafe_allow_html=True)
        
        signal_container = st.container(height=600)
        
        with signal_container:
            if signals:
                # Show recent signals (including HOLD but no duplicates)
                display_signals = sorted(
                    [s for s in signals if not s.get('is_duplicate', False)],
                    key=lambda x: x['timestamp'],
                    reverse=True
                )[:20]
                
                for sig in display_signals:
                    sig_time = datetime.fromisoformat(sig['timestamp'])
                    time_str = sig_time.strftime('%H:%M:%S')
                    
                    if sig['action'] == 'LONG':
                        st.markdown(f"""
                        <div class="signal-card signal-long">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="color: #34C759; font-weight: 600; font-size: 15px;">
                                        🟢 LONG - {sig['symbol']}
                                    </div>
                                    <div style="color: rgba(255,255,255,0.5); font-size: 13px; margin-top: 4px;">
                                        {time_str} • ${sig['price']:.2f}
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="color: rgba(255,255,255,0.5); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">
                                        Confidence
                                    </div>
                                    <div style="color: #34C759; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">
                                        {sig['confidence']*100:.1f}%
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif sig['action'] == 'EXIT':
                        st.markdown(f"""
                        <div class="signal-card signal-exit">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="color: #FF453A; font-weight: 600; font-size: 15px;">
                                        🔴 EXIT - {sig['symbol']}
                                    </div>
                                    <div style="color: rgba(255,255,255,0.5); font-size: 13px; margin-top: 4px;">
                                        {time_str} • ${sig['price']:.2f}
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="color: rgba(255,255,255,0.5); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">
                                        Confidence
                                    </div>
                                    <div style="color: #FF453A; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">
                                        {sig['confidence']*100:.1f}%
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:  # HOLD
                        st.markdown(f"""
                        <div class="signal-card signal-hold">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="color: rgba(255,255,255,0.6); font-weight: 500; font-size: 15px;">
                                        ⚪ HOLD - {sig['symbol']}
                                    </div>
                                    <div style="color: rgba(255,255,255,0.4); font-size: 13px; margin-top: 4px;">
                                        {time_str} • ${sig['price']:.2f}
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="color: rgba(255,255,255,0.4); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">
                                        Confidence
                                    </div>
                                    <div style="color: rgba(255,255,255,0.5); font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">
                                        {sig['confidence']*100:.1f}%
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align: center; padding: 40px;">
                    <div style="color: rgba(255,255,255,0.4); font-size: 16px;">
                        Waiting for trading signals...
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Performance Section - Clean iOS style
    st.markdown('<div class="section-header">📊 Performance Analytics</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Unique trades pie
        if unique_longs > 0 or unique_exits > 0:
            fig = go.Figure(data=[go.Pie(
                labels=['Long', 'Exit'],
                values=[unique_longs, unique_exits],
                hole=0.7,
                marker=dict(colors=['#34C759', '#FF453A']),
                textinfo='value',
                textfont=dict(size=14, color='white', family='-apple-system, BlinkMacSystemFont, Inter')
            )])
            
            fig.update_layout(
                showlegend=False,
                height=180,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=30, b=0),
                title=dict(
                    text='Unique Trades',
                    font=dict(size=14, color='rgba(255,255,255,0.8)', family='-apple-system, BlinkMacSystemFont, Inter'),
                    y=0.95
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Activity heatmap
        if signals:
            hours = [datetime.fromisoformat(s['timestamp']).hour for s in signals if s.get('is_new_trade')]
            if hours:
                hour_counts = pd.Series(hours).value_counts().sort_index()
                
                fig = go.Figure(data=[go.Bar(
                    x=hour_counts.index,
                    y=hour_counts.values,
                    marker=dict(
                        color=hour_counts.values,
                        colorscale=[[0, 'rgba(52, 199, 89, 0.2)'], [1, '#34C759']],
                        showscale=False
                    )
                )])
                
                fig.update_layout(
                    title=dict(
                        text='Hourly Activity',
                        font=dict(size=14, color='rgba(255,255,255,0.8)', family='-apple-system, BlinkMacSystemFont, Inter'),
                        y=0.95
                    ),
                    xaxis=dict(
                        gridcolor='rgba(255,255,255,0.05)',
                        color='rgba(255,255,255,0.5)'
                    ),
                    yaxis=dict(
                        gridcolor='rgba(255,255,255,0.05)',
                        color='rgba(255,255,255,0.5)'
                    ),
                    height=180,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(255,255,255,0.02)',
                    font=dict(color='rgba(255,255,255,0.5)', size=11),
                    margin=dict(l=0, r=0, t=30, b=30),
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        # Win Rate gauge
        if unique_exits > 0:
            # Simplified win rate (would need actual P&L calculation)
            win_rate = 65  # Placeholder
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=win_rate,
                title={'text': "Win Rate", 'font': {'size': 14, 'color': 'rgba(255,255,255,0.8)'}},
                number={'suffix': "%", 'font': {'size': 24, 'color': '#34C759'}},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, 100], 'tickcolor': 'rgba(255,255,255,0.3)'},
                    'bar': {'color': "#34C759"},
                    'steps': [
                        {'range': [0, 100], 'color': "rgba(255,255,255,0.05)"}
                    ],
                    'threshold': {
                        'line': {'color': "rgba(255,255,255,0.3)", 'width': 2},
                        'thickness': 0.75,
                        'value': 50
                    }
                }
            ))
            
            fig.update_layout(
                height=180,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='-apple-system, BlinkMacSystemFont, Inter'),
                margin=dict(l=20, r=20, t=30, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col4:
        # Average confidence
        if signals:
            recent_signals = signals[-10:] if len(signals) > 10 else signals
            avg_confidence = np.mean([s['confidence'] for s in recent_signals]) * 100
            
            fig = go.Figure(go.Indicator(
                mode="number",
                value=avg_confidence,
                title={'text': "Avg Confidence", 'font': {'size': 14, 'color': 'rgba(255,255,255,0.8)'}},
                number={'suffix': "%", 'font': {'size': 32, 'color': '#34C759' if avg_confidence > 50 else '#FF453A'}},
                domain={'x': [0, 1], 'y': [0, 1]}
            ))
            
            fig.update_layout(
                height=180,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='-apple-system, BlinkMacSystemFont, Inter'),
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Footer - Minimal iOS style
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: rgba(255,255,255,0.3); font-size: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;">
        Last Update: {datetime.now().strftime('%H:%M:%S')} • Auto-refresh: 5 seconds • Polygon + Alpaca APIs
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
