import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
import json

class SimulatedTrader:
    def __init__(self, initial_balance: float = 500.0):
        self.initial_balance = Decimal(str(initial_balance))
        self.current_balance = self.initial_balance
        self.positions = {}
        self.trade_history = []
        self.start_time = datetime.utcnow()
        
        # Performance tracking
        self.wins = 0
        self.losses = 0
        self.total_trades = 0
        
        # Risk management
        self.max_position_size = self.initial_balance * Decimal('0.10')  # 10% max per trade
        self.stop_loss_pct = Decimal('0.08')  # 8% stop loss
        self.take_profit_levels = {
            'first': Decimal('1.30'),    # 30% first target
            'second': Decimal('1.80'),   # 80% second target
            'moonbag': Decimal('5.00')   # 5x moonbag target
        }
        
    async def execute_trade(self, token_address: str, action: str, amount: float, price: float) -> Dict:
        """Execute a simulated trade using real-time price data"""
        try:
            amount = Decimal(str(amount))
            price = Decimal(str(price))
            
            if action.upper() == 'BUY':
                if self.current_balance < amount * price:
                    raise ValueError("Insufficient balance for trade")
                    
                # Execute buy
                position_size = amount * price
                if position_size > self.max_position_size:
                    raise ValueError("Position size exceeds maximum allowed")
                    
                self.current_balance -= position_size
                self.positions[token_address] = {
                    'amount': amount,
                    'entry_price': price,
                    'current_price': price,
                    'position_size': position_size,
                    'stop_loss': price * (1 - self.stop_loss_pct),
                    'take_profits': {
                        'first': price * self.take_profit_levels['first'],
                        'second': price * self.take_profit_levels['second'],
                        'moonbag': price * self.take_profit_levels['moonbag']
                    },
                    'moonbag_reserved': False
                }
                
            elif action.upper() == 'SELL':
                if token_address not in self.positions:
                    raise ValueError("No open position for this token")
                    
                position = self.positions[token_address]
                profit = (price - position['entry_price']) * position['amount']
                self.current_balance += position['amount'] * price
                
                # Track performance
                if price > position['entry_price']:
                    self.wins += 1
                else:
                    self.losses += 1
                self.total_trades += 1
                
                # Record trade
                self.trade_history.append({
                    'token': token_address,
                    'action': action,
                    'amount': float(position['amount']),
                    'entry_price': float(position['entry_price']),
                    'exit_price': float(price),
                    'profit': float(profit),
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                del self.positions[token_address]
                
            return {
                'success': True,
                'balance': float(self.current_balance),
                'action': action,
                'amount': float(amount),
                'price': float(price)
            }
            
        except Exception as e:
            logging.error(f"Trade execution error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def update_positions(self, market_data: Dict):
        """Update positions with real-time market data"""
        for token, data in market_data.items():
            if token in self.positions:
                position = self.positions[token]
                current_price = Decimal(str(data['price']))
                position['current_price'] = current_price
                
                # Check stop loss
                if current_price <= position['stop_loss']:
                    await self.execute_trade(token, 'SELL', position['amount'], current_price)
                    continue
                    
                # Check take profit levels
                if not position['moonbag_reserved']:
                    if current_price >= position['take_profits']['first']:
                        # Sell 40% at first target
                        sell_amount = position['amount'] * Decimal('0.40')
                        await self.execute_trade(token, 'SELL', sell_amount, current_price)
                        position['amount'] -= sell_amount
                        
                    if current_price >= position['take_profits']['second']:
                        # Sell another 40% at second target
                        sell_amount = position['amount'] * Decimal('0.40')
                        await self.execute_trade(token, 'SELL', sell_amount, current_price)
                        position['amount'] -= sell_amount
                        position['moonbag_reserved'] = True
                        
                    if current_price >= position['take_profits']['moonbag']:
                        # Sell remaining at moonbag target
                        await self.execute_trade(token, 'SELL', position['amount'], current_price)
                        
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        win_rate = (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0
        roi = ((self.current_balance / self.initial_balance) - 1) * 100
        
        return {
            'current_balance': float(self.current_balance),
            'initial_balance': float(self.initial_balance),
            'total_trades': self.total_trades,
            'win_rate': float(win_rate),
            'roi': float(roi),
            'active_positions': len(self.positions),
            'trade_history': self.trade_history[-100:]  # Last 100 trades
        }
        
    def save_results(self, filename: str):
        """Save simulation results to file"""
        results = {
            'performance': self.get_performance_metrics(),
            'config': {
                'initial_balance': float(self.initial_balance),
                'max_position_size': float(self.max_position_size),
                'stop_loss': float(self.stop_loss_pct),
                'take_profit_levels': {k: float(v) for k, v in self.take_profit_levels.items()}
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)
