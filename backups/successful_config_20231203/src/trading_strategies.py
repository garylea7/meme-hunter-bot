from typing import Dict, List, Optional
import logging
from datetime import datetime
import json
from decimal import Decimal
import os
from dotenv import load_dotenv
from .market_analysis import MarketAnalyzer

logger = logging.getLogger(__name__)

class TradingStrategy:
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', False)
        self.risk_level = config.get('risk_level', 'medium')
        self.max_position_size = Decimal(str(config.get('max_position_size', '0.1')))
        self.stop_loss = Decimal(str(config.get('stop_loss', '0.05')))
        self.take_profit = Decimal(str(config.get('take_profit', '0.2')))

    def should_enter(self, market_data: Dict) -> bool:
        """Determine if we should enter a position"""
        raise NotImplementedError

    def should_exit(self, position_data: Dict, market_data: Dict) -> bool:
        """Determine if we should exit a position"""
        raise NotImplementedError

class WhaleFollowStrategy(TradingStrategy):
    def __init__(self, config: Dict):
        super().__init__('whale_follow', config)
        self.min_whale_transaction = Decimal(str(config.get('min_whale_transaction', '10000')))
        self.follow_delay = config.get('follow_delay_seconds', 30)
        self.min_liquidity = Decimal(str(config.get('min_liquidity', '100000')))

    def should_enter(self, market_data: Dict) -> bool:
        try:
            # Check if there's significant whale buying
            whale_buys = [move for move in market_data.get('whale_movements', [])
                         if move['type'] == 'buy' and 
                         Decimal(str(move['value_usd'])) >= self.min_whale_transaction]
            
            if not whale_buys:
                return False

            # Check liquidity
            if Decimal(str(market_data.get('liquidity_usd', 0))) < self.min_liquidity:
                return False

            # Check contract safety
            safety = market_data.get('safety_analysis', {})
            if safety.get('honeypot_risk') != 'safe' or safety.get('rugpull_risk') != 'safe':
                return False

            return True
        except Exception as e:
            logger.error(f"Error in whale follow strategy: {e}")
            return False

    def should_exit(self, position_data: Dict, market_data: Dict) -> bool:
        try:
            current_price = Decimal(str(market_data.get('price_usd', 0)))
            entry_price = Decimal(str(position_data.get('entry_price', 0)))
            
            if current_price == 0 or entry_price == 0:
                return False

            price_change = (current_price - entry_price) / entry_price
            
            # Check stop loss and take profit
            if price_change <= -self.stop_loss or price_change >= self.take_profit:
                return True

            # Exit if whales are selling
            recent_whale_sells = [move for move in market_data.get('whale_movements', [])
                                if move['type'] == 'sell' and 
                                Decimal(str(move['value_usd'])) >= self.min_whale_transaction]
            
            return len(recent_whale_sells) > 0
        except Exception as e:
            logger.error(f"Error in whale follow exit strategy: {e}")
            return False

class SentimentMomentumStrategy(TradingStrategy):
    def __init__(self, config: Dict):
        super().__init__('sentiment_momentum', config)
        self.min_sentiment_score = Decimal(str(config.get('min_sentiment_score', '0.7')))
        self.min_mentions = config.get('min_mentions', 1000)
        self.min_price_momentum = Decimal(str(config.get('min_price_momentum', '0.05')))

    def should_enter(self, market_data: Dict) -> bool:
        try:
            sentiment = market_data.get('social_sentiment', {})
            
            # Check overall sentiment score
            if Decimal(str(sentiment.get('overall_score', 0))) < self.min_sentiment_score:
                return False

            # Check social media activity
            twitter_data = sentiment.get('twitter', {})
            if twitter_data.get('mentions_24h', 0) < self.min_mentions:
                return False

            # Check price momentum
            price_change_24h = Decimal(str(market_data.get('price_change_24h', 0)))
            if price_change_24h < self.min_price_momentum:
                return False

            # Verify token safety
            safety = market_data.get('safety_analysis', {})
            if safety.get('safety_score', 0) < 70:
                return False

            return True
        except Exception as e:
            logger.error(f"Error in sentiment momentum strategy: {e}")
            return False

    def should_exit(self, position_data: Dict, market_data: Dict) -> bool:
        try:
            current_price = Decimal(str(market_data.get('price_usd', 0)))
            entry_price = Decimal(str(position_data.get('entry_price', 0)))
            
            if current_price == 0 or entry_price == 0:
                return False

            price_change = (current_price - entry_price) / entry_price
            
            # Check stop loss and take profit
            if price_change <= -self.stop_loss or price_change >= self.take_profit:
                return True

            # Check if sentiment has turned negative
            sentiment = market_data.get('social_sentiment', {})
            if Decimal(str(sentiment.get('overall_score', 0))) < Decimal('0.4'):
                return True

            return False
        except Exception as e:
            logger.error(f"Error in sentiment momentum exit strategy: {e}")
            return False

class AutoSniper(TradingStrategy):
    def __init__(self, config: Dict):
        super().__init__('auto_sniper', config)
        self.min_initial_liquidity = Decimal(str(config.get('min_initial_liquidity', '50000')))
        self.max_buy_tax = Decimal(str(config.get('max_buy_tax', '10')))
        self.max_sell_tax = Decimal(str(config.get('max_sell_tax', '10')))
        self.required_contract_features = config.get('required_contract_features', [])

    def should_enter(self, market_data: Dict) -> bool:
        try:
            # Check initial liquidity
            if Decimal(str(market_data.get('liquidity_usd', 0))) < self.min_initial_liquidity:
                return False

            # Check taxes
            if (Decimal(str(market_data.get('buy_tax', 100))) > self.max_buy_tax or
                Decimal(str(market_data.get('sell_tax', 100))) > self.max_sell_tax):
                return False

            # Verify contract safety
            safety = market_data.get('safety_analysis', {})
            if not safety.get('contract_verified'):
                return False
            
            if safety.get('honeypot_risk') != 'safe':
                return False

            # Check required contract features
            contract_features = set(market_data.get('contract_features', []))
            required_features = set(self.required_contract_features)
            if not required_features.issubset(contract_features):
                return False

            return True
        except Exception as e:
            logger.error(f"Error in auto sniper strategy: {e}")
            return False

    def should_exit(self, position_data: Dict, market_data: Dict) -> bool:
        try:
            current_price = Decimal(str(market_data.get('price_usd', 0)))
            entry_price = Decimal(str(position_data.get('entry_price', 0)))
            
            if current_price == 0 or entry_price == 0:
                return False

            price_change = (current_price - entry_price) / entry_price
            
            # Check stop loss and take profit
            if price_change <= -self.stop_loss or price_change >= self.take_profit:
                return True

            # Exit if safety concerns arise
            safety = market_data.get('safety_analysis', {})
            if (safety.get('honeypot_risk') != 'safe' or 
                safety.get('rugpull_risk') != 'safe'):
                return True

            return False
        except Exception as e:
            logger.error(f"Error in auto sniper exit strategy: {e}")
            return False

class MemeSniper(TradingStrategy):
    def __init__(self, config: Dict):
        super().__init__('meme_sniper', config)
        self.min_liquidity = Decimal(str(config.get('min_liquidity', '10000')))  # Lower for memecoins
        self.max_holders = config.get('max_holders', 1000)  # Want to get in early
        self.min_social_engagement = config.get('min_social_engagement', 100)
        self.max_dev_wallet = Decimal(str(config.get('max_dev_wallet', '15')))  # Max % held by dev
        self.required_socials = config.get('required_socials', ['twitter', 'telegram'])

    def should_enter(self, market_data: Dict) -> bool:
        try:
            # Check if token is too old
            launch_time = market_data.get('launch_time', 0)
            if (datetime.now().timestamp() - launch_time) > 86400:  # 24 hours
                return False

            # Check liquidity
            if Decimal(str(market_data.get('liquidity_usd', 0))) < self.min_liquidity:
                return False

            # Check holder count - want to be early
            if market_data.get('holder_count', 0) > self.max_holders:
                return False

            # Check dev wallet %
            dev_wallet = Decimal(str(market_data.get('dev_wallet_percentage', 100)))
            if dev_wallet > self.max_dev_wallet:
                return False

            # Check social presence
            socials = market_data.get('social_links', {})
            if not all(platform in socials for platform in self.required_socials):
                return False

            # Check social engagement
            social_data = market_data.get('social_metrics', {})
            total_engagement = sum(
                social_data.get(platform, {}).get('engagement', 0) 
                for platform in ['twitter', 'telegram', 'tiktok']
            )
            if total_engagement < self.min_social_engagement:
                return False

            return True
        except Exception as e:
            logger.error(f"Error in meme sniper strategy: {e}")
            return False

    def should_exit(self, position_data: Dict, market_data: Dict) -> bool:
        try:
            current_price = Decimal(str(market_data.get('price_usd', 0)))
            entry_price = Decimal(str(position_data.get('entry_price', 0)))
            
            if current_price == 0 or entry_price == 0:
                return False

            price_change = (current_price - entry_price) / entry_price
            
            # Quick take profit for memecoins
            if price_change >= self.take_profit:
                return True

            # Stricter stop loss for memecoins
            if price_change <= -self.stop_loss:
                return True

            # Exit if social engagement drops significantly
            current_engagement = sum(
                market_data.get('social_metrics', {}).get(platform, {}).get('engagement', 0)
                for platform in ['twitter', 'telegram', 'tiktok']
            )
            initial_engagement = position_data.get('initial_social_engagement', 0)
            if initial_engagement > 0 and current_engagement < initial_engagement * 0.5:
                return True

            return False
        except Exception as e:
            logger.error(f"Error in meme sniper exit strategy: {e}")
            return False

class StrategyManager:
    def __init__(self):
        load_dotenv()
        self.market_analyzer = MarketAnalyzer()
        self.strategies = {}
        self._load_strategies()

    def _load_strategies(self):
        """Load strategy configurations from environment or config file"""
        try:
            # Load strategy configs
            strategy_configs = {
                'whale_follow': {
                    'enabled': True,
                    'risk_level': 'medium',
                    'max_position_size': 0.1,
                    'stop_loss': 0.05,
                    'take_profit': 0.2,
                    'min_whale_transaction': 10000,
                    'min_liquidity': 100000
                },
                'sentiment_momentum': {
                    'enabled': True,
                    'risk_level': 'high',
                    'max_position_size': 0.05,
                    'stop_loss': 0.1,
                    'take_profit': 0.3,
                    'min_sentiment_score': 0.7,
                    'min_mentions': 1000
                },
                'auto_sniper': {
                    'enabled': True,
                    'risk_level': 'high',
                    'max_position_size': 0.05,
                    'stop_loss': 0.1,
                    'take_profit': 0.5,
                    'min_initial_liquidity': 50000,
                    'max_buy_tax': 10,
                    'max_sell_tax': 10,
                    'required_contract_features': ['anti_bot', 'locked_liquidity']
                },
                'meme_sniper': {
                    'enabled': True,
                    'risk_level': 'high',
                    'max_position_size': 0.05,
                    'stop_loss': 0.1,
                    'take_profit': 0.5,
                    'min_liquidity': 10000,
                    'max_holders': 1000,
                    'min_social_engagement': 100,
                    'max_dev_wallet': 15,
                    'required_socials': ['twitter', 'telegram']
                }
            }

            # Initialize strategy instances
            self.strategies['whale_follow'] = WhaleFollowStrategy(strategy_configs['whale_follow'])
            self.strategies['sentiment_momentum'] = SentimentMomentumStrategy(strategy_configs['sentiment_momentum'])
            self.strategies['auto_sniper'] = AutoSniper(strategy_configs['auto_sniper'])
            self.strategies['meme_sniper'] = MemeSniper(strategy_configs['meme_sniper'])

        except Exception as e:
            logger.error(f"Error loading strategies: {e}")

    def evaluate_token(self, token_address: str) -> Dict:
        """Evaluate a token against all enabled strategies"""
        try:
            # Gather market data
            market_data = {
                'whale_movements': self.market_analyzer.get_whale_movements(token_address),
                'social_sentiment': self.market_analyzer.get_social_sentiment(token_address),
                **self.market_analyzer.get_market_metrics(token_address),
                'safety_analysis': self.market_analyzer.analyze_token_safety(token_address)
            }

            # Evaluate each strategy
            results = {}
            for name, strategy in self.strategies.items():
                if strategy.enabled:
                    results[name] = {
                        'should_enter': strategy.should_enter(market_data),
                        'config': strategy.config
                    }

            return {
                'market_data': market_data,
                'strategy_results': results
            }
        except Exception as e:
            logger.error(f"Error evaluating token: {e}")
            return {}
