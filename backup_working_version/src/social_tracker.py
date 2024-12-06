import logging
from typing import Dict, List, Optional
import aiohttp
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import json
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class SocialTracker:
    def __init__(self):
        load_dotenv()
        self.tiktok_api_key = os.getenv('TIKTOK_API_KEY')
        self.twitter_api_key = os.getenv('TWITTER_API_KEY')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        # Cache settings
        self._cache = {}
        self._cache_duration = timedelta(minutes=5)
        
        # Trend tracking
        self.trending_topics = defaultdict(lambda: {
            'mentions': 0,
            'engagement': 0,
            'sentiment': 0,
            'first_seen': None,
            'platforms': set()
        })
        
    async def track_tiktok_trends(self) -> List[Dict]:
        """Track trending crypto-related content on TikTok"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'keywords': 'crypto,memecoin,trading',
                    'count': 50,
                    'sort_by': 'views'
                }
                headers = {'X-API-Key': self.tiktok_api_key}
                
                async with session.get(
                    'https://api.tiktok.com/v1/trending/search',
                    params=params,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return []
                        
                    data = await response.json()
                    trends = []
                    
                    for video in data.get('videos', []):
                        trend = {
                            'id': video['id'],
                            'description': video['desc'],
                            'views': video['stats']['play_count'],
                            'likes': video['stats']['digg_count'],
                            'shares': video['stats']['share_count'],
                            'comments': video['stats']['comment_count'],
                            'hashtags': [tag['name'] for tag in video.get('challenges', [])],
                            'created_at': video['create_time'],
                            'engagement_rate': self._calculate_engagement_rate(video['stats'])
                        }
                        
                        # Extract mentioned tokens
                        trend['mentioned_tokens'] = self._extract_token_mentions(trend['description'])
                        
                        trends.append(trend)
                    
                    return sorted(trends, key=lambda x: x['engagement_rate'], reverse=True)
                    
        except Exception as e:
            logger.error(f"Error tracking TikTok trends: {str(e)}")
            return []
            
    def _calculate_engagement_rate(self, stats: Dict) -> float:
        """Calculate engagement rate from video stats"""
        try:
            total_engagement = (
                stats.get('digg_count', 0) +     # likes
                stats.get('comment_count', 0) +   # comments
                stats.get('share_count', 0)       # shares
            )
            views = stats.get('play_count', 1)    # avoid division by zero
            
            return (total_engagement / views) * 100
            
        except Exception as e:
            logger.error(f"Error calculating engagement rate: {str(e)}")
            return 0
            
    def _extract_token_mentions(self, text: str) -> List[str]:
        """Extract potential token mentions from text"""
        # Implementation would use regex and known token patterns
        # For demo, returning empty list
        return []
        
    async def get_trending_tokens(self) -> List[Dict]:
        """Get tokens trending on TikTok"""
        trends = await self.track_tiktok_trends()
        
        # Aggregate token mentions
        token_trends = defaultdict(lambda: {
            'mentions': 0,
            'total_views': 0,
            'total_engagement': 0,
            'videos': []
        })
        
        for trend in trends:
            for token in trend['mentioned_tokens']:
                data = token_trends[token]
                data['mentions'] += 1
                data['total_views'] += trend['views']
                data['total_engagement'] += (
                    trend['likes'] + trend['comments'] + trend['shares']
                )
                data['videos'].append({
                    'id': trend['id'],
                    'views': trend['views'],
                    'engagement_rate': trend['engagement_rate']
                })
                
        # Convert to list and sort by engagement
        return sorted([
            {
                'token': token,
                'stats': stats,
                'virality_score': self._calculate_virality_score(stats)
            }
            for token, stats in token_trends.items()
        ], key=lambda x: x['virality_score'], reverse=True)
        
    def _calculate_virality_score(self, stats: Dict) -> float:
        """Calculate virality score based on views and engagement"""
        try:
            views_weight = 0.4
            engagement_weight = 0.6
            
            normalized_views = min(stats['total_views'] / 1_000_000, 1)  # Cap at 1M views
            normalized_engagement = min(stats['total_engagement'] / 100_000, 1)  # Cap at 100K
            
            return (
                normalized_views * views_weight +
                normalized_engagement * engagement_weight
            ) * 100
            
        except Exception as e:
            logger.error(f"Error calculating virality score: {str(e)}")
            return 0
