import requests
import logging
from typing import Dict, Optional
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self):
        load_dotenv()
        self.bullx_api_key = os.getenv('BULLX_API_KEY')
        self.gmgn_api_key = os.getenv('GMGN_API_KEY')
        
        # Cache settings
        self._cache = {}
        self._cache_duration = timedelta(minutes=5)

    def analyze_token(self, token_address: str) -> Dict:
        """Analyze token using both BullX and GMGN AI"""
        try:
            bullx_analysis = self._get_bullx_analysis(token_address)
            gmgn_analysis = self._get_gmgn_analysis(token_address)
            
            # Combine and compare analyses
            combined_analysis = {
                'bullx': bullx_analysis,
                'gmgn': gmgn_analysis,
                'comparison': self._compare_analyses(bullx_analysis, gmgn_analysis),
                'recommendation': self._generate_recommendation(bullx_analysis, gmgn_analysis)
            }
            
            return combined_analysis
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {}

    def _get_bullx_analysis(self, token_address: str) -> Dict:
        """Get analysis from BullX AI"""
        cache_key = f'bullx_{token_address}'
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            url = f"https://api.bullx.io/v1/token/analysis/{token_address}"
            headers = {"X-API-Key": self.bullx_api_key}
            response = requests.get(url, headers=headers)
            data = response.json()
            
            analysis = {
                'safety_score': data.get('safety_score', 0),
                'honeypot_risk': data.get('honeypot_risk', 'unknown'),
                'rugpull_risk': data.get('rugpull_risk', 'unknown'),
                'contract_risks': data.get('contract_risks', []),
                'ownership_analysis': {
                    'owner_type': data.get('owner_type', 'unknown'),
                    'owner_actions': data.get('owner_actions', []),
                    'renounced': data.get('ownership_renounced', False)
                },
                'trading_analysis': {
                    'buy_tax': data.get('buy_tax', 0),
                    'sell_tax': data.get('sell_tax', 0),
                    'max_tx': data.get('max_tx_amount', 0),
                    'liquidity_analysis': data.get('liquidity_analysis', {})
                },
                'ai_prediction': {
                    'short_term': data.get('short_term_prediction', {}),
                    'long_term': data.get('long_term_prediction', {}),
                    'confidence': data.get('prediction_confidence', 0)
                }
            }
            
            self._cache[cache_key] = analysis
            self._cache[f"{cache_key}_time"] = datetime.now()
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting BullX analysis: {e}")
            return {}

    def _get_gmgn_analysis(self, token_address: str) -> Dict:
        """Get analysis from GMGN AI"""
        cache_key = f'gmgn_{token_address}'
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            url = f"https://api.gmgn.ai/v1/token/analyze/{token_address}"
            headers = {"Authorization": f"Bearer {self.gmgn_api_key}"}
            response = requests.get(url, headers=headers)
            data = response.json()
            
            analysis = {
                'safety_score': data.get('safety_rating', 0),
                'contract_analysis': {
                    'honeypot_risk': data.get('honeypot_probability', 0),
                    'rugpull_risk': data.get('rugpull_probability', 0),
                    'malicious_code': data.get('malicious_code_detected', []),
                    'security_issues': data.get('security_issues', [])
                },
                'market_analysis': {
                    'price_manipulation': data.get('price_manipulation_risk', 0),
                    'wash_trading': data.get('wash_trading_detected', False),
                    'liquidity_health': data.get('liquidity_health_score', 0)
                },
                'social_signals': {
                    'sentiment_score': data.get('social_sentiment', 0),
                    'community_growth': data.get('community_growth_rate', 0),
                    'bot_activity': data.get('bot_activity_percentage', 0)
                },
                'ai_prediction': {
                    'trend_prediction': data.get('trend_prediction', {}),
                    'price_targets': data.get('price_targets', {}),
                    'confidence_score': data.get('prediction_confidence', 0)
                }
            }
            
            self._cache[cache_key] = analysis
            self._cache[f"{cache_key}_time"] = datetime.now()
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting GMGN analysis: {e}")
            return {}

    def _compare_analyses(self, bullx: Dict, gmgn: Dict) -> Dict:
        """Compare analyses from both AIs"""
        try:
            # Convert risk levels to numerical scores for comparison
            bullx_score = bullx.get('safety_score', 0)
            gmgn_score = gmgn.get('safety_score', 0)
            
            # Compare honeypot detection
            bullx_honeypot = bullx.get('honeypot_risk', 'unknown') == 'high'
            gmgn_honeypot = gmgn.get('contract_analysis', {}).get('honeypot_risk', 0) > 0.7
            
            # Compare rugpull risk
            bullx_rugpull = bullx.get('rugpull_risk', 'unknown') == 'high'
            gmgn_rugpull = gmgn.get('contract_analysis', {}).get('rugpull_risk', 0) > 0.7
            
            # Calculate agreement scores
            safety_agreement = 1 - abs(bullx_score - gmgn_score) / 100
            risk_agreement = (
                (1 if bullx_honeypot == gmgn_honeypot else 0) +
                (1 if bullx_rugpull == gmgn_rugpull else 0)
            ) / 2
            
            return {
                'safety_score_difference': abs(bullx_score - gmgn_score),
                'risk_assessment_agreement': risk_agreement,
                'overall_agreement': (safety_agreement + risk_agreement) / 2,
                'conflicting_points': self._identify_conflicts(bullx, gmgn)
            }
        except Exception as e:
            logger.error(f"Error comparing analyses: {e}")
            return {}

    def _identify_conflicts(self, bullx: Dict, gmgn: Dict) -> list:
        """Identify conflicting points between the two analyses"""
        conflicts = []
        
        # Check for major disagreements
        if abs(bullx.get('safety_score', 0) - gmgn.get('safety_score', 0)) > 30:
            conflicts.append("Major disagreement in overall safety score")
            
        if bullx.get('honeypot_risk') == 'safe' and gmgn.get('contract_analysis', {}).get('honeypot_risk', 0) > 0.7:
            conflicts.append("Conflicting honeypot risk assessment")
            
        if bullx.get('rugpull_risk') == 'safe' and gmgn.get('contract_analysis', {}).get('rugpull_risk', 0) > 0.7:
            conflicts.append("Conflicting rugpull risk assessment")
            
        return conflicts

    def _generate_recommendation(self, bullx: Dict, gmgn: Dict) -> Dict:
        """Generate a final recommendation based on both analyses"""
        try:
            # Calculate weighted scores
            bullx_score = bullx.get('safety_score', 0) * 0.5  # BullX weight
            gmgn_score = gmgn.get('safety_score', 0) * 0.5    # GMGN weight
            combined_score = bullx_score + gmgn_score
            
            # Determine confidence level based on agreement
            confidence = self._compare_analyses(bullx, gmgn).get('overall_agreement', 0)
            
            # Generate action recommendation
            if combined_score >= 80 and confidence >= 0.8:
                action = "Strong Buy"
                reasoning = "High safety scores with strong AI agreement"
            elif combined_score >= 70 and confidence >= 0.6:
                action = "Buy"
                reasoning = "Good safety scores with moderate AI agreement"
            elif combined_score <= 30 or confidence <= 0.3:
                action = "Avoid"
                reasoning = "Low safety scores or significant AI disagreement"
            else:
                action = "DYOR"
                reasoning = "Mixed signals or moderate risk indicators"
            
            return {
                'action': action,
                'reasoning': reasoning,
                'combined_score': combined_score,
                'confidence': confidence,
                'strengths': self._identify_strengths(bullx, gmgn),
                'concerns': self._identify_concerns(bullx, gmgn)
            }
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return {}

    def _identify_strengths(self, bullx: Dict, gmgn: Dict) -> list:
        """Identify strong positive signals from both analyses"""
        strengths = []
        
        # Check BullX strengths
        if bullx.get('safety_score', 0) >= 80:
            strengths.append("High BullX safety score")
        if bullx.get('ownership_analysis', {}).get('renounced'):
            strengths.append("Ownership renounced (BullX)")
            
        # Check GMGN strengths
        if gmgn.get('safety_score', 0) >= 80:
            strengths.append("High GMGN safety score")
        if gmgn.get('market_analysis', {}).get('liquidity_health', 0) >= 80:
            strengths.append("Strong liquidity health (GMGN)")
        if gmgn.get('social_signals', {}).get('sentiment_score', 0) >= 0.8:
            strengths.append("Positive social sentiment (GMGN)")
            
        return strengths

    def _identify_concerns(self, bullx: Dict, gmgn: Dict) -> list:
        """Identify potential concerns from both analyses"""
        concerns = []
        
        # Check BullX concerns
        if bullx.get('contract_risks'):
            concerns.extend(bullx['contract_risks'])
        if bullx.get('trading_analysis', {}).get('sell_tax', 0) > 10:
            concerns.append("High sell tax detected (BullX)")
            
        # Check GMGN concerns
        if gmgn.get('contract_analysis', {}).get('security_issues'):
            concerns.extend(gmgn['contract_analysis']['security_issues'])
        if gmgn.get('market_analysis', {}).get('wash_trading'):
            concerns.append("Wash trading detected (GMGN)")
        if gmgn.get('social_signals', {}).get('bot_activity', 0) > 50:
            concerns.append("High bot activity in social signals (GMGN)")
            
        return concerns

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache:
            return False
        
        cache_time = self._cache.get(f"{key}_time")
        if not cache_time:
            return False
            
        return datetime.now() - cache_time < self._cache_duration
