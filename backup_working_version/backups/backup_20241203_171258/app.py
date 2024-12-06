from flask import Flask, jsonify, render_template
import json
import os
from datetime import datetime

app = Flask(__name__)

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
    return render_template('dashboard_v2.html')

@app.route('/api/status')
def get_status():
    wallet_data = load_wallet_data()
    return jsonify({
        'trading_mode': 'Live Mode',
        'status': 'Online',
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

    # Calculate profit categories
    profit_categories = {
        'small': sum(1 for trade in trades if 0 < trade.get('profit', 0) <= 5),
        'medium': sum(1 for trade in trades if 5 < trade.get('profit', 0) <= 10),
        'large': sum(1 for trade in trades if 10 < trade.get('profit', 0) <= 20),
        'moonshot': sum(1 for trade in trades if trade.get('profit', 0) > 20)
    }

    return jsonify({
        'total_trades': total_trades,
        'win_rate': win_rate,
        'profit_categories': profit_categories
    })

@app.route('/api/trade_history')
def get_trade_history():
    trade_history = load_trade_history()
    return jsonify({
        'trades': trade_history.get('trades', [])
    })

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
