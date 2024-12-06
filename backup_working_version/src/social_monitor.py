import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from collections import deque

class SocialMonitor:
    def __init__(self):
        self.platforms = {
            'twitter': 'https://api.twitter.com/2/tweets/search/recent',
            'telegram': 'https://api.telegram.org/bot{token}',
            'discord': 'https://discord.com/api/v10',
            '4chan': 'https://a.4cdn.org/biz'
        }
        
        # Track mentions and sentiment
        self.mentions = {}
        self.sentiment_cache = {}
        
        # Momentum tracking
        self.momentum_scores = deque(maxlen=1000)
        
        # Influencer tracking
        self.known_influencers = set()
        self.influencer_alerts = deque(maxlen=100)
        
    async def start_monitoring(self):
        """Start all monitoring tasks"""
        tasks = [
            self.monitor_twitter(),
            self.monitor_telegram(),
            self.monitor_discord(),
            self.monitor_4chan(),
            self.analyze_trends()
        ]
        await asyncio.gather(*tasks)
        
    async def monitor_twitter(self):
        """Monitor Twitter for token mentions and sentiment"""
        while True:
            try:
                # Search for crypto-related tweets
                queries = [
                    "new gem crypto",
                    "next moonshot",
                    "100x token",
                    "memecoin launch"
                ]
                
                for query in queries:
                    tweets = await self.search_twitter(query)
                    for tweet in tweets:
                        await self.process_tweet(tweet)
                        
                await asyncio.sleep(30)  # Rate limit friendly
                
            except Exception as e:
                logging.error(f"Twitter monitoring error: {str(e)}")
                await asyncio.sleep(5)
                
    async def monitor_telegram(self):
        """Monitor Telegram crypto groups"""
        while True:
            try:
                # Monitor known crypto groups
                groups = [
                    "cryptomoonshots",
                    "cryptogems",
                    "uniswapgemspro",
                    "dexgemschat"
                ]
                
                for group in groups:
                    messages = await self.get_telegram_messages(group)
                    for msg in messages:
                        await self.process_telegram_message(msg)
                        
                await asyncio.sleep(20)
                
            except Exception as e:
                logging.error(f"Telegram monitoring error: {str(e)}")
                await asyncio.sleep(5)
                
    async def process_social_data(self, data: Dict, platform: str):
        """Process social media data for token mentions"""
        try:
            # Extract token mentions
            tokens = self.extract_token_mentions(data['text'])
            
            for token in tokens:
                if token not in self.mentions:
                    self.mentions[token] = {
                        'count': 0,
                        'platforms': set(),
                        'first_seen': datetime.now(),
                        'sentiment': [],
                        'influencer_mentions': []
                    }
                
                # Update mentions
                self.mentions[token]['count'] += 1
                self.mentions[token]['platforms'].add(platform)
                
                # Calculate sentiment
                sentiment = await self.analyze_sentiment(data['text'])
                self.mentions[token]['sentiment'].append(sentiment)
                
                # Check if from influencer
                if self.is_influencer(data['user']):
                    self.mentions[token]['influencer_mentions'].append({
                        'user': data['user'],
                        'time': datetime.now(),
                        'platform': platform
                    })
                    
                    # Alert if significant influencer
                    if self.is_significant_influencer(data['user']):
                        await self.send_influencer_alert(token, data)
                        
        except Exception as e:
            logging.error(f"Error processing social data: {str(e)}")
            
    async def analyze_sentiment(self, text: str) -> float:
        """Analyze text sentiment (-1 to 1 scale)"""
        try:
            # Basic sentiment indicators
            positive_words = {'moon', 'gem', 'pump', 'buy', 'bullish', 'launch'}
            negative_words = {'scam', 'rug', 'dump', 'avoid', 'bearish'}
            
            words = text.lower().split()
            
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            
            total = positive_count + negative_count
            if total == 0:
                return 0
                
            return (positive_count - negative_count) / total
            
        except Exception as e:
            logging.error(f"Sentiment analysis error: {str(e)}")
            return 0
            
    async def calculate_momentum_score(self, token: str) -> Dict:
        """Calculate social momentum score"""
        try:
            if token not in self.mentions:
                return {'score': 0, 'details': {}}
                
            data = self.mentions[token]
            
            # Base score from mentions
            score = min(data['count'] / 100, 1) * 40  # Max 40 points
            
            # Platform diversity (max 10 points)
            platform_score = len(data['platforms']) * 2.5
            score += min(platform_score, 10)
            
            # Sentiment score (max 20 points)
            avg_sentiment = sum(data['sentiment']) / len(data['sentiment'])
            sentiment_score = (avg_sentiment + 1) * 10  # Convert -1:1 to 0:20
            score += sentiment_score
            
            # Influencer impact (max 30 points)
            influencer_score = len(data['influencer_mentions']) * 5
            score += min(influencer_score, 30)
            
            return {
                'score': score,
                'details': {
                    'mention_score': score,
                    'platform_score': platform_score,
                    'sentiment_score': sentiment_score,
                    'influencer_score': influencer_score,
                    'mentions': data['count'],
                    'platforms': list(data['platforms']),
                    'sentiment': avg_sentiment,
                    'influencers': len(data['influencer_mentions'])
                }
            }
            
        except Exception as e:
            logging.error(f"Momentum calculation error: {str(e)}")
            return {'score': 0, 'details': {}}
            
    async def send_influencer_alert(self, token: str, data: Dict):
        """Send alert when significant influencer mentions token"""
        try:
            alert = {
                'token': token,
                'influencer': data['user'],
                'platform': data['platform'],
                'time': datetime.now(),
                'text': data['text'],
                'followers': await self.get_follower_count(data['user'], data['platform'])
            }
            
            self.influencer_alerts.append(alert)
            
            # Trigger immediate analysis
            score = await self.calculate_momentum_score(token)
            if score['score'] >= 80:
                await self.send_high_priority_alert(token, score, alert)
                
        except Exception as e:
            logging.error(f"Influencer alert error: {str(e)}")
            
    def is_significant_influencer(self, user: Dict) -> bool:
        """Check if user is a significant influencer"""
        try:
            # Criteria for significant influencer
            min_followers = {
                'twitter': 100000,
                'telegram': 50000,
                'discord': 20000
            }
            
            platform = user.get('platform', '')
            followers = user.get('followers', 0)
            
            return followers >= min_followers.get(platform, 0)
            
        except Exception as e:
            logging.error(f"Influencer check error: {str(e)}")
            return False
            
    async def get_follower_count(self, user: Dict, platform: str) -> int:
        """Get follower count for user on platform"""
        # Implementation for each platform's API
        pass
        
    async def send_high_priority_alert(self, token: str, score: Dict, alert: Dict):
        """Send high priority alert for significant opportunities"""
        # Implementation for alerts
        pass
