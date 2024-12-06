import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import logging
from typing import Dict, List, Optional
import os
from pathlib import Path
from src.solana_trader import SolanaTrader
from src.market_analysis import MarketAnalyzer
from src.trading_strategies import StrategyManager
from decimal import Decimal
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingDashboard:
    def __init__(self):
        self.data_dir = Path("dashboard_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.market_analyzer = MarketAnalyzer()
        self.strategy_manager = StrategyManager()
        
        # Initialize trading bot with configuration
        try:
            wallet_address = os.environ.get('WALLET_ADDRESS')
            private_key = os.environ.get('PRIVATE_KEY')
            config_path = os.environ.get('OCEAN_CONFIG_PATH', 'config.json')
            
            logger.info(f"Initializing with wallet: {wallet_address}")
            
            if not all([wallet_address, private_key]):
                logger.warning("Trading bot credentials not found. Running in demo mode.")
                self._demo_mode = True
            else:
                logger.info("Credentials found, initializing trader...")
                self.trader = SolanaTrader(
                    wallet_address=wallet_address,
                    private_key=private_key,
                    ocean_config_path=config_path
                )
                self._demo_mode = False
                logger.info("Trader initialized successfully!")
        except Exception as e:
            logger.error(f"Error initializing trading bot: {e}")
            self._demo_mode = True
        
        # Initialize with default values
        self._portfolio = {
            'timestamp': datetime.now().isoformat(),
            'total_value': 0.0,
            'positions': []
        }
        self._trades = []
        self._last_24h_value = None
        self._tracked_tokens = self._load_tracked_tokens()
        self._whale_alerts = []
        self._trading_opportunities = []
        
        # Load existing data
        self._load_data()
        
        if self._demo_mode:
            self._initialize_demo_data()
    
    def _load_tracked_tokens(self) -> List[Dict]:
        """Load list of tokens to track"""
        try:
            file_path = self.data_dir / "tracked_tokens.json"
            if file_path.exists():
                with open(file_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tracked tokens: {e}")
        return []
    
    def _save_tracked_tokens(self):
        """Save tracked tokens list"""
        try:
            with open(self.data_dir / "tracked_tokens.json", "w") as f:
                json.dump(self._tracked_tokens, f)
        except Exception as e:
            logger.error(f"Error saving tracked tokens: {e}")
    
    def add_tracked_token(self, token_address: str, name: str = None):
        """Add a token to track"""
        if not any(t['address'] == token_address for t in self._tracked_tokens):
            self._tracked_tokens.append({
                'address': token_address,
                'name': name,
                'added_at': datetime.now().isoformat()
            })
            self._save_tracked_tokens()
    
    def remove_tracked_token(self, token_address: str):
        """Remove a token from tracking"""
        self._tracked_tokens = [t for t in self._tracked_tokens if t['address'] != token_address]
        self._save_tracked_tokens()
    
    def _initialize_demo_data(self):
        """Initialize demo data for testing"""
        self._portfolio = {
            'timestamp': datetime.now().isoformat(),
            'total_value': 1000.0,
            'positions': [
                {
                    'token': 'SOL',
                    'amount': 10.5,
                    'value': 500.0
                },
                {
                    'token': 'RAY',
                    'amount': 100.0,
                    'value': 250.0
                }
            ]
        }
        
        # Generate some demo trades
        self._trades = [
            {
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                'token': 'SOL',
                'type': 'buy' if i % 2 == 0 else 'sell',
                'amount': 1.0,
                'price': 50.0,
                'pnl': 5.0 if i % 3 == 0 else -3.0
            }
            for i in range(10)
        ]
        
        self._last_24h_value = 950.0  # For demo 24h change
        
        # Demo whale alerts
        self._whale_alerts = [
            {
                'timestamp': (datetime.now() - timedelta(minutes=30)).isoformat(),
                'token': 'BONK',
                'type': 'buy',
                'value_usd': 50000,
                'wallet': '0x1234...abcd'
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'token': 'WEN',
                'type': 'sell',
                'value_usd': 75000,
                'wallet': '0xabcd...1234'
            }
        ]
        
        # Demo trading opportunities
        self._trading_opportunities = [
            {
                'token': 'MYRO',
                'address': '0x1234...5678',
                'signal_type': 'whale_accumulation',
                'confidence': 0.85,
                'metrics': {
                    'price_usd': 0.00001234,
                    'volume_24h': 500000,
                    'social_score': 0.8
                }
            },
            {
                'token': 'POPCAT',
                'address': '0xabcd...efgh',
                'signal_type': 'viral_momentum',
                'confidence': 0.75,
                'metrics': {
                    'price_usd': 0.00000789,
                    'volume_24h': 300000,
                    'social_score': 0.9
                }
            }
        ]
            
    def _load_data(self):
        """Load data from files"""
        try:
            portfolio_file = self.data_dir / "portfolio.json"
            trades_file = self.data_dir / "trades.json"
            whale_alerts_file = self.data_dir / "whale_alerts.json"
            opportunities_file = self.data_dir / "opportunities.json"
            
            if portfolio_file.exists():
                with open(portfolio_file, "r") as f:
                    self._portfolio = json.load(f)
                    
            if trades_file.exists():
                with open(trades_file, "r") as f:
                    self._trades = json.load(f)
                    
            if whale_alerts_file.exists():
                with open(whale_alerts_file, "r") as f:
                    self._whale_alerts = json.load(f)
                    
            if opportunities_file.exists():
                with open(opportunities_file, "r") as f:
                    self._trading_opportunities = json.load(f)
                    
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            
    def _save_data(self):
        """Save data to files"""
        if not self._demo_mode:  # Only save data in live mode
            try:
                with open(self.data_dir / "portfolio.json", "w") as f:
                    json.dump(self._portfolio, f)
                    
                with open(self.data_dir / "trades.json", "w") as f:
                    json.dump(self._trades[-1000:], f)
                    
                with open(self.data_dir / "whale_alerts.json", "w") as f:
                    json.dump(self._whale_alerts[-100:], f)
                    
                with open(self.data_dir / "opportunities.json", "w") as f:
                    json.dump(self._trading_opportunities, f)
                    
            except Exception as e:
                logger.error(f"Error saving data: {e}")
            
    async def update_data(self, force: bool = False):
        """Update all dashboard data"""
        if not self._demo_mode or force:
            await self._update_portfolio()
            await self._update_trades()
            await self._update_market_data()
            await self._update_trading_signals()
            
    async def _update_portfolio(self):
        """Update portfolio data from trading bot"""
        try:
            if not self._demo_mode and hasattr(self, 'trader'):
                logger.info("Getting real wallet balance...")
                try:
                    balance = await self.trader.get_wallet_balance()
                    logger.info(f"Wallet balance: ${balance:.2f}")
                    
                    # Update portfolio
                    self._portfolio = {
                        'timestamp': datetime.now().isoformat(),
                        'total_value': float(balance),  # Ensure it's a float
                        'positions': []  # We'll implement position tracking later
                    }
                    
                    # Save the current value for 24h comparison if needed
                    if self._last_24h_value is None:
                        self._last_24h_value = float(balance)
                        
                    self._save_data()
                    logger.info("Portfolio updated with real balance")
                except Exception as e:
                    logger.error(f"Error getting wallet balance: {e}")
                    raise
            else:
                logger.warning("Using demo mode, not fetching real balance")
                # In demo mode, just update the timestamp
                self._portfolio['timestamp'] = datetime.now().isoformat()
                
        except Exception as e:
            logger.error(f"Error in _update_portfolio: {e}")
            # Don't hide the error, let it propagate
            raise
            
    async def _update_trades(self):
        """Update trades from trading bot"""
        if self._demo_mode:
            return  # No updates needed in demo mode
            
        try:
            # Get new trades since last update
            last_trade_time = None
            if self._trades:
                last_trade_time = datetime.fromisoformat(self._trades[-1]['timestamp'])
            
            new_trades = self.trader.get_trades(since=last_trade_time)
            if new_trades:
                self._trades.extend(new_trades)
                if len(self._trades) > 1000:
                    self._trades = self._trades[-1000:]
                self._save_data()
                
        except Exception as e:
            logger.error(f"Error updating trades: {e}")
            
    async def _update_market_data(self):
        """Update market data for tracked tokens"""
        try:
            for token in self._tracked_tokens:
                # Get whale movements
                whale_moves = self.market_analyzer.get_whale_movements(token['address'])
                if whale_moves:
                    self._whale_alerts.extend(whale_moves)
                    if len(self._whale_alerts) > 100:
                        self._whale_alerts = self._whale_alerts[-100:]
                
                # Update token metrics
                token.update(self.market_analyzer.get_market_metrics(token['address']))
                
            self._save_data()
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
            
    async def _update_trading_signals(self):
        """Update trading signals and opportunities"""
        try:
            new_opportunities = []
            for token in self._tracked_tokens:
                evaluation = self.strategy_manager.evaluate_token(token['address'])
                
                # Check if any strategy suggests entering
                signals = evaluation.get('strategy_results', {})
                if any(s.get('should_enter', False) for s in signals.values()):
                    new_opportunities.append({
                        'token': token.get('name', token['address']),
                        'address': token['address'],
                        'signal_type': 'strategy_signal',
                        'confidence': max(s.get('confidence', 0) for s in signals.values()),
                        'metrics': evaluation.get('market_data', {})
                    })
            
            self._trading_opportunities = new_opportunities
            self._save_data()
        except Exception as e:
            logger.error(f"Error updating trading signals: {e}")
            
    def get_portfolio_value(self) -> float:
        """Get current portfolio value"""
        self._update_portfolio()
        return self._portfolio.get('total_value', 0.0)
            
    def get_24h_change(self) -> float:
        """Get 24h change percentage"""
        try:
            current = self._portfolio.get('total_value', 0.0)
            if self._last_24h_value and self._last_24h_value > 0:
                return ((current - self._last_24h_value) / self._last_24h_value) * 100
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating 24h change: {e}")
            return 0.0
            
    def get_total_pnl(self) -> float:
        """Get total profit/loss"""
        try:
            return sum(float(trade.get('pnl', 0)) for trade in self._trades)
        except Exception as e:
            logger.error(f"Error calculating total PnL: {e}")
            return 0.0
            
    def get_active_positions(self) -> List[Dict]:
        """Get current active positions"""
        self._update_portfolio()
        return self._portfolio.get('positions', [])
            
    def get_win_loss_ratio(self) -> Dict:
        """Get win/loss statistics"""
        try:
            self._update_trades()
            wins = len([t for t in self._trades if float(t.get('pnl', 0)) > 0])
            losses = len([t for t in self._trades if float(t.get('pnl', 0)) <= 0])
            total = wins + losses
            return {
                'wins': wins,
                'losses': losses,
                'ratio': (wins / total) if total > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error calculating win/loss ratio: {e}")
            return {'wins': 0, 'losses': 0, 'ratio': 0}
            
    def get_whale_alerts(self) -> List[Dict]:
        """Get recent whale movements"""
        return self._whale_alerts
        
    def get_trading_opportunities(self) -> List[Dict]:
        """Get current trading opportunities"""
        return self._trading_opportunities
        
    def get_token_analysis(self, token_address: str) -> Dict:
        """Get comprehensive token analysis"""
        try:
            return {
                'market_metrics': self.market_analyzer.get_market_metrics(token_address),
                'social_sentiment': self.market_analyzer.get_social_sentiment(token_address),
                'safety_analysis': self.market_analyzer.analyze_token_safety(token_address),
                'strategy_evaluation': self.strategy_manager.evaluate_token(token_address)
            }
        except Exception as e:
            logger.error(f"Error analyzing token: {e}")
            return {}
