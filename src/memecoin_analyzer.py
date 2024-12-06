import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from web3 import Web3
import json
from decimal import Decimal
import aiohttp

class MemecoinAnalyzer:
    def __init__(self):
        self.indicators = {
            'liquidity': self.analyze_liquidity,
            'holders': self.analyze_holders,
            'contract': self.analyze_contract,
            'momentum': self.analyze_price_momentum,
            'volume': self.analyze_volume,
            'social': self.analyze_social_metrics,
            'ai_relevance': self.analyze_ai_relevance
        }
        
        # Known patterns
        self.bullish_patterns = {
            'organic_growth': {
                'holder_increase': '5-10% per hour',
                'volume_profile': 'steady increase',
                'price_action': 'stair-stepping up'
            },
            'viral_potential': {
                'social_momentum': 'exponential',
                'community_growth': 'rapid',
                'influencer_interest': 'growing'
            },
            'ai_trend': {
                'ai_mentions': 'increasing',
                'tech_validation': 'present',
                'chain_compatibility': ['base', 'solana'],
                'agent_integration': 'growing'
            },
            'whale_accumulation': {
                'large_buys': 'distributed',
                'holder_concentration': 'decreasing',
                'buy_pressure': 'consistent'
            }
        }
        
        # Nick's trading criteria
        self.NICK_FILTERS = {
            'max_dev_holding': 0.10,          # Max 10% developer holding
            'ideal_dev_holding': 0.05,        # Ideal: 5% or less
            'min_market_cap': 10_000,         # $10k minimum for beginners
            'max_market_cap': 30_000,         # $30k maximum for good R/R
            'graduation_threshold': 105_000,   # $105k for Raydium graduation
            'max_top10_holders': 0.15,        # 15% max for top 10 holders
            'min_holders': 50,                # Minimum holder count
            'volume_threshold': 50_000        # $50k minimum volume for graduated
        }
        
    async def analyze_token(self, token_address: str) -> Dict:
        """Complete token analysis"""
        try:
            results = {}
            
            # Run all indicators concurrently
            tasks = [
                indicator(token_address)
                for indicator in self.indicators.values()
            ]
            
            scores = await asyncio.gather(*tasks)
            
            # Combine scores with weights
            weights = {
                'liquidity': 20,
                'holders': 15,
                'contract': 25,
                'momentum': 15,
                'volume': 15,
                'social': 10,
                'ai_relevance': 10
            }
            
            total_score = 0
            for score, (name, weight) in zip(scores, weights.items()):
                results[name] = score
                total_score += score * weight / 100
                
            results['total_score'] = total_score
            results['analysis_time'] = datetime.now()
            
            # Add pattern recognition
            results['patterns'] = await self.identify_patterns(results)
            
            return results
            
        except Exception as e:
            logging.error(f"Token analysis error: {str(e)}")
            return {'error': str(e)}
            
    async def analyze_liquidity(self, token_address: str) -> float:
        """Analyze liquidity depth and stability"""
        try:
            # Get liquidity data
            liquidity = await self.get_liquidity_data(token_address)
            
            score = 0
            
            # 1. Total Liquidity (40 points)
            if liquidity['total_usd'] >= 100000:  # $100k+
                score += 40
            elif liquidity['total_usd'] >= 50000:  # $50k+
                score += 30
            elif liquidity['total_usd'] >= 20000:  # $20k+
                score += 20
                
            # 2. Liquidity/MCap Ratio (30 points)
            liq_ratio = liquidity['total_usd'] / liquidity['market_cap']
            if liq_ratio >= 0.3:  # 30%+ liquidity
                score += 30
            elif liq_ratio >= 0.2:  # 20%+ liquidity
                score += 20
            elif liq_ratio >= 0.1:  # 10%+ liquidity
                score += 10
                
            # 3. Liquidity Lock (30 points)
            if liquidity['locked_percentage'] >= 90:  # 90%+ locked
                score += 30
            elif liquidity['locked_percentage'] >= 80:  # 80%+ locked
                score += 20
            elif liquidity['locked_percentage'] >= 70:  # 70%+ locked
                score += 10
                
            return score
            
        except Exception as e:
            logging.error(f"Liquidity analysis error: {str(e)}")
            return 0
            
    async def analyze_contract(self, token_address: str) -> float:
        """Analyze contract for security and features"""
        try:
            # Get contract data
            contract = await self.get_contract_data(token_address)
            
            score = 0
            
            # 1. Security Features (40 points)
            security_score = 0
            security_features = {
                'anti_whale': 10,
                'anti_bot': 10,
                'locked_liquidity': 10,
                'renounced_ownership': 10
            }
            
            for feature, points in security_features.items():
                if contract['features'].get(feature):
                    security_score += points
                    
            score += security_score
            
            # 2. Code Quality (30 points)
            if contract['verified']:
                score += 15
                
            if not contract['high_risk_patterns']:
                score += 15
                
            # 3. Tokenomics (30 points)
            tokenomics_score = 0
            
            # Tax within reasonable range (0-10%)
            if 0 <= contract['buy_tax'] <= 10:
                tokenomics_score += 15
                
            # Supply distribution
            if contract['owner_percentage'] < 5:
                tokenomics_score += 15
                
            score += tokenomics_score
            
            return score
            
        except Exception as e:
            logging.error(f"Contract analysis error: {str(e)}")
            return 0
            
    async def analyze_price_momentum(self, token_address: str) -> float:
        """Analyze price momentum and patterns"""
        try:
            # Get price data
            prices = await self.get_price_history(token_address)
            
            score = 0
            
            # 1. Price Trend (40 points)
            trend_score = self.calculate_trend_strength(prices)
            score += min(trend_score * 40, 40)
            
            # 2. Volume Profile (30 points)
            volume_score = self.analyze_volume_profile(prices)
            score += min(volume_score * 30, 30)
            
            # 3. Pattern Recognition (30 points)
            patterns = self.identify_chart_patterns(prices)
            pattern_score = sum(pattern['strength'] for pattern in patterns)
            score += min(pattern_score * 30, 30)
            
            return score
            
        except Exception as e:
            logging.error(f"Momentum analysis error: {str(e)}")
            return 0
            
    async def analyze_ai_relevance(self, token_address: str) -> float:
        """Analyze AI relevance and integration potential"""
        try:
            score = 0
            token_data = await self.get_token_metadata(token_address)
            
            # Check for AI-related features (40 points)
            ai_features = {
                'agent_integration': 15,
                'ai_functionality': 15,
                'tech_validation': 10
            }
            
            for feature, points in ai_features.items():
                if feature in token_data.get('features', []):
                    score += points
            
            # Chain compatibility (30 points)
            if token_data.get('chain') in ['base', 'solana']:
                score += 30
            
            # Community and developer activity (30 points)
            github_activity = await self.check_github_activity(token_data.get('github', ''))
            if github_activity:
                score += 15
                
            if token_data.get('developer_count', 0) >= 3:
                score += 15
            
            return score
            
        except Exception as e:
            logging.error(f"AI relevance analysis error: {str(e)}")
            return 0
            
    async def identify_patterns(self, analysis_results: Dict) -> List[Dict]:
        """Identify bullish patterns in token data"""
        try:
            patterns = []
            
            # Check for organic growth pattern
            if (analysis_results['holders'] > 70 and
                analysis_results['volume'] > 60 and
                analysis_results['momentum'] > 60):
                patterns.append({
                    'name': 'organic_growth',
                    'confidence': min(
                        analysis_results['holders'],
                        analysis_results['volume'],
                        analysis_results['momentum']
                    ) / 100,
                    'indicators': {
                        'holders': analysis_results['holders'],
                        'volume': analysis_results['volume'],
                        'momentum': analysis_results['momentum']
                    }
                })
                
            # Check for viral potential
            if (analysis_results['social'] > 80 and
                analysis_results['momentum'] > 70):
                patterns.append({
                    'name': 'viral_potential',
                    'confidence': min(
                        analysis_results['social'],
                        analysis_results['momentum']
                    ) / 100,
                    'indicators': {
                        'social': analysis_results['social'],
                        'momentum': analysis_results['momentum']
                    }
                })
                
            # Check for AI trend
            if (analysis_results['ai_relevance'] > 70 and
                analysis_results['momentum'] > 60):
                patterns.append({
                    'name': 'ai_trend',
                    'confidence': min(
                        analysis_results['ai_relevance'],
                        analysis_results['momentum']
                    ) / 100,
                    'indicators': {
                        'ai_relevance': analysis_results['ai_relevance'],
                        'momentum': analysis_results['momentum']
                    }
                })
                
            # Check for whale accumulation
            if (analysis_results['volume'] > 70 and
                analysis_results['holders'] > 60):
                patterns.append({
                    'name': 'whale_accumulation',
                    'confidence': min(
                        analysis_results['volume'],
                        analysis_results['holders']
                    ) / 100,
                    'indicators': {
                        'volume': analysis_results['volume'],
                        'holders': analysis_results['holders']
                    }
                })
                
            return patterns
            
        except Exception as e:
            logging.error(f"Pattern identification error: {str(e)}")
            return []
            
    async def analyze_new_memecoin(self, token_address: str) -> Dict:
        """Analyze new memecoin using Nick's criteria"""
        try:
            analysis = {
                'is_safe': False,
                'dev_holding': 0,
                'market_cap': 0,
                'holder_distribution': {},
                'volume_analysis': {},
                'narrative_match': False,
                'real_volume': False,
                'community_driven': False,
                'recommendation': '',
                'risk_level': 'HIGH'
            }

            # 1. Check developer holding
            dev_data = await self._get_developer_holding(token_address)
            analysis['dev_holding'] = dev_data['percentage']
            
            if analysis['dev_holding'] > self.NICK_FILTERS['max_dev_holding']:
                analysis['recommendation'] = "AVOID: Developer holding too high"
                return analysis

            # 2. Check market cap
            market_data = await self._get_market_data(token_address)
            analysis['market_cap'] = market_data['market_cap']
            
            if not (self.NICK_FILTERS['min_market_cap'] <= analysis['market_cap'] <= self.NICK_FILTERS['max_market_cap']):
                analysis['recommendation'] = f"AVOID: Market cap outside safe range (${analysis['market_cap']:,.0f})"
                return analysis

            # 3. Analyze holder distribution
            holders = await self._get_holder_distribution(token_address)
            analysis['holder_distribution'] = holders
            
            if holders['top10_percentage'] > self.NICK_FILTERS['max_top10_holders']:
                analysis['recommendation'] = "AVOID: Top holders own too much"
                return analysis

            # 4. Check if volume is real
            volume_check = await self._verify_real_volume(token_address)
            analysis['volume_analysis'] = volume_check
            analysis['real_volume'] = volume_check['is_real']
            
            if not analysis['real_volume']:
                analysis['recommendation'] = "AVOID: Suspicious volume patterns"
                return analysis

            # 5. Check narrative alignment
            narrative = await self._check_current_narrative(token_address)
            analysis['narrative_match'] = narrative['matches']
            analysis['narrative_details'] = narrative

            # 6. Community analysis
            community = await self._analyze_community_potential(token_address)
            analysis['community_driven'] = community['is_community_driven']
            analysis['community_details'] = community

            # Final safety assessment
            analysis['is_safe'] = (
                analysis['dev_holding'] <= self.NICK_FILTERS['ideal_dev_holding'] and
                self.NICK_FILTERS['min_market_cap'] <= analysis['market_cap'] <= self.NICK_FILTERS['max_market_cap'] and
                holders['top10_percentage'] <= self.NICK_FILTERS['max_top10_holders'] and
                analysis['real_volume'] and
                (analysis['narrative_match'] or analysis['community_driven'])
            )

            if analysis['is_safe']:
                analysis['recommendation'] = "POTENTIAL ENTRY: Meets safety criteria"
                analysis['risk_level'] = 'MEDIUM' if analysis['narrative_match'] else 'HIGH'
            else:
                analysis['recommendation'] = "CAUTION: Some risk factors present"

            return analysis

        except Exception as e:
            logging.error(f"Memecoin analysis error: {str(e)}")
            return {'is_safe': False, 'recommendation': "ERROR: Analysis failed"}

    async def _verify_real_volume(self, token_address: str) -> Dict:
        """Verify if trading volume is real (not wash trading)"""
        try:
            volume_data = {
                'is_real': False,
                'unique_platforms': set(),
                'suspicious_patterns': [],
                'volume_24h': 0,
                'trades_analysis': {}
            }

            # Get recent trades
            trades = await self._get_recent_trades(token_address)
            
            # Check trading platforms diversity
            for trade in trades:
                volume_data['unique_platforms'].add(trade.get('platform', 'unknown'))

            # Flag suspicious patterns
            platform_trades = defaultdict(list)
            for trade in trades:
                platform = trade.get('platform', 'unknown')
                platform_trades[platform].append(trade)

            # Check for wash trading patterns
            for platform, platform_trades in platform_trades.items():
                if len(platform_trades) >= 10:
                    # Check for identical amounts
                    amounts = [t['amount'] for t in platform_trades]
                    if len(set(amounts)) < len(amounts) * 0.7:  # 70% unique
                        volume_data['suspicious_patterns'].append(f"Identical amounts on {platform}")

                    # Check for regular time intervals
                    times = [t['timestamp'] for t in platform_trades]
                    intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
                    if len(set(intervals)) < len(intervals) * 0.7:  # 70% unique
                        volume_data['suspicious_patterns'].append(f"Regular intervals on {platform}")

            # Volume is considered real if:
            # 1. Multiple trading platforms used
            # 2. No suspicious patterns
            # 3. Reasonable trade distribution
            volume_data['is_real'] = (
                len(volume_data['unique_platforms']) >= 2 and
                len(volume_data['suspicious_patterns']) == 0
            )

            return volume_data

        except Exception as e:
            logging.error(f"Volume verification error: {str(e)}")
            return {'is_real': False}

    async def _check_current_narrative(self, token_address: str) -> Dict:
        """Check if token matches current market narrative"""
        try:
            narrative = {
                'matches': False,
                'current_narratives': [],
                'token_themes': [],
                'strength': 0
            }

            # Get token metadata
            metadata = await self.get_token_metadata(token_address)
            token_name = metadata.get('name', '').lower()
            token_symbol = metadata.get('symbol', '').lower()

            # Current narratives (from video)
            current_narratives = [
                {
                    'theme': 'solana_ecosystem',
                    'keywords': ['sol', 'solana', 'saga', 'bonk', 'wen'],
                    'strength': 1.0
                },
                {
                    'theme': 'golden_memes',
                    'keywords': ['golden', 'gold', 'yellow', 'treasure'],
                    'strength': 0.8
                },
                {
                    'theme': 'ai_tokens',
                    'keywords': ['ai', 'bot', 'gpt', 'intelligence'],
                    'strength': 0.7
                }
            ]

            # Check each narrative
            for narrative_type in current_narratives:
                if any(kw in token_name or kw in token_symbol for kw in narrative_type['keywords']):
                    narrative['current_narratives'].append(narrative_type['theme'])
                    narrative['strength'] = max(narrative['strength'], narrative_type['strength'])

            # Get social sentiment for narrative confirmation
            social = await self._check_social_sentiment(token_address)
            
            # Token matches narrative if:
            # 1. Name/symbol matches current narrative
            # 2. Strong social sentiment
            narrative['matches'] = (
                len(narrative['current_narratives']) > 0 and
                social['score'] >= 70
            )

            return narrative

        except Exception as e:
            logging.error(f"Narrative check error: {str(e)}")
            return {'matches': False}

    async def _analyze_community_potential(self, token_address: str) -> Dict:
        """Analyze if token can thrive without developer"""
        try:
            community = {
                'is_community_driven': False,
                'telegram_members': 0,
                'twitter_followers': 0,
                'unique_holders': 0,
                'growth_rate': 0,
                'engagement_score': 0
            }

            # Get social metrics
            social_data = await self.fetch_token_social_data(token_address)
            community.update(social_data)

            # Calculate holder growth rate
            holder_history = await self._get_holder_history(token_address)
            if holder_history and len(holder_history) >= 2:
                time_diff = holder_history[-1]['timestamp'] - holder_history[0]['timestamp']
                holder_diff = holder_history[-1]['count'] - holder_history[0]['count']
                if time_diff > 0:
                    community['growth_rate'] = (holder_diff / time_diff) * 3600  # Per hour

            # Calculate engagement score
            if community['telegram_members'] > 0:
                telegram_engagement = await self._get_telegram_engagement(token_address)
                community['engagement_score'] = telegram_engagement['score']

            # Community is considered self-sustaining if:
            # 1. Good holder growth rate (50+ per hour from video)
            # 2. Active community engagement
            # 3. Multiple social platforms
            community['is_community_driven'] = (
                community['growth_rate'] >= 50 and
                community['engagement_score'] >= 70 and
                community['telegram_members'] >= 500 and
                community['twitter_followers'] >= 100
            )

            return community

        except Exception as e:
            logging.error(f"Community analysis error: {str(e)}")
            return {'is_community_driven': False}

    # Helper methods to be implemented
    async def get_liquidity_data(self, token_address: str) -> Dict:
        """Get liquidity data for token"""
        pass
        
    async def get_contract_data(self, token_address: str) -> Dict:
        """Get contract data and features"""
        pass
        
    async def get_price_history(self, token_address: str) -> List[Dict]:
        """Get price history data"""
        pass
        
    def calculate_trend_strength(self, prices: List[Dict]) -> float:
        """Calculate trend strength"""
        pass
        
    def analyze_volume_profile(self, prices: List[Dict]) -> float:
        """Analyze volume profile"""
        pass
        
    def identify_chart_patterns(self, prices: List[Dict]) -> List[Dict]:
        """Identify technical chart patterns"""
        pass

    async def get_token_metadata(self, token_address: str) -> Dict:
        """Get token metadata including AI features"""
        try:
            # Initialize web3 connection based on chain
            w3 = self.get_web3_connection(token_address)
            
            # Get token contract
            contract = w3.eth.contract(
                address=w3.to_checksum_address(token_address),
                abi=self.get_token_abi()
            )
            
            # Basic token info
            metadata = {
                'name': await contract.functions.name().call(),
                'symbol': await contract.functions.symbol().call(),
                'chain': self.detect_chain(token_address),
                'features': [],
                'github': '',
                'developer_count': 0
            }
            
            # Check for AI features in token name/symbol
            ai_keywords = ['ai', 'agent', 'gpt', 'neural', 'brain', 'smart', 'intel']
            if any(kw in metadata['name'].lower() for kw in ai_keywords) or \
               any(kw in metadata['symbol'].lower() for kw in ai_keywords):
                metadata['features'].append('ai_functionality')
            
            # Get social links and documentation from token website
            social_data = await self.fetch_token_social_data(token_address)
            metadata.update(social_data)
            
            # Check for agent integration
            if await self.check_agent_integration(token_address):
                metadata['features'].append('agent_integration')
            
            # Validate technical implementation
            if await self.validate_tech_implementation(token_address):
                metadata['features'].append('tech_validation')
            
            return metadata
            
        except Exception as e:
            logging.error(f"Error fetching token metadata: {str(e)}")
            return {}

    async def check_github_activity(self, github_url: str) -> bool:
        """Check GitHub activity for AI-related development"""
        try:
            if not github_url:
                return False
                
            # Extract owner and repo from GitHub URL
            parts = github_url.strip('/').split('/')
            if len(parts) < 2:
                return False
                
            owner = parts[-2]
            repo = parts[-1]
            
            # Initialize aiohttp session
            async with aiohttp.ClientSession() as session:
                # Get repository info
                async with session.get(
                    f'https://api.github.com/repos/{owner}/{repo}',
                    headers={'Accept': 'application/vnd.github.v3+json'}
                ) as response:
                    if response.status != 200:
                        return False
                    repo_data = await response.json()
                
                # Check recent commits
                async with session.get(
                    f'https://api.github.com/repos/{owner}/{repo}/commits',
                    headers={'Accept': 'application/vnd.github.v3+json'}
                ) as response:
                    if response.status != 200:
                        return False
                    commits = await response.json()
                
                # Check AI-related files and activity
                async with session.get(
                    f'https://api.github.com/repos/{owner}/{repo}/contents',
                    headers={'Accept': 'application/vnd.github.v3+json'}
                ) as response:
                    if response.status != 200:
                        return False
                    contents = await response.json()
                
                # Scoring criteria
                score = 0
                
                # Recent activity (up to 20 points)
                if len(commits) >= 10:  # Active development
                    score += 20
                elif len(commits) >= 5:
                    score += 10
                
                # Repository stats (up to 20 points)
                if repo_data.get('stargazers_count', 0) > 100:
                    score += 10
                if repo_data.get('forks_count', 0) > 20:
                    score += 10
                
                # AI-related files check (up to 60 points)
                ai_keywords = ['ai', 'model', 'neural', 'train', 'inference', 'agent']
                ai_files = 0
                
                for item in contents:
                    if item['type'] == 'file':
                        name_lower = item['name'].lower()
                        if any(kw in name_lower for kw in ai_keywords):
                            ai_files += 1
                
                if ai_files >= 5:
                    score += 60
                elif ai_files >= 3:
                    score += 40
                elif ai_files >= 1:
                    score += 20
                
                return score >= 60  # Consider active if score is 60 or higher
                
        except Exception as e:
            logging.error(f"Error checking GitHub activity: {str(e)}")
            return False

    async def check_agent_integration(self, token_address: str) -> bool:
        """Check if token has agent integration capabilities"""
        try:
            # Check for agent-related contract functions
            contract = self.get_contract(token_address)
            functions = contract.all_functions()
            
            agent_keywords = ['agent', 'execute', 'interact', 'automate', 'delegate']
            
            # Check function names for agent-related keywords
            for func in functions:
                if any(kw in func.fn_name.lower() for kw in agent_keywords):
                    return True
            
            # Check for integration with known agent platforms
            known_platforms = [
                'virtuals',  # From video: "virtuals protocol easily the top ecosystem"
                'eliza',     # Mentioned in video but with some controversy
                'ai6z'       # Mentioned as part of trending tokens
            ]
            
            for platform in known_platforms:
                if await self.check_platform_integration(token_address, platform):
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking agent integration: {str(e)}")
            return False

    async def validate_tech_implementation(self, token_address: str) -> bool:
        """Validate the technical implementation quality"""
        try:
            contract = self.get_contract(token_address)
            
            # Security checks
            security_features = {
                'has_ownership': False,
                'has_pause': False,
                'has_blacklist': False,
                'has_max_tx': False
            }
            
            # Check for standard security features
            for func in contract.all_functions():
                name = func.fn_name.lower()
                if 'owner' in name:
                    security_features['has_ownership'] = True
                elif 'pause' in name:
                    security_features['has_pause'] = True
                elif 'blacklist' in name:
                    security_features['has_blacklist'] = True
                elif 'maxtransaction' in name or 'maxamount' in name:
                    security_features['has_max_tx'] = True
            
            # Check source code verification
            is_verified = await self.is_contract_verified(token_address)
            
            # Check for common vulnerabilities
            vulnerabilities = await self.scan_for_vulnerabilities(token_address)
            
            # Score the implementation
            score = 0
            
            # Security features (40 points)
            score += sum(10 for feature in security_features.values() if feature)
            
            # Contract verification (30 points)
            if is_verified:
                score += 30
            
            # No vulnerabilities (30 points)
            if not vulnerabilities:
                score += 30
            
            return score >= 70  # Consider valid if score is 70 or higher
            
        except Exception as e:
            logging.error(f"Error validating tech implementation: {str(e)}")
            return False

    def detect_chain(self, token_address: str) -> str:
        """Detect which chain the token is on based on address format and RPC"""
        try:
            # Check address format
            if token_address.startswith('0x'):
                # Check if Base chain
                if self.is_base_chain(token_address):
                    return 'base'
                # Check if Solana address format
                elif len(token_address) == 44:
                    return 'solana'
                else:
                    return 'ethereum'
            return 'unknown'
        except Exception as e:
            logging.error(f"Chain detection error: {str(e)}")
            return 'unknown'

    async def fetch_token_social_data(self, token_address: str) -> Dict:
        """Fetch social links and documentation for token"""
        try:
            social_data = {
                'telegram_members': 0,
                'twitter_followers': 0,
                'holder_count': 0,
                'market_cap': 0,
                'launch_date': None,
                'community_driven': False
            }
            
            # Get contract data
            contract = self.get_contract(token_address)
            
            # Get holder data
            holders = await self.get_holder_data(token_address)
            social_data['holder_count'] = holders['total_holders']
            
            # Calculate market metrics
            market_data = await self.get_market_data(token_address)
            social_data['market_cap'] = market_data['market_cap']
            
            # Early stage detection (key from video)
            if 0 < market_data['market_cap'] <= 50_000_000:  # Below 50M mcap
                social_data['early_stage'] = True
                social_data['growth_potential'] = self.calculate_growth_potential(market_data)
            else:
                social_data['early_stage'] = False
                social_data['growth_potential'] = 0
                
            # Community analysis
            community_data = await self.analyze_community(token_address)
            social_data.update(community_data)
            
            return social_data
            
        except Exception as e:
            logging.error(f"Social data fetch error: {str(e)}")
            return {}

    async def calculate_growth_potential(self, market_data: Dict) -> float:
        """Calculate potential growth multiplier based on market data"""
        try:
            current_mcap = market_data['market_cap']
            
            # Target market caps from video analysis
            potential_targets = {
                'conservative': 1_000_000_000,  # 1B
                'moderate': 10_000_000_000,     # 10B
                'ambitious': 50_000_000_000     # 50B
            }
            
            if current_mcap <= 0:
                return 0
                
            multipliers = {
                target: target_mcap / current_mcap 
                for target, target_mcap in potential_targets.items()
                if target_mcap > current_mcap
            }
            
            # Score based on realistic growth potential
            score = 0
            
            # Higher score for tokens under 10M mcap (from video: "below 10M has highest potential")
            if current_mcap < 10_000_000:
                score += 40
            elif current_mcap < 50_000_000:
                score += 20
                
            # Check holder distribution
            holder_distribution = await self.get_holder_distribution(market_data['token_address'])
            if holder_distribution['is_well_distributed']:
                score += 30
                
            # Community engagement score
            community_score = await self.get_community_engagement_score(market_data['token_address'])
            score += min(community_score, 30)
            
            return score
            
        except Exception as e:
            logging.error(f"Growth potential calculation error: {str(e)}")
            return 0

    async def analyze_community(self, token_address: str) -> Dict:
        """Analyze if token is genuinely community driven"""
        try:
            community_data = {
                'is_community_driven': False,
                'whale_concentration': 0,
                'organic_growth': False
            }
            
            # Get top holders
            holders = await self.get_holder_distribution(token_address)
            
            # Check whale concentration (from video: community-driven should have low whale concentration)
            whale_threshold = 0.02  # 2% per wallet considered whale
            whale_concentration = sum(
                1 for holding in holders['holdings']
                if holding['percentage'] > whale_threshold
            )
            
            community_data['whale_concentration'] = whale_concentration
            
            # Check if community driven
            if (whale_concentration < 5 and  # Few whales
                holders['unique_holders'] > 1000 and  # Good holder base
                await self.check_organic_growth(token_address)):  # Organic growth pattern
                community_data['is_community_driven'] = True
                
            return community_data
            
        except Exception as e:
            logging.error(f"Community analysis error: {str(e)}")
            return {}

    async def check_organic_growth(self, token_address: str) -> bool:
        """Check if token shows organic growth patterns"""
        try:
            # Get historical data
            history = await self.get_token_history(token_address, days=30)
            
            if not history:
                return False
                
            # Check holder growth pattern
            holder_growth = self.analyze_holder_growth(history)
            
            # Check price pattern
            price_pattern = self.analyze_price_pattern(history)
            
            # Check volume distribution
            volume_pattern = self.analyze_volume_pattern(history)
            
            # Organic growth criteria (from video insights)
            return (
                holder_growth['is_organic'] and
                price_pattern['is_stable'] and
                volume_pattern['is_distributed']
            )
            
        except Exception as e:
            logging.error(f"Organic growth check error: {str(e)}")
            return False

    async def get_holder_distribution(self, token_address: str) -> Dict:
        """Get detailed holder distribution data"""
        # Implementation to be added
        pass

    async def get_token_history(self, token_address: str, days: int) -> List:
        """Get historical token data"""
        # Implementation to be added
        pass

    def analyze_holder_growth(self, history: List) -> Dict:
        """Analyze holder growth pattern"""
        # Implementation to be added
        pass

    def analyze_price_pattern(self, history: List) -> Dict:
        """Analyze price movement pattern"""
        # Implementation to be added
        pass

    def analyze_volume_pattern(self, history: List) -> Dict:
        """Analyze volume distribution pattern"""
        # Implementation to be added
        pass

    async def is_base_chain(self, token_address: str) -> bool:
        """Check if token is on Base chain"""
        # Implementation to be added
        pass

    async def get_market_data(self, token_address: str) -> Dict:
        """Get market data for token"""
        # Implementation to be added
        pass

    async def get_community_engagement_score(self, token_address: str) -> float:
        """Get community engagement score"""
        # Implementation to be added
        pass

    async def check_platform_integration(self, token_address: str, platform: str) -> bool:
        """Check if token integrates with a specific agent platform"""
        # Implementation to be added
        pass

    async def is_contract_verified(self, token_address: str) -> bool:
        """Check if contract is verified on block explorer"""
        # Implementation to be added
        pass

    async def scan_for_vulnerabilities(self, token_address: str) -> List[str]:
        """Scan contract for common vulnerabilities"""
        # Implementation to be added
        pass
