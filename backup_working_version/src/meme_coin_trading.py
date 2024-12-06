import os
import logging
from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from .market_analysis import MarketAnalyzer

logger = logging.getLogger(__name__)

class MemeCoinTrader:
    def __init__(self):
        load_dotenv()
        self.bullx_api_key = os.getenv('BULLX_API_KEY')
        self.market_analyzer = MarketAnalyzer()
        
        # Trading mode configuration
        self.trading_mode = os.getenv('TRADING_MODE', 'conservative')  # 'conservative' or 'aggressive'
        
        # Conservative mode settings
        self.conservative_settings = {
            'min_market_cap': 10000,
            'max_dev_holdings': 5,
            'take_profit_levels': [
                {"percentage": 25, "position_size": 0.3},
                {"percentage": 50, "position_size": 0.3},
                {"percentage": 100, "position_size": 0.4}
            ],
            'stop_loss': 15
        }
        
        # Aggressive mode settings (based on successful meme trader)
        self.aggressive_settings = {
            'min_market_cap': 1000,  # Lower minimum to catch very early opportunities
            'max_dev_holdings': 10,  # More tolerant of developer holdings
            'take_profit_levels': [
                {"percentage": 100, "position_size": 0.2},   # 2x - Take 20%
                {"percentage": 300, "position_size": 0.3},   # 4x - Take 30%
                {"percentage": 700, "position_size": 0.3},   # 8x - Take 30%
                {"percentage": 1000, "position_size": 0.2}   # 11x - Take final 20%
            ],
            'stop_loss': 25  # Slightly tighter stop loss
        }
        
        # Use settings based on mode
        self.settings = (self.aggressive_settings if self.trading_mode == 'aggressive' 
                        else self.conservative_settings)

    def analyze_new_tokens(self) -> List[Dict]:
        """Analyze newly created tokens on pump.fun"""
        try:
            # Get new token creations from Bullx API
            headers = {"X-API-Key": self.bullx_api_key}
            response = requests.get(
                "https://api.bullx.io/v1/new-tokens",
                headers=headers
            )
            tokens = response.json()

            analyzed_tokens = []
            for token in tokens:
                if self._passes_initial_filters(token):
                    analysis = self._deep_analyze_token(token)
                    if analysis['recommendation']['is_potential_good_trade']:
                        analyzed_tokens.append(analysis)

            return analyzed_tokens
        except Exception as e:
            logger.error(f"Error analyzing new tokens: {e}")
            return []

    def _passes_initial_filters(self, token: Dict) -> bool:
        """Apply initial filtering criteria"""
        try:
            # Check market cap
            if token.get('market_cap', 0) < self.settings['min_market_cap']:
                return False

            # Check developer holdings
            if token.get('dev_holdings_percentage', 100) > self.settings['max_dev_holdings']:
                return False

            # Check holder distribution
            top_holders = token.get('top_holders', [])
            if len(top_holders) < 10:
                return False

            top_10_percentage = sum(holder['percentage'] for holder in top_holders[:10])
            if top_10_percentage > 80:  # If top 10 holders have more than 80%
                return False

            return True
        except Exception as e:
            logger.error(f"Error in initial filters: {e}")
            return False

    def _deep_analyze_token(self, token: Dict) -> Dict:
        """Perform deep analysis on a token"""
        try:
            # Get AI analysis
            safety_analysis = self.market_analyzer.analyze_token_safety(token['address'])

            # Check for copy/clone
            is_copy = self._check_if_copy(token)

            # Analyze social metrics and narrative
            social_analysis = self._analyze_social_metrics(token)

            # Check if token is boosted/promoted
            promotion_status = self._check_promotion_status(token)

            return {
                'token_address': token['address'],
                'token_name': token['name'],
                'market_cap': token['market_cap'],
                'holders': token.get('holders_count', 0),
                'safety_analysis': safety_analysis,
                'is_copy': is_copy,
                'social_metrics': social_analysis,
                'promotion': promotion_status,
                'recommendation': self._generate_recommendation(
                    safety_analysis,
                    is_copy,
                    social_analysis,
                    promotion_status
                )
            }
        except Exception as e:
            logger.error(f"Error in deep analysis: {e}")
            return {}

    def _check_if_copy(self, token: Dict) -> Dict:
        """Check if token is a copy of existing project"""
        try:
            # Query for similar token names/symbols
            response = requests.get(
                f"https://api.bullx.io/v1/similar-tokens/{token['name']}",
                headers={"X-API-Key": self.bullx_api_key}
            )
            similar_tokens = response.json()

            return {
                'is_copy': len(similar_tokens) > 0,
                'similar_tokens': similar_tokens
            }
        except Exception as e:
            logger.error(f"Error checking for copies: {e}")
            return {'is_copy': False, 'similar_tokens': []}

    def _analyze_social_metrics(self, token: Dict) -> Dict:
        """Analyze social media presence and narrative"""
        try:
            # Get social metrics from Bullx
            response = requests.get(
                f"https://api.bullx.io/v1/social-metrics/{token['address']}",
                headers={"X-API-Key": self.bullx_api_key}
            )
            metrics = response.json()

            return {
                'twitter_followers': metrics.get('twitter_followers', 0),
                'telegram_members': metrics.get('telegram_members', 0),
                'social_engagement': metrics.get('social_engagement', 0),
                'narrative_strength': metrics.get('narrative_score', 0),
                'trending_score': metrics.get('trending_score', 0),
                'social_growth_rate': metrics.get('social_growth_rate', 0),
                'whale_accumulation': metrics.get('whale_accumulation', False)
            }
        except Exception as e:
            logger.error(f"Error analyzing social metrics: {e}")
            return {}

    def _check_promotion_status(self, token: Dict) -> Dict:
        """Check if token is being promoted/boosted"""
        try:
            response = requests.get(
                f"https://api.bullx.io/v1/promotion-status/{token['address']}",
                headers={"X-API-Key": self.bullx_api_key}
            )
            status = response.json()

            return {
                'is_promoted': status.get('is_promoted', False),
                'promotion_type': status.get('promotion_type', None),
                'promotion_strength': status.get('promotion_strength', 0)
            }
        except Exception as e:
            logger.error(f"Error checking promotion status: {e}")
            return {'is_promoted': False}

    def _generate_recommendation(
        self,
        safety_analysis: Dict,
        copy_info: Dict,
        social_metrics: Dict,
        promotion: Dict
    ) -> Dict:
        """Generate trading recommendation based on all analyses"""
        try:
            score = 0
            red_flags = []
            strengths = []
            
            if self.trading_mode == 'aggressive':
                # Aggressive mode prioritizes viral potential and early entry
                if social_metrics.get('narrative_strength', 0) > 5:
                    score += 30
                    strengths.append("Strong meme potential")
                
                if social_metrics.get('trending_score', 0) > 3:
                    score += 25
                    strengths.append("Early trending signals")
                
                # Check for rapid social growth
                if social_metrics.get('social_growth_rate', 0) > 50:
                    score += 25
                    strengths.append("Viral growth detected")
                
                # Look for whale accumulation
                if social_metrics.get('whale_accumulation', False):
                    score += 20
                    strengths.append("Whale accumulation detected")
                
            else:
                # Conservative mode (original logic)
                if safety_analysis.get('ai_comparison', {}).get('agreement_level', 0) > 0.7:
                    score += 30
                    strengths.append("High AI agreement on safety")
                
                if copy_info.get('is_copy', False):
                    score -= 20
                    red_flags.append("Token appears to be a copy")
                
                if social_metrics.get('narrative_strength', 0) > 7:
                    score += 20
                    strengths.append("Strong narrative")

            # Common checks for both modes
            if promotion.get('is_promoted', False):
                if promotion.get('promotion_strength', 0) > 7:
                    score += 10
                    strengths.append("Strong promotional backing")
            
            # Calculate potential return based on mode
            potential_return = self._calculate_potential_return(
                social_metrics, promotion, safety_analysis
            )

            return {
                'score': score,
                'is_potential_good_trade': score > 50,
                'red_flags': red_flags,
                'strengths': strengths,
                'recommendation': "Buy" if score > 50 else "Skip",
                'confidence': min(score, 100),
                'potential_return': potential_return
            }
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return {
                'score': 0,
                'is_potential_good_trade': False,
                'red_flags': ["Error in analysis"],
                'strengths': [],
                'recommendation': "Skip",
                'confidence': 0,
                'potential_return': 0
            }

    def _calculate_potential_return(self, social_metrics: Dict, 
                                  promotion: Dict, safety_analysis: Dict) -> Dict:
        """Calculate potential return ranges based on metrics"""
        try:
            if self.trading_mode == 'aggressive':
                # Aggressive calculations for potential 2x-11x returns (based on $20 to $22,000 success case)
                base_multiplier = 2  # Start with 2x potential
                
                # Viral potential multipliers
                if social_metrics.get('narrative_strength', 0) > 8:
                    base_multiplier *= 1.5
                if social_metrics.get('trending_score', 0) > 7:
                    base_multiplier *= 1.5
                if social_metrics.get('social_growth_rate', 0) > 100:
                    base_multiplier *= 2
                
                # Whale activity multiplier
                if social_metrics.get('whale_accumulation', False):
                    base_multiplier *= 1.25
                
                return {
                    'min_return': base_multiplier,
                    'max_return': min(base_multiplier * 5, 11),  # Cap at 11x (real case maximum)
                    'likely_return': base_multiplier * 2
                }
            else:
                # Conservative calculations
                return {
                    'min_return': 1.25,  # 25% minimum target
                    'max_return': 3.0,    # 300% maximum target
                    'likely_return': 2.0   # 100% likely target
                }
        except Exception as e:
            logger.error(f"Error calculating potential return: {e}")
            return {'min_return': 1, 'max_return': 1, 'likely_return': 1}
