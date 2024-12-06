import sys
from pathlib import Path
import json
import time
import logging

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from flask import Flask, render_template, jsonify

# Configure basic logging
logging.basicConfig(
    filename='dashboard.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

def read_simulation_data():
    """Read data from simulation_results.json"""
    try:
        with open('simulation_results.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading data: {e}")
        return {
            "wallet_balance": 500.00,
            "win_rate": 0.0,
            "active_positions": [],
            "recent_trades": [],
            "moonshots": 0,
            "total_trades": 0
        }

@app.route('/')
def index():
    """Render dashboard"""
    return render_template('dashboard.html')

@app.route('/get_data')
def get_data():
    """Get latest simulation data"""
    return jsonify(read_simulation_data())

if __name__ == '__main__':
    logging.info("Starting server...")
    app.run(debug=True, host='127.0.0.1', port=5000)
