import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import json
import time
from datetime import datetime, timedelta
from solana_arbitrage_bot import SolanaArbitrageBot
import random
import numpy as np

# Page config
st.set_page_config(
    page_title="Solana Flash Arbitrage",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .profit { color: #00ff00; }
    .loss { color: #ff0000; }
    .warning { color: #ffbb00; }
    .info { color: #00bbff; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0px 24px;
        background-color: #1e1e1e;
        border-radius: 5px;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

class ArbitrageGUI:
    def __init__(self):
        self.bot = SolanaArbitrageBot()
        self.practice_trades = []
        self.real_trades = []
        self.practice_balance = 1000  # Start with 1000 USDC
        
    def run(self):
        st.title("🚀 Solana Flash Arbitrage Dashboard")
        
        # Sidebar
        with st.sidebar:
            st.header("Settings")
            min_profit = st.slider("Minimum Profit (USDC)", 1, 100, 10)
            update_interval = st.slider("Update Interval (sec)", 1, 10, 2)
            
            st.header("Practice Account")
            st.metric("Practice Balance", f"${self.practice_balance:.2f} USDC")
            
            if st.button("Reset Practice Account"):
                self.practice_balance = 1000
                self.practice_trades = []
        
        # Main tabs
        tab1, tab2, tab3 = st.tabs(["🔥 Live Opportunities", "📈 Practice Mode", "📊 Analytics"])
        
        with tab1:
            self.show_live_opportunities()
            
        with tab2:
            self.show_practice_mode()
            
        with tab3:
            self.show_analytics()
    
    def show_live_opportunities(self):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Real-time Arbitrage Opportunities")
            opportunities = asyncio.run(self.bot.find_arbitrage_opportunity())
            
            if opportunities:
                for opp in opportunities:
                    with st.expander(f"💰 {opp['pair']} - Profit: ${opp['potential_profit']:.2f}", expanded=True):
                        cols = st.columns(3)
                        with cols[0]:
                            st.markdown(f"**Buy from:** {opp['buy_dex']}")
                            st.markdown(f"**Price:** ${opp['buy_price']:.4f}")
                        with cols[1]:
                            st.markdown(f"**Sell to:** {opp['sell_dex']}")
                            st.markdown(f"**Price:** ${opp['sell_price']:.4f}")
                        with cols[2]:
                            profit_color = "profit" if opp['potential_profit'] > 0 else "loss"
                            st.markdown(f"**Profit:** <span class='{profit_color}'>${opp['potential_profit']:.2f}</span>", unsafe_allow_html=True)
                            
                            # Risk assessment
                            risk_score = self.calculate_risk_score(opp)
                            risk_color = "profit" if risk_score < 30 else "warning" if risk_score < 70 else "loss"
                            st.markdown(f"**Risk Score:** <span class='{risk_color}'>{risk_score}%</span>", unsafe_allow_html=True)
                            
                            if st.button("Execute Trade", key=f"trade_{opp['pair']}"):
                                st.markdown("Opening Phantom Wallet...")
            else:
                st.info("No profitable opportunities found at the moment...")
        
        with col2:
            st.subheader("Market Overview")
            self.show_market_overview()
    
    def show_practice_mode(self):
        st.subheader("Practice Trading")
        
        # Generate some simulated opportunities
        sim_opportunities = self.generate_simulated_opportunities()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Simulated Opportunities")
            for opp in sim_opportunities:
                with st.expander(f"💫 {opp['pair']} - Potential: ${opp['potential_profit']:.2f}", expanded=True):
                    cols = st.columns(3)
                    with cols[0]:
                        st.markdown(f"**Buy from:** {opp['buy_dex']}")
                        st.markdown(f"**Price:** ${opp['buy_price']:.4f}")
                    with cols[1]:
                        st.markdown(f"**Sell to:** {opp['sell_dex']}")
                        st.markdown(f"**Price:** ${opp['sell_price']:.4f}")
                    with cols[2]:
                        st.markdown(f"**Potential Profit:** ${opp['potential_profit']:.2f}")
                        
                        if st.button("Practice Trade", key=f"practice_{opp['pair']}"):
                            success_rate = random.uniform(0, 1)
                            if success_rate > 0.3:  # 70% success rate
                                profit = opp['potential_profit']
                                self.practice_balance += profit
                                self.practice_trades.append({
                                    'timestamp': datetime.now(),
                                    'pair': opp['pair'],
                                    'profit': profit,
                                    'success': True
                                })
                                st.success(f"Trade successful! Profit: ${profit:.2f}")
                            else:
                                loss = opp['potential_profit'] * random.uniform(0.5, 1.0)
                                self.practice_balance -= loss
                                self.practice_trades.append({
                                    'timestamp': datetime.now(),
                                    'pair': opp['pair'],
                                    'profit': -loss,
                                    'success': False
                                })
                                st.error(f"Trade failed! Loss: ${loss:.2f}")
        
        with col2:
            st.markdown("### Practice Performance")
            self.show_practice_performance()
    
    def show_analytics(self):
        st.subheader("Trading Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Profit/Loss Over Time")
            if self.practice_trades:
                df = pd.DataFrame(self.practice_trades)
                df['cumulative_profit'] = df['profit'].cumsum()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['cumulative_profit'],
                    mode='lines+markers',
                    name='P&L',
                    line=dict(color='#00ff00' if df['cumulative_profit'].iloc[-1] > 0 else '#ff0000')
                ))
                fig.update_layout(
                    title='Cumulative Profit/Loss',
                    xaxis_title='Trades',
                    yaxis_title='USDC',
                    template='plotly_dark'
                )
                st.plotly_chart(fig)
            else:
                st.info("No practice trades yet...")
        
        with col2:
            st.markdown("### Success Rate")
            if self.practice_trades:
                success_rate = len([t for t in self.practice_trades if t['success']]) / len(self.practice_trades) * 100
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = success_rate,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#00ff00"},
                        'steps': [
                            {'range': [0, 50], 'color': "#ff0000"},
                            {'range': [50, 80], 'color': "#ffbb00"},
                            {'range': [80, 100], 'color': "#00ff00"}
                        ]
                    }
                ))
                fig.update_layout(title='Trade Success Rate (%)')
                st.plotly_chart(fig)
            else:
                st.info("No practice trades yet...")
    
    def show_market_overview(self):
        # Create a sample market overview with random data
        fig = make_subplots(rows=2, cols=1)
        
        # Price chart
        times = pd.date_range(start='now', periods=50, freq='1min').strftime('%H:%M').tolist()
        prices = np.random.normal(100, 2, 50).cumsum()
        
        fig.add_trace(
            go.Scatter(x=times, y=prices, name="Market Price"),
            row=1, col=1
        )
        
        # Volume bars
        volumes = np.random.uniform(1000, 5000, 50)
        fig.add_trace(
            go.Bar(x=times, y=volumes, name="Volume"),
            row=2, col=1
        )
        
        fig.update_layout(
            height=400,
            template='plotly_dark',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def show_practice_performance(self):
        if self.practice_trades:
            total_trades = len(self.practice_trades)
            successful_trades = len([t for t in self.practice_trades if t['success']])
            total_profit = sum([t['profit'] for t in self.practice_trades])
            
            metrics = {
                "Total Trades": total_trades,
                "Success Rate": f"{(successful_trades/total_trades)*100:.1f}%",
                "Total P/L": f"${total_profit:.2f}"
            }
            
            for label, value in metrics.items():
                st.metric(label, value)
        else:
            st.info("No practice trades yet...")
    
    def calculate_risk_score(self, opportunity):
        """Calculate a risk score for an opportunity"""
        # This is a simplified risk calculation
        # In production, you'd want more sophisticated metrics
        risk_factors = [
            random.uniform(0, 20),  # Market volatility
            random.uniform(0, 20),  # Liquidity risk
            random.uniform(0, 20),  # Execution risk
            random.uniform(0, 20),  # Price impact
            random.uniform(0, 20)   # Smart contract risk
        ]
        return sum(risk_factors)
    
    def generate_simulated_opportunities(self):
        """Generate simulated trading opportunities for practice mode"""
        opportunities = []
        pairs = ["SOL-USDC", "RAY-USDC", "SRM-USDC", "ORCA-USDC"]
        dexes = ["Raydium", "Orca", "Serum"]
        
        for _ in range(random.randint(2, 5)):
            pair = random.choice(pairs)
            base_price = random.uniform(10, 100)
            price_diff = random.uniform(0.1, 2.0)
            
            buy_dex, sell_dex = random.sample(dexes, 2)
            
            opportunities.append({
                'pair': pair,
                'buy_dex': buy_dex,
                'sell_dex': sell_dex,
                'buy_price': base_price,
                'sell_price': base_price + price_diff,
                'potential_profit': price_diff * random.uniform(0.8, 1.2)
            })
        
        return opportunities

if __name__ == "__main__":
    gui = ArbitrageGUI()
    gui.run()
