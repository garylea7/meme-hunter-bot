from src.solana_trader import SolanaTrader
import os
import logging
import time
import random
from datetime import datetime, timezone
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

def simulate_trade(trader):
    """Simulate a trade with random profit/loss"""
    try:
        # Random trade parameters
        amount = random.uniform(0.1, 1.0)
        price = random.uniform(70, 80)
        base_profit = random.uniform(-5, 15)
        
        # 1% chance of moonshot
        if random.random() < 0.01:
            base_profit *= random.uniform(50, 200)
        
        # Execute trade
        trade = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'token': f"TOKEN{random.randint(1,5)}",
            'type': "BUY" if random.random() > 0.5 else "SELL",
            'amount': amount,
            'price': price,
            'profit': base_profit,
            'status': 'COMPLETED'
        }
        
        # Update trade history
        trader.trade_history['test_trades'].append(trade)
        
        # Update wallet balance
        wallet_path = os.path.join('database', 'wallet.json')
        with open(wallet_path, 'r') as f:
            wallet_data = json.load(f)
        
        new_balance = wallet_data['balance'] + base_profit
        wallet_data['balance'] = new_balance
        wallet_data['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        with open(wallet_path, 'w') as f:
            json.dump(wallet_data, f, indent=4)
        
        # Update trade history
        trader.trade_history['portfolio']['total_value'] = new_balance
        with open(trader.trade_history_path, 'w') as f:
            json.dump(trader.trade_history, f, indent=4)
        
        logger.info(f"Trade executed: {trade['type']} {trade['token']} - Profit/Loss: ${base_profit:.2f}")
        logger.info(f"New balance: ${new_balance:.2f}")
        
        return True
    except Exception as e:
        logger.error(f"Error simulating trade: {e}")
        return False

def main():
    """Start test trading with $500"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize trader
        trader = SolanaTrader(
            wallet_address=os.getenv('WALLET_ADDRESS'),
            private_key=os.getenv('PRIVATE_KEY'),
            ocean_config_path=os.path.join('config', 'ocean.json')
        )
        
        logger.info("Starting test trading with $500 initial balance...")
        logger.info("Simulating trades every 10 seconds...")
        
        # Start trading loop
        while True:
            simulate_trade(trader)
            time.sleep(10)  # Wait 10 seconds between trades
        
    except Exception as e:
        logger.error(f"Error in test trading: {e}")
        raise

if __name__ == '__main__':
    main()
