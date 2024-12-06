import asyncio
import json
import logging
from web3 import Web3
from decimal import Decimal
from typing import List, Dict, Tuple
import os
from dotenv import load_dotenv
from eth_typing import Address
import time
import aiohttp
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='flash_arbitrage.log'
)

load_dotenv()

class ArbitrageBot:
    def __init__(self):
        # Initialize Web3 with your private node (not public ones to avoid detection)
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('PRIVATE_RPC_URL')))
        
        # Load contracts
        self.flash_loan_contract = self.load_contract(
            os.getenv('FLASH_LOAN_ADDRESS'),
            'FlashLoanArbitrage.json'
        )
        
        # Initialize DEX contracts
        self.dex_contracts = self.load_dex_contracts()
        
        # Bot configuration
        self.min_profit_usd = float(os.getenv('MIN_PROFIT_USD', '100'))
        self.max_gas_price = int(os.getenv('MAX_GAS_GWEI', '50'))
        self.private_key = os.getenv('PRIVATE_KEY')
        self.account = self.w3.eth.account.from_key(self.private_key)
        
        # Trading pairs to monitor
        self.trading_pairs = [
            ("WETH", "USDC"),
            ("WETH", "DAI"),
            ("WBTC", "USDC"),
            # Add more pairs as needed
        ]
        
        # DEX addresses (using random addresses for example)
        self.dexes = {
            "uniswap_v2": "0x1234...",
            "sushiswap": "0x5678...",
            "pancakeswap": "0x9abc..."
        }
        
        # Initialize price cache
        self.price_cache = {}
        
    def load_contract(self, address: str, contract_file: str) -> object:
        """Load contract ABI and return contract instance"""
        with open(f'artifacts/contracts/{contract_file}') as f:
            contract_json = json.load(f)
        return self.w3.eth.contract(
            address=self.w3.to_checksum_address(address),
            abi=contract_json['abi']
        )
    
    def load_dex_contracts(self) -> Dict:
        """Load DEX contract instances"""
        # Implementation would load actual DEX contracts
        return {}
    
    async def get_token_price(self, token: str, dex: str) -> float:
        """Get token price from DEX with randomized delays to avoid detection"""
        await asyncio.sleep(random.uniform(0.1, 0.5))  # Random delay
        
        # In production, this would make actual DEX calls
        # For now, simulate price with some randomness
        base_prices = {
            "WETH": 2000.0,
            "WBTC": 35000.0,
            "USDC": 1.0,
            "DAI": 1.0
        }
        
        # Add some random variation to simulate market movement
        variation = random.uniform(-0.001, 0.001)
        return base_prices.get(token, 0) * (1 + variation)
    
    async def find_arbitrage_opportunity(self) -> Tuple[bool, Dict]:
        """Scan for arbitrage opportunities across DEXes"""
        for base, quote in self.trading_pairs:
            prices = {}
            
            # Get prices from different DEXes
            for dex in self.dexes.keys():
                try:
                    price = await self.get_token_price(base, dex)
                    prices[dex] = price
                except Exception as e:
                    logging.error(f"Error getting price from {dex}: {str(e)}")
                    continue
            
            # Find best buy and sell prices
            if len(prices) < 2:
                continue
                
            buy_dex = min(prices.items(), key=lambda x: x[1])
            sell_dex = max(prices.items(), key=lambda x: x[1])
            
            price_diff = sell_dex[1] - buy_dex[1]
            profit_usd = price_diff * 1  # Assuming 1 unit trade
            
            if profit_usd >= self.min_profit_usd:
                opportunity = {
                    'base_token': base,
                    'quote_token': quote,
                    'buy_dex': buy_dex[0],
                    'sell_dex': sell_dex[0],
                    'buy_price': buy_dex[1],
                    'sell_price': sell_dex[1],
                    'potential_profit_usd': profit_usd
                }
                return True, opportunity
                
        return False, {}
    
    async def execute_arbitrage(self, opportunity: Dict) -> bool:
        """Execute the arbitrage trade"""
        try:
            # Check gas price first
            gas_price = self.w3.eth.gas_price
            if gas_price > self.max_gas_price * 10**9:
                logging.info(f"Gas price too high: {gas_price/10**9} gwei")
                return False
            
            # Prepare transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Encode the trade data
            trade_data = self.flash_loan_contract.encodeABI(
                fn_name='executeArbitrage',
                args=[
                    self.w3.to_checksum_address(opportunity['base_token']),
                    Web3.to_wei(1, 'ether'),  # Amount to borrow
                    self.w3.to_bytes(hexstr=opportunity['buy_dex']),
                    [opportunity['buy_dex'], opportunity['sell_dex']]
                ]
            )
            
            # Build transaction
            tx = {
                'nonce': nonce,
                'gas': 500000,  # Estimate gas
                'gasPrice': gas_price,
                'to': self.flash_loan_contract.address,
                'data': trade_data,
                'value': 0
            }
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                logging.info(f"Arbitrage executed successfully! Tx: {tx_hash.hex()}")
                return True
            else:
                logging.error(f"Arbitrage failed! Tx: {tx_hash.hex()}")
                return False
                
        except Exception as e:
            logging.error(f"Error executing arbitrage: {str(e)}")
            return False
    
    async def run_bot(self):
        """Main bot loop"""
        logging.info("Starting arbitrage bot...")
        
        while True:
            try:
                # Find opportunity
                found, opportunity = await self.find_arbitrage_opportunity()
                
                if found:
                    logging.info(f"Found opportunity: {json.dumps(opportunity, indent=2)}")
                    
                    # Execute if profitable
                    if opportunity['potential_profit_usd'] > self.min_profit_usd:
                        success = await self.execute_arbitrage(opportunity)
                        if success:
                            # Add random delay to avoid detection
                            await asyncio.sleep(random.uniform(1, 3))
                        
                # Random delay between scans to avoid detection
                await asyncio.sleep(random.uniform(0.5, 2))
                
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    bot = ArbitrageBot()
    asyncio.run(bot.run_bot())
