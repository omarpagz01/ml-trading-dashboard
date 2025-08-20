"""
ML Trading System - Live Dashboard
Real-time monitoring of trading positions and signals
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

# Page configuration
st.set_page_config(
    page_title="Signals Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for iOS-inspired dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main title styling */
    h1 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-weight: 700 !important;
        font-size: 32px !important;
        background: linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        letter-spacing: -0.5px;
        margin-bottom: 30px !important;
        padding: 20px 0;
    }
    
    /* Subheader styling */
    h2 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-weight: 600 !important;
        font-size: 18px !important;
        color: #ffffff !important;
        letter-spacing: -0.3px;
        margin-top: 20px !important;
        margin-bottom: 15px !important;
    }
    
    h3 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-weight: 500 !important;
        color: #e0e0e0 !important;
    }
    
    /* Metric containers */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 16px;
        border-radius: 16px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1), inset 0 1px 0 rgba(255,255,255,0.1);
    }
    
    [data-testid="metric-container"] label {
        font-size: 12px !important;
        font-weight: 500 !important;
        color: rgba(255,255,255,0.6) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 24px !important;
        font-weight: 600 !important;
        color: #ffffff !important;
    }
    
    /* Dataframe styling */
    [data-testid="stDataFrame"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        overflow: hidden;
    }
    
    .dataframe {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.04) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-weight: 500 !important;
        color: #ffffff !important;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.06) 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    [data-testid="stExpander"] {
        border: none !important;
        margin-bottom: 8px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: rgba(255,255,255,0.6);
        font-weight: 500;
        background: transparent;
        border: none;
        transition: all 0.3s ease;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255,255,255,0.08);
        color: rgba(255,255,255,0.9);
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(255,255,255,0.15) !important;
        color: #ffffff !important;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #4a9eff 0%, #0066ff 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: 600;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,102,255,0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,102,255,0.4);
    }
    
    /* Divider styling */
    hr {
        margin: 30px 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    }
    
    /* Info box styling */
    .stAlert {
        background: linear-gradient(135deg, rgba(74,158,255,0.1) 0%, rgba(74,158,255,0.05) 100%);
        border: 1px solid rgba(74,158,255,0.3);
        border-radius: 12px;
        color: #ffffff;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Custom card styling */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.1);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.15);
    }
    
    /* Status indicators */
    .status-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-active {
        background: linear-gradient(135deg, rgba(76,217,100,0.2) 0%, rgba(76,217,100,0.1) 100%);
        border: 1px solid rgba(76,217,100,0.5);
        color: #4cd964;
    }
    
    .status-inactive {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        border: 1px solid rgba(255,255,255,0.2);
        color: rgba(255,255,255,0.6);
    }
    
    /* Glassmorphism effect for containers */
    .glass-container {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    /* Caption styling */
    .caption {
        font-size: 11px;
        color: rgba(255,255,255,0.4);
        text-align: center;
        margin-top: 40px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: 0.3px;
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
    """Check if market is open"""
    now = datetime.now(timezone(timedelta(hours=-4)))  # ET
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday >= 5:  # Weekend
        return "Weekend", "#ff453a", "⚫"
    elif current_time < pd.Timestamp("09:30").time():
        return "Pre-Market", "#ff9f0a", "��"
    elif current_time >= pd.Timestamp("16:00").time():
        return "After-Hours", "#ff9f0a", "🟠"
    elif pd.Timestamp("09:30").time() <= current_time < pd.Timestamp("16:00").time():
        return "Market Open", "#30d158", "🟢"
    else:
        return "Market Closed", "#ff453a", "🔴"

# Main Dashboard
def main():
    # Header
    st.markdown("<h1>Signals Dashboard</h1>", unsafe_allow_html=True)
    
    # Load data
    signals = load_signals()
    status = load_status()
    
    # Check if we have data
    if not status:
        st.warning("⚠️ No status data available. Make sure the trading system is running.")
        time.sleep(5)
        st.rerun()
        return
    
    # Top metrics with glassmorphism effect
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    market_status, status_color, status_emoji = get_market_status()
    
    with col1:
        st.metric(
            label="Market Status",
            value=market_status,
            delta=None
        )
    
    with col2:
        last_update = datetime.fromisoformat(status['timestamp']) if 'timestamp' in status else datetime.now()
        st.metric(
            label="Last Update",
            value=last_update.strftime('%H:%M:%S')
        )
    
    with col3:
        total_signals = len(signals)
        long_signals = len([s for s in signals if s['action'] == 'LONG'])
        st.metric(
            label="Today's Signals",
            value=total_signals,
            delta=f"{long_signals} long" if long_signals > 0 else None
        )
    
    with col4:
        if status and 'positions' in status:
            active = sum(1 for p in status['positions'].values() if p['is_open'])
            st.metric(
                label="Active Positions",
                value=active,
                delta=f"/{len(ASSETS)} total"
            )
        else:
            st.metric("Active Positions", 0)
    
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
        
        st.metric(
            label="Open P&L",
            value=f"{total_pnl:+.2f}%",
            delta="Live" if total_pnl != 0 else None
        )
    
    with col6:
        if signals:
            exits = [s for s in signals if s['action'] == 'EXIT']
            st.metric(
                label="Closed Trades",
                value=len(exits),
                delta="Today"
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Main content area with better spacing
    col_left, col_right = st.columns([3, 2], gap="large")
    
    with col_left:
        # Positions Section
        st.markdown("## Positions Overview")
        
        if status and 'positions' in status:
            positions_data = []
            
            for symbol in ASSETS:
                if symbol in status['positions']:
                    pos = status['positions'][symbol]
                    
                    row_data = {
                        'Symbol': symbol,
                        'Status': '🟢' if pos['is_open'] else '⚫',
                        'Position': 'LONG' if pos['is_open'] else 'FLAT',
                        'Entry': f"${pos['entry_price']:.2f}" if pos['entry_price'] > 0 else '—',
                    }
                    
                    if pos['is_open'] and symbol in status.get('latest_prices', {}):
                        current = status['latest_prices'][symbol]
                        entry = pos['entry_price']
                        if entry > 0:
                            pnl_pct = ((current - entry) / entry * 100)
                            row_data['Current'] = f"${current:.2f}"
                            row_data['P&L'] = f"{pnl_pct:+.2f}%"
                        else:
                            row_data['Current'] = f"${current:.2f}"
                            row_data['P&L'] = '—'
                    else:
                        row_data['Current'] = '—'
                        row_data['P&L'] = '—'
                    
                    row_data['Signal'] = pos.get('last_signal', '—')
                    row_data['Confidence'] = f"{pos.get('last_confidence', 0):.2f}" if pos.get('last_confidence', 0) > 0 else '—'
                    
                    positions_data.append(row_data)
            
            if positions_data:
                df_positions = pd.DataFrame(positions_data)
                
                st.dataframe(
                    df_positions,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Status": st.column_config.TextColumn(width="small"),
                        "Symbol": st.column_config.TextColumn(width="small"),
                        "Position": st.column_config.TextColumn(width="medium"),
                        "P&L": st.column_config.TextColumn(width="small"),
                    }
                )
        
        # Price Charts with modern styling
        st.markdown("## Price Action")
        
        if status and 'latest_prices' in status:
            tabs = st.tabs([f" {symbol} " for symbol in ASSETS])
            
            for tab, symbol in zip(tabs, ASSETS):
                with tab:
                    hist_data = load_historical_data(symbol)
                    
                    if hist_data is not None and not hist_data.empty:
                        fig = go.Figure()
                        
                        # Candlestick with iOS colors
                        fig.add_trace(go.Candlestick(
                            x=pd.to_datetime(hist_data['timestamp']),
                            open=hist_data['open'],
                            high=hist_data['high'],
                            low=hist_data['low'],
                            close=hist_data['close'],
                            name=symbol,
                            increasing_line_color='#30d158',
                            decreasing_line_color='#ff453a',
                            increasing_fillcolor='#30d158',
                            decreasing_fillcolor='#ff453a'
                        ))
                        
                        # Add signals
                        symbol_signals = [s for s in signals if s['symbol'] == symbol]
                        if symbol_signals:
                            long_signals = [s for s in symbol_signals if s['action'] == 'LONG']
                            exit_signals = [s for s in symbol_signals if s['action'] == 'EXIT']
                            
                            if long_signals:
                                fig.add_trace(go.Scatter(
                                    x=[datetime.fromisoformat(s['timestamp']) for s in long_signals],
                                    y=[s['price'] for s in long_signals],
                                    mode='markers',
                                    name='LONG',
                                    marker=dict(
                                        symbol='triangle-up',
                                        size=12,
                                        color='#30d158',
                                        line=dict(color='white', width=1)
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
                                        size=12,
                                        color='#ff453a',
                                        line=dict(color='white', width=1)
                                    )
                                ))
                        
                        # Update layout with dark theme
                        fig.update_layout(
                            title=None,
                            yaxis_title="Price ($)",
                            xaxis_title=None,
                            template="plotly_dark",
                            height=350,
                            showlegend=False,
                            hovermode='x unified',
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(
                                gridcolor='rgba(255,255,255,0.05)',
                                showgrid=True
                            ),
                            yaxis=dict(
                                gridcolor='rgba(255,255,255,0.05)',
                                showgrid=True
                            ),
                            margin=dict(l=0, r=0, t=0, b=40)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        if symbol in status.get('latest_prices', {}):
                            current = status['latest_prices'][symbol]
                            st.metric(f"Current Price", f"${current:.2f}")
    
    with col_right:
        # Signal Feed with modern cards
        st.markdown("## Live Signals")
        
        signal_container = st.container()
        
        with signal_container:
            if signals:
                recent_signals = sorted(signals, key=lambda x: x['timestamp'], reverse=True)[:10]
                
                for sig in recent_signals:
                    sig_time = datetime.fromisoformat(sig['timestamp'])
                    time_str = sig_time.strftime('%H:%M:%S')
                    
                    # iOS-style signal indicators
                    if sig['action'] == 'LONG':
                        emoji = "🟢"
                        action_style = "color: #30d158; font-weight: 600;"
                    elif sig['action'] == 'EXIT':
                        emoji = "🔴"
                        action_style = "color: #ff453a; font-weight: 600;"
                    else:
                        emoji = "⚫"
                        action_style = "color: rgba(255,255,255,0.6); font-weight: 500;"
                    
                    # Create expandable signal cards
                    with st.expander(f"{emoji} {sig['symbol']} • {sig['action']} • ${sig['price']:.2f}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Time**  \n{time_str}")
                            st.markdown(f"**Price**  \n${sig['price']:.2f}")
                        with col2:
                            st.markdown(f"**Confidence**  \n{sig['confidence']:.3f}")
                            if 'ml_scores' in sig and sig['ml_scores']:
                                scores_text = "**ML Scores**  \n"
                                for model, score in list(sig['ml_scores'].items())[:3]:
                                    if isinstance(score, (int, float)):
                                        model_name = model.replace('_', ' ').title()
                                        scores_text += f"{model_name}: {score:.2f}  \n"
                                st.markdown(scores_text)
            else:
                st.info("Waiting for signals...")
    
    # Analytics Section
    st.markdown("---")
    st.markdown("## Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if signals:
            signal_types = {'LONG': 0, 'EXIT': 0, 'HOLD': 0}
            for sig in signals:
                if sig['action'] in signal_types:
                    signal_types[sig['action']] += 1
            
            if sum(signal_types.values()) > 0:
                fig = go.Figure(data=[go.Pie(
                    labels=list(signal_types.keys()),
                    values=list(signal_types.values()),
                    marker=dict(colors=['#30d158', '#ff453a', '#8e8e93']),
                    hole=0.6,
                    textinfo='label+percent',
                    textfont=dict(color='white', size=12)
                )])
                
                fig.update_layout(
                    title="Signal Distribution",
                    title_font_size=14,
                    title_font_color='rgba(255,255,255,0.8)',
                    template="plotly_dark",
                    height=250,
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if signals:
            hours = [datetime.fromisoformat(s['timestamp']).hour for s in signals]
            hour_counts = pd.Series(hours).value_counts().sort_index()
            
            fig = go.Figure(data=[go.Bar(
                x=hour_counts.index,
                y=hour_counts.values,
                marker=dict(
                    color=hour_counts.values,
                    colorscale=[[0, '#0066ff'], [1, '#30d158']],
                    line=dict(color='rgba(255,255,255,0.1)', width=1)
                )
            )])
            
            fig.update_layout(
                title="Hourly Activity",
                title_font_size=14,
                title_font_color='rgba(255,255,255,0.8)',
                xaxis_title="Hour (ET)",
                yaxis_title="Signals",
                template="plotly_dark",
                height=250,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                margin=dict(l=0, r=0, t=40, b=40)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        if signals:
            symbol_counts = {}
            for sig in signals:
                sym = sig['symbol']
                symbol_counts[sym] = symbol_counts.get(sym, 0) + 1
            
            if symbol_counts:
                fig = go.Figure(data=[go.Bar(
                    x=list(symbol_counts.keys()),
                    y=list(symbol_counts.values()),
                    marker=dict(
                        color=list(symbol_counts.values()),
                        colorscale=[[0, '#ff453a'], [0.5, '#ff9f0a'], [1, '#30d158']],
                        line=dict(color='rgba(255,255,255,0.1)', width=1)
                    )
                )])
                
                fig.update_layout(
                    title="Symbol Activity",
                    title_font_size=14,
                    title_font_color='rgba(255,255,255,0.8)',
                    xaxis_title="Symbol",
                    yaxis_title="Count",
                    template="plotly_dark",
                    height=250,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    margin=dict(l=0, r=0, t=40, b=40)
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div class="caption">
            ML Trading System • Real-time monitoring • Auto-refresh: 5s<br>
            Data: Polygon + Alpaca APIs
        </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
