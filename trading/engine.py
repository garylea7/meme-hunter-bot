import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging
import asyncio
import numpy as np

import aiohttp
from solana.rpc.async_api import AsyncClient
from pycoingecko import CoinGeckoAPI
import pandas as pd
from web3 import Web3

from src.market_data import MarketDataHandler
from src.social_tracker import SocialTracker

class TradingEngine:
    def __init__(self):
        self.config = self._load_config()
        self.market_data = MarketDataHandler()
        self.social_tracker = SocialTracker()
        self.active_positions = {}
        self.trade_history = []
        self.total_trades = 0
        self.winning_trades = 0
        
        # Load previous simulation state
        try:
            with open('simulation_results.json', 'r') as f:
                data = json.load(f)
                self.practice_balance = data['wallet_balance']
                self.initial_balance = 500.0
                self.trade_history = data.get('recent_trades', [])
                self.total_trades = data.get('total_trades', 0)
                self.winning_trades = int(data.get('win_rate', 0) * self.total_trades / 100)
        except:
            # Start fresh if no previous state
            self.practice_balance = 500.0
            self.initial_balance = 500.0
        
        # Trading settings - more aggressive for memecoins
        self.trade_interval = 2  # Check every 2 seconds
        self.tokens = ['PEPE', 'DOGE', 'SHIB', 'FLOKI', 'WOJAK']
        self.min_profit = 0.5  # Enter on smaller moves
        self.max_loss = 1.0  # Tight stop loss
        self.position_size_range = (20, 100)  # Larger positions
        self.min_volume = 1000  # Lower volume requirement
        
        # Trading settings from successful simulation
        self.trade_interval = 5  # Seconds between trades
        self.tokens = ['PEPE', 'DOGE', 'SHIB', 'FLOKI', 'WOJAK']
        self.min_profit = 3.0
        self.max_loss = 2.0
        self.position_size_range = (10, 45)
        
    async def start(self):
        """Start the trading engine with real market data"""
        logging.info(f"Starting trading engine with practice account (${self.practice_balance:.2f})")
        
        try:
            while True:
                # Get real market data for our tokens
                for token in self.tokens:
                    try:
                        # Get token data
                        market_data = await self.market_data.get_token_data(token)
                        if not market_data:
                            continue
                        
                        # Check if we should enter a position
                        if token not in self.active_positions and len(self.active_positions) < 3:
                            if self._should_enter_position(market_data):
                                size = self._calculate_position_size()
                                await self._enter_position(token, size, market_data)
                        
                        # Update existing position
                        elif token in self.active_positions:
                            await self._update_position(token, market_data)
                            
                    except Exception as e:
                        logging.error(f"Error processing {token}: {str(e)}")
                        continue
                
                # Save current state
                self._save_state()
                
                # Wait before next iteration
                await asyncio.sleep(self.trade_interval)
                
        except Exception as e:
            logging.error(f"Error in trading engine: {str(e)}")
            
    def _should_enter_position(self, market_data: Dict) -> bool:
        """Check if we should enter a position based on market data"""
        try:
            # Check volume
            if market_data['volume_24h'] < self.min_volume:
                return False
            
            # Check price momentum - look for any small movement
            if abs(market_data['price_change_1h']) < self.min_profit:
                return False
            
            # Check if we have enough balance
            min_position = self.position_size_range[0]
            if self.practice_balance < min_position:
                return False
            
            # Add randomness to entries (30% chance)
            if np.random.random() > 0.3:
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error in entry check: {str(e)}")
            return False
            
    def _calculate_position_size(self) -> float:
        """Calculate position size based on available balance"""
        try:
            # Use 20-40% of available balance
            max_size = min(self.practice_balance * 0.4, self.position_size_range[1])
            size = max(self.position_size_range[0], max_size)
            return round(size, 2)
            
        except Exception as e:
            logging.error(f"Error calculating position size: {str(e)}")
            return self.position_size_range[0]
            
    async def _enter_position(self, token: str, size: float, market_data: Dict):
        """Enter a new position"""
        try:
            if size > self.practice_balance:
                return
            
            position = {
                'token': token,
                'entry_price': market_data['price'],
                'size': size,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stop_loss': market_data['price'] * (1 - self.max_loss/100),
                'take_profit': market_data['price'] * (1 + self.min_profit/100)
            }
            
            self.practice_balance -= size
            self.active_positions[token] = position
            
            # Log entry
            logging.info(f"Entered {token} position: ${size:.2f} @ ${market_data['price']:.2f}")
            
        except Exception as e:
            logging.error(f"Error entering position: {str(e)}")
            
    async def _update_position(self, token: str, market_data: Dict):
        """Update an existing position"""
        try:
            position = self.active_positions[token]
            current_price = market_data['price']
            
            # Calculate profit/loss
            profit_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100
            
            # Check if we should exit
            should_exit = (
                current_price <= position['stop_loss'] or
                current_price >= position['take_profit'] or
                abs(profit_pct) > 50  # Take big wins/cut big losses
            )
            
            if should_exit:
                # Calculate position value
                position_value = position['size'] * (1 + profit_pct/100)
                self.practice_balance += position_value
                
                # Record trade
                self.trade_history.append({
                    'token': token,
                    'type': 'SELL',
                    'amount': position['size'],
                    'price': current_price,
                    'profit': profit_pct,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                # Update stats
                self.total_trades += 1
                if profit_pct > 0:
                    self.winning_trades += 1
                
                # Remove position
                del self.active_positions[token]
                
                # Log exit
                logging.info(f"Exited {token} position: {profit_pct:.2f}% profit")
                
        except Exception as e:
            logging.error(f"Error updating position: {str(e)}")
            
    def _save_state(self):
        """Save current trading state"""
        try:
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            
            state = {
                'wallet_balance': round(self.practice_balance, 2),
                'win_rate': round(win_rate, 1),
                'total_trades': self.total_trades,
                'moonshots': sum(1 for trade in self.trade_history if trade['profit'] > 100),
                'active_positions': list(self.active_positions.values()),
                'recent_trades': self.trade_history[-10:]  # Keep last 10 trades
            }
            
            with open('simulation_results.json', 'w') as f:
                json.dump(state, f, indent=4)
                
        except Exception as e:
            logging.error(f"Error saving state: {str(e)}")
            
    async def _get_market_data(self) -> Dict:
        """Get market data for analysis"""
        try:
            # Implementation for getting market data
            market_data = {}
            tokens = self._get_tracked_tokens()
            
            async with aiohttp.ClientSession() as session:
                tasks = []
                for token in tokens:
                    task = self._fetch_token_data(session, token)
                    tasks.append(task)
                results = await asyncio.gather(*tasks)
                
                for token, data in zip(tokens, results):
                    market_data[token] = data
                    
            return market_data
        except Exception as e:
            logging.error(f"Error getting market data: {str(e)}")
            return {}
    
    def _calculate_momentum_signals(self, market_data: Dict) -> Optional[List[Dict]]:
        """Calculate momentum indicators and generate signals"""
        signals = []
        try:
            for token, data in market_data.items():
                momentum = self._calculate_momentum_indicators(data)
                if self._is_momentum_signal(momentum):
                    signals.append({
                        'type': 'momentum',
                        'token': token,
                        'direction': momentum['direction'],
                        'strength': momentum['strength'],
                        'confidence': momentum['confidence']
                    })
        except Exception as e:
            logging.error(f"Error calculating momentum signals: {str(e)}")
        return signals if signals else None
    
    async def _execute_momentum_strategy(self, signals: List[Dict]):
        """Execute trades based on momentum signals"""
        for signal in signals:
            try:
                if signal['confidence'] >= self.config['risk_management']['min_confidence']:
                    trade_params = self._prepare_momentum_trade(signal)
                    await self._execute_trade(trade_params)
            except Exception as e:
                logging.error(f"Error executing momentum strategy: {str(e)}")
    
    async def _get_volume_data(self) -> Dict:
        """Get volume data across exchanges"""
        try:
            volume_data = {}
            tokens = self._get_tracked_tokens()
            
            for token in tokens:
                data = self.cg.get_coin_market_chart_by_id(
                    token,
                    vs_currency='usd',
                    days=1
                )
                volume_data[token] = data
                
            return volume_data
        except Exception as e:
            logging.error(f"Error getting volume data: {str(e)}")
            return {}
    
    def _detect_volume_anomalies(self, volume_data: Dict) -> Optional[List[Dict]]:
        """Detect volume anomalies and generate signals"""
        signals = []
        try:
            for token, data in volume_data.items():
                anomalies = self._analyze_volume_patterns(data)
                if anomalies:
                    signals.append({
                        'type': 'volume_anomaly',
                        'token': token,
                        'anomaly_type': anomalies['type'],
                        'magnitude': anomalies['magnitude'],
                        'confidence': anomalies['confidence']
                    })
        except Exception as e:
            logging.error(f"Error detecting volume anomalies: {str(e)}")
        return signals if signals else None
    
    async def _execute_volume_strategy(self, signals: List[Dict]):
        """Execute trades based on volume signals"""
        for signal in signals:
            try:
                if signal['confidence'] >= self.config['risk_management']['min_confidence']:
                    trade_params = self._prepare_volume_trade(signal)
                    await self._execute_trade(trade_params)
            except Exception as e:
                logging.error(f"Error executing volume strategy: {str(e)}")
    
    async def _get_social_data(self) -> Dict:
        """Get social media sentiment data"""
        try:
            # Implementation for getting social media data
            social_data = {}
            tokens = self._get_tracked_tokens()
            
            # Add social media API integration here
            
            return social_data
        except Exception as e:
            logging.error(f"Error getting social data: {str(e)}")
            return {}
    
    def _analyze_social_sentiment(self, social_data: Dict) -> Optional[List[Dict]]:
        """Analyze social media sentiment and generate signals"""
        signals = []
        try:
            for token, data in social_data.items():
                sentiment = self._calculate_sentiment_score(data)
                if self._is_sentiment_signal(sentiment):
                    signals.append({
                        'type': 'sentiment',
                        'token': token,
                        'sentiment': sentiment['score'],
                        'trend': sentiment['trend'],
                        'confidence': sentiment['confidence']
                    })
        except Exception as e:
            logging.error(f"Error analyzing social sentiment: {str(e)}")
        return signals if signals else None
    
    async def _execute_sentiment_strategy(self, signals: List[Dict]):
        """Execute trades based on sentiment signals"""
        for signal in signals:
            try:
                if signal['confidence'] >= self.config['risk_management']['min_confidence']:
                    trade_params = self._prepare_sentiment_trade(signal)
                    await self._execute_trade(trade_params)
            except Exception as e:
                logging.error(f"Error executing sentiment strategy: {str(e)}")
    
    async def _execute_trade(self, trade_params: Dict):
        """Execute a trade with the given parameters"""
        try:
            # Implement trade execution logic here
            # This should interface with your Phantom wallet
            
            # Log trade
            self._log_trade(trade_params)
            
            # Update metrics
            await self._update_metrics(trade_params)
            
        except Exception as e:
            logging.error(f"Error executing trade: {str(e)}")
    
    def _log_trade(self, trade_params: Dict):
        """Log trade details to database"""
        try:
            with open('database/trade_history.json', 'r+') as f:
                trades = json.load(f)
                trades.append({
                    'timestamp': datetime.now().isoformat(),
                    **trade_params
                })
                f.seek(0)
                json.dump(trades, f, indent=4)
        except Exception as e:
            logging.error(f"Error logging trade: {str(e)}")
    
    async def _update_metrics(self, trade_params: Dict):
        """Update trading metrics after a trade"""
        try:
            with open('database/metrics.json', 'r+') as f:
                metrics = json.load(f)
                
                # Update relevant metrics
                metrics['total_trades'] += 1
                metrics['volume'] += trade_params['amount']
                
                if trade_params.get('profit'):
                    metrics['total_profit'] += trade_params['profit']
                    
                f.seek(0)
                json.dump(metrics, f, indent=4)
        except Exception as e:
            logging.error(f"Error updating metrics: {str(e)}")
    
    def get_trading_metrics(self) -> Dict:
        """Get current trading metrics"""
        try:
            # Calculate total profit/loss
            total_pnl = 0
            for trade in self.trade_history:
                # Convert percentage to decimal and multiply by position size
                profit_decimal = trade['profit'] / 100
                position_value = trade['amount'] * trade['price']
                trade_pnl = position_value * profit_decimal
                total_pnl += trade_pnl
            
            # Update wallet balance with profits/losses
            current_balance = round(self.initial_balance + total_pnl, 2)
            
            # Calculate win rate
            if self.total_trades > 0:
                win_rate = (self.winning_trades / self.total_trades) * 100
            else:
                win_rate = 0
                
            return {
                'wallet_balance': current_balance,
                'win_rate': win_rate,
                'total_trades': self.total_trades,
                'moonshots': sum(1 for trade in self.trade_history if trade['profit'] > 100),
                'active_positions': list(self.active_positions.values()),
                'recent_trades': self.trade_history[-10:]  # Keep last 10 trades
            }
            
        except Exception as e:
            logging.error(f"Error getting metrics: {str(e)}")
            return {
                'wallet_balance': self.practice_balance,
                'win_rate': 0,
                'total_trades': 0,
                'moonshots': 0,
                'active_positions': [],
                'recent_trades': []
            }
            
    def _load_config(self) -> Dict:
        """Load trading configuration"""
        try:
            with open('config/trading_config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading config: {str(e)}")
            return {}
            
    def stop(self):
        """Stop the trading engine"""
        self.running = False
        logging.info("Trading engine stopped")

if __name__ == "__main__":
    engine = TradingEngine()
    asyncio.run(engine.start())
