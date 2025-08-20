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
    page_title="ML Trading Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    /* Dark theme styling */
    .stApp {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        margin: 10px 0;
    }
    .signal-long {
        background-color: #1e3a1e;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #00ff00;
        margin: 5px 0;
    }
    .signal-exit {
        background-color: #3a1e1e;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #ff0000;
        margin: 5px 0;
    }
    .signal-hold {
        background-color: #2a2a2a;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #888888;
        margin: 5px 0;
    }
    h1 {
        color: #00ff00 !important;
        text-align: center;
        font-family: 'Courier New', monospace;
    }
    .stMetric {
        background-color: #1a1a1a;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# Define your assets (same as main file)
ASSETS = ['TSLA', 'HOOD', 'COIN', 'PLTR', 'AAPL']

# Helper functions
@st.cache_data(ttl=2)  # Cache for 2 seconds
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
        return "🔴 WEEKEND", "#ff4444"
    elif current_time < pd.Timestamp("09:30").time():
        return "🟡 PRE-MARKET", "#ffaa00"
    elif current_time >= pd.Timestamp("16:00").time():
        return "🟠 AFTER-HOURS", "#ff8800"
    elif pd.Timestamp("09:30").time() <= current_time < pd.Timestamp("16:00").time():
        return "🟢 MARKET OPEN", "#00ff00"
    else:
        return "🔴 MARKET CLOSED", "#ff4444"

def format_number(value, decimals=2):
    """Format numbers for display"""
    if value is None or value == 0:
        return "-"
    return f"{value:,.{decimals}f}"

# Main Dashboard
def main():
    # Header with custom styling
    st.markdown("<h1>🤖 ML TRADING SYSTEM DASHBOARD</h1>", unsafe_allow_html=True)
    
    # Load data
    signals = load_signals()
    status = load_status()
    
    # Check if we have data
    if not status:
        st.warning("⚠️ No status data available. Make sure the trading system is running.")
        time.sleep(5)
        st.rerun()
        return
    
    # Top metrics row
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    market_status, status_color = get_market_status()
    
    with col1:
        st.markdown(f"""
        <div style='text-align: center'>
            <p style='margin: 0; color: #888'>Market Status</p>
            <h3 style='margin: 0; color: {status_color}'>{market_status}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        last_update = datetime.fromisoformat(status['timestamp']) if 'timestamp' in status else datetime.now()
        st.metric(
            "Last Update",
            last_update.strftime('%H:%M:%S'),
            delta=None
        )
    
    with col3:
        total_signals = len(signals)
        long_signals = len([s for s in signals if s['action'] == 'LONG'])
        st.metric(
            "Signals Today",
            total_signals,
            delta=f"{long_signals} longs"
        )
    
    with col4:
        if status and 'positions' in status:
            active = sum(1 for p in status['positions'].values() if p['is_open'])
            st.metric("Active Positions", active)
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
        
        color = "normal" if total_pnl >= 0 else "inverse"
        st.metric(
            "Total Open P&L",
            f"{total_pnl:+.2f}%",
            delta=None,
            delta_color=color
        )
    
    with col6:
        # Win rate calculation
        if signals:
            exits = [s for s in signals if s['action'] == 'EXIT']
            # This is simplified - you'd need to track actual P&L
            st.metric("Trades Today", len(exits))
    
    st.markdown("---")
    
    # Main content area
    main_col1, main_col2 = st.columns([3, 2])
    
    with main_col1:
        # Positions Table
        st.subheader("📊 Current Positions")
        
        if status and 'positions' in status:
            positions_data = []
            
            for symbol in ASSETS:  # Use consistent ordering
                if symbol in status['positions']:
                    pos = status['positions'][symbol]
                    
                    row_data = {
                        'Symbol': symbol,
                        'Status': '🟢' if pos['is_open'] else '⚪',
                        'Position': 'LONG' if pos['is_open'] else 'FLAT',
                        'Entry': f"${pos['entry_price']:.2f}" if pos['entry_price'] > 0 else '-',
                    }
                    
                    if pos['is_open'] and symbol in status.get('latest_prices', {}):
                        current = status['latest_prices'][symbol]
                        entry = pos['entry_price']
                        if entry > 0:
                            pnl_pct = ((current - entry) / entry * 100)
                            pnl_dollar = (current - entry) * 100  # Assuming 100 shares
                            
                            row_data['Current'] = f"${current:.2f}"
                            row_data['P&L %'] = pnl_pct
                            row_data['P&L $'] = pnl_dollar
                        else:
                            row_data['Current'] = f"${current:.2f}"
                            row_data['P&L %'] = 0
                            row_data['P&L $'] = 0
                    else:
                        row_data['Current'] = '-'
                        row_data['P&L %'] = 0
                        row_data['P&L $'] = 0
                    
                    row_data['Signal'] = pos.get('last_signal', '-')
                    row_data['Confidence'] = pos.get('last_confidence', 0)
                    
                    positions_data.append(row_data)
            
            if positions_data:
                df_positions = pd.DataFrame(positions_data)
                
                # Format the dataframe for display
                def style_pnl(val):
                    """Style P&L values"""
                    if isinstance(val, (int, float)):
                        if val > 0:
                            return 'color: #00ff00'
                        elif val < 0:
                            return 'color: #ff4444'
                    return ''
                
                # Format P&L columns
                df_display = df_positions.copy()
                df_display['P&L %'] = df_display['P&L %'].apply(lambda x: f"{x:+.2f}%" if x != 0 else "-")
                df_display['P&L $'] = df_display['P&L $'].apply(lambda x: f"${x:+.2f}" if x != 0 else "-")
                df_display['Confidence'] = df_display['Confidence'].apply(lambda x: f"{x:.3f}" if x > 0 else "-")
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Status": st.column_config.TextColumn(width="small"),
                        "Symbol": st.column_config.TextColumn(width="small"),
                        "Position": st.column_config.TextColumn(width="small"),
                    }
                )
        
        # Price Charts
        st.subheader("💹 Price Action")
        
        if status and 'latest_prices' in status:
            # Create tabs for each symbol
            tabs = st.tabs(ASSETS)
            
            for tab, symbol in zip(tabs, ASSETS):
                with tab:
                    # Load historical data
                    hist_data = load_historical_data(symbol)
                    
                    if hist_data is not None and not hist_data.empty:
                        # Create candlestick chart
                        fig = go.Figure()
                        
                        # Add candlestick
                        fig.add_trace(go.Candlestick(
                            x=pd.to_datetime(hist_data['timestamp']),
                            open=hist_data['open'],
                            high=hist_data['high'],
                            low=hist_data['low'],
                            close=hist_data['close'],
                            name=symbol,
                            increasing_line_color='#00ff00',
                            decreasing_line_color='#ff4444'
                        ))
                        
                        # Add signals as markers
                        symbol_signals = [s for s in signals if s['symbol'] == symbol]
                        if symbol_signals:
                            long_signals = [s for s in symbol_signals if s['action'] == 'LONG']
                            exit_signals = [s for s in symbol_signals if s['action'] == 'EXIT']
                            
                            # Add long signals
                            if long_signals:
                                fig.add_trace(go.Scatter(
                                    x=[datetime.fromisoformat(s['timestamp']) for s in long_signals],
                                    y=[s['price'] for s in long_signals],
                                    mode='markers',
                                    name='LONG',
                                    marker=dict(
                                        symbol='triangle-up',
                                        size=15,
                                        color='#00ff00',
                                    )
                                ))
                            
                            # Add exit signals
                            if exit_signals:
                                fig.add_trace(go.Scatter(
                                    x=[datetime.fromisoformat(s['timestamp']) for s in exit_signals],
                                    y=[s['price'] for s in exit_signals],
                                    mode='markers',
                                    name='EXIT',
                                    marker=dict(
                                        symbol='triangle-down',
                                        size=15,
                                        color='#ff4444',
                                    )
                                ))
                        
                        # Update layout
                        fig.update_layout(
                            title=f"{symbol} - Hourly",
                            yaxis_title="Price ($)",
                            xaxis_title="Time",
                            template="plotly_dark",
                            height=400,
                            showlegend=True,
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        # Simple metric if no historical data
                        if symbol in status.get('latest_prices', {}):
                            current = status['latest_prices'][symbol]
                            
                            # Get latest candle data if available
                            candle_key = f'{symbol}_latest_candle'
                            if candle_key in status:
                                candle = status[candle_key]
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Open", f"${candle['open']:.2f}")
                                with col2:
                                    st.metric("High", f"${candle['high']:.2f}")
                                with col3:
                                    st.metric("Low", f"${candle['low']:.2f}")
                                with col4:
                                    st.metric("Close", f"${current:.2f}")
                            else:
                                st.metric(f"Current Price", f"${current:.2f}")
    
    with main_col2:
        # Recent Signals Feed
        st.subheader("📈 Live Signal Feed")
        
        signal_container = st.container(height=500)
        
        with signal_container:
            if signals:
                # Show last 20 signals, most recent first
                recent_signals = sorted(signals, key=lambda x: x['timestamp'], reverse=True)[:20]
                
                for sig in recent_signals:
                    sig_time = datetime.fromisoformat(sig['timestamp'])
                    time_str = sig_time.strftime('%H:%M:%S')
                    
                    # Style based on action
                    if sig['action'] == 'LONG':
                        st.markdown(f"""
                        <div class='signal-long'>
                            <strong>🟢 LONG - {sig['symbol']}</strong><br/>
                            Time: {time_str}<br/>
                            Price: ${sig['price']:.2f}<br/>
                            Confidence: {sig['confidence']:.3f}
                        </div>
                        """, unsafe_allow_html=True)
                    elif sig['action'] == 'EXIT':
                        st.markdown(f"""
                        <div class='signal-exit'>
                            <strong>🔴 EXIT - {sig['symbol']}</strong><br/>
                            Time: {time_str}<br/>
                            Price: ${sig['price']:.2f}<br/>
                            Confidence: {sig['confidence']:.3f}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class='signal-hold'>
                            <strong>⚪ HOLD - {sig['symbol']}</strong><br/>
                            Time: {time_str}<br/>
                            Price: ${sig['price']:.2f}<br/>
                            Confidence: {sig['confidence']:.3f}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No signals generated today. Waiting for market activity...")
    
    # Performance Analytics Section
    st.markdown("---")
    st.subheader("📊 Performance Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Signal Distribution Pie Chart
        if signals:
            signal_types = {'LONG': 0, 'EXIT': 0, 'HOLD': 0}
            for sig in signals:
                if sig['action'] in signal_types:
                    signal_types[sig['action']] += 1
            
            if sum(signal_types.values()) > 0:
                fig = go.Figure(data=[go.Pie(
                    labels=list(signal_types.keys()),
                    values=list(signal_types.values()),
                    marker=dict(colors=['#00ff00', '#ff4444', '#888888']),
                    hole=0.3
                )])
                
                fig.update_layout(
                    title="Signal Distribution",
                    template="plotly_dark",
                    height=300,
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Hourly Activity
        if signals:
            hours = [datetime.fromisoformat(s['timestamp']).hour for s in signals]
            hour_counts = pd.Series(hours).value_counts().sort_index()
            
            fig = go.Figure(data=[go.Bar(
                x=hour_counts.index,
                y=hour_counts.values,
                marker_color='#00ffff'
            )])
            
            fig.update_layout(
                title="Signals by Hour (ET)",
                xaxis_title="Hour",
                yaxis_title="Count",
                template="plotly_dark",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        # Symbol Activity
        if signals:
            symbol_counts = {}
            for sig in signals:
                sym = sig['symbol']
                symbol_counts[sym] = symbol_counts.get(sym, 0) + 1
            
            if symbol_counts:
                fig = go.Figure(data=[go.Bar(
                    x=list(symbol_counts.keys()),
                    y=list(symbol_counts.values()),
                    marker_color='#ff00ff'
                )])
                
                fig.update_layout(
                    title="Signals by Symbol",
                    xaxis_title="Symbol",
                    yaxis_title="Count",
                    template="plotly_dark",
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # ML Model Confidence Section
    if signals and len(signals) > 0:
        latest_signals = sorted(signals, key=lambda x: x['timestamp'], reverse=True)[:5]
        
        st.markdown("---")
        st.subheader("🧠 Latest ML Model Confidence Scores")
        
        score_cols = st.columns(len(ASSETS))
        
        for idx, symbol in enumerate(ASSETS):
            with score_cols[idx]:
                # Find latest signal for this symbol
                symbol_signal = next((s for s in latest_signals if s['symbol'] == symbol), None)
                
                if symbol_signal and 'ml_scores' in symbol_signal:
                    scores = symbol_signal['ml_scores']
                    
                    # Create a small bar chart for scores
                    score_data = []
                    for model, score in scores.items():
                        if isinstance(score, (int, float)):
                            score_data.append({'Model': model.replace('_', ' ').upper(), 'Score': score})
                    
                    if score_data:
                        df_scores = pd.DataFrame(score_data)
                        
                        fig = go.Figure(data=[go.Bar(
                            x=df_scores['Model'],
                            y=df_scores['Score'],
                            marker_color=['#00ff00' if s > 0.5 else '#ff4444' for s in df_scores['Score']],
                            text=[f"{s:.2f}" for s in df_scores['Score']],
                            textposition='auto',
                        )])
                        
                        fig.update_layout(
                            title=f"{symbol}",
                            yaxis_range=[0, 1],
                            template="plotly_dark",
                            height=200,
                            showlegend=False,
                            margin=dict(l=0, r=0, t=30, b=0)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"{symbol}\nNo recent signal")
    
    # Footer
    st.markdown("---")
    st.caption(f"""
    🤖 ML Trading System Dashboard | 
    Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
    Auto-refresh: Every 5 seconds | 
    Data: Polygon + Alpaca APIs
    """)
    
    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()