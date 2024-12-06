from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
import json
import logging
import asyncio
import time
from decimal import Decimal
import os
from dotenv import load_dotenv
import base58
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='solana_arbitrage.log'
)

class SolanaArbitrageBot:
    def __init__(self):
        load_dotenv('.env.private')
        
        # Initialize Solana client with your preferred RPC (can use public or private)
        self.client = Client(os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com'))
        
        # Load configuration
        self.min_profit_usdc = float(os.getenv('MIN_PROFIT_USDC', '10'))
        self.max_transaction_fee = float(os.getenv('MAX_TRANSACTION_FEE', '0.1'))
        
        # Solana DEXes to monitor
        self.dexes = {
            "raydium": os.getenv('RAYDIUM_PROGRAM_ID'),
            "orca": os.getenv('ORCA_PROGRAM_ID'),
            "serum": os.getenv('SERUM_PROGRAM_ID')
        }
        
        # Token pairs to monitor (using token mints)
        self.trading_pairs = [
            {
                "name": "SOL-USDC",
                "base_mint": os.getenv('SOL_MINT'),
                "quote_mint": os.getenv('USDC_MINT')
            },
            {
                "name": "RAY-USDC",
                "base_mint": os.getenv('RAY_MINT'),
                "quote_mint": os.getenv('USDC_MINT')
            }
        ]
        
        # Initialize price cache
        self.price_cache = {}
        
    async def get_pool_price(self, dex: str, base_mint: str, quote_mint: str) -> float:
        """Get token price from a specific DEX pool"""
        try:
            # Different implementation for each DEX
            if dex == "raydium":
                # Example Raydium price fetch
                pool_info = await self.get_raydium_pool_info(base_mint, quote_mint)
                return self.calculate_raydium_price(pool_info)
            
            elif dex == "orca":
                # Example Orca price fetch
                pool_info = await self.get_orca_pool_info(base_mint, quote_mint)
                return self.calculate_orca_price(pool_info)
            
            return 0
        except Exception as e:
            logging.error(f"Error getting price from {dex}: {str(e)}")
            return 0
    
    async def get_raydium_pool_info(self, base_mint: str, quote_mint: str):
        """Get Raydium pool information"""
        try:
            # Get pool account info
            response = self.client.get_account_info(base58.b58decode(os.getenv('RAYDIUM_POOL')))
            if response["result"]["value"]:
                return response["result"]["value"]["data"]
            return None
        except Exception as e:
            logging.error(f"Error getting Raydium pool info: {str(e)}")
            return None
    
    async def get_orca_pool_info(self, base_mint: str, quote_mint: str):
        """Get Orca pool information"""
        try:
            # Get pool account info
            response = self.client.get_account_info(base58.b58decode(os.getenv('ORCA_POOL')))
            if response["result"]["value"]:
                return response["result"]["value"]["data"]
            return None
        except Exception as e:
            logging.error(f"Error getting Orca pool info: {str(e)}")
            return None
    
    def calculate_raydium_price(self, pool_info) -> float:
        """Calculate price from Raydium pool data"""
        # Implement Raydium-specific price calculation
        return 0
    
    def calculate_orca_price(self, pool_info) -> float:
        """Calculate price from Orca pool data"""
        # Implement Orca-specific price calculation
        return 0
    
    async def find_arbitrage_opportunity(self):
        """Find arbitrage opportunities between DEXes"""
        opportunities = []
        
        for pair in self.trading_pairs:
            prices = {}
            
            # Get prices from different DEXes
            for dex_name, dex_program in self.dexes.items():
                price = await self.get_pool_price(
                    dex_name,
                    pair["base_mint"],
                    pair["quote_mint"]
                )
                if price > 0:
                    prices[dex_name] = price
            
            # Need at least 2 prices to compare
            if len(prices) < 2:
                continue
            
            # Find best buy and sell prices
            buy_dex = min(prices.items(), key=lambda x: x[1])
            sell_dex = max(prices.items(), key=lambda x: x[1])
            
            price_diff = sell_dex[1] - buy_dex[1]
            potential_profit = price_diff - self.max_transaction_fee
            
            if potential_profit >= self.min_profit_usdc:
                opportunity = {
                    'pair': pair["name"],
                    'buy_dex': buy_dex[0],
                    'sell_dex': sell_dex[0],
                    'buy_price': buy_dex[1],
                    'sell_price': sell_dex[1],
                    'potential_profit': potential_profit,
                    'timestamp': datetime.now().isoformat()
                }
                opportunities.append(opportunity)
                
                # Log the opportunity
                logging.info(f"Found opportunity: {json.dumps(opportunity, indent=2)}")
                
                # Save to opportunities file
                self.save_opportunity(opportunity)
        
        return opportunities
    
    def save_opportunity(self, opportunity):
        """Save opportunity to a file for manual review"""
        try:
            filename = 'opportunities.json'
            opportunities = []
            
            # Load existing opportunities
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    opportunities = json.load(f)
            
            # Add new opportunity
            opportunities.append(opportunity)
            
            # Save updated list
            with open(filename, 'w') as f:
                json.dump(opportunities, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error saving opportunity: {str(e)}")
    
    async def run(self):
        """Main bot loop"""
        logging.info("Starting Solana arbitrage bot...")
        
        while True:
            try:
                # Find opportunities
                opportunities = await self.find_arbitrage_opportunity()
                
                if opportunities:
                    print(f"\nFound {len(opportunities)} opportunities!")
                    print("Check opportunities.json for details")
                    print("Open your Phantom wallet to execute trades\n")
                
                # Wait before next scan
                await asyncio.sleep(1)
                
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    bot = SolanaArbitrageBot()
    asyncio.run(bot.run())
