from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import asyncio
import subprocess
from trading.engine import TradingEngine
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
import base58
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize trading engine
trading_engine = TradingEngine()

def check_vpn_connection():
    """Check Ocean VPN connection status"""
    try:
        result = subprocess.run(['oceanvpn', 'status'], capture_output=True, text=True)
        return 'connected' in result.stdout.lower()
    except:
        return False

def load_wallet_data():
    try:
        with open('database/wallet.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {"balance": 1993.25, "initial_balance": 500.0}

def load_trade_history():
    try:
        with open('database/trade_history.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {"trades": []}

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    wallet_data = load_wallet_data()
    vpn_connected = check_vpn_connection()
    
    return jsonify({
        'trading_mode': 'Live Trading',
        'status': 'Online',
        'vpn_status': 'Connected' if vpn_connected else 'Disconnected',
        'initial_balance': wallet_data['initial_balance'],
        'current_balance': wallet_data['balance'],
        'roi': ((wallet_data['balance'] - wallet_data['initial_balance']) / wallet_data['initial_balance']) * 100,
        'last_update': datetime.now().isoformat()
    })

@app.route('/api/metrics')
def get_metrics():
    trade_history = load_trade_history()
    trades = trade_history.get('trades', [])
    total_trades = len(trades)
    winning_trades = sum(1 for trade in trades if trade.get('profit', 0) > 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    return jsonify({
        'total_trades': total_trades,
        'win_rate': win_rate,
        'winning_trades': winning_trades,
        'losing_trades': total_trades - winning_trades
    })

@app.route('/api/data')
def get_data():
    wallet_data = load_wallet_data()
    trade_history = load_trade_history()
    trades = trade_history.get('trades', [])
    total_trades = len(trades)
    winning_trades = sum(1 for trade in trades if trade.get('profit', 0) > 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    return jsonify({
        'wallet_data': wallet_data,
        'trade_history': trade_history,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'winning_trades': winning_trades,
        'losing_trades': total_trades - winning_trades
    })

@socketio.on('connect')
def handle_connect():
    emit('vpn_status', {'connected': check_vpn_connection()})
    emit('wallet_update', {
        'balance': trading_engine.wallet_balance,
        'pnl': trading_engine.total_pnl,
        'winRate': trading_engine.win_rate
    })

async def broadcast_updates():
    """Broadcast real-time updates to connected clients"""
    while True:
        try:
            # Update VPN status
            emit('vpn_status', {'connected': check_vpn_connection()}, broadcast=True)
            
            # Update wallet info
            wallet_data = {
                'balance': trading_engine.wallet_balance,
                'pnl': trading_engine.total_pnl,
                'winRate': trading_engine.win_rate
            }
            emit('wallet_update', wallet_data, broadcast=True)
            
            # Get recent trades
            trades = trading_engine.recent_trades
            for trade in trades:
                emit('trade_update', trade, broadcast=True)
            
            await asyncio.sleep(1)  # Update every second
            
        except Exception as e:
            print(f"Error broadcasting updates: {str(e)}")
            await asyncio.sleep(5)

@socketio.on('start_trading')
def handle_start_trading():
    """Start the trading engine"""
    try:
        asyncio.run(trading_engine.start())
        emit('status', {'message': 'Trading engine started successfully'})
    except Exception as e:
        emit('status', {'message': f'Error starting trading engine: {str(e)}'})

@socketio.on('stop_trading')
def handle_stop_trading():
    """Stop the trading engine"""
    try:
        trading_engine.stop()
        emit('status', {'message': 'Trading engine stopped successfully'})
    except Exception as e:
        emit('status', {'message': f'Error stopping trading engine: {str(e)}'})

if __name__ == '__main__':
    # Start the background tasks
    socketio.start_background_task(broadcast_updates)
    
    # Run the app with socketio
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
