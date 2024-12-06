import streamlit as st
import plotly.graph_objs as go
from datetime import datetime
import pandas as pd
from .analytics_dashboard import TradingDashboard
from .copy_trader import CopyTrader
import asyncio

def run_dashboard():
    # Page config
    st.set_page_config(
        page_title="Trading Bot Dashboard",
        layout="wide",
        menu_items={'About': 'Trading Bot Analytics Dashboard'}
    )
    
    # Initialize the dashboard backend
    dashboard = TradingDashboard()
    
    # Header
    st.title("Trading Bot Analytics Dashboard")
    st.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Tabs for different sections
    tab1, tab2 = st.tabs(["Trading Analytics", "Copy Trading"])
    
    with tab1:
        try:
            # Key Metrics Row
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_value = dashboard.get_portfolio_value()
                st.metric("Total Portfolio Value", f"{total_value:.2f} SOL")
                
            with col2:
                change_24h = dashboard.get_24h_change()
                st.metric("24h Change", f"{change_24h:+.2f}%")
                
            with col3:
                total_pnl = dashboard.get_total_pnl()
                st.metric("Total P/L", f"${total_pnl:+,.2f}")
            
            # Active Positions
            st.subheader("Active Positions")
            positions = dashboard.get_active_positions()
            if positions:
                df_positions = pd.DataFrame(positions)
                st.dataframe(df_positions)
            else:
                st.info("No active positions")
            
            # Trading Performance
            st.subheader("Trading Performance")
            win_loss = dashboard.get_win_loss_ratio()
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Win Rate", f"{win_loss['ratio']*100:.1f}%")
                
            with col2:
                st.metric("Total Trades", f"{win_loss['wins'] + win_loss['losses']}")
                
            # Add refresh button
            if st.button('Refresh Data'):
                st.experimental_rerun()
                
        except Exception as e:
            st.error(f"Error updating dashboard: {str(e)}")
            
    with tab2:
        st.header("Copy Trading")
        
        # Test mode toggle
        test_mode = st.toggle("Test Mode", value=True, help="Run in test mode with simulated trades")
        
        # Initialize copy trader
        if 'copy_trader' not in st.session_state or st.session_state.get('test_mode') != test_mode:
            st.session_state.copy_trader = CopyTrader(test_mode=test_mode)
            st.session_state.test_mode = test_mode
            
        # Test mode performance metrics
        if test_mode:
            st.subheader("Test Mode Performance")
            metrics = st.session_state.copy_trader.get_test_performance()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Test Balance", f"${metrics['current_balance']:.2f}")
            with col2:
                st.metric("ROI", f"{metrics['roi']:.2f}%")
            with col3:
                st.metric("Win Rate", f"{metrics['win_rate']*100:.1f}%" if metrics['total_trades'] > 0 else "N/A")
            
            # Show recent test trades
            if st.session_state.copy_trader.test_trades:
                st.subheader("Recent Test Trades")
                df_trades = pd.DataFrame(st.session_state.copy_trader.test_trades)
                df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp'])
                df_trades = df_trades.sort_values('timestamp', ascending=False)
                st.dataframe(df_trades)
        
        # Find traders section
        st.subheader("Find Traders to Copy")
        if st.button("Find Top Traders"):
            with st.spinner("Finding successful traders..."):
                # Run async code in sync context
                traders = asyncio.run(st.session_state.copy_trader.find_traders_to_copy())
                st.session_state.found_traders = traders
                
        if 'found_traders' in st.session_state and st.session_state.found_traders:
            for trader in st.session_state.found_traders:
                with st.expander(f"Trader {trader['address'][:8]}...{trader['address'][-6:]}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Score", f"{trader['score']:.2f}")
                        st.metric("Win Rate (30d)", f"{trader['stats'].get('win_rate_30d', 0):.2%}")
                    with col2:
                        st.metric("Profit (30d)", f"{trader['stats'].get('profit_30d', 0):.2%}")
                        st.metric("Total Trades", trader['stats'].get('total_trades', 0))
                    
                    # Recommendation
                    rec = trader['recommendation']
                    st.info(f"**Recommendation:** {rec['action']} | Confidence: {rec['confidence']} | Suggested Allocation: {rec['allocation']}")
                    
                    if st.button("Follow Trader", key=trader['address']):
                        st.session_state.copy_trader.followed_traders.add(trader['address'])
                        st.success("Now following trader!")
        
        # Followed traders section
        if st.session_state.copy_trader.followed_traders:
            st.subheader("Currently Following")
            for address in st.session_state.copy_trader.followed_traders:
                st.text(f"Trader: {address[:8]}...{address[-6:]}")
                if st.button("Unfollow", key=f"unfollow_{address}"):
                    st.session_state.copy_trader.followed_traders.remove(address)
                    st.success("Trader unfollowed!")

if __name__ == "__main__":
    run_dashboard()
