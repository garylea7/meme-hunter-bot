import streamlit as st
import json
import time
from datetime import datetime
import pandas as pd

def load_data():
    try:
        with open('simulation_results.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        return {
            "wallet_balance": 500.00,
            "win_rate": 0.0,
            "active_positions": [],
            "recent_trades": [],
            "moonshots": 0,
            "total_trades": 0
        }

def main():
    st.set_page_config(
        page_title="MemeHunter Trading Bot",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Title with custom styling
    st.markdown("""
        <style>
        .big-font {
            font-size:50px !important;
            color: #1E88E5;
            text-align: center;
        }
        .metric-card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #1E88E5;
        }
        .metric-label {
            font-size: 16px;
            color: #666;
        }
        </style>
        <h1 class='big-font'>MemeHunter Trading Bot</h1>
        """, unsafe_allow_html=True)

    # Load latest data
    data = load_data()

    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
            <div class='metric-card'>
                <div class='metric-value'>$%.2f</div>
                <div class='metric-label'>Wallet Balance</div>
            </div>
        """ % data['wallet_balance'], unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class='metric-card'>
                <div class='metric-value'>%.1f%%</div>
                <div class='metric-label'>Win Rate</div>
            </div>
        """ % data['win_rate'], unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class='metric-card'>
                <div class='metric-value'>%d</div>
                <div class='metric-label'>Total Trades</div>
            </div>
        """ % data['total_trades'], unsafe_allow_html=True)

    with col4:
        st.markdown("""
            <div class='metric-card'>
                <div class='metric-value'>%d</div>
                <div class='metric-label'>Moonshots</div>
            </div>
        """ % data['moonshots'], unsafe_allow_html=True)

    # Active Positions
    st.markdown("### Active Positions")
    if data['active_positions']:
        st.write(data['active_positions'])
    else:
        st.info("No active positions")

    # Recent Trades
    st.markdown("### Recent Trades")
    if data['recent_trades']:
        df = pd.DataFrame(data['recent_trades'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No recent trades")

    # Auto-refresh every 2 seconds
    time.sleep(2)
    st.experimental_rerun()

if __name__ == "__main__":
    main()
