import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
import json

class FastTokenScanner:
    def __init__(self):
        # Use deque for fast operations
        self.recent_tokens = deque(maxlen=1000)
        self.potential_gems = deque(maxlen=100)
        
        # Async session for faster API calls
        self.session = None
        
        # Rate limiting
        self.calls_per_minute = 60
        self.call_timestamps = deque(maxlen=self.calls_per_minute)
        
        # Batch processing
        self.batch_size = 10
        self.processing_queue = asyncio.Queue()
        
        # Configurable settings
        self.settings = {
            'min_liquidity': 10000,  # $10k
            'max_holders': 1000,     # New token indicator
            'min_holders': 50,       # Avoid too new/risky
            'min_price_increase': 10 # 10x minimum pump
        }
        
    async def start(self):
        """Start the scanner with connection pooling"""
        # Create persistent aiohttp session
        self.session = aiohttp.ClientSession()
        
        # Start workers
        workers = [
            self.token_scanner(),
            self.price_tracker(),
            self.whale_tracker(),
            self.process_queue()
        ]
        
        await asyncio.gather(*workers)
        
    async def token_scanner(self):
        """Scan for new tokens without blocking"""
        while True:
            try:
                # Get new tokens in batches
                tokens = await self.get_new_tokens_batch()
                
                # Queue them for processing
                for token in tokens:
                    await self.processing_queue.put(token)
                
                # Rate limiting sleep
                await self.smart_sleep()
                
            except Exception as e:
                logging.error(f"Scanner error: {str(e)}")
                await asyncio.sleep(1)
                
    async def get_new_tokens_batch(self) -> List[Dict]:
        """Get new tokens in batches for efficiency"""
        if not await self.can_make_call():
            return []
            
        try:
            # Use DexScreener API for fastest response
            async with self.session.get(
                "https://api.dexscreener.com/latest/dex/tokens/recent"
            ) as response:
                data = await response.json()
                
                # Basic filtering for speed
                return [
                    token for token in data.get('tokens', [])
                    if self.quick_filter(token)
                ]
                
        except Exception as e:
            logging.error(f"Batch fetch error: {str(e)}")
            return []
            
    def quick_filter(self, token: Dict) -> bool:
        """Ultra-fast initial filtering"""
        try:
            # Only check essential fields
            liquidity = float(token.get('liquidity', 0))
            holders = int(token.get('holders', 0))
            
            return (
                liquidity >= self.settings['min_liquidity'] and
                holders >= self.settings['min_holders'] and
                holders <= self.settings['max_holders']
            )
        except:
            return False
            
    async def process_queue(self):
        """Process tokens in batches"""
        while True:
            try:
                # Get batch of tokens
                batch = []
                for _ in range(self.batch_size):
                    if self.processing_queue.empty():
                        break
                    batch.append(await self.processing_queue.get())
                
                if not batch:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process batch concurrently
                await asyncio.gather(*[
                    self.analyze_token(token)
                    for token in batch
                ])
                
            except Exception as e:
                logging.error(f"Queue processing error: {str(e)}")
                await asyncio.sleep(1)
                
    async def analyze_token(self, token: Dict):
        """Non-blocking token analysis"""
        try:
            # Quick price check
            initial_price = await self.get_token_price(token['address'])
            if not initial_price:
                return
                
            # Store for monitoring
            token['initial_price'] = initial_price
            token['found_at'] = datetime.now()
            self.recent_tokens.append(token)
            
            # Initial analysis looks good
            if await self.is_potential_gem(token):
                self.potential_gems.append(token)
                await self.alert_new_gem(token)
                
        except Exception as e:
            logging.error(f"Analysis error: {str(e)}")
            
    async def price_tracker(self):
        """Track prices of potential gems"""
        while True:
            try:
                for token in list(self.potential_gems):
                    current_price = await self.get_token_price(token['address'])
                    if not current_price:
                        continue
                        
                    price_increase = current_price / token['initial_price']
                    
                    if price_increase >= self.settings['min_price_increase']:
                        await self.alert_pump(token, price_increase)
                        
                await asyncio.sleep(1)
                
            except Exception as e:
                logging.error(f"Price tracking error: {str(e)}")
                await asyncio.sleep(1)
                
    async def whale_tracker(self):
        """Track whale movements without blocking"""
        while True:
            try:
                for token in list(self.potential_gems):
                    whale_data = await self.get_whale_data(token['address'])
                    if self.is_whale_buying(whale_data):
                        await self.alert_whale_activity(token, whale_data)
                        
                await asyncio.sleep(2)
                
            except Exception as e:
                logging.error(f"Whale tracking error: {str(e)}")
                await asyncio.sleep(1)
                
    async def can_make_call(self) -> bool:
        """Smart rate limiting"""
        now = datetime.now()
        
        # Remove old timestamps
        while self.call_timestamps and (now - self.call_timestamps[0]) > timedelta(minutes=1):
            self.call_timestamps.popleft()
            
        if len(self.call_timestamps) < self.calls_per_minute:
            self.call_timestamps.append(now)
            return True
            
        return False
        
    async def smart_sleep(self):
        """Dynamic sleep based on API usage"""
        if len(self.call_timestamps) >= self.calls_per_minute:
            sleep_time = (self.call_timestamps[0] + timedelta(minutes=1) - datetime.now()).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                
    async def get_token_price(self, address: str) -> Optional[float]:
        """Get token price with caching"""
        # Implementation for price fetching
        pass
        
    async def is_potential_gem(self, token: Dict) -> bool:
        """Check if token could be a gem"""
        # Implementation for gem detection
        pass
        
    async def alert_new_gem(self, token: Dict):
        """Alert about new potential gem"""
        logging.info(f"New Gem Found: {token['symbol']}")
        # Add your notification logic here
        
    async def alert_pump(self, token: Dict, increase: float):
        """Alert about price pump"""
        logging.info(f"Price Pump: {token['symbol']} up {increase}x")
        # Add your notification logic here
        
    async def get_whale_data(self, address: str) -> Dict:
        """Get whale transaction data"""
        # Implementation for whale tracking
        pass
        
    def is_whale_buying(self, whale_data: Dict) -> bool:
        """Check if whales are buying"""
        # Implementation for whale analysis
        pass
        
    async def alert_whale_activity(self, token: Dict, whale_data: Dict):
        """Alert about whale activity"""
        logging.info(f"Whale Activity: {token['symbol']}")
        # Add your notification logic here

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scanner = FastTokenScanner()
    asyncio.run(scanner.start())
