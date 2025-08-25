"""
ML Trading System - Real-Time Dashboard
Live monitoring with 2-minute price updates
"""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time

# Page configuration
st.set_page_config(
    page_title="ML Trading Dashboard - LIVE",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional dark theme
st.markdown("""
<style>
    /* Dark theme */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Price update indicator */
    .live-indicator {
        animation: pulse 2s infinite;
        color: #00ff00;
        font-weight: bold;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1e1e1e, #2a2a2a);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        margin: 10px 0;
    }
    
    /* Headers */
    h1 {
        color: #00ff00 !important;
        text-align: center;
        font-family: 'Courier New', monospace;
        text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
    }
    
    /* Position cards */
    .position-card {
        background: #1a1a1a;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #00ff00;
        margin: 5px 0;
    }
    
    .position-card.short {
        border-left-color: #ff4444;
    }
    
    .position-card.flat {
        border-left-color: #888888;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for tracking signals
if 'previous_signals' not in st.session_state:
    st.session_state.previous_signals = set()
if 'sound_played' not in st.session_state:
    st.session_state.sound_played = False

# Define assets
ASSETS = ['TSLA', 'HOOD', 'COIN', 'PLTR', 'AAPL']

# Helper function to play notification sound
def play_notification_sound(signal_type='LONG'):
    """Play a notification sound using JavaScript with minimal ping style"""
    if signal_type == 'LONG':
        # LONG Signal - Higher pitch (C6 with C5 octave)
        sound_script = """
        <script>
        var audioContext = new (window.AudioContext || window.webkitAudioContext)();
        var now = audioContext.currentTime;
        
        // Primary tone - C6
        var osc = audioContext.createOscillator();
        var gain = audioContext.createGain();
        var filter = audioContext.createBiquadFilter();
        
        osc.connect(filter);
        filter.connect(gain);
        gain.connect(audioContext.destination);
        
        filter.type = 'lowpass';
        filter.frequency.value = 4000;
        filter.Q.value = 0.1;
        
        osc.frequency.value = 1046.50; // C6
        osc.type = 'sine';
        
        gain.gain.setValueAtTime(0, now);
        gain.gain.linearRampToValueAtTime(0.3, now + 0.008);
        gain.gain.exponentialRampToValueAtTime(0.12, now + 0.05);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
        
        osc.start(now);
        osc.stop(now + 0.25);
        
        // Subtle octave below - C5
        var octave = audioContext.createOscillator();
        var octaveGain = audioContext.createGain();
        octave.connect(octaveGain);
        octaveGain.connect(audioContext.destination);
        octave.frequency.value = 523.25; // C5
        octave.type = 'sine';
        octaveGain.gain.setValueAtTime(0, now);
        octaveGain.gain.linearRampToValueAtTime(0.09, now + 0.01);
        octaveGain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
        octave.start(now);
        octave.stop(now + 0.2);
        </script>
        """
    else:  # EXIT signal
        # EXIT Signal - Lower pitch (F5 with F4 octave)
        sound_script = """
        <script>
        var audioContext = new (window.AudioContext || window.webkitAudioContext)();
        var now = audioContext.currentTime;
        
        // Primary tone - F5
        var osc = audioContext.createOscillator();
        var gain = audioContext.createGain();
        var filter = audioContext.createBiquadFilter();
        
        osc.connect(filter);
        filter.connect(gain);
        gain.connect(audioContext.destination);
        
        filter.type = 'lowpass';
        filter.frequency.value = 3500;
        filter.Q.value = 0.1;
        
        osc.frequency.value = 698.46; // F5
        osc.type = 'sine';
        
        gain.gain.setValueAtTime(0, now);
        gain.gain.linearRampToValueAtTime(0.3, now + 0.008);
        gain.gain.exponentialRampToValueAtTime(0.12, now + 0.06);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
        
        osc.start(now);
        osc.stop(now + 0.3);
        
        // Subtle octave below - F4
        var octave = audioContext.createOscillator();
        var octaveGain = audioContext.createGain();
        octave.connect(octaveGain);
        octaveGain.connect(audioContext.destination);
        octave.frequency.value = 349.23; // F4
        octave.type = 'sine';
        octaveGain.gain.setValueAtTime(0, now);
        octaveGain.gain.linearRampToValueAtTime(0.09, now + 0.01);
        octaveGain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
        octave.start(now);
        octave.stop(now + 0.25);
        </script>
        """
    
    st.components.v1.html(sound_script, height=0)

# Helper functions
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

def check_for_new_signals(signals):
    """Check if there are new non-HOLD signals and play sound if needed"""
    if not signals:
        return
    
    # Create a set of current signal identifiers (excluding HOLD signals)
    current_signals = set()
    latest_signal_type = None
    
    for sig in signals:
        if sig['action'] != 'HOLD':
            # Create unique identifier for each signal
            sig_id = f"{sig['symbol']}_{sig['action']}_{sig['timestamp']}"
            current_signals.add(sig_id)
            
            # Track the type of the newest signal
            if sig_id not in st.session_state.previous_signals:
                latest_signal_type = sig['action']
    
    # Check if there are new signals
    new_signals = current_signals - st.session_state.previous_signals
    
    if new_signals and st.session_state.previous_signals:  # Don't play on first load
        # Play sound based on the latest signal type
        if latest_signal_type:
            play_notification_sound(signal_type=latest_signal_type)
    
    # Update the stored signals
    st.session_state.previous_signals = current_signals

def get_market_status():
    """Get current market status"""
    now = datetime.now(timezone(timedelta(hours=-4)))  # ET
    weekday = now.weekday()
    current_time = now.time()
    
    from datetime import time as dt_time
    
    if weekday >= 5:
        return "🔴 WEEKEND", "#ff4444"
    elif current_time < dt_time(9, 30):
        return "🟡 PRE-MARKET", "#ffaa00"
    elif current_time >= dt_time(16, 0):
        return "🟠 AFTER-HOURS", "#ff8800"
    elif dt_time(9, 30) <= current_time < dt_time(16, 0):
        return "🟢 MARKET OPEN", "#00ff00"
    else:
        return "🔴 MARKET CLOSED", "#ff4444"

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
        return f'<span style="color: {color}">{symbol}{value:.2f}%</span>'
    else:
        return f'<span style="color: {color}">{symbol}${value:.2f}</span>'

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
    # Use container to prevent flickering
    placeholder = st.empty()
    
    with placeholder.container():
        # Header
        st.markdown("<h1>🚀 REAL-TIME ML TRADING DASHBOARD</h1>", unsafe_allow_html=True)
        
        # Load all data
        status = load_status()
        realtime_prices = load_realtime_prices()
        signals = load_signals()
        
        # Check for new signals and play sound if needed
        check_for_new_signals(signals)
        
        if not status:
            st.warning("⚠️ No status data. Make sure the trading system is running.")
            time.sleep(1)
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
            # Price update indicator
            if 'last_update' in realtime_prices:
                last_update = datetime.fromisoformat(realtime_prices['last_update'])
                seconds_ago = (datetime.now(timezone.utc) - last_update).total_seconds()
                
                if seconds_ago < 150:  # Less than 2.5 minutes
                    st.markdown("""
                    <div style='text-align: center'>
                        <p style='margin: 0; color: #888'>Price Feed</p>
                        <h3 class='live-indicator'>● LIVE</h3>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='text-align: center'>
                        <p style='margin: 0; color: #888'>Price Feed</p>
                        <h3 style='color: #ffaa00'>● {int(seconds_ago/60)}m ago</h3>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col3:
            # Active positions
            active = sum(1 for p in status.get('positions', {}).values() if p['is_open'])
            st.metric("Active Positions", f"{active}/{len(ASSETS)}")
        
        with col4:
            # Today's signals
            total_signals = len(signals)
            long_signals = len([s for s in signals if s['action'] == 'LONG'])
            st.metric("Today's Signals", total_signals, delta=f"{long_signals} longs")
        
        with col5:
            # Total P&L
            total_pnl = 0
            if 'positions' in status:
                for pos in status['positions'].values():
                    if pos.get('realtime_pnl_pct'):
                        total_pnl += pos['realtime_pnl_pct']
            
            st.metric(
                "Total Open P&L",
                f"{total_pnl:+.2f}%",
                delta=None,
                delta_color="normal" if total_pnl >= 0 else "inverse"
            )
        
        with col6:
            # Win rate (simplified)
            exits = [s for s in signals if s['action'] == 'EXIT']
            st.metric("Closed Trades", len(exits))
        
        st.markdown("---")
        
        # Main content area
        main_col1, main_col2 = st.columns([3, 2])
        
        with main_col1:
            st.subheader("📊 Live Positions & Prices")
            
            # Create position cards with real-time prices
            for symbol in ASSETS:
                if symbol in status.get('positions', {}):
                    pos = status['positions'][symbol]
                    
                    # Get real-time price
                    current_price = 0
                    price_source = ""
                    
                    if 'prices' in realtime_prices and symbol in realtime_prices['prices']:
                        current_price = realtime_prices['prices'][symbol]
                        price_source = "LIVE"
                    elif 'realtime_prices' in status and symbol in status['realtime_prices']:
                        current_price = status['realtime_prices'][symbol]
                        price_source = "CACHED"
                    
                    # Create columns for position display
                    pcol1, pcol2, pcol3, pcol4 = st.columns([1, 2, 2, 2])
                    
                    with pcol1:
                        if pos['is_open']:
                            st.markdown(f"<h3 style='color: #00ff00'>🟢</h3>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<h3 style='color: #888'>⚪</h3>", unsafe_allow_html=True)
                    
                    with pcol2:
                        st.markdown(f"**{symbol}**")
                        if current_price > 0:
                            st.markdown(f"${current_price:.2f} <small style='color: #888'>({price_source})</small>", 
                                      unsafe_allow_html=True)
                    
                    with pcol3:
                        if pos['is_open']:
                            st.markdown(f"Entry: ${pos['entry_price']:.2f}")
                            if pos.get('realtime_pnl_pct'):
                                pnl_html = format_pnl(pos['realtime_pnl_pct'])
                                st.markdown(f"P&L: {pnl_html}", unsafe_allow_html=True)
                        else:
                            st.markdown("Position: FLAT")
                            st.markdown(f"<small style='color: #666'>Waiting for signal</small>", 
                                      unsafe_allow_html=True)
                    
                    with pcol4:
                        # Mini sparkline
                        if 'price_history' in realtime_prices and symbol in realtime_prices['price_history']:
                            fig = create_price_sparkline(realtime_prices['price_history'][symbol])
                            if fig:
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    
                    st.markdown("---")
            
            # Price chart
            st.subheader("💹 Price Action")
            
            # Tabs for each symbol
            tabs = st.tabs(ASSETS)
            
            for tab, symbol in zip(tabs, ASSETS):
                with tab:
                    # Create price chart with recent data
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
                            
                            # Add signals as annotations
                            symbol_signals = [s for s in signals if s['symbol'] == symbol]
                            for sig in symbol_signals:
                                color = '#00ff00' if sig['action'] == 'LONG' else '#ff4444'
                                symbol_mark = '▲' if sig['action'] == 'LONG' else '▼'
                                
                                fig.add_annotation(
                                    x=datetime.fromisoformat(sig['timestamp']),
                                    y=sig['price'],
                                    text=symbol_mark,
                                    showarrow=False,
                                    font=dict(size=20, color=color)
                                )
                            
                            fig.update_layout(
                                title=f"{symbol} - Real-Time (2-min updates)",
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
            st.subheader("📡 Live Signal Feed")
            
            # Signal feed
            if signals:
                recent_signals = sorted(signals, key=lambda x: x['timestamp'], reverse=True)[:10]
                
                for sig in recent_signals:
                    sig_time = datetime.fromisoformat(sig['timestamp'])
                    time_str = sig_time.strftime('%H:%M:%S')
                    
                    # Signal card
                    if sig['action'] == 'LONG':
                        st.success(f"🟢 **LONG** - {sig['symbol']} @ ${sig['price']:.2f}")
                    elif sig['action'] == 'EXIT':
                        st.error(f"🔴 **EXIT** - {sig['symbol']} @ ${sig['price']:.2f}")
                    else:
                        st.info(f"⚪ **HOLD** - {sig['symbol']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption(f"Time: {time_str}")
                    with col2:
                        st.caption(f"Confidence: {sig['confidence']:.3f}")
                    
                    st.markdown("---")
            else:
                st.info("No signals yet today")
            
            # Performance metrics
            st.subheader("📈 Performance")
            
            if 'positions' in status:
                # Calculate metrics
                total_value = 0
                total_pnl_dollar = 0
                
                for pos in status['positions'].values():
                    if pos.get('realtime_pnl_dollar'):
                        total_pnl_dollar += pos['realtime_pnl_dollar']
                
                metric1, metric2 = st.columns(2)
                
                with metric1:
                    st.metric("Day P&L", f"${total_pnl_dollar:+,.2f}")
                
                with metric2:
                    win_rate = 0  # Calculate from signals
                    st.metric("Win Rate", f"{win_rate:.1f}%")
        
        # Footer with update time
        st.markdown("---")
        
        update_info = []
        if 'timestamp' in status:
            update_info.append(f"System: {datetime.fromisoformat(status['timestamp']).strftime('%H:%M:%S')}")
        if 'last_update' in realtime_prices:
            update_info.append(f"Prices: {datetime.fromisoformat(realtime_prices['last_update']).strftime('%H:%M:%S')}")
        
        st.caption(f"""
        🚀 Real-Time ML Trading System | 
        Updates: {' | '.join(update_info)} | 
        Auto-refresh: 2 seconds | 
        Data: Alpaca Real-Time | 
        🔔 Sound notifications enabled
        """)
    
    # Auto-refresh
    time.sleep(2)
    st.rerun()

if __name__ == "__main__":
    main()
