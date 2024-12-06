import asyncio
import logging
from datetime import datetime
from src.solana_trader import SolanaTrader
from src.analytics_dashboard import TradingDashboard
import json
import time
from typing import Dict, List
import pandas as pd
import streamlit as st

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LiveTestTrader:
    def __init__(self, config_path: str = 'config/rpc_config.json'):
        self.config_path = config_path
        self.test_balance = 100  # Start with 100 SOL test balance
        self.positions = {}
        self.trade_history = []
        self.start_time = datetime.now()
        
        # Performance tracking
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit_loss': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'average_win': 0,
            'average_loss': 0,
            'win_rate': 0
        }
        
        # Risk management
        self.risk_settings = {
            'max_position_size': 5,  # SOL
            'max_positions': 3,
            'stop_loss': 0.05,      # 5%
            'take_profit': 0.15,    # 15%
            'max_daily_loss': 10,   # SOL
            'trailing_stop': 0.02   # 2%
        }
        
    async def initialize(self):
        """Initialize trading bot and dashboard"""
        # Load config
        with open(self.config_path, 'r') as f:
            config = json.load(f)
            
        # Initialize trader
        self.trader = SolanaTrader(
            wallet_address=config['test_wallet_address'],
            private_key=config['test_private_key'],
            ocean_config_path=self.config_path
        )
        
        # Initialize dashboard with default data
        self.dashboard = TradingDashboard()
        initial_data = {
            'timestamp': datetime.now(),
            'total_value': self.test_balance,
            'positions': []
        }
        self.dashboard.update_data(
            portfolio_data=initial_data,
            trade_data=[],
            token_metrics={},
            risk_metrics={'risk_level': 0.1}
        )
        
        logging.info("Initialized test trader with 100 SOL")
        
    async def start_live_testing(self, duration_hours: float = 24):
        """Run live testing for specified duration"""
        try:
            await self.initialize()
            end_time = time.time() + (duration_hours * 3600)
            
            logging.info(f"Starting live testing for {duration_hours} hours")
            logging.info("Using practice balance - NO REAL FUNDS AT RISK")
            
            while time.time() < end_time:
                await self.trading_cycle()
                await asyncio.sleep(10)  # Check every 10 seconds
                
                # Print periodic updates
                await self.print_status()
                
        except Exception as e:
            logging.error(f"Error in live testing: {str(e)}")
        finally:
            await self.cleanup()
            
    async def trading_cycle(self):
        """Execute one trading cycle"""
        try:
            # 1. Update market data
            market_data = await self.trader.get_market_data()
            
            # 2. Check existing positions
            await self.manage_positions()
            
            # 3. Look for new opportunities
            if len(self.positions) < self.risk_settings['max_positions']:
                await self.scan_for_opportunities()
                
            # 4. Update metrics
            self.update_metrics()
            
            # Update dashboard
            await self.update_dashboard()
            
        except Exception as e:
            logging.error(f"Error in trading cycle: {str(e)}")
            
    async def manage_positions(self):
        """Manage existing positions"""
        for token, position in list(self.positions.items()):
            try:
                current_price = await self.trader._get_current_price(token)
                entry_price = position['entry_price']
                
                # Calculate profit/loss
                pnl_percent = (current_price - entry_price) / entry_price
                
                # Check stop loss
                if pnl_percent <= -self.risk_settings['stop_loss']:
                    await self.close_position(token, 'Stop loss hit')
                    continue
                    
                # Check take profit
                if pnl_percent >= self.risk_settings['take_profit']:
                    await self.close_position(token, 'Take profit hit')
                    continue
                    
                # Update trailing stop if applicable
                if pnl_percent > position.get('highest_pnl', 0):
                    position['highest_pnl'] = pnl_percent
                    position['trailing_stop'] = current_price * (1 - self.risk_settings['trailing_stop'])
                    
                # Check trailing stop
                if position.get('trailing_stop') and current_price < position['trailing_stop']:
                    await self.close_position(token, 'Trailing stop hit')
                    
            except Exception as e:
                logging.error(f"Error managing position {token}: {str(e)}")
                
    async def scan_for_opportunities(self):
        """Scan for new trading opportunities"""
        try:
            # Get potential tokens
            tokens = await self.trader.scan_market()
            
            for token in tokens:
                # Skip if we already have a position
                if token in self.positions:
                    continue
                    
                # Run security checks
                security = await self.trader.check_token_security(token)
                if not security['safe'] or security['score'] < 0.8:
                    continue
                    
                # Analyze token
                analysis = await self.trader.analyze_token(token)
                
                # Check if it's a good opportunity
                if self.is_good_opportunity(analysis):
                    await self.open_position(token, analysis)
                    
        except Exception as e:
            logging.error(f"Error scanning for opportunities: {str(e)}")
            
    def is_good_opportunity(self, analysis: Dict) -> bool:
        """Determine if token presents a good trading opportunity"""
        try:
            # Must meet all criteria
            conditions = [
                analysis['liquidity'] > 50000,  # Min $50k liquidity
                analysis['volume_24h'] > 10000,  # Min $10k daily volume
                analysis['holders'] > 100,      # Min 100 holders
                analysis.get('top_holders_percentage', 0) < 0.5,  # Max 50% top holders
                analysis.get('momentum_score', 0) > 0.7  # Strong momentum
            ]
            
            return all(conditions)
            
        except Exception as e:
            logging.error(f"Error evaluating opportunity: {str(e)}")
            return False
            
    async def open_position(self, token: str, analysis: Dict):
        """Open new position"""
        try:
            # Calculate position size
            size = min(
                self.risk_settings['max_position_size'],
                self.test_balance * 0.1  # Max 10% of balance per trade
            )
            
            # Simulate buy
            price = await self.trader._get_current_price(token)
            
            self.positions[token] = {
                'entry_price': price,
                'size': size,
                'time': datetime.now(),
                'highest_pnl': 0
            }
            
            self.test_balance -= size
            
            logging.info(f"Opened test position in {token}")
            logging.info(f"Size: {size} SOL, Price: {price}")
            
        except Exception as e:
            logging.error(f"Error opening position: {str(e)}")
            
    async def close_position(self, token: str, reason: str):
        """Close position"""
        try:
            position = self.positions[token]
            current_price = await self.trader._get_current_price(token)
            
            # Calculate profit/loss
            pnl = position['size'] * (current_price - position['entry_price']) / position['entry_price']
            
            # Update balance
            self.test_balance += position['size'] + pnl
            
            # Record trade
            self.trade_history.append({
                'token': token,
                'entry_price': position['entry_price'],
                'exit_price': current_price,
                'size': position['size'],
                'pnl': pnl,
                'duration': datetime.now() - position['time'],
                'reason': reason
            })
            
            # Remove position
            del self.positions[token]
            
            logging.info(f"Closed position in {token}")
            logging.info(f"PNL: {pnl:.3f} SOL, Reason: {reason}")
            
        except Exception as e:
            logging.error(f"Error closing position: {str(e)}")
            
    def update_metrics(self):
        """Update performance metrics"""
        if not self.trade_history:
            return
            
        self.metrics['total_trades'] = len(self.trade_history)
        
        profits = [t['pnl'] for t in self.trade_history if t['pnl'] > 0]
        losses = [t['pnl'] for t in self.trade_history if t['pnl'] <= 0]
        
        self.metrics['winning_trades'] = len(profits)
        self.metrics['losing_trades'] = len(losses)
        self.metrics['total_profit_loss'] = sum(t['pnl'] for t in self.trade_history)
        
        if profits:
            self.metrics['largest_win'] = max(profits)
            self.metrics['average_win'] = sum(profits) / len(profits)
            
        if losses:
            self.metrics['largest_loss'] = min(losses)
            self.metrics['average_loss'] = sum(losses) / len(losses)
            
        if self.metrics['total_trades'] > 0:
            self.metrics['win_rate'] = self.metrics['winning_trades'] / self.metrics['total_trades']
            
    async def update_dashboard(self):
        """Update dashboard with latest data"""
        portfolio_data = {
            'timestamp': datetime.now(),
            'total_value': self.test_balance + sum(pos['size'] for pos in self.positions.values()),
            'positions': [
                {
                    'token': token,
                    'amount': pos['size'],
                    'value': pos['size'] * await self.trader._get_current_price(token),
                    'pnl': pos['size'] * (await self.trader._get_current_price(token) - pos['entry_price']) / pos['entry_price'],
                    'time': pos['time']
                } for token, pos in self.positions.items()
            ]
        }
        
        trade_data = self.trade_history
        
        token_metrics = {
            'tokens': list(self.positions.keys()),
            'liquidity': [await self.trader.get_token_liquidity(token) for token in self.positions.keys()],
            'volume': [await self.trader.get_token_volume(token) for token in self.positions.keys()]
        }
        
        risk_metrics = {
            'risk_level': len(self.positions) / self.risk_settings['max_positions'],
            'position_distribution': [
                {'token': token, 'size': pos['size']} 
                for token, pos in self.positions.items()
            ],
            'alerts': []  # Add any security alerts here
        }
        
        self.dashboard.update_data(
            portfolio_data=portfolio_data,
            trade_data=trade_data,
            token_metrics=token_metrics,
            risk_metrics=risk_metrics
        )
        
    async def print_status(self):
        """Print current status to console"""
        logging.info("\n=== Test Trading Status ===")
        logging.info(f"Test Balance: {self.test_balance:.3f} SOL")
        logging.info(f"Open Positions: {len(self.positions)}")
        logging.info(f"Total Trades: {self.metrics['total_trades']}")
        logging.info(f"Win Rate: {self.metrics['win_rate']*100:.1f}%")
        logging.info(f"Total P/L: {self.metrics['total_profit_loss']:.3f} SOL")
        
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Close all positions
            for token in list(self.positions.keys()):
                await self.close_position(token, 'Test ended')
                
            # Save results
            self.save_results()
            
            # Shutdown dashboard
            await self.dashboard.shutdown()
            
        except Exception as e:
            logging.error(f"Error in cleanup: {str(e)}")
            
    def save_results(self):
        """Save test results to file"""
        try:
            # Convert trade history to DataFrame
            df = pd.DataFrame(self.trade_history)
            
            # Save to CSV
            filename = f"test_results_{self.start_time.strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            
            logging.info(f"Results saved to {filename}")
            
        except Exception as e:
            logging.error(f"Error saving results: {str(e)}")

if __name__ == "__main__":
    try:
        # Run live testing for 5 minutes instead of 24 hours
        trader = LiveTestTrader()
        asyncio.run(trader.start_live_testing(duration_hours=0.083))  # 5 minutes
    except KeyboardInterrupt:
        logging.info("Test stopped by user")
    except Exception as e:
        logging.error(f"Test failed with error: {str(e)}")
    finally:
        logging.info("Test complete")
