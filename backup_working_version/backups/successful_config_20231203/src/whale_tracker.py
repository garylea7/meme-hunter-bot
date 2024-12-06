import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Set
import aiohttp
from collections import defaultdict

class WhaleTracker:
    """Track and analyze whale wallets using GMGN.ai strategy"""

    def __init__(self):
        # Enhanced wallet tracking settings
        self.MIN_WIN_RATE_7D = 0.50       # 50%+ win rate in 7 days
        self.MIN_PROFIT_30D = 10.0        # 1000% profit in 30 days
        self.MIN_TRANSACTIONS = 20        # Minimum trades to consider
        self.MAX_ENTRY_MCAP = 30_000     # Maximum entry market cap ($30k)
        self.MIN_HOLDERS = 50            # Minimum token holders
        self.MAX_TOP10_HOLDINGS = 0.15   # Max 15% for top 10 holders
        self.MIN_VOLUME = 50_000         # Minimum volume for graduated tokens
        
        # Telegram settings
        self.telegram_token = None
        self.telegram_chat_id = None
        self.telegram_alerts_enabled = False
        
        # Enhanced tracking
        self.followed_wallets = set()
        self.wallet_stats = {}
        self.trending_memes = set()
        self.meme_scores = {}
        self.processed_txs = set()
        
        # Track social metrics
        self.social_metrics = defaultdict(lambda: {
            'telegram_members': 0,
            'twitter_followers': 0,
            'holder_growth_rate': 0,
            'volume_growth_rate': 0,
            'price_growth_rate': 0
        })

    async def find_whale_wallets(self, token_address: str) -> List[Dict]:
        """Enhanced whale wallet finding with additional filters"""
        try:
            whale_wallets = []
            
            # Get token traders from GMGN
            async with aiohttp.ClientSession() as session:
                # Get token data first
                token_data = await self._get_token_data(token_address)
                if not self._validate_token_metrics(token_data):
                    return []
                
                # Get traders
                async with session.get(
                    f'https://api.gmgn.ai/v1/token/{token_address}/traders',
                    params={
                        'sort': 'pnl',
                        'limit': 100
                    }
                ) as response:
                    if response.status != 200:
                        return []
                        
                    traders = await response.json()
                    
                    # Enhanced filtering for successful traders
                    for trader in traders:
                        if (
                            not trader.get('is_suspicious') and
                            trader.get('win_rate_7d', 0) >= self.MIN_WIN_RATE_7D and
                            trader.get('profit_30d', 0) >= self.MIN_PROFIT_30D and
                            trader.get('total_trades', 0) >= self.MIN_TRANSACTIONS and
                            trader.get('avg_hold_time', 0) >= 300 and  # Min 5 min hold
                            trader.get('unique_tokens', 0) >= 10 and   # Diverse portfolio
                            self._check_trading_pattern(trader)
                        ):
                            # Calculate comprehensive score
                            entry_score = self._calculate_entry_score(trader)
                            pattern_score = self._analyze_trading_pattern(trader)
                            social_score = await self._calculate_social_score(trader['address'])
                            
                            total_score = (
                                entry_score * 0.4 +    # 40% weight on entry
                                pattern_score * 0.3 +  # 30% weight on pattern
                                social_score * 0.3     # 30% weight on social
                            )
                            
                            if total_score >= 70:  # Only high-quality wallets
                                whale_wallets.append({
                                    'address': trader['address'],
                                    'win_rate_7d': trader['win_rate_7d'],
                                    'profit_30d': trader['profit_30d'],
                                    'total_trades': trader['total_trades'],
                                    'entry_score': entry_score,
                                    'pattern_score': pattern_score,
                                    'social_score': social_score,
                                    'total_score': total_score,
                                    'badges': trader.get('badges', []),
                                    'avg_hold_time': trader.get('avg_hold_time', 0),
                                    'unique_tokens': trader.get('unique_tokens', 0)
                                })
            
            return sorted(whale_wallets, key=lambda x: x['total_score'], reverse=True)
            
        except Exception as e:
            logging.error(f"Error finding whale wallets: {str(e)}")
            return []

    def _validate_token_metrics(self, token_data: Dict) -> bool:
        """Validate token metrics based on Nick's criteria"""
        try:
            # Check holder distribution
            if token_data.get('holder_count', 0) < self.MIN_HOLDERS:
                return False
                
            # Check top 10 holder percentage
            top10_percentage = sum(
                holder['percentage'] 
                for holder in token_data.get('holders', [])[:10]
            )
            if top10_percentage > self.MAX_TOP10_HOLDINGS:
                return False
                
            # Check volume for graduated tokens
            if (token_data.get('market_cap', 0) > 105_000 and  # Graduated
                token_data.get('volume_24h', 0) < self.MIN_VOLUME):
                return False
                
            # Check developer holdings
            dev_percentage = token_data.get('developer_holdings', 0)
            if dev_percentage > 0.10:  # Max 10%
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error validating token metrics: {str(e)}")
            return False

    def _check_trading_pattern(self, trader: Dict) -> bool:
        """Check if trader follows successful patterns"""
        try:
            # Get recent trades
            trades = trader.get('recent_trades', [])
            if not trades:
                return False
                
            # Check for consistent entry points
            entry_mcaps = [
                trade['entry_mcap'] 
                for trade in trades 
                if trade.get('entry_mcap')
            ]
            if not entry_mcaps:
                return False
                
            # Calculate consistency metrics
            avg_entry = sum(entry_mcaps) / len(entry_mcaps)
            entry_variance = sum(
                (mcap - avg_entry) ** 2 
                for mcap in entry_mcaps
            ) / len(entry_mcaps)
            
            # Prefer consistent early entries
            if avg_entry > self.MAX_ENTRY_MCAP:
                return False
            if entry_variance > 1_000_000:  # Too inconsistent
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error checking trading pattern: {str(e)}")
            return False

    async def _calculate_social_score(self, wallet_address: str) -> float:
        """Calculate social influence score"""
        try:
            score = 0
            
            # Get wallet's social data
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://api.gmgn.ai/v1/wallet/{wallet_address}/social'
                ) as response:
                    if response.status != 200:
                        return 0
                        
                    social_data = await response.json()
                    
                    # Check Twitter influence
                    followers = social_data.get('twitter_followers', 0)
                    if followers >= 10_000:
                        score += 30
                    elif followers >= 1_000:
                        score += 15
                        
                    # Check Telegram presence
                    if social_data.get('telegram_active', False):
                        score += 20
                        
                    # Check trading group membership
                    trading_groups = social_data.get('trading_groups', [])
                    score += min(len(trading_groups) * 10, 30)
                    
                    # Check content creation
                    content_score = social_data.get('content_score', 0)
                    score += min(content_score, 20)
                    
            return min(score, 100)
            
        except Exception as e:
            logging.error(f"Error calculating social score: {str(e)}")
            return 0

    async def setup_telegram(self, token: str, chat_id: str):
        """Setup Telegram notifications"""
        self.telegram_token = token
        self.telegram_chat_id = chat_id
        self.telegram_alerts_enabled = True
        
        # Test connection
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://api.telegram.org/bot{token}/getMe'
                ) as response:
                    if response.status == 200:
                        logging.info("Telegram bot connected successfully")
                    else:
                        logging.error("Failed to connect Telegram bot")
                        self.telegram_alerts_enabled = False
                        
        except Exception as e:
            logging.error(f"Error setting up Telegram: {str(e)}")
            self.telegram_alerts_enabled = False

    async def send_telegram_alert(self, message: str):
        """Send Telegram notification"""
        if not self.telegram_alerts_enabled:
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f'https://api.telegram.org/bot{self.telegram_token}/sendMessage',
                    json={
                        'chat_id': self.telegram_chat_id,
                        'text': message,
                        'parse_mode': 'HTML'
                    }
                )
        except Exception as e:
            logging.error(f"Error sending Telegram alert: {str(e)}")

    async def track_trending_memes(self):
        """Enhanced meme trend tracking"""
        try:
            # Track across multiple platforms
            platforms = {
                'tiktok': self._get_tiktok_trends,
                'twitter': self._get_twitter_trends,
                'telegram': self._get_telegram_trends,
                'reddit': self._get_reddit_trends,
                'youtube': self._get_youtube_trends
            }
            
            meme_data = defaultdict(lambda: {
                'mentions': 0,
                'platforms': set(),
                'first_seen': datetime.now(),
                'growth_rate': 0,
                'sentiment': 0,
                'engagement': 0,
                'virality_score': 0
            })
            
            # Gather trends from all platforms
            for platform, getter in platforms.items():
                trends = await getter()
                for trend in trends:
                    name = trend['name']
                    data = meme_data[name]
                    
                    # Update metrics
                    data['mentions'] += trend['mentions']
                    data['platforms'].add(platform)
                    data['sentiment'] += trend.get('sentiment', 0)
                    data['engagement'] += trend.get('engagement', 0)
                    
                    # Calculate growth rate
                    time_diff = (datetime.now() - data['first_seen']).total_seconds()
                    if time_diff > 0:
                        data['growth_rate'] = data['mentions'] / time_diff
                        
                    # Calculate virality score
                    platform_multiplier = len(data['platforms'])
                    sentiment_factor = (data['sentiment'] / len(data['platforms']) + 1) / 2
                    engagement_rate = data['engagement'] / data['mentions'] if data['mentions'] > 0 else 0
                    
                    data['virality_score'] = (
                        data['growth_rate'] * 0.4 +
                        platform_multiplier * 20 * 0.3 +
                        sentiment_factor * 100 * 0.15 +
                        engagement_rate * 100 * 0.15
                    )
            
            # Update trending memes
            self.trending_memes = {
                name for name, data in meme_data.items()
                if (len(data['platforms']) >= 2 and    # Multi-platform
                    data['growth_rate'] >= 1.0 and     # Growing fast
                    data['virality_score'] >= 60)      # Viral potential
            }
            
            # Update meme scores
            self.meme_scores = {
                name: data['virality_score']
                for name, data in meme_data.items()
            }
            
            # Alert on new viral memes
            for name, data in meme_data.items():
                if (data['virality_score'] >= 80 and  # Highly viral
                    name not in self._alerted_memes):
                    await self.send_telegram_alert(
                        f"🔥 <b>Viral Meme Alert</b> 🔥\n\n"
                        f"Meme: {name}\n"
                        f"Virality Score: {data['virality_score']:.1f}\n"
                        f"Platforms: {', '.join(data['platforms'])}\n"
                        f"Growth Rate: {data['growth_rate']:.1f} mentions/sec"
                    )
                    self._alerted_memes.add(name)
            
        except Exception as e:
            logging.error(f"Error tracking memes: {str(e)}")

    async def follow_wallet(self, wallet_address: str):
        """Follow a whale wallet for notifications"""
        try:
            # Add to followed wallets
            self.followed_wallets.add(wallet_address)
            
            # Get initial wallet stats
            stats = await self._get_wallet_stats(wallet_address)
            self.wallet_stats[wallet_address] = stats
            
            logging.info(f"Started following wallet: {wallet_address}")
            logging.info(f"Initial stats: {stats}")
            
        except Exception as e:
            logging.error(f"Error following wallet: {str(e)}")
            
    async def _get_wallet_stats(self, wallet_address: str) -> Dict:
        """Get detailed wallet statistics"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://api.gmgn.ai/v1/wallet/{wallet_address}/stats'
                ) as response:
                    if response.status != 200:
                        return {}
                        
                    return await response.json()
                    
        except Exception as e:
            logging.error(f"Error getting wallet stats: {str(e)}")
            return {}
            
    async def monitor_followed_wallets(self):
        """Monitor followed wallets for new trades"""
        try:
            while True:
                for wallet in list(self.followed_wallets):
                    # Get latest transactions
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f'https://api.gmgn.ai/v1/wallet/{wallet}/transactions',
                            params={'limit': 10}
                        ) as response:
                            if response.status != 200:
                                continue
                                
                            transactions = await response.json()
                            
                            for tx in transactions:
                                if self._is_new_trade(tx):
                                    await self._process_whale_trade(wallet, tx)
                                    
                await asyncio.sleep(1)  # Check every second
                
        except Exception as e:
            logging.error(f"Error monitoring wallets: {str(e)}")
            
    def _is_new_trade(self, transaction: Dict) -> bool:
        """Check if this is a new trade we haven't processed"""
        # Implementation depends on how you want to track processed transactions
        pass
        
    async def _process_whale_trade(self, wallet: str, transaction: Dict):
        """Process a new whale trade"""
        try:
            # Get token details
            token_address = transaction.get('token_address')
            if not token_address:
                return
                
            # Check if token matches any trending memes
            token_data = await self._get_token_data(token_address)
            token_name = token_data.get('name', '').lower()
            
            meme_match = None
            for meme in self.trending_memes:
                if meme.lower() in token_name:
                    meme_match = meme
                    break
                    
            # Generate alert
            alert = {
                'wallet': wallet,
                'token': token_address,
                'amount': transaction.get('amount'),
                'type': transaction.get('type'),  # buy/sell
                'timestamp': datetime.now(),
                'meme_match': meme_match,
                'meme_score': self.meme_scores.get(meme_match, 0) if meme_match else 0
            }
            
            # Log alert
            logging.info(f"Whale Trade Alert: {alert}")
            
            # TODO: Send notification via preferred method (Telegram, etc.)
            
        except Exception as e:
            logging.error(f"Error processing whale trade: {str(e)}")
            
    async def _get_token_data(self, token_address: str) -> Dict:
        """Get token metadata"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://api.gmgn.ai/v1/token/{token_address}'
                ) as response:
                    if response.status != 200:
                        return {}
                        
                    return await response.json()
                    
        except Exception as e:
            logging.error(f"Error getting token data: {str(e)}")
            return {}
            
    async def _get_platform_trends(self, platform: str) -> List[Dict]:
        """Get trending topics from a social platform"""
        # Implementation would depend on platform APIs
        pass

    def _calculate_entry_score(self, trader: Dict) -> float:
        """Calculate how good the trader is at finding early opportunities"""
        try:
            score = 0
            
            # Check entry timing
            if trader.get('avg_entry_mcap', 0) <= 30_000:  # Under $30k mcap entries
                score += 40
            elif trader.get('avg_entry_mcap', 0) <= 100_000:  # Under $100k mcap entries
                score += 20
                
            # Check consistency
            if trader.get('win_rate_7d', 0) >= 0.7:  # 70%+ win rate
                score += 30
                
            # Check badges
            badges = trader.get('badges', [])
            if 'top_holder' in badges:
                score += 15
            if 'whale' in badges:
                score += 15
                
            # Penalize if holding time is too short
            avg_hold_time = trader.get('avg_hold_time', 0)
            if avg_hold_time < 300:  # Less than 5 minutes
                score -= 20
                
            return max(0, min(score, 100))  # Clamp between 0-100
            
        except Exception as e:
            logging.error(f"Error calculating entry score: {str(e)}")
            return 0
            
    def _analyze_trading_pattern(self, trader: Dict) -> float:
        """Analyze trading pattern for consistency and profitability"""
        try:
            score = 0
            
            # Check for consistent entry points
            entry_mcaps = [
                trade['entry_mcap'] 
                for trade in trader.get('recent_trades', []) 
                if trade.get('entry_mcap')
            ]
            if not entry_mcaps:
                return 0
                
            # Calculate consistency metrics
            avg_entry = sum(entry_mcaps) / len(entry_mcaps)
            entry_variance = sum(
                (mcap - avg_entry) ** 2 
                for mcap in entry_mcaps
            ) / len(entry_mcaps)
            
            # Prefer consistent early entries
            if avg_entry <= self.MAX_ENTRY_MCAP:
                score += 30
            if entry_variance <= 1_000_000:  # Consistent entries
                score += 20
                
            # Check for profitable exits
            exit_prices = [
                trade['exit_price'] 
                for trade in trader.get('recent_trades', []) 
                if trade.get('exit_price')
            ]
            if not exit_prices:
                return 0
                
            # Calculate profitability metrics
            avg_profit = sum(exit_prices) / len(exit_prices)
            profit_variance = sum(
                (price - avg_profit) ** 2 
                for price in exit_prices
            ) / len(exit_prices)
            
            # Prefer profitable exits
            if avg_profit >= 1.5:  # 50%+ profit
                score += 30
            if profit_variance <= 0.5:  # Consistent profits
                score += 20
                
            return min(score, 100)  # Cap at 100
            
        except Exception as e:
            logging.error(f"Error analyzing trading pattern: {str(e)}")
            return 0
