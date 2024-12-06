import asyncio
import logging
from datetime import datetime
import json
import time
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LiveTestTrader:
    def __init__(self):
        self.test_balance = 500.0  # Start with $500
        self.positions = {}
        self.trade_history = []
        self.start_time = datetime.now()
        
    async def initialize(self):
        """Initialize with default data"""
        initial_data = {
            "wallet_balance": self.test_balance,
            "win_rate": 0.0,
            "active_positions": [],
            "recent_trades": [],
            "moonshots": 0,
            "total_trades": 0
        }
        
        # Save initial data
        with open('simulation_results.json', 'w') as f:
            json.dump(initial_data, f, indent=4)
            
        logging.info("Initialized test trader with $500")
        
    async def start_live_testing(self, duration_hours: float = 24):
        """Run live testing for specified duration"""
        try:
            await self.initialize()
            end_time = time.time() + (duration_hours * 3600)
            
            logging.info(f"Starting live testing for {duration_hours} hours")
            
            while time.time() < end_time:
                await self.generate_fake_trade()
                await self.update_dashboard()
                await asyncio.sleep(5)  # Generate a trade every 5 seconds
                
        except Exception as e:
            logging.error(f"Error in live testing: {str(e)}")
            
    async def generate_fake_trade(self):
        """Generate a fake trade"""
        try:
            # Random token from a list
            tokens = ["PEPE", "DOGE", "SHIB", "FLOKI", "WOJAK"]
            token = random.choice(tokens)
            
            # Random trade type
            trade_type = random.choice(["BUY", "SELL"])
            
            # Random amount between $10 and $50
            amount = round(random.uniform(10, 50), 2)
            
            # Random price between $0.1 and $10
            price = round(random.uniform(0.1, 10), 2)
            
            # Random profit between -20% and +40%
            profit = round(random.uniform(-20, 40), 2)
            
            trade = {
                "token": token,
                "type": trade_type,
                "amount": amount,
                "price": price,
                "profit": profit,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Update trade history
            self.trade_history.append(trade)
            if len(self.trade_history) > 10:  # Keep only last 10 trades
                self.trade_history = self.trade_history[-10:]
            
            # Update wallet balance based on profit/loss
            if trade_type == "SELL":
                self.test_balance += (amount * profit / 100)
            
            logging.info(f"Generated trade: {trade}")
            
        except Exception as e:
            logging.error(f"Error generating fake trade: {str(e)}")
            
    async def update_dashboard(self):
        """Update dashboard with latest data"""
        try:
            # Calculate win rate
            closed_trades = [t for t in self.trade_history if t["type"] == "SELL"]
            winning_trades = [t for t in closed_trades if t["profit"] > 0]
            win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0
            
            # Count moonshots (trades with >20% profit)
            moonshots = len([t for t in self.trade_history if t["profit"] > 20])
            
            # Update simulation results
            data = {
                "wallet_balance": round(self.test_balance, 2),
                "win_rate": round(win_rate, 1),
                "active_positions": list(self.positions.keys()),
                "recent_trades": self.trade_history,
                "moonshots": moonshots,
                "total_trades": len(self.trade_history)
            }
            
            # Save to simulation_results.json
            with open('simulation_results.json', 'w') as f:
                json.dump(data, f, indent=4)
                
            logging.info(f"Dashboard updated - Balance: ${self.test_balance:.2f}, Win Rate: {win_rate:.1f}%")
            
        except Exception as e:
            logging.error(f"Error updating dashboard: {str(e)}")

if __name__ == "__main__":
    try:
        trader = LiveTestTrader()
        asyncio.run(trader.start_live_testing(duration_hours=24))
    except KeyboardInterrupt:
        logging.info("Test interrupted by user")
    except Exception as e:
        logging.error(f"Error running test: {str(e)}")
