from decimal import Decimal
import logging
import json
from datetime import datetime, timedelta

class RiskManager:
    def __init__(self, initial_capital: float = 500):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_trade_size = initial_capital * 0.1  # 10% max per trade
        self.daily_loss_limit = initial_capital * 0.05  # 5% daily loss limit
        self.profit_targets = {
            "take_profit": 3.0,  # 3% profit target
            "stop_loss": -1.0    # 1% stop loss
        }
        
        # Track performance
        self.trades = []
        self.daily_pnl = {}
        
    def can_take_trade(self, trade_size: float, token_address: str) -> bool:
        """Check if trade meets risk parameters"""
        try:
            # 1. Check trade size
            if trade_size > self.max_trade_size:
                logging.warning(f"Trade size ${trade_size} exceeds max ${self.max_trade_size}")
                return False
                
            # 2. Check daily loss limit
            today = datetime.now().date()
            daily_loss = self.calculate_daily_loss(today)
            if abs(daily_loss) > self.daily_loss_limit:
                logging.warning(f"Daily loss limit reached: ${daily_loss}")
                return False
                
            # 3. Check token exposure
            if self.get_token_exposure(token_address) > 20:  # Max 20% in one token
                logging.warning("Too much exposure to this token")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error in risk check: {str(e)}")
            return False
            
    def record_trade(self, token_address: str, buy_price: float, 
                    sell_price: float, amount: float, timestamp: datetime):
        """Record trade for analysis"""
        profit = (sell_price - buy_price) * amount
        roi = (profit / (buy_price * amount)) * 100
        
        trade = {
            "token": token_address,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "amount": amount,
            "profit": profit,
            "roi": roi,
            "timestamp": timestamp
        }
        
        self.trades.append(trade)
        
        # Update daily PnL
        date = timestamp.date()
        if date not in self.daily_pnl:
            self.daily_pnl[date] = 0
        self.daily_pnl[date] += profit
        
        # Update current capital
        self.current_capital += profit
        
        # Adjust max trade size based on new capital
        self.update_risk_parameters()
        
    def update_risk_parameters(self):
        """Update risk parameters based on performance"""
        # Adjust max trade size based on capital
        self.max_trade_size = self.current_capital * 0.1
        
        # Adjust daily loss limit
        self.daily_loss_limit = self.current_capital * 0.05
        
        # If we're doing well, we can be slightly more aggressive
        if self.current_capital > self.initial_capital * 1.5:  # Up 50%
            self.profit_targets["take_profit"] = 2.5  # Lower profit target
            self.max_trade_size = self.current_capital * 0.15  # Higher trade size
            
        # If we're down, get more conservative
        elif self.current_capital < self.initial_capital * 0.8:  # Down 20%
            self.profit_targets["take_profit"] = 3.5  # Higher profit target
            self.max_trade_size = self.current_capital * 0.08  # Lower trade size
            
    def get_performance_stats(self) -> dict:
        """Get detailed performance statistics"""
        if not self.trades:
            return {}
            
        total_trades = len(self.trades)
        profitable_trades = len([t for t in self.trades if t['profit'] > 0])
        
        stats = {
            "total_trades": total_trades,
            "win_rate": (profitable_trades / total_trades) * 100,
            "current_capital": self.current_capital,
            "total_profit": self.current_capital - self.initial_capital,
            "roi": ((self.current_capital - self.initial_capital) / self.initial_capital) * 100,
            "largest_win": max(self.trades, key=lambda x: x['profit'])['profit'],
            "largest_loss": min(self.trades, key=lambda x: x['profit'])['profit'],
            "average_roi": sum(t['roi'] for t in self.trades) / total_trades
        }
        
        return stats
        
    def calculate_daily_loss(self, date) -> float:
        """Calculate total loss for a given day"""
        return self.daily_pnl.get(date, 0)
        
    def get_token_exposure(self, token_address: str) -> float:
        """Calculate current exposure to a token as percentage of capital"""
        token_trades = [t for t in self.trades if t['token'] == token_address]
        if not token_trades:
            return 0
            
        return sum(t['amount'] for t in token_trades) / self.current_capital * 100
