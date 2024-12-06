import requests
import pandas as pd
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from .ai_analysis import AIAnalyzer
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self):
        load_dotenv()
        self.dextools_api_key = os.getenv('DEXTOOLS_API_KEY')
        self.dexscreener_api_key = os.getenv('DEXSCREENER_API_KEY')
        self.bullx_api_key = os.getenv('BULLX_API_KEY')
        self.ai_analyzer = AIAnalyzer()
        
        # Minimum transaction value to consider as whale movement
        self.whale_threshold = float(os.getenv('WHALE_THRESHOLD', '10000'))  # in USD
        
        # Cache for API responses
        self._cache = {}
        self._cache_duration = timedelta(minutes=5)
        
        self.api_endpoints = {
            'dexscreener': 'https://api.dexscreener.com/latest/dex/tokens/',
            'coingecko': 'https://api.coingecko.com/api/v3/',
            'twitter': 'https://api.twitter.com/2/',
            'telegram': 'https://api.telegram.org/'
        }
        self.cache_duration = 30  # 30 seconds cache
        self._realtime_cache = {}
        
    async def get_realtime_data(self, token_address: str) -> Dict:
        """Get comprehensive real-time market data"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._get_price_data(session, token_address),
                self._get_social_data(session, token_address),
                self._get_whale_data(session, token_address),
                self._get_exchange_signals(session, token_address)
            ]
            results = await asyncio.gather(*tasks)
            
            return {
                'price_data': results[0],
                'social_data': results[1],
                'whale_data': results[2],
                'exchange_signals': results[3],
                'timestamp': datetime.utcnow().isoformat()
            }
            
    async def _get_price_data(self, session, token_address: str) -> Dict:
        """Real-time price and volume data"""
        endpoint = f"{self.api_endpoints['dexscreener']}{token_address}"
        try:
            async with session.get(endpoint) as response:
                data = await response.json()
                return {
                    'price': data.get('priceUsd'),
                    'price_change_24h': data.get('priceChange24h'),
                    'volume_24h': data.get('volume24h'),
                    'liquidity': data.get('liquidity'),
                    'holders': data.get('holderCount')
                }
        except Exception as e:
            logging.error(f"Error fetching price data: {str(e)}")
            return {}
            
    async def _get_social_data(self, session, token_address: str) -> Dict:
        """Real-time social media metrics"""
        # Implementation for Twitter and Telegram API calls
        return {
            'twitter_mentions': await self._get_twitter_mentions(session, token_address),
            'telegram_members': await self._get_telegram_members(session, token_address),
            'influencer_mentions': await self._get_influencer_mentions(session, token_address)
        }
        
    async def _get_whale_data(self, session, token_address: str) -> Dict:
        """Track whale wallet movements"""
        # Implementation for blockchain API calls
        return {
            'recent_transactions': [],
            'whale_holdings': {},
            'liquidity_changes': []
        }
        
    async def _get_exchange_signals(self, session, token_address: str) -> Dict:
        """Detect potential exchange listing signals"""
        return {
            'exchange_wallet_interactions': [],
            'listing_hints': [],
            'volume_spikes': []
        }
        
    def get_whale_movements(self, token_address: str) -> List[Dict]:
        """Track large transactions for a given token"""
        try:
            url = f"https://api.dextools.io/v1/token/{token_address}/trades"
            headers = {"X-API-Key": self.dextools_api_key}
            response = requests.get(url, headers=headers)
            trades = response.json()

            whale_moves = []
            for trade in trades:
                if float(trade.get('value_usd', 0)) >= self.whale_threshold:
                    whale_moves.append({
                        'timestamp': trade['timestamp'],
                        'type': trade['type'],
                        'value_usd': trade['value_usd'],
                        'wallet': trade['maker'],
                        'tx_hash': trade['transaction_hash']
                    })
            return whale_moves
        except Exception as e:
            logger.error(f"Error fetching whale movements: {e}")
            return []

    def get_social_sentiment(self, token_address: str) -> Dict:
        """Analyze social media sentiment for a token"""
        try:
            # Aggregate sentiment from multiple sources
            sentiment_data = {
                'twitter': self._get_twitter_sentiment(token_address),
                'telegram': self._get_telegram_sentiment(token_address),
                'overall_score': 0  # Will be calculated
            }
            
            # Calculate overall sentiment score
            weights = {'twitter': 0.6, 'telegram': 0.4}
            sentiment_data['overall_score'] = (
                sentiment_data['twitter']['score'] * weights['twitter'] +
                sentiment_data['telegram']['score'] * weights['telegram']
            )
            
            return sentiment_data
        except Exception as e:
            logger.error(f"Error analyzing social sentiment: {e}")
            return {'overall_score': 0, 'twitter': {}, 'telegram': {}}

    def _get_twitter_sentiment(self, token_address: str) -> Dict:
        """Analyze Twitter sentiment"""
        # Implementation would use Twitter API to gather mentions and analyze sentiment
        # For demo, returning mock data
        return {
            'score': 0.75,
            'mentions_24h': 1500,
            'positive_ratio': 0.8,
            'trending_hashtags': ['#memecoin', '#tothemoon']
        }

    def _get_telegram_sentiment(self, token_address: str) -> Dict:
        """Analyze Telegram sentiment"""
        # Implementation would use Telegram API to analyze group activity
        # For demo, returning mock data
        return {
            'score': 0.65,
            'group_members': 25000,
            'messages_24h': 3500,
            'active_users': 1200
        }

    def get_market_metrics(self, token_address: str) -> Dict:
        """Get comprehensive market metrics from DEX tools and scanners"""
        try:
            # Combine data from multiple sources
            dextools_data = self._get_dextools_metrics(token_address)
            dexscreener_data = self._get_dexscreener_metrics(token_address)
            
            return {
                'price_usd': dextools_data.get('price_usd'),
                'price_change_24h': dextools_data.get('price_change_24h'),
                'volume_24h': dextools_data.get('volume_24h'),
                'liquidity_usd': dexscreener_data.get('liquidity_usd'),
                'market_cap': dextools_data.get('market_cap'),
                'holders': dextools_data.get('holders'),
                'buy_tax': dexscreener_data.get('buy_tax'),
                'sell_tax': dexscreener_data.get('sell_tax'),
                'liquidity_locked': dexscreener_data.get('liquidity_locked'),
                'contract_verified': dexscreener_data.get('contract_verified')
            }
        except Exception as e:
            logger.error(f"Error fetching market metrics: {e}")
            return {}

    def _get_dextools_metrics(self, token_address: str) -> Dict:
        """Fetch metrics from DEXTools"""
        cache_key = f'dextools_{token_address}'
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            url = f"https://api.dextools.io/v1/token/{token_address}"
            headers = {"X-API-Key": self.dextools_api_key}
            response = requests.get(url, headers=headers)
            data = response.json()
            
            self._cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error fetching DEXTools metrics: {e}")
            return {}

    def _get_dexscreener_metrics(self, token_address: str) -> Dict:
        """Fetch metrics from DEXScreener"""
        cache_key = f'dexscreener_{token_address}'
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            headers = {"X-API-Key": self.dexscreener_api_key}
            response = requests.get(url, headers=headers)
            data = response.json()
            
            self._cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error fetching DEXScreener metrics: {e}")
            return {}

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache:
            return False
        
        cache_time = self._cache.get(f"{key}_time")
        if not cache_time:
            return False
            
        return datetime.now() - cache_time < self._cache_duration

    def analyze_token_safety(self, token_address: str) -> Dict:
        """Analyze token contract for potential risks using multiple AI models"""
        try:
            # Get comprehensive AI analysis
            ai_analysis = self.ai_analyzer.analyze_token(token_address)
            
            # Extract the most relevant information
            return {
                'ai_comparison': {
                    'bullx_score': ai_analysis.get('bullx', {}).get('safety_score', 0),
                    'gmgn_score': ai_analysis.get('gmgn', {}).get('safety_score', 0),
                    'agreement_level': ai_analysis.get('comparison', {}).get('overall_agreement', 0)
                },
                'risks': {
                    'honeypot_risk': ai_analysis.get('bullx', {}).get('honeypot_risk'),
                    'rugpull_risk': ai_analysis.get('bullx', {}).get('rugpull_risk'),
                    'contract_risks': ai_analysis.get('bullx', {}).get('contract_risks', []),
                    'wash_trading': ai_analysis.get('gmgn', {}).get('market_analysis', {}).get('wash_trading', False)
                },
                'predictions': {
                    'bullx_prediction': ai_analysis.get('bullx', {}).get('ai_prediction', {}),
                    'gmgn_prediction': ai_analysis.get('gmgn', {}).get('ai_prediction', {}),
                },
                'recommendation': ai_analysis.get('recommendation', {}),
                'strengths': ai_analysis.get('recommendation', {}).get('strengths', []),
                'concerns': ai_analysis.get('recommendation', {}).get('concerns', [])
            }
        except Exception as e:
            logger.error(f"Error analyzing token safety: {e}")
            return {}

    def get_trading_opportunities(self) -> List[Dict]:
        """Identify potential trading opportunities based on various metrics"""
        try:
            opportunities = []
            # Implementation would analyze multiple tokens and identify opportunities
            # based on whale movements, social sentiment, and market metrics
            return opportunities
        except Exception as e:
            logger.error(f"Error finding trading opportunities: {e}")
            return []
