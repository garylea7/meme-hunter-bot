import logging
from typing import Dict, List, Optional
import aiohttp
from datetime import datetime, timedelta
import asyncio
from decimal import Decimal
import os
from dotenv import load_dotenv
import random
from base64 import b64decode, b64encode
import json

logger = logging.getLogger(__name__)

class CopyTrader:
    def __init__(self, test_mode=True):
        self.GMGN_API_HOST = 'https://gmgn.ai'
        self.test_mode = test_mode
        self.followed_traders = set()
        self.trader_stats = {}
        self.trader_scores = {}
        
        # Test mode settings
        self.test_trades = []
        self.initial_test_balance = Decimal('1000')  # Start with $1000 test balance
        self.test_balance = self.initial_test_balance
        
        # Tracking settings
        self.min_trade_size_sol = Decimal('0.1')  # Minimum 0.1 SOL trades to track
        self.min_profit_threshold = Decimal('0.05')  # 5% minimum profit to consider successful
        
    async def track_successful_trades(self):
        """Monitor the network for successful trades"""
        try:
            # In test mode, generate sample successful trades
            if self.test_mode:
                return await self._generate_test_trades()
                
            # In real mode, monitor GMGN router for successful trades
            async with aiohttp.ClientSession() as session:
                # Example tokens to monitor (SOL and popular tokens)
                tokens = {
                    'SOL': 'So11111111111111111111111111111111111111112',
                    'BONK': '7EYnhQoR9YM3N7UoaKRoA44Uy8JeaZV3qyouov87awMs'
                }
                
                successful_trades = []
                
                # Monitor trades between these tokens
                for token_in, token_out in [(t1, t2) for t1 in tokens.values() for t2 in tokens.values() if t1 != t2]:
                    # Query router for recent trades
                    route_url = f"{self.GMGN_API_HOST}/defi/router/v1/sol/tx/get_swap_route"
                    params = {
                        'token_in_address': token_in,
                        'token_out_address': token_out,
                        'in_amount': str(int(self.min_trade_size_sol * 1e9)),  # Convert to lamports
                        'from_address': '2kpJ5QRh16aRQ4oLZ5LnucHFDAZtEFz6omqWWMzDSNrx',  # Example address
                        'slippage': '0.5'
                    }
                    
                    async with session.get(route_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('code') == 0:
                                trade = data['data']['quote']
                                # Calculate implied profit
                                in_amount = Decimal(trade['inAmount']) / Decimal('1e9')  # Convert from lamports
                                out_amount = Decimal(trade['outAmount']) / Decimal('1e9')
                                
                                if out_amount > in_amount * (1 + self.min_profit_threshold):
                                    successful_trades.append({
                                        'trader': trade.get('from_address'),
                                        'profit_percentage': float((out_amount / in_amount - 1) * 100),
                                        'tokens': (token_in, token_out),
                                        'amounts': (float(in_amount), float(out_amount))
                                    })
                
                return successful_trades
                
        except Exception as e:
            logger.error(f"Error tracking trades: {str(e)}")
            return []
            
    async def _generate_test_trades(self) -> List[Dict]:
        """Generate sample successful trades for testing"""
        test_traders = [
            f'trader{i}' for i in range(5)
        ]
        
        successful_trades = []
        for _ in range(random.randint(3, 8)):
            trader = random.choice(test_traders)
            profit = random.uniform(0.05, 0.30)  # 5% to 30% profit
            successful_trades.append({
                'trader': trader,
                'profit_percentage': profit * 100,
                'tokens': ('SOL', 'BONK'),
                'amounts': (1.0, 1.0 * (1 + profit))
            })
            
        return successful_trades
        
    async def find_traders_to_copy(self) -> List[Dict]:
        """Find successful traders based on their trading history"""
        try:
            # Get recent successful trades
            trades = await self.track_successful_trades()
            
            # Aggregate trader performance
            trader_performance = {}
            for trade in trades:
                trader = trade['trader']
                if trader not in trader_performance:
                    trader_performance[trader] = {
                        'total_trades': 0,
                        'profitable_trades': 0,
                        'total_profit': 0,
                        'avg_profit': 0
                    }
                    
                perf = trader_performance[trader]
                perf['total_trades'] += 1
                perf['profitable_trades'] += 1 if trade['profit_percentage'] > 0 else 0
                perf['total_profit'] += trade['profit_percentage']
                perf['avg_profit'] = perf['total_profit'] / perf['total_trades']
                
            # Convert to list and calculate scores
            traders = []
            for address, perf in trader_performance.items():
                if perf['total_trades'] >= 3:  # Minimum trades threshold
                    score = self._calculate_trader_score(perf)
                    traders.append({
                        'address': address,
                        'stats': perf,
                        'score': score,
                        'recommendation': self._generate_recommendation(score)
                    })
                    
            return sorted(traders, key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error finding traders: {str(e)}")
            return []
            
    def _calculate_trader_score(self, stats: Dict) -> float:
        """Calculate trader score based on performance metrics"""
        try:
            win_rate = stats['profitable_trades'] / stats['total_trades']
            avg_profit = stats['avg_profit']
            
            # Score components
            consistency_score = win_rate * 100
            profit_score = min(avg_profit * 2, 100)  # Cap at 50% avg profit
            
            # Weighted average
            weights = {'consistency': 0.6, 'profit': 0.4}
            return (
                consistency_score * weights['consistency'] +
                profit_score * weights['profit']
            )
            
        except Exception as e:
            logger.error(f"Error calculating score: {str(e)}")
            return 0
            
    def _generate_recommendation(self, score: float) -> Dict:
        """Generate copy trading recommendation based on score"""
        if score >= 80:
            return {
                'action': 'Copy',
                'confidence': 'High',
                'allocation': '5-10% of portfolio'
            }
        elif score >= 60:
            return {
                'action': 'Copy with caution',
                'confidence': 'Medium',
                'allocation': '2-5% of portfolio'
            }
        else:
            return {
                'action': 'Monitor',
                'confidence': 'Low',
                'allocation': 'Not recommended'
            }
            
    async def execute_trade(self, token_in: str, token_out: str, amount: float) -> Dict:
        """Execute a trade using GMGN router"""
        if self.test_mode:
            return await self.simulate_trade('test_trader', 'buy', token_out, amount)
            
        try:
            # Get quote and unsigned transaction
            route_url = f"{self.GMGN_API_HOST}/defi/router/v1/sol/tx/get_swap_route"
            params = {
                'token_in_address': token_in,
                'token_out_address': token_out,
                'in_amount': str(int(amount * 1e9)),  # Convert to lamports
                'from_address': os.getenv('WALLET_ADDRESS'),
                'slippage': '0.5'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(route_url, params=params) as response:
                    if response.status != 200:
                        raise Exception("Failed to get route")
                        
                    route_data = await response.json()
                    if route_data.get('code') != 0:
                        raise Exception(f"Route error: {route_data.get('msg')}")
                        
                    # Note: In real implementation, you would:
                    # 1. Decode base64 transaction
                    # 2. Sign with wallet
                    # 3. Submit signed transaction
                    # 4. Monitor transaction status
                    
                    return route_data['data']
                    
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            return None

    async def simulate_trade(self, trader_address: str, trade_type: str, token: str, amount: float):
        """Simulate a trade in test mode"""
        if not self.test_mode:
            return
            
        timestamp = datetime.now()
        profit_loss = random.uniform(-0.2, 0.3) if trade_type == 'sell' else 0
        
        trade = {
            'timestamp': timestamp,
            'trader': trader_address,
            'type': trade_type,
            'token': token,
            'amount': amount,
            'profit_loss': profit_loss,
            'balance_after': float(self.test_balance * (1 + profit_loss)) if trade_type == 'sell' else float(self.test_balance)
        }
        
        if trade_type == 'sell':
            self.test_balance *= Decimal(str(1 + profit_loss))
            
        self.test_trades.append(trade)
        return trade
        
    def get_test_performance(self) -> Dict:
        """Get performance metrics for test mode"""
        if not self.test_mode:
            return {}
            
        total_trades = len(self.test_trades)
        if total_trades == 0:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_profit_loss': 0,
                'current_balance': float(self.test_balance),
                'roi': 0
            }
            
        winning_trades = sum(1 for trade in self.test_trades if trade['profit_loss'] > 0)
        total_pnl = sum(trade['profit_loss'] for trade in self.test_trades)
        
        return {
            'total_trades': total_trades,
            'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
            'total_profit_loss': total_pnl,
            'current_balance': float(self.test_balance),
            'roi': (float(self.test_balance) - float(self.initial_test_balance)) / float(self.initial_test_balance) * 100
        }
