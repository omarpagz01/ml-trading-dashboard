"""
ML Trading System - Real-Time Dashboard
Live monitoring with 2-minute price updates via Alpaca
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
import pytz

# Page configuration
st.set_page_config(
    page_title="ML Trading - LIVE",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional dark theme CSS
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
    
    /* Hide Streamlit defaults */
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
    
    /* Live Price Indicator */
    .live-indicator {
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
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--primary-green);
        box-shadow: 0 0 8px var(--primary-green);
    }
    
    .delayed-dot {
        background: var(--primary-orange);
        box-shadow: 0 0 8px var(--primary-orange);
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
    
    /* Position Cards */
    .position-card {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid var(--border-color);
        transition: all 0.15s ease;
    }
    
    .position-card:hover {
        background: var(--bg-hover);
        transform: translateX(2px);
    }
    
    .position-long {
        background: linear-gradient(90deg, rgba(52, 199, 89, 0.1), transparent);
        border-left: 3px solid var(--primary-green);
    }
    
    .position-flat {
        border-left: 3px solid rgba(255, 255, 255, 0.2);
        opacity: 0.6;
    }
    
    /* Price Display */
    .price-display {
        display: flex;
        align-items: baseline;
        gap: 8px;
        font-size: 20px;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .price-source {
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .source-live {
        background: rgba(52, 199, 89, 0.2);
        color: var(--primary-green);
    }
    
    .source-cached {
        background: rgba(255, 149, 0, 0.2);
        color: var(--primary-orange);
    }
    
    /* Signal Cards */
    .signal-card {
        background: var(--bg-secondary);
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
        border: 1px solid var(--border-color);
        transition: all 0.15s ease;
    }
    
    .signal-card:hover {
        background: var(--bg-hover);
        transform: translateX(2px);
    }
    
    .signal-long {
        background: linear-gradient(90deg, rgba(52, 199, 89, 0.1), transparent);
        border-left: 3px solid var(--primary-green);
    }
    
    .signal-exit {
        background: linear-gradient(90deg, rgba(255, 69, 58, 0.1), transparent);
        border-left: 3px solid var(--primary-red);
    }
    
    /* Sparkline Container */
    .sparkline-container {
        height: 60px;
        width: 100%;
        position: relative;
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
    
    /* Disable animations to prevent flicker */
    * {
        animation: none !important;
        transition: none !important;
    }
    
    /* Re-enable specific transitions */
    .metric-card,
    .position-card,
    .signal-card {
        transition: transform 0.15s ease, background 0.15s ease !important;
    }
    
    /* Keep pulse animation for live indicator */
    .live-indicator {
        animation: pulse 2s infinite !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'counter' not in st.session_state:
    st.session_state.counter = 0
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# Define assets
ASSETS = ['TSLA', 'HOOD', 'COIN', 'PLTR', 'AAPL']

# Set timezone
ET = pytz.timezone('US/Eastern')

# Helper Functions
@st.cache_data(ttl=2)
def load_status():
    """Load main status file"""
    status_file = Path("status.json")
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

@st.cache_data(ttl=2)
def load_realtime_prices():
    """Load real-time prices (updated every 2 minutes)"""
    price_file = Path("realtime_prices.json")
    if price_file.exists():
        try:
            with open(price_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

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

def get_market_status():
    """Get current market status"""
    now = datetime.now(ET)
    weekday = now.weekday()
    current_time = now.time()
    
    from datetime import time as dt_time
    
    if weekday >= 5:
        return "WEEKEND", "#ff4444"
    elif current_time < dt_time(9, 30):
        return "PRE-MARKET", "#ffaa00"
    elif current_time >= dt_time(16, 0):
        return "AFTER-HOURS", "#ff8800"
    elif dt_time(9, 30) <= current_time < dt_time(16, 0):
        return "MARKET OPEN", "#00ff00"
    else:
        return "CLOSED", "#ff4444"

def format_pnl(value, is_percent=True):
    """Format P&L with color"""
    if value > 0:
        color = "#00ff00"
        symbol = "+"
    elif value < 0:
        color = "#ff4444"
        symbol = ""
    else:
        return "-"
    
    if is_percent:
        return f'{symbol}{value:.2f}%'
    else:
        return f'{symbol}${abs(value):.2f}'

def create_price_sparkline(price_history):
    """Create mini sparkline chart"""
    if not price_history or len(price_history) < 2:
        return None
    
    prices = [p['price'] for p in price_history]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=prices,
        mode='lines',
        line=dict(
            color='#00ff00' if prices[-1] >= prices[0] else '#ff4444',
            width=2
        ),
        fill='tozeroy',
        fillcolor='rgba(0,255,0,0.1)' if prices[-1] >= prices[0] else 'rgba(255,68,68,0.1)',
        showlegend=False,
        hovertemplate='$%{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        height=60,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        hovermode='x'
    )
    
    return fig

# Main Dashboard
def main():
    # Create container to prevent flicker
    main_container = st.container()
    
    with main_container:
        # Load all data
        status = load_status()
        realtime_prices = load_realtime_prices()
        signals = load_signals()
        
        # Check if system is running
        is_connected = bool(status and 'timestamp' in status)
        if is_connected:
            try:
                last_update = datetime.fromisoformat(status['timestamp'])
                if last_update.tzinfo is None:
                    last_update = last_update.replace(tzinfo=pytz.UTC)
                now_utc = datetime.now(pytz.UTC)
                time_diff = (now_utc - last_update).total_seconds()
                is_connected = time_diff < 120
            except:
                is_connected = False
        
        # Header with live indicator
        price_status = ""
        if 'last_update' in realtime_prices:
            try:
                price_update = datetime.fromisoformat(realtime_prices['last_update'])
                if price_update.tzinfo is None:
                    price_update = price_update.replace(tzinfo=pytz.UTC)
                price_age = (datetime.now(pytz.UTC) - price_update).total_seconds()
                
                if price_age < 150:  # Less than 2.5 minutes
                    price_status = f"""
                    <div class="live-indicator">
                        <div class="live-dot"></div>
                        LIVE PRICES
                    </div>
                    """
                else:
                    price_status = f"""
                    <div class="live-indicator" style="background: rgba(255, 149, 0, 0.1); border-color: rgba(255, 149, 0, 0.3);">
                        <div class="live-dot delayed-dot"></div>
                        {int(price_age/60)}m AGO
                    </div>
                    """
            except:
                pass
        
        st.markdown(f"""
        <h1 class="main-title">
            REAL-TIME ML TRADING
            {price_status}
        </h1>
        """, unsafe_allow_html=True)
        
        if not status:
            st.warning("Waiting for trading system data...")
            time.sleep(5)
            st.rerun()
            return
        
        # Get market status
        market_status, status_color = get_market_status()
        
        # Top metrics row
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Market Status</div>
                <div class="metric-value" style="font-size: 16px; color: {status_color};">
                    {market_status}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Active positions
            active = sum(1 for p in status.get('positions', {}).values() if p['is_open'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Active Positions</div>
                <div class="metric-value">{active}/{len(ASSETS)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Today's signals
            total_signals = len(signals)
            long_signals = len([s for s in signals if s['action'] == 'LONG'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Today's Signals</div>
                <div class="metric-value">{total_signals}</div>
                <div class="metric-delta" style="color: #34C759;">{long_signals} longs</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Real-time P&L
            total_pnl = 0
            if 'positions' in status:
                for symbol, pos in status['positions'].items():
                    if pos.get('realtime_pnl_pct'):
                        total_pnl += pos['realtime_pnl_pct']
            
            pnl_color = "#34C759" if total_pnl > 0 else "#FF453A" if total_pnl < 0 else "#888"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Live P&L</div>
                <div class="metric-value" style="color: {pnl_color};">
                    {format_pnl(total_pnl)}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            # Closed trades
            exits = len([s for s in signals if s['action'] == 'EXIT'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Closed Today</div>
                <div class="metric-value">{exits}</div>
                <div class="metric-delta">trades</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col6:
            # Last signal time
            if signals:
                last_sig = sorted(signals, key=lambda x: x['timestamp'])[-1]
                sig_time = datetime.fromisoformat(last_sig['timestamp'])
                if sig_time.tzinfo is None:
                    sig_time = sig_time.replace(tzinfo=pytz.UTC)
                sig_time_et = sig_time.astimezone(ET)
                time_str = sig_time_et.strftime('%H:%M')
            else:
                time_str = "--:--"
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Last Signal</div>
                <div class="metric-value" style="font-size: 22px;">{time_str}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Main content area
        main_col1, main_col2 = st.columns([3, 2])
        
        with main_col1:
            st.markdown('<div class="section-header">Live Positions & Prices</div>', unsafe_allow_html=True)
            
            # Position cards with real-time prices
            for symbol in ASSETS:
                if symbol in status.get('positions', {}):
                    pos = status['positions'][symbol]
                    
                    # Determine position status
                    if pos['is_open']:
                        card_class = "position-long"
                        position_text = "LONG"
                        position_icon = "🟢"
                    else:
                        card_class = "position-flat"
                        position_text = "FLAT"
                        position_icon = "⚪"
                    
                    # Get real-time price
                    current_price = 0
                    price_source = ""
                    
                    # Check multiple price sources
                    if 'prices' in realtime_prices and symbol in realtime_prices['prices']:
                        current_price = realtime_prices['prices'][symbol]
                        price_source = "LIVE"
                    elif 'realtime_prices' in status and symbol in status['realtime_prices']:
                        current_price = status['realtime_prices'][symbol]
                        price_source = "CACHED"
                    elif 'latest_candle_prices' in status and symbol in status['latest_candle_prices']:
                        current_price = status['latest_candle_prices'][symbol]
                        price_source = "CANDLE"
                    
                    # Create position card
                    st.markdown(f"""
                    <div class="position-card {card_class}">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                                    <span style="font-size: 24px;">{position_icon}</span>
                                    <span style="font-size: 18px; font-weight: 600; color: var(--text-primary);">
                                        {symbol}
                                    </span>
                                    <span style="font-size: 14px; color: var(--text-secondary);">
                                        {position_text}
                                    </span>
                                </div>
                    """, unsafe_allow_html=True)
                    
                    if current_price > 0:
                        source_class = "source-live" if price_source == "LIVE" else "source-cached"
                        st.markdown(f"""
                                <div class="price-display">
                                    <span>${current_price:.2f}</span>
                                    <span class="price-source {source_class}">{price_source}</span>
                                </div>
                        """, unsafe_allow_html=True)
                    
                    if pos['is_open'] and current_price > 0:
                        entry = pos['entry_price']
                        if entry > 0:
                            pnl_pct = ((current_price - entry) / entry * 100)
                            pnl_dollar = (current_price - entry) * 100
                            pnl_color = "#34C759" if pnl_pct > 0 else "#FF453A"
                            
                            st.markdown(f"""
                                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 12px;">
                                    <div>
                                        <div style="color: var(--text-tertiary); font-size: 11px; text-transform: uppercase;">Entry</div>
                                        <div style="color: var(--text-primary); font-weight: 600;">${entry:.2f}</div>
                                    </div>
                                    <div>
                                        <div style="color: var(--text-tertiary); font-size: 11px; text-transform: uppercase;">P&L %</div>
                                        <div style="color: {pnl_color}; font-weight: 600;">{format_pnl(pnl_pct)}</div>
                                    </div>
                                    <div>
                                        <div style="color: var(--text-tertiary); font-size: 11px; text-transform: uppercase;">P&L $</div>
                                        <div style="color: {pnl_color}; font-weight: 600;">{format_pnl(pnl_dollar, False)}</div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    
                    st.markdown("""
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Add sparkline if available
                    if 'price_history' in realtime_prices and symbol in realtime_prices['price_history']:
                        col1, col2 = st.columns([3, 1])
                        with col2:
                            fig = create_price_sparkline(realtime_prices['price_history'][symbol])
                            if fig:
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Price chart
            st.markdown('<div class="section-header">Price Action (2-min updates)</div>', unsafe_allow_html=True)
            
            # Tabs for each symbol
            tabs = st.tabs(ASSETS)
            
            for tab, symbol in zip(tabs, ASSETS):
                with tab:
                    if 'price_history' in realtime_prices and symbol in realtime_prices['price_history']:
                        history = realtime_prices['price_history'][symbol]
                        
                        if len(history) > 1:
                            df = pd.DataFrame(history)
                            df['timestamp'] = pd.to_datetime(df['timestamp'])
                            
                            fig = go.Figure()
                            
                            # Add price line
                            fig.add_trace(go.Scatter(
                                x=df['timestamp'],
                                y=df['price'],
                                mode='lines+markers',
                                name=symbol,
                                line=dict(color='#00ff00', width=2),
                                marker=dict(size=4)
                            ))
                            
                            # Add today's signals
                            symbol_signals = [s for s in signals if s['symbol'] == symbol]
                            for sig in symbol_signals:
                                color = '#00ff00' if sig['action'] == 'LONG' else '#ff4444'
                                marker_symbol = 'triangle-up' if sig['action'] == 'LONG' else 'triangle-down'
                                
                                fig.add_trace(go.Scatter(
                                    x=[datetime.fromisoformat(sig['timestamp'])],
                                    y=[sig['price']],
                                    mode='markers',
                                    name=sig['action'],
                                    marker=dict(
                                        symbol=marker_symbol,
                                        size=15,
                                        color=color,
                                        line=dict(width=2, color=color)
                                    ),
                                    showlegend=False
                                ))
                            
                            fig.update_layout(
                                title=f"{symbol} - Real-Time",
                                yaxis_title="Price ($)",
                                xaxis_title="Time",
                                template="plotly_dark",
                                height=400,
                                hovermode='x unified'
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Waiting for price history...")
                    else:
                        st.info("No price data yet")
        
        with main_col2:
            st.markdown('<div class="section-header">Signal Feed</div>', unsafe_allow_html=True)
            
            if signals:
                recent_signals = sorted(signals, key=lambda x: x['timestamp'], reverse=True)[:10]
                
                for sig in recent_signals:
                    sig_time = datetime.fromisoformat(sig['timestamp'])
                    if sig_time.tzinfo is None:
                        sig_time = sig_time.replace(tzinfo=pytz.UTC)
                    sig_time_et = sig_time.astimezone(ET)
                    time_str = sig_time_et.strftime('%H:%M:%S')
                    
                    if sig['action'] == 'LONG':
                        card_class = "signal-long"
                        icon = "🟢"
                        action_color = "#34C759"
                    elif sig['action'] == 'EXIT':
                        card_class = "signal-exit"
                        icon = "🔴"
                        action_color = "#FF453A"
                    else:
                        card_class = ""
                        icon = "⚪"
                        action_color = "#888"
                    
                    st.markdown(f"""
                    <div class="signal-card {card_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span style="font-size: 16px;">{icon}</span>
                                    <span style="font-weight: 600; color: {action_color};">
                                        {sig['symbol']} - {sig['action']}
                                    </span>
                                </div>
                                <div style="color: var(--text-secondary); font-size: 12px; margin-top: 4px;">
                                    ${sig['price']:.2f} • {time_str}
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="color: {action_color}; font-size: 20px; font-weight: 700;">
                                    {sig['confidence']*100:.1f}%
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No signals yet today")
            
            # Performance summary
            st.markdown('<div class="section-header">Performance</div>', unsafe_allow_html=True)
            
            if 'positions' in status:
                total_pnl_dollar = 0
                winning = 0
                losing = 0
                
                for pos in status['positions'].values():
                    if pos.get('realtime_pnl_dollar'):
                        total_pnl_dollar += pos['realtime_pnl_dollar']
                        if pos['realtime_pnl_dollar'] > 0:
                            winning += 1
                        elif pos['realtime_pnl_dollar'] < 0:
                            losing += 1
                
                col1, col2 = st.columns(2)
                
                with col1:
                    pnl_color = "#34C759" if total_pnl_dollar > 0 else "#FF453A" if total_pnl_dollar < 0 else "#888"
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <div style="color: var(--text-tertiary); font-size: 12px;">Day P&L</div>
                        <div style="color: {pnl_color}; font-size: 24px; font-weight: 700;">
                            {format_pnl(total_pnl_dollar, False)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <div style="color: var(--text-tertiary); font-size: 12px;">W/L</div>
                        <div style="font-size: 24px; font-weight: 700;">
                            <span style="color: #34C759;">{winning}</span> / 
                            <span style="color: #FF453A;">{losing}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Footer
        st.markdown("---")
        
        update_info = []
        if 'timestamp' in status:
            update_info.append(f"System: {datetime.fromisoformat(status['timestamp']).strftime('%H:%M:%S')}")
        if 'last_update' in realtime_prices:
            update_info.append(f"Prices: {datetime.fromisoformat(realtime_prices['last_update']).strftime('%H:%M:%S')}")
        
        st.caption(f"""
        Real-Time ML Trading System | 
        Updates: {' | '.join(update_info)} | 
        Auto-refresh: 2 seconds | 
        Data: Alpaca Real-Time
        """)
    
    # Auto-refresh
    time.sleep(2)
    st.session_state.counter += 1
    st.rerun()

if __name__ == "__main__":
    main()
