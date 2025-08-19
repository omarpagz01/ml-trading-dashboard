"""
ML Trading System - Professional Dashboard
Modern, fluid design with real-time updates
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
    page_title="ML Trading System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern Dark Theme CSS
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Main App Background */
    .stApp {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Title */
    .main-title {
        font-size: 32px;
        font-weight: 700;
        color: #00ff88;
        text-align: center;
        margin-bottom: 30px;
        letter-spacing: 2px;
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(145deg, #1e1e2e, #2a2a3e);
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.5);
    }
    
    .metric-label {
        color: #8b8b8b;
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    
    .metric-delta {
        font-size: 14px;
        font-weight: 500;
    }
    
    .metric-delta-positive {
        color: #00ff88;
    }
    
    .metric-delta-negative {
        color: #ff4757;
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 30px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .status-open {
        background: linear-gradient(90deg, #00ff88, #00cc70);
        color: #000;
    }
    
    .status-closed {
        background: linear-gradient(90deg, #ff4757, #ff6b7a);
        color: #fff;
    }
    
    .status-after-hours {
        background: linear-gradient(90deg, #ff9f43, #ffb265);
        color: #000;
    }
    
    /* Position Table */
    .position-table {
        background: #1e1e2e;
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
    }
    
    /* Signal Cards */
    .signal-card {
        background: linear-gradient(145deg, #1e1e2e, #2a2a3e);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid;
        transition: all 0.3s ease;
    }
    
    .signal-card:hover {
        transform: translateX(5px);
    }
    
    .signal-long {
        border-left-color: #00ff88;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
    }
    
    .signal-exit {
        border-left-color: #ff4757;
        box-shadow: 0 0 20px rgba(255, 71, 87, 0.2);
    }
    
    .signal-hold {
        border-left-color: #8b8b8b;
    }
    
    /* Charts */
    .chart-container {
        background: #1e1e2e;
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
    }
    
    /* Animated Background */
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 0.8; }
        100% { opacity: 0.6; }
    }
    
    .pulse-animation {
        animation: pulse 2s infinite;
    }
    
    /* Section Headers */
    .section-header {
        color: #ffffff;
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #00ff88;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e1e2e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #00ff88;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00cc70;
    }
    
    /* Responsive Grid */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }
    
    /* Glow Effects */
    .glow-green {
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
    }
    
    .glow-red {
        box-shadow: 0 0 20px rgba(255, 71, 87, 0.5);
    }
    
    /* Loading Animation */
    .loading-pulse {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #00ff88;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
        margin-left: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# Define your assets
ASSETS = ['TSLA', 'HOOD', 'COIN', 'PLTR', 'AAPL']

# Helper functions
@st.cache_data(ttl=2)
def load_signals():
    """Load today's signals with deduplication"""
    signal_file = Path("signals") / f"signals_{datetime.now().strftime('%Y%m%d')}.json"
    if signal_file.exists():
        try:
            with open(signal_file, 'r') as f:
                content = f.read()
                if content.strip():
                    signals = json.loads(content)
                    return process_signals(signals)
        except Exception as e:
            st.error(f"Error loading signals: {e}")
    return []

def process_signals(signals):
    """Process signals to count unique positions"""
    if not signals:
        return []
    
    # Track position changes for accurate counting
    position_tracker = {}
    processed_signals = []
    unique_trades = 0
    
    for sig in sorted(signals, key=lambda x: x['timestamp']):
        symbol = sig['symbol']
        action = sig['action']
        
        # Track position changes
        if symbol not in position_tracker:
            position_tracker[symbol] = 'FLAT'
        
        current_position = position_tracker[symbol]
        
        # Count unique trades (position changes)
        if action == 'LONG' and current_position != 'LONG':
            position_tracker[symbol] = 'LONG'
            sig['is_new_trade'] = True
            unique_trades += 1
        elif action == 'EXIT' and current_position == 'LONG':
            position_tracker[symbol] = 'FLAT'
            sig['is_new_trade'] = True
            unique_trades += 1
        else:
            sig['is_new_trade'] = False
        
        processed_signals.append(sig)
    
    return processed_signals

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
    color = "metric-delta-positive" if value > 0 else "metric-delta-negative"
    return f'<span class="{color}">{value:+.2f}%</span>'

# Main Dashboard
def main():
    # Title with modern styling
    st.markdown('<h1 class="main-title">🤖 ML TRADING SYSTEM DASHBOARD</h1>', unsafe_allow_html=True)
    
    # Load data
    signals = load_signals()
    status = load_status()
    
    if not status:
        st.warning("⚠️ Waiting for trading system data...")
        time.sleep(5)
        st.rerun()
        return
    
    # Get market status
    market_status, status_class, status_icon = get_market_status()
    
    # Count unique trades
    unique_long_trades = len(set(s['symbol'] for s in signals if s.get('is_new_trade') and s['action'] == 'LONG'))
    unique_exit_trades = len(set(s['symbol'] for s in signals if s.get('is_new_trade') and s['action'] == 'EXIT'))
    
    # Top Metrics Row with Modern Cards
    st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Market Status</div>
            <div class="status-badge {status_class}">{status_icon} {market_status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        last_update = datetime.fromisoformat(status['timestamp']) if 'timestamp' in status else datetime.now()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Last Update</div>
            <div class="metric-value">{last_update.strftime('%H:%M:%S')}</div>
            <div class="loading-pulse"></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Signals Today</div>
            <div class="metric-value">{len(signals)}</div>
            <div class="metric-delta metric-delta-positive">↑ {unique_long_trades} longs</div>
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
        
        pnl_html = format_percentage(total_pnl)
        st.markdown(f"""
        <div class="metric-card {'glow-green' if total_pnl > 0 else 'glow-red' if total_pnl < 0 else ''}">
            <div class="metric-label">Total Open P&L</div>
            <div class="metric-value">{pnl_html}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Trades Today</div>
            <div class="metric-value">{unique_exit_trades}</div>
            <div class="metric-delta">exits</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
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
                    
                    row_data = {
                        'Symbol': symbol,
                        'Status': '��' if pos['is_open'] else '⚪',
                        'Position': 'LONG' if pos['is_open'] else 'FLAT',
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
                    
                    row_data['Confidence'] = f"{pos.get('last_confidence', 0):.3f}" if pos.get('last_confidence', 0) > 0 else '-'
                    
                    positions_data.append(row_data)
            
            if positions_data:
                df_positions = pd.DataFrame(positions_data)
                
                # Custom styling for the dataframe
                def style_dataframe(val):
                    if isinstance(val, str):
                        if '+' in val and '%' in val:
                            return 'color: #00ff88'
                        elif '-' in val and '%' in val and val != '-':
                            return 'color: #ff4757'
                    return ''
                
                styled_df = df_positions.style.applymap(style_dataframe, subset=['P&L %', 'P&L $'])
                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    hide_index=True,
                    height=250
                )
        
        # Price Charts
        st.markdown('<div class="section-header">💹 Price Action</div>', unsafe_allow_html=True)
        
        if status and 'latest_prices' in status:
            # Create modern tabs
            tab_list = st.tabs(ASSETS)
            
            for tab, symbol in zip(tab_list, ASSETS):
                with tab:
                    hist_data = load_historical_data(symbol)
                    
                    if hist_data is not None and not hist_data.empty:
                        # Create professional candlestick chart
                        fig = go.Figure()
                        
                        fig.add_trace(go.Candlestick(
                            x=pd.to_datetime(hist_data['timestamp']),
                            open=hist_data['open'],
                            high=hist_data['high'],
                            low=hist_data['low'],
                            close=hist_data['close'],
                            name=symbol,
                            increasing=dict(line=dict(color='#00ff88', width=1), fillcolor='#00ff88'),
                            decreasing=dict(line=dict(color='#ff4757', width=1), fillcolor='#ff4757')
                        ))
                        
                        # Add volume bars
                        fig.add_trace(go.Bar(
                            x=pd.to_datetime(hist_data['timestamp']),
                            y=hist_data['volume'],
                            name='Volume',
                            yaxis='y2',
                            marker=dict(color='rgba(0, 255, 136, 0.3)')
                        ))
                        
                        # Add signals as markers
                        symbol_signals = [s for s in signals if s['symbol'] == symbol]
                        if symbol_signals:
                            long_signals = [s for s in symbol_signals if s['action'] == 'LONG' and s.get('is_new_trade')]
                            exit_signals = [s for s in symbol_signals if s['action'] == 'EXIT' and s.get('is_new_trade')]
                            
                            if long_signals:
                                fig.add_trace(go.Scatter(
                                    x=[datetime.fromisoformat(s['timestamp']) for s in long_signals],
                                    y=[s['price'] for s in long_signals],
                                    mode='markers',
                                    name='LONG',
                                    marker=dict(
                                        symbol='triangle-up',
                                        size=15,
                                        color='#00ff88',
                                        line=dict(width=2, color='#00ff88')
                                    )
                                ))
                            
                            if exit_signals:
                                fig.add_trace(go.Scatter(
                                    x=[datetime.fromisoformat(s['timestamp']) for s in exit_signals],
                                    y=[s['price'] for s in exit_signals],
                                    mode='markers',
                                    name='EXIT',
                                    marker=dict(
                                        symbol='triangle-down',
                                        size=15,
                                        color='#ff4757',
                                        line=dict(width=2, color='#ff4757')
                                    )
                                ))
                        
                        # Update layout for modern look
                        fig.update_layout(
                            template='plotly_dark',
                            height=400,
                            showlegend=False,
                            xaxis=dict(
                                rangeslider=dict(visible=False),
                                gridcolor='#2a2a3e',
                                showgrid=True
                            ),
                            yaxis=dict(
                                title='Price ($)',
                                side='right',
                                gridcolor='#2a2a3e',
                                showgrid=True
                            ),
                            yaxis2=dict(
                                title='Volume',
                                overlaying='y',
                                side='left',
                                showgrid=False
                            ),
                            paper_bgcolor='#1e1e2e',
                            plot_bgcolor='#1e1e2e',
                            font=dict(color='#ffffff', family='Inter'),
                            margin=dict(l=0, r=0, t=0, b=0)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        # Show current price as metric
                        if symbol in status.get('latest_prices', {}):
                            current = status['latest_prices'][symbol]
                            st.metric(label=f"{symbol} Price", value=format_currency(current))
    
    with col_right:
        # Live Signal Feed
        st.markdown('<div class="section-header">📈 Live Signal Feed</div>', unsafe_allow_html=True)
        
        signal_container = st.container(height=600)
        
        with signal_container:
            if signals:
                # Show only unique trades
                recent_signals = sorted(
                    [s for s in signals if s.get('is_new_trade')],
                    key=lambda x: x['timestamp'],
                    reverse=True
                )[:20]
                
                for sig in recent_signals:
                    sig_time = datetime.fromisoformat(sig['timestamp'])
                    time_str = sig_time.strftime('%H:%M:%S')
                    
                    if sig['action'] == 'LONG':
                        st.markdown(f"""
                        <div class="signal-card signal-long">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="color: #00ff88; font-weight: 600;">🟢 LONG - {sig['symbol']}</div>
                                    <div style="color: #8b8b8b; font-size: 12px; margin-top: 5px;">
                                        {time_str} • ${sig['price']:.2f}
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="color: #ffffff; font-size: 14px;">Confidence</div>
                                    <div style="color: #00ff88; font-size: 20px; font-weight: 700;">
                                        {sig['confidence']:.1%}
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
                                    <div style="color: #ff4757; font-weight: 600;">🔴 EXIT - {sig['symbol']}</div>
                                    <div style="color: #8b8b8b; font-size: 12px; margin-top: 5px;">
                                        {time_str} • ${sig['price']:.2f}
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="color: #ffffff; font-size: 14px;">Confidence</div>
                                    <div style="color: #ff4757; font-size: 20px; font-weight: 700;">
                                        {sig['confidence']:.1%}
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Waiting for trading signals...")
    
    # Performance Analytics Section
    st.markdown('<div class="section-header">📊 Performance Analytics</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Signal Distribution
        if signals:
            unique_longs = unique_long_trades
            unique_exits = unique_exit_trades
            
            fig = go.Figure(data=[go.Pie(
                labels=['LONG', 'EXIT'],
                values=[unique_longs, unique_exits],
                hole=0.6,
                marker=dict(colors=['#00ff88', '#ff4757']),
                textinfo='label+value'
            )])
            
            fig.update_layout(
                showlegend=False,
                height=200,
                paper_bgcolor='#1e1e2e',
                plot_bgcolor='#1e1e2e',
                font=dict(color='#ffffff'),
                margin=dict(l=0, r=0, t=20, b=0),
                title=dict(text='Unique Trades', font=dict(size=14))
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Hourly Activity
        if signals:
            hours = [datetime.fromisoformat(s['timestamp']).hour for s in signals if s.get('is_new_trade')]
            if hours:
                hour_counts = pd.Series(hours).value_counts().sort_index()
                
                fig = go.Figure(data=[go.Bar(
                    x=hour_counts.index,
                    y=hour_counts.values,
                    marker=dict(
                        color=hour_counts.values,
                        colorscale=[[0, '#1e1e2e'], [1, '#00ff88']],
                        showscale=False
                    )
                )])
                
                fig.update_layout(
                    title=dict(text='Activity by Hour', font=dict(size=14)),
                    xaxis=dict(title='Hour (ET)', gridcolor='#2a2a3e'),
                    yaxis=dict(title='Trades', gridcolor='#2a2a3e'),
                    height=200,
                    paper_bgcolor='#1e1e2e',
                    plot_bgcolor='#1e1e2e',
                    font=dict(color='#ffffff'),
                    margin=dict(l=0, r=0, t=40, b=40),
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        # Win Rate (if we have exits)
        exit_signals = [s for s in signals if s['action'] == 'EXIT' and s.get('is_new_trade')]
        if exit_signals:
            # This is simplified - in production you'd calculate actual P&L
            wins = len([s for s in exit_signals if s.get('pnl', 0) >= 0])
            losses = len(exit_signals) - wins
            win_rate = (wins / len(exit_signals)) * 100 if exit_signals else 0
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=win_rate,
                title={'text': "Win Rate %"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#00ff88"},
                    'steps': [
                        {'range': [0, 50], 'color': "#1e1e2e"},
                        {'range': [50, 100], 'color': "#2a2a3e"}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': 50
                    }
                }
            ))
            
            fig.update_layout(
                height=200,
                paper_bgcolor='#1e1e2e',
                font=dict(color='#ffffff'),
                margin=dict(l=0, r=0, t=40, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col4:
        # ML Model Confidence Average
        if signals and len(signals) > 0:
            recent_signals = signals[-10:]
            avg_confidence = np.mean([s['confidence'] for s in recent_signals])
            
            fig = go.Figure(go.Indicator(
                mode="number+delta",
                value=avg_confidence * 100,
                title={'text': "Avg Confidence"},
                number={'suffix': "%"},
                delta={'reference': 50, 'relative': False}
            ))
            
            fig.update_layout(
                height=200,
                paper_bgcolor='#1e1e2e',
                font=dict(color='#ffffff'),
                margin=dict(l=0, r=0, t=40, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #8b8b8b; font-size: 12px;">
        🤖 ML Trading System | 
        Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
        Auto-refresh: 5 seconds | 
        Data: Polygon + Alpaca APIs
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
