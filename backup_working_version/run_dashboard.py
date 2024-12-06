import sys
from pathlib import Path
import json
import time
from threading import Thread, Event, Lock
import logging

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# Cache for simulation data
cache = {
    "data": None,
    "last_update": 0
}
cache_lock = Lock()
CACHE_DURATION = 1  # seconds

def read_simulation_data(force=False):
    current_time = time.time()
    
    with cache_lock:
        # Return cached data if it's fresh enough
        if not force and cache["data"] is not None and (current_time - cache["last_update"]) < CACHE_DURATION:
            return cache["data"]
        
        try:
            with open('simulation_results.json', 'r') as f:
                data = json.load(f)
                cache["data"] = data
                cache["last_update"] = current_time
                return data
        except Exception as e:
            logger.error(f"Error reading data: {e}")
            return {
                "wallet_balance": 0.00,
                "win_rate": 0.0,
                "active_positions": [],
                "recent_trades": [],
                "moonshots": 0
            }

@app.route('/')
def index():
    return render_template('dashboard.html')

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    data = read_simulation_data(force=True)
    emit('update', data)

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('request_update')
def handle_update_request():
    logger.info('Update requested')
    data = read_simulation_data()
    emit('update', data)

if __name__ == '__main__':
    logger.info("Starting server...")
    socketio.run(app, debug=False, host='127.0.0.1', port=5000)
