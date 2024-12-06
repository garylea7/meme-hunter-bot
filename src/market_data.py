import aiohttp
import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import json
from collections import defaultdict
from pycoingecko import CoinGeckoAPI
from binance.client import Client
import requests

logger = logging.getLogger(__name__)

class MarketDataHandler:
    def __init__(self):
        # Initialize APIs
        self.coingecko = CoinGeckoAPI()
        self.binance = Client(None, None)  # Public API doesn't need keys
        
        # Token IDs for different platforms
        self.token_ids = {
            'PEPE': {
                'coingecko': 'pepe',
                'binance': 'PEPEUSDT',
                'poocoin': '0x6982508145454ce325ddbe47a25d4ec3d2311933'
            },
            'DOGE': {
                'coingecko': 'dogecoin',
                'binance': 'DOGEUSDT',
                'poocoin': None  # Not on BSC
            },
            'SHIB': {
                'coingecko': 'shiba-inu',
                'binance': 'SHIBUSDT',
                'poocoin': '0x2859e4544c4bb03966803b044a93563bd2d0dd4d'
            },
            'FLOKI': {
                'coingecko': 'floki',
                'binance': 'FLOKIUSDT',
                'poocoin': '0xcf0c122c6b73ff809c693db761e7baebe62b6a2e'
            },
            'WOJAK': {
                'coingecko': 'wojak',
                'binance': None,
                'poocoin': '0x5344c20fd242545f31723689662ac12b9556fc3d'
            }
        }
        
        # Cache settings - much shorter duration
        self._cache = {}
        self._cache_duration = timedelta(seconds=5)  # Update every 5 seconds
        
        # API rate limits - more aggressive
        self._last_request = defaultdict(lambda: datetime.now() - timedelta(minutes=1))
        self._rate_limits = {
            'coingecko': 0.2,  # 300 calls per minute
            'binance': 0.05,   # 1200 calls per minute
            'poocoin': 0.1     # 600 calls per minute
        }
        
    async def get_token_data(self, token_symbol: str) -> Optional[Dict]:
        """Get comprehensive token data from multiple sources"""
        try:
            # Check cache but with very short duration
            if token_symbol in self._cache:
                cached = self._cache[token_symbol]
                if datetime.now() - cached['timestamp'] < self._cache_duration:
                    return cached['data']
            
            # Get data from multiple sources
            tasks = [
                self._get_binance_data(token_symbol),  # Fastest API first
                self._get_poocoin_data(token_symbol),  # Second fastest
                self._get_coingecko_data(token_symbol)  # Backup source
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            valid_results = [r for r in results if isinstance(r, dict)]
            
            if not valid_results:
                logger.warning(f"No valid data found for {token_symbol}")
                return None
            
            # Merge data preferring real-time sources
            merged_data = self._merge_token_data(valid_results)
            if merged_data:
                self._cache[token_symbol] = {
                    'data': merged_data,
                    'timestamp': datetime.now()
                }
                return merged_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching token data: {str(e)}")
            return None
            
    async def _get_coingecko_data(self, token_symbol: str) -> Optional[Dict]:
        """Get data from CoinGecko"""
        try:
            # Respect rate limit
            await self._wait_for_rate_limit('coingecko')
            
            token_id = self.token_ids[token_symbol]['coingecko']
            data = self.coingecko.get_coin_by_id(
                token_id,
                localization=False,
                tickers=True,
                market_data=True,
                community_data=False,
                developer_data=False
            )
            
            return {
                'price': data['market_data']['current_price']['usd'],
                'volume_24h': data['market_data']['total_volume']['usd'],
                'price_change_24h': data['market_data']['price_change_percentage_24h'],
                'market_cap': data['market_data']['market_cap']['usd'],
                'fully_diluted_valuation': data['market_data'].get('fully_diluted_valuation', {}).get('usd', 0),
                'total_supply': data['market_data']['total_supply'],
                'max_supply': data['market_data'].get('max_supply', 0),
                'source': 'coingecko'
            }
            
        except Exception as e:
            logger.error(f"CoinGecko error for {token_symbol}: {str(e)}")
            return None
            
    async def _get_binance_data(self, token_symbol: str) -> Optional[Dict]:
        """Get data from Binance"""
        try:
            symbol = self.token_ids[token_symbol].get('binance')
            if not symbol:
                return None
                
            # Respect rate limit
            await self._wait_for_rate_limit('binance')
            
            # Get 24h ticker
            ticker = self.binance.get_ticker(symbol=symbol)
            
            return {
                'price': float(ticker['lastPrice']),
                'volume_24h': float(ticker['volume']) * float(ticker['lastPrice']),
                'price_change_24h': float(ticker['priceChangePercent']),
                'high_24h': float(ticker['highPrice']),
                'low_24h': float(ticker['lowPrice']),
                'source': 'binance'
            }
            
        except Exception as e:
            logger.error(f"Binance error for {token_symbol}: {str(e)}")
            return None
            
    async def _get_poocoin_data(self, token_symbol: str) -> Optional[Dict]:
        """Get data from PooCoin API"""
        try:
            contract = self.token_ids[token_symbol].get('poocoin')
            if not contract:
                return None
                
            # Respect rate limit
            await self._wait_for_rate_limit('poocoin')
            
            async with aiohttp.ClientSession() as session:
                url = f"https://api.poocoin.app/tokens/{contract}"
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                        
                    data = await response.json()
                    
                    return {
                        'price': float(data['price']),
                        'volume_24h': float(data['volume24h']),
                        'price_change_1h': float(data['priceChange1h']),
                        'price_change_24h': float(data['priceChange24h']),
                        'liquidity': float(data['liquidity']),
                        'source': 'poocoin'
                    }
                    
        except Exception as e:
            logger.error(f"PooCoin error for {token_symbol}: {str(e)}")
            return None
            
    async def _wait_for_rate_limit(self, api: str):
        """Respect API rate limits"""
        wait_time = self._rate_limits[api]
        last_request = self._last_request[api]
        time_since = (datetime.now() - last_request).total_seconds()
        
        if time_since < wait_time:
            await asyncio.sleep(wait_time - time_since)
        
        self._last_request[api] = datetime.now()
        
    def _merge_token_data(self, results: List[Dict]) -> Optional[Dict]:
        """Merge data from multiple sources, preferring real-time sources"""
        try:
            # Prefer Binance for real-time data
            binance_data = next((r for r in results if r['source'] == 'binance'), None)
            if binance_data:
                return binance_data
            
            # Fall back to PooCoin
            poocoin_data = next((r for r in results if r['source'] == 'poocoin'), None)
            if poocoin_data:
                return poocoin_data
            
            # Last resort: CoinGecko
            coingecko_data = next((r for r in results if r['source'] == 'coingecko'), None)
            if coingecko_data:
                return coingecko_data
            
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Error merging data: {str(e)}")
            return None
