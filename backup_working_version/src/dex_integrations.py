from abc import ABC, abstractmethod
import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
import json
import os
from decimal import Decimal

class DEXInterface(ABC):
    @abstractmethod
    async def get_price(self, base_token: str, quote_token: str) -> float:
        pass
    
    @abstractmethod
    async def get_liquidity(self, base_token: str, quote_token: str) -> float:
        pass

class RaydiumDEX(DEXInterface):
    def __init__(self):
        self.base_url = "https://api.raydium.io/v2"
        self.pools = {}
        
    async def get_price(self, base_token: str, quote_token: str) -> float:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/main/pool/{base_token}-{quote_token}") as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['price'])
                return 0.0
    
    async def get_liquidity(self, base_token: str, quote_token: str) -> float:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/main/pool/{base_token}-{quote_token}") as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['liquidity'])
                return 0.0

class OrcaDEX(DEXInterface):
    def __init__(self):
        self.base_url = "https://api.orca.so"
        self.pools = {}
        
    async def get_price(self, base_token: str, quote_token: str) -> float:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/v1/pool/{base_token}-{quote_token}") as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['price'])
                return 0.0
    
    async def get_liquidity(self, base_token: str, quote_token: str) -> float:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/v1/pool/{base_token}-{quote_token}") as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['liquidity'])
                return 0.0

class JupiterDEX(DEXInterface):
    def __init__(self):
        self.base_url = "https://price.jup.ag/v4"
        
    async def get_price(self, base_token: str, quote_token: str) -> float:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/price?ids={base_token}&vsToken={quote_token}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['data'][base_token]['price'])
                return 0.0
    
    async def get_liquidity(self, base_token: str, quote_token: str) -> float:
        # Jupiter aggregates liquidity from multiple sources
        return float('inf')

class SarosDEX(DEXInterface):
    def __init__(self):
        self.base_url = "https://api.saros.finance"
        
    async def get_price(self, base_token: str, quote_token: str) -> float:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/pools/{base_token}-{quote_token}") as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['price'])
                return 0.0
    
    async def get_liquidity(self, base_token: str, quote_token: str) -> float:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/pools/{base_token}-{quote_token}") as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['liquidity'])
                return 0.0

class MarinadeFinance(DEXInterface):
    def __init__(self):
        self.base_url = "https://api.marinade.finance"
        
    async def get_price(self, base_token: str, quote_token: str) -> float:
        if base_token != "mSOL" and quote_token != "mSOL":
            return 0.0
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/v1/price") as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['price'])
                return 0.0
    
    async def get_liquidity(self, base_token: str, quote_token: str) -> float:
        if base_token != "mSOL" and quote_token != "mSOL":
            return 0.0
            
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/v1/info") as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['total_liquidity'])
                return 0.0

class DEXManager:
    def __init__(self):
        self.dexes = {
            "Raydium": RaydiumDEX(),
            "Orca": OrcaDEX(),
            "Jupiter": JupiterDEX(),
            "Saros": SarosDEX(),
            "Marinade": MarinadeFinance()
        }
        
        # Trading pairs configuration
        self.trading_pairs = [
            ("SOL", "USDC"),
            ("SOL", "USDT"),
            ("BTC", "USDC"),
            ("ETH", "USDC"),
            ("RAY", "USDC"),
            ("ORCA", "USDC"),
            ("SRM", "USDC"),
            ("mSOL", "SOL"),
            ("mSOL", "USDC"),
            ("BONK", "USDC"),
            ("SAMO", "USDC"),
            ("COPE", "USDC"),
            ("FIDA", "USDC"),
            ("MNGO", "USDC"),
            ("SLND", "USDC")
        ]
    
    async def get_all_prices(self) -> Dict[str, Dict[str, float]]:
        """Get prices for all pairs across all DEXes"""
        prices = {}
        
        for base, quote in self.trading_pairs:
            pair_key = f"{base}-{quote}"
            prices[pair_key] = {}
            
            # Get prices from all DEXes in parallel
            tasks = []
            for dex_name, dex in self.dexes.items():
                task = asyncio.create_task(dex.get_price(base, quote))
                tasks.append((dex_name, task))
            
            # Wait for all price fetches to complete
            for dex_name, task in tasks:
                try:
                    price = await task
                    if price > 0:
                        prices[pair_key][dex_name] = price
                except Exception as e:
                    logging.error(f"Error getting price from {dex_name}: {str(e)}")
        
        return prices
    
    async def get_arbitrage_opportunities(self, min_profit_percentage: float = 1.0) -> List[Dict]:
        """Find arbitrage opportunities across all DEXes"""
        opportunities = []
        prices = await self.get_all_prices()
        
        for pair, dex_prices in prices.items():
            if len(dex_prices) < 2:
                continue
            
            # Find lowest and highest prices
            min_price_dex = min(dex_prices.items(), key=lambda x: x[1])
            max_price_dex = max(dex_prices.items(), key=lambda x: x[1])
            
            # Calculate potential profit percentage
            profit_percentage = ((max_price_dex[1] - min_price_dex[1]) / min_price_dex[1]) * 100
            
            if profit_percentage >= min_profit_percentage:
                opportunities.append({
                    'pair': pair,
                    'buy_dex': min_price_dex[0],
                    'sell_dex': max_price_dex[0],
                    'buy_price': min_price_dex[1],
                    'sell_price': max_price_dex[1],
                    'profit_percentage': profit_percentage
                })
        
        return opportunities
    
    async def get_liquidity_info(self, pair: Tuple[str, str]) -> Dict[str, float]:
        """Get liquidity information for a pair across all DEXes"""
        liquidity = {}
        base, quote = pair
        
        for dex_name, dex in self.dexes.items():
            try:
                liq = await dex.get_liquidity(base, quote)
                if liq > 0:
                    liquidity[dex_name] = liq
            except Exception as e:
                logging.error(f"Error getting liquidity from {dex_name}: {str(e)}")
        
        return liquidity
