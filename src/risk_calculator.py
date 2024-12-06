import numpy as np
from typing import Dict, List, Optional
import aiohttp
import json
import logging
from datetime import datetime, timedelta

class RiskCalculator:
    def __init__(self):
        self.price_history = {}
        self.volatility_cache = {}
        self.liquidity_cache = {}
        self.last_update = datetime.now()
        
        # Risk weights
        self.weights = {
            'volatility': 0.3,
            'liquidity': 0.25,
            'spread': 0.15,
            'volume': 0.15,
            'smart_contract': 0.15
        }
        
        # DEX risk scores (based on security audits and history)
        self.dex_risk_scores = {
            'Raydium': 15,    # Lower score = less risky
            'Orca': 20,
            'Jupiter': 25,
            'Saros': 35,
            'Marinade': 30
        }
    
    async def calculate_risk_score(self, opportunity: Dict) -> Dict:
        """Calculate comprehensive risk score for an arbitrage opportunity"""
        try:
            # Get various risk components
            volatility_risk = await self.calculate_volatility_risk(opportunity['pair'])
            liquidity_risk = await self.calculate_liquidity_risk(
                opportunity['buy_dex'],
                opportunity['sell_dex']
            )
            spread_risk = self.calculate_spread_risk(
                opportunity['buy_price'],
                opportunity['sell_price']
            )
            volume_risk = await self.calculate_volume_risk(opportunity['pair'])
            smart_contract_risk = self.calculate_smart_contract_risk(
                opportunity['buy_dex'],
                opportunity['sell_dex']
            )
            
            # Calculate weighted risk score
            total_risk = (
                volatility_risk * self.weights['volatility'] +
                liquidity_risk * self.weights['liquidity'] +
                spread_risk * self.weights['spread'] +
                volume_risk * self.weights['volume'] +
                smart_contract_risk * self.weights['smart_contract']
            )
            
            risk_breakdown = {
                'total_risk': total_risk,
                'components': {
                    'volatility_risk': volatility_risk,
                    'liquidity_risk': liquidity_risk,
                    'spread_risk': spread_risk,
                    'volume_risk': volume_risk,
                    'smart_contract_risk': smart_contract_risk
                },
                'risk_level': self.get_risk_level(total_risk),
                'recommendations': self.get_risk_recommendations(total_risk)
            }
            
            return risk_breakdown
            
        except Exception as e:
            logging.error(f"Error calculating risk score: {str(e)}")
            return {
                'total_risk': 100,  # Maximum risk on error
                'error': str(e)
            }
    
    async def calculate_volatility_risk(self, pair: str) -> float:
        """Calculate volatility risk based on recent price movements"""
        try:
            # Check cache first
            if pair in self.volatility_cache:
                cache_time, volatility = self.volatility_cache[pair]
                if datetime.now() - cache_time < timedelta(minutes=5):
                    return volatility
            
            # Get recent price history
            prices = await self.get_price_history(pair)
            if not prices:
                return 50.0  # Default medium risk if no data
            
            # Calculate volatility (standard deviation of returns)
            returns = np.diff(np.log(prices))
            volatility = np.std(returns) * 100
            
            # Normalize volatility to 0-100 scale
            risk_score = min(100, volatility * 20)  # Adjust multiplier as needed
            
            # Cache the result
            self.volatility_cache[pair] = (datetime.now(), risk_score)
            
            return risk_score
            
        except Exception as e:
            logging.error(f"Error calculating volatility risk: {str(e)}")
            return 50.0
    
    async def calculate_liquidity_risk(self, buy_dex: str, sell_dex: str) -> float:
        """Calculate liquidity risk based on DEX liquidity"""
        try:
            # Get liquidity scores for both DEXes
            buy_liquidity = await self.get_dex_liquidity(buy_dex)
            sell_liquidity = await self.get_dex_liquidity(sell_dex)
            
            # Lower liquidity = higher risk
            buy_risk = 100 - min(100, (buy_liquidity / 10000) * 100)
            sell_risk = 100 - min(100, (sell_liquidity / 10000) * 100)
            
            # Return the higher of the two risks
            return max(buy_risk, sell_risk)
            
        except Exception as e:
            logging.error(f"Error calculating liquidity risk: {str(e)}")
            return 50.0
    
    def calculate_spread_risk(self, buy_price: float, sell_price: float) -> float:
        """Calculate risk based on price spread"""
        try:
            spread_percentage = ((sell_price - buy_price) / buy_price) * 100
            
            # Larger spreads might indicate higher risk
            if spread_percentage > 5:
                return 80.0  # High risk
            elif spread_percentage > 2:
                return 50.0  # Medium risk
            else:
                return 20.0  # Low risk
                
        except Exception as e:
            logging.error(f"Error calculating spread risk: {str(e)}")
            return 50.0
    
    async def calculate_volume_risk(self, pair: str) -> float:
        """Calculate risk based on trading volume"""
        try:
            volume = await self.get_trading_volume(pair)
            
            # Higher volume = lower risk
            if volume > 1000000:  # $1M+ daily volume
                return 20.0
            elif volume > 100000:  # $100K+ daily volume
                return 50.0
            else:
                return 80.0
                
        except Exception as e:
            logging.error(f"Error calculating volume risk: {str(e)}")
            return 50.0
    
    def calculate_smart_contract_risk(self, buy_dex: str, sell_dex: str) -> float:
        """Calculate risk based on DEX smart contract security"""
        try:
            buy_risk = self.dex_risk_scores.get(buy_dex, 50.0)
            sell_risk = self.dex_risk_scores.get(sell_dex, 50.0)
            
            # Return the higher of the two risks
            return max(buy_risk, sell_risk)
            
        except Exception as e:
            logging.error(f"Error calculating smart contract risk: {str(e)}")
            return 50.0
    
    async def get_price_history(self, pair: str) -> List[float]:
        """Get recent price history for a pair"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.coingecko.com/api/v3/coins/{pair}/market_chart?vs_currency=usd&days=1&interval=hourly"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [price[1] for price in data['prices']]
            return []
        except Exception:
            return []
    
    async def get_dex_liquidity(self, dex: str) -> float:
        """Get liquidity information for a DEX"""
        # In production, this would fetch real liquidity data
        # For now, return mock data
        return {
            'Raydium': 1000000,
            'Orca': 800000,
            'Jupiter': 1200000,
            'Saros': 300000,
            'Marinade': 500000
        }.get(dex, 100000)
    
    async def get_trading_volume(self, pair: str) -> float:
        """Get 24h trading volume for a pair"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.coingecko.com/api/v3/simple/price?ids={pair}&vs_currencies=usd&include_24hr_vol=true"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data[pair]['usd_24h_vol']
            return 0
        except Exception:
            return 0
    
    def get_risk_level(self, risk_score: float) -> str:
        """Convert numerical risk score to categorical level"""
        if risk_score < 30:
            return "Low Risk"
        elif risk_score < 60:
            return "Medium Risk"
        else:
            return "High Risk"
    
    def get_risk_recommendations(self, risk_score: float) -> List[str]:
        """Get risk-based recommendations"""
        recommendations = []
        
        if risk_score >= 60:
            recommendations.extend([
                "⚠️ High risk detected - proceed with caution",
                "🔍 Consider reducing trade size",
                "⏰ Monitor execution closely"
            ])
        elif risk_score >= 30:
            recommendations.extend([
                "⚠️ Moderate risk - maintain standard precautions",
                "💰 Consider standard position sizing",
                "📊 Monitor market conditions"
            ])
        else:
            recommendations.extend([
                "✅ Low risk opportunity",
                "📈 Standard trading parameters acceptable",
                "🔄 Regular monitoring sufficient"
            ])
        
        return recommendations
