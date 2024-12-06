import subprocess
import sys
import time
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ocean_runner.log'),
        logging.StreamHandler()
    ]
)

def start_flask_server():
    """Start the Flask server"""
    try:
        flask_process = subprocess.Popen(
            [sys.executable, 'app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logging.info("Flask server started")
        return flask_process
    except Exception as e:
        logging.error(f"Error starting Flask server: {str(e)}")
        return None

def start_trading_engine():
    """Start the trading engine"""
    try:
        trading_process = subprocess.Popen(
            [sys.executable, 'trading/engine.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logging.info("Trading engine started")
        return trading_process
    except Exception as e:
        logging.error(f"Error starting trading engine: {str(e)}")
        return None

def monitor_processes(processes):
    """Monitor and restart processes if they fail"""
    while True:
        for name, process in processes.items():
            if process.poll() is not None:  # Process has terminated
                logging.warning(f"{name} has stopped. Restarting...")
                if name == "flask":
                    processes[name] = start_flask_server()
                elif name == "trading":
                    processes[name] = start_trading_engine()
        time.sleep(10)

def main():
    """Main function to run both servers"""
    logging.info("Starting Ocean runner...")
    
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    
    # Start processes
    flask_process = start_flask_server()
    trading_process = start_trading_engine()
    
    if not flask_process or not trading_process:
        logging.error("Failed to start one or more processes")
        return
    
    processes = {
        "flask": flask_process,
        "trading": trading_process
    }
    
    try:
        monitor_processes(processes)
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        for process in processes.values():
            process.terminate()
    except Exception as e:
        logging.error(f"Error in main loop: {str(e)}")
        for process in processes.values():
            process.terminate()

if __name__ == "__main__":
    main()
