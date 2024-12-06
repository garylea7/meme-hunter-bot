import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import asyncio
from whale_tracker import WhaleTracker

# Page config
st.set_page_config(
    page_title="Whale Tracker Dashboard",
    page_icon="🐋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E88E5;
        color: white;
    }
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .whale-card {
        background-color: #262626;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .meme-card {
        background-color: #2D2D2D;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1E88E5;
    }
    .trade-card {
        background-color: #2D2D2D;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class WhaleTrackerGUI:
    def __init__(self):
        self.tracker = WhaleTracker()
        if 'whale_alerts' not in st.session_state:
            st.session_state.whale_alerts = []
        if 'meme_alerts' not in st.session_state:
            st.session_state.meme_alerts = []
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = {
                'memory_usage': [],
                'cpu_usage': [],
                'network_latency': [],
                'rpc_stats': {},
                'vpn_status': 'disconnected'
            }
        
        # Initialize test mode
        self.test_mode = False
        self.test_balance = 500  # Default test balance
        self.test_trades = []

    def render_sidebar(self):
        with st.sidebar:
            st.title("🐋 Settings")
            
            st.subheader("Wallet Tracking")
            min_win_rate = st.slider("Min Win Rate (7D)", 0.0, 1.0, 0.5, 0.05)
            min_profit = st.slider("Min Profit (30D)", 5.0, 20.0, 10.0, 0.5)
            min_transactions = st.number_input("Min Transactions", 10, 100, 20)
            
            st.subheader("Token Metrics")
            max_dev_holding = st.slider("Max Dev Holding", 0.0, 0.2, 0.1, 0.01)
            min_holders = st.number_input("Min Holders", 10, 200, 50)
            max_top10_holdings = st.slider("Max Top 10 Holdings", 0.0, 0.3, 0.15, 0.01)
            
            st.subheader("Telegram Notifications")
            telegram_enabled = st.toggle("Enable Telegram", True)
            if telegram_enabled:
                telegram_token = st.text_input("Bot Token", type="password")
                telegram_chat = st.text_input("Chat ID")
                if st.button("Test Connection"):
                    asyncio.run(self.tracker.setup_telegram(telegram_token, telegram_chat))

    def render_metrics_cards(self):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>Active Whales</h3>
                <h2>24</h2>
                <p>↑ 4 new today</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>Tracked Tokens</h3>
                <h2>156</h2>
                <p>↑ 12 new today</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>Viral Memes</h3>
                <h2>8</h2>
                <p>↑ 3 trending</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>Profit/Loss</h3>
                <h2>+284%</h2>
                <p>↑ 24hr change</p>
            </div>
            """, unsafe_allow_html=True)

    def render_whale_activity(self):
        # Sample whale activity data
        whale_data = pd.DataFrame({
            'Time': pd.date_range(start='2024-01-01', periods=24, freq='H'),
            'Token': ['TOKEN' + str(i%5) for i in range(24)],
            'Action': ['Buy' if i%3 else 'Sell' for i in range(24)],
            'Amount': [10000 + i*1000 for i in range(24)],
            'Price': [1 + i*0.1 for i in range(24)]
        })
        
        fig = go.Figure()
        
        # Add buy transactions
        buys = whale_data[whale_data['Action'] == 'Buy']
        fig.add_trace(go.Scatter(
            x=buys['Time'],
            y=buys['Amount'],
            mode='markers',
            name='Buys',
            marker=dict(
                size=10,
                color='green',
                symbol='triangle-up'
            )
        ))
        
        # Add sell transactions
        sells = whale_data[whale_data['Action'] == 'Sell']
        fig.add_trace(go.Scatter(
            x=sells['Time'],
            y=sells['Amount'],
            mode='markers',
            name='Sells',
            marker=dict(
                size=10,
                color='red',
                symbol='triangle-down'
            )
        ))
        
        fig.update_layout(
            title='Whale Activity (24h)',
            xaxis_title='Time',
            yaxis_title='Transaction Amount ($)',
            template='plotly_dark',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def render_meme_trends(self):
        # Sample meme trend data
        meme_data = pd.DataFrame({
            'Meme': ['BONK', 'WIF', 'POPCAT', 'DOGE', 'PEPE'],
            'Virality': [85, 76, 72, 68, 65],
            'Growth': [120, 95, 88, 75, 70],
            'Platforms': [5, 4, 4, 3, 3]
        })
        
        fig = px.bar(
            meme_data,
            x='Meme',
            y=['Virality', 'Growth'],
            barmode='group',
            title='Top Trending Memes',
            template='plotly_dark'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    def render_whale_list(self):
        st.subheader("Top Performing Whales")
        
        cols = st.columns(2)
        for i in range(6):  # Show top 6 whales
            with cols[i % 2]:
                st.markdown(f"""
                <div class="whale-card">
                    <h4>🐋 Whale #{i+1}</h4>
                    <p><b>Address:</b> 0x7a...{i}f2</p>
                    <p><b>Win Rate:</b> {85+i}%</p>
                    <p><b>Profit (30D):</b> +{1200+i*100}%</p>
                    <p><b>Score:</b> {95-i}</p>
                </div>
                """, unsafe_allow_html=True)

    def render_alerts(self):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Recent Whale Alerts")
            for alert in st.session_state.whale_alerts[-5:]:
                st.markdown(f"""
                <div class="whale-card">
                    <p>{alert}</p>
                </div>
                """, unsafe_allow_html=True)
                
        with col2:
            st.subheader("Meme Alerts")
            for alert in st.session_state.meme_alerts[-5:]:
                st.markdown(f"""
                <div class="meme-card">
                    <p>{alert}</p>
                </div>
                """, unsafe_allow_html=True)

    def render_performance_metrics(self):
        """Render performance monitoring section"""
        st.subheader("System Performance")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Memory Usage",
                f"{st.session_state.performance_metrics['memory_usage'][-1]:.1f}MB" 
                if st.session_state.performance_metrics['memory_usage'] else "N/A"
            )
            
        with col2:
            st.metric(
                "CPU Usage",
                f"{st.session_state.performance_metrics['cpu_usage'][-1]:.1f}%" 
                if st.session_state.performance_metrics['cpu_usage'] else "N/A"
            )
            
        with col3:
            st.metric(
                "Network Latency",
                f"{st.session_state.performance_metrics['network_latency'][-1]:.0f}ms" 
                if st.session_state.performance_metrics['network_latency'] else "N/A"
            )
        
        # RPC Status
        st.subheader("RPC Endpoints Status")
        for endpoint, stats in st.session_state.performance_metrics['rpc_stats'].items():
            st.progress(
                1 - (stats['fails'] / 5),  # 5 max fails
                text=f"{endpoint}: {stats['fails']} fails"
            )
        
        # VPN Status
        st.info(f"VPN Status: {st.session_state.performance_metrics['vpn_status']}")

    def render_test_mode_section(self):
        """Render test mode controls and stats"""
        st.subheader("Test Mode")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self.test_mode = st.toggle("Enable Test Mode", self.test_mode)
            if self.test_mode:
                self.test_balance = st.number_input(
                    "Test Balance (USDC)",
                    min_value=100,
                    max_value=10000,
                    value=500
                )
                
        with col2:
            if self.test_mode:
                st.metric("Test Balance", f"${self.test_balance:.2f}")
                st.metric(
                    "24h P/L",
                    f"{self.calculate_test_pnl():.1f}%",
                    delta=f"{self.calculate_test_pnl(1):.1f}%"
                )
        
        if self.test_mode and self.test_trades:
            st.subheader("Test Trades")
            for trade in self.test_trades[-5:]:
                st.markdown(f"""
                <div class="trade-card">
                    <p><b>Token:</b> {trade['token']}</p>
                    <p><b>Type:</b> {trade['type']}</p>
                    <p><b>Amount:</b> ${trade['amount']:.2f}</p>
                    <p><b>P/L:</b> {trade['pnl']:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)

    def calculate_test_pnl(self, hours=24):
        """Calculate test P/L for given timeframe"""
        if not self.test_trades:
            return 0.0
            
        relevant_trades = [
            t for t in self.test_trades
            if t['timestamp'] > datetime.now() - timedelta(hours=hours)
        ]
        
        if not relevant_trades:
            return 0.0
            
        total_pnl = sum(t['pnl'] for t in relevant_trades)
        return total_pnl

    def main(self):
        st.title("🐋 Whale Tracker Dashboard")
        
        # Add performance monitoring
        self.render_performance_metrics()
        
        # Add test mode section
        self.render_test_mode_section()
        
        # Render sidebar
        self.render_sidebar()
        
        # Main tabs
        tab1, tab2, tab3 = st.tabs(["Overview", "Whale Analysis", "Meme Tracker"])
        
        with tab1:
            # Metrics overview
            self.render_metrics_cards()
            
            # Charts
            col1, col2 = st.columns(2)
            with col1:
                self.render_whale_activity()
            with col2:
                self.render_meme_trends()
                
            # Recent alerts
            self.render_alerts()
            
        with tab2:
            # Whale analysis tab
            self.render_whale_list()
            
            # Additional whale metrics
            st.subheader("Whale Performance Metrics")
            metrics_tab1, metrics_tab2 = st.tabs(["Entry Analysis", "Exit Analysis"])
            
            with metrics_tab1:
                entry_data = pd.DataFrame({
                    'Time': pd.date_range(start='2024-01-01', periods=100, freq='H'),
                    'Entry Price': [1 + i*0.01 for i in range(100)]
                })
                
                fig = px.line(
                    entry_data,
                    x='Time',
                    y='Entry Price',
                    title='Entry Price Analysis',
                    template='plotly_dark'
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with metrics_tab2:
                exit_data = pd.DataFrame({
                    'Time': pd.date_range(start='2024-01-01', periods=100, freq='H'),
                    'Exit Price': [2 + i*0.02 for i in range(100)]
                })
                
                fig = px.line(
                    exit_data,
                    x='Time',
                    y='Exit Price',
                    title='Exit Price Analysis',
                    template='plotly_dark'
                )
                st.plotly_chart(fig, use_container_width=True)
            
        with tab3:
            # Meme tracker tab
            st.subheader("Trending Memes Analysis")
            
            # Platform distribution
            platform_data = pd.DataFrame({
                'Platform': ['Twitter', 'TikTok', 'Telegram', 'Reddit', 'YouTube'],
                'Mentions': [1200, 980, 750, 500, 300]
            })
            
            fig = px.pie(
                platform_data,
                values='Mentions',
                names='Platform',
                title='Meme Mentions by Platform',
                template='plotly_dark'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Meme timeline
            timeline_data = pd.DataFrame({
                'Time': pd.date_range(start='2024-01-01', periods=48, freq='H'),
                'Virality': [50 + i + (i%5)*10 for i in range(48)]
            })
            
            fig = px.line(
                timeline_data,
                x='Time',
                y='Virality',
                title='Meme Virality Timeline',
                template='plotly_dark'
            )
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    gui = WhaleTrackerGUI()
    gui.main()
