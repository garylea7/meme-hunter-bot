from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import logging
import json
from dotenv import load_dotenv
from src.solana_trader import SolanaTrader
import asyncio
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Get absolute paths
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(root_dir, 'templates')
static_dir = os.path.join(root_dir, 'static')

logger.info(f"Root directory: {root_dir}")
logger.info(f"Template directory: {template_dir}")
logger.info(f"Static directory: {static_dir}")

app = Flask(__name__, 
    template_folder=template_dir,
    static_folder=static_dir,
    static_url_path='/static'
)

# Enable CORS with proper configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize trader
try:
    trader = SolanaTrader(
        wallet_address=os.getenv('WALLET_ADDRESS'),
        private_key=os.getenv('PRIVATE_KEY'),
        ocean_config_path=os.path.join(root_dir, 'config', 'ocean.json')
    )
    
    # Initialize trade history with sample data
    trader.initialize_trade_history()
    
    logger.info("Trading bot initialized successfully")
except Exception as e:
    logger.error(f"Error initializing trading bot: {e}")
    raise

@app.route('/')
def index():
    """Render the main dashboard page"""
    logger.info("Serving dashboard_v2.html")
    try:
        return render_template('dashboard_v2.html')
    except Exception as e:
        logger.error(f"Error serving dashboard_v2.html: {e}")
        return str(e), 500

@app.route('/api/data')
def get_data():
    """Get all dashboard data"""
    try:
        # Read wallet balance
        wallet_path = os.path.join(root_dir, 'database', 'wallet.json')
        with open(wallet_path, 'r') as f:
            wallet_data = json.load(f)
        
        # Read trade history
        trade_history_path = os.path.join(root_dir, 'database', 'trade_history.json')
        with open(trade_history_path, 'r') as f:
            trade_history = json.load(f)
        
        # Calculate metrics
        test_trades = trade_history.get('test_trades', [])
        profitable_trades = len([t for t in test_trades if t['profit'] > 0])
        total_trades = len(test_trades)
        
        # Calculate win rate
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate ROI
        initial_balance = wallet_data.get('initial_balance', 500.0)
        current_balance = wallet_data.get('balance', 500.0)
        roi = ((current_balance - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0
        
        # Calculate 24h change
        now = datetime.now(timezone.utc)
        trades_24h = [
            t for t in test_trades
            if (now - datetime.fromisoformat(t['timestamp'])).total_seconds() <= 86400
        ]
        change_24h = sum(t['profit'] for t in trades_24h)
        
        data = {
            'status': 'online',
            'wallet_balance': current_balance,
            'portfolio_value': current_balance,
            'change_24h': change_24h,
            'win_rate': round(win_rate, 2),
            'roi': round(roi, 2),
            'positions': []
        }
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting data: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/status')
def get_status():
    try:
        with open(os.path.join(root_dir, 'database', 'wallet.json'), 'r') as f:
            wallet = json.load(f)
        
        last_updated = datetime.fromisoformat(wallet['last_updated'])
        current_time = datetime.now(timezone.utc)
        time_diff = (current_time - last_updated).total_seconds()
        
        return jsonify({
            'trading_mode': 'Test Mode',  # or 'Real Trading' based on configuration
            'status': 'Online' if time_diff < 30 else 'Offline',
            'last_update': wallet['last_updated'],
            'uptime': time_diff,
            'initial_balance': wallet['initial_balance'],
            'current_balance': wallet['balance'],
            'roi': ((wallet['balance'] - wallet['initial_balance']) / wallet['initial_balance']) * 100
        })
    except Exception as e:
        logging.error(f"Error in status endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics')
def get_metrics():
    try:
        with open(os.path.join(root_dir, 'database', 'trade_history.json'), 'r') as f:
            history = json.load(f)
        
        trades = history['test_trades']
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['profit'] > 0])
        
        metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'profit_categories': {
                'small': len([t for t in trades if 0 < t['profit'] <= 5]),
                'medium': len([t for t in trades if 5 < t['profit'] <= 10]),
                'large': len([t for t in trades if 10 < t['profit'] <= 20]),
                'moonshot': len([t for t in trades if t['profit'] > 20])
            }
        }
        
        return jsonify(metrics)
    except Exception as e:
        logging.error(f"Error in metrics endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_metrics')
def get_test_metrics():
    """Get test mode metrics"""
    logger.info("Getting test metrics")
    try:
        # Get portfolio value and metrics
        portfolio = trader.get_portfolio_value()
        
        # Calculate win rate and ROI from test trades
        test_trades = trader.trade_history.get('test_trades', [])
        profitable_trades = len([t for t in test_trades if t['profit'] > 0])
        total_trades = len(test_trades)
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_profit = sum(t['profit'] for t in test_trades)
        total_invested = sum(t['amount'] * t['price'] for t in test_trades)
        roi = (total_profit / total_invested * 100) if total_invested > 0 else 0
        
        data = {
            'success': True,
            'data': {
                'roi': round(roi, 2),
                'win_rate': round(win_rate, 2),
                'balance': trader.get_wallet_balance()
            }
        }
        logger.info(f"Returning test metrics: {data}")
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting test metrics: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trade_history')
def get_trade_history():
    try:
        with open(os.path.join(root_dir, 'database', 'trade_history.json'), 'r') as f:
            history = json.load(f)
        
        return jsonify({
            'trades': history['test_trades'][-10:]  # Return last 10 trades
        })
    except Exception as e:
        logging.error(f"Error in trade history endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.after_request
def after_request(response):
    """Add headers to every response"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler"""
    logger.error(f"Unhandled error: {error}")
    logger.error(traceback.format_exc())
    return jsonify({
        'success': False,
        'error': str(error)
    }), 500

def run_server():
    """Run the Flask server"""
    app.run(debug=True)

if __name__ == '__main__':
    # Log the paths when starting
    logger.info("Starting Flask server...")
    logger.info(f"Template folder: {app.template_folder}")
    logger.info(f"Static folder: {app.static_folder}")
    run_server()
