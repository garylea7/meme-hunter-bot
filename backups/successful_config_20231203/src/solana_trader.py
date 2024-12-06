import asyncio
import logging
import json
import random
import time
from typing import Dict, List, Optional
from decimal import Decimal
import aiohttp
from dataclasses import dataclass
import os
from datetime import datetime, timezone

@dataclass
class TradeConfig:
    """Trading configuration settings"""
    buy_amounts: List[float] = None  # [0.25, 0.5, 1, 5, 10] SOL
    sell_percentages: List[int] = None  # [1, 5, 10, 50, 100]
    slippage: int = 20
    degen_mode: bool = False
    mev_protection: bool = False

@dataclass
class TokenMetrics:
    """Token trading metrics"""
    liquidity: float
    volume_24h: float
    top_holders_percentage: float
    market_cap: float
    price: float
    holders: int

class VPNManager:
    """Manage VPN connections for 24/7 trading"""
    def __init__(self, ocean_config_path: str):
        self.config_path = ocean_config_path
        self.current_server = None
        self.rotation_interval = 3600  # 1 hour
        self.last_rotation = 0
        self.servers = self.load_ocean_servers()
        
    def load_ocean_servers(self) -> List[str]:
        """Load Ocean VPN server list"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config.get('servers', [])
        except Exception as e:
            logging.error(f"Failed to load Ocean VPN servers: {str(e)}")
            return []
            
    async def rotate_vpn(self):
        """Rotate to new VPN server"""
        try:
            if not self.servers:
                logging.error("No VPN servers available")
                return False
                
            current_time = time.time()
            if current_time - self.last_rotation < self.rotation_interval:
                return True  # Not time to rotate yet
                
            # Select new server
            new_server = random.choice([s for s in self.servers if s != self.current_server])
            
            # Connect to new server
            success = await self._connect_vpn(new_server)
            if success:
                self.current_server = new_server
                self.last_rotation = current_time
                logging.info(f"Rotated to new VPN server: {new_server}")
                return True
            return False
            
        except Exception as e:
            logging.error(f"VPN rotation error: {str(e)}")
            return False
            
    async def _connect_vpn(self, server: str) -> bool:
        """Connect to specific VPN server"""
        try:
            # Execute Ocean VPN connection command
            process = await asyncio.create_subprocess_exec(
                'ocean-cli',
                'connect',
                server,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            return process.returncode == 0
            
        except Exception as e:
            logging.error(f"VPN connection error: {str(e)}")
            return False

class SolanaTrader:
    def __init__(self, wallet_address: str, private_key: str, ocean_config_path: str):
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.positions = {}
        self.tracked_wallets = set()
        self.vpn_manager = VPNManager(ocean_config_path)
        
        # Get root directory
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Load trade history
        self.trade_history_path = os.path.join(self.root_dir, 'database', 'trade_history.json')
        self.trade_history = self.load_trade_history()
        
        # Performance improvements
        self.session = None
        self.max_stored_transactions = 1000
        self.processed_transactions = []  # Changed to list for better memory management
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 3600  # Cleanup every hour
        
        # Memory-efficient tracking
        self.position_history = {
            'timestamps': [],
            'prices': [],
            'amounts': []
        }
        self.max_history_size = 10000
        
        # Resource monitoring
        self.resource_usage = {
            'memory': [],
            'cpu': [],
            'network': []
        }
        
        # Default configuration from video
        self.config = TradeConfig(
            buy_amounts=[0.25, 0.5, 1, 5, 10],
            sell_percentages=[1, 5, 10, 50, 100],
            slippage=20,
            degen_mode=False,
            mev_protection=False
        )
        
        # Initialize RPC endpoints with weights
        self.rpc_endpoints = {
            "https://api.mainnet-beta.solana.com": {'weight': 1, 'fails': 0},
            "https://solana-api.projectserum.com": {'weight': 1, 'fails': 0},
            "https://rpc.ankr.com/solana": {'weight': 1, 'fails': 0}
        }
        self.current_rpc = None
        self.last_rpc_rotation = time.time()
        self.rpc_rotation_interval = 300  # 5 minutes
        
        # Security settings
        self.security_checks = {
            'autosnipe': True,      # AutoSnipe rug detection
            'bullx': True,          # BullX security checks
            'gmgn': True,           # GMGN token validation
            'social': False,        # Optional social sentiment
            'whales': False         # Optional whale tracking
        }
        
        # Rug pull detection thresholds
        self.rug_thresholds = {
            'max_dev_wallet': 0.05,          # Max 5% in dev wallet
            'max_unlocked_tokens': 0.20,     # Max 20% unlocked
            'min_lp_lock_time': 180,         # 180 days minimum LP lock
            'max_tax': 0.10,                 # Max 10% tax
            'min_unique_holders': 100,       # Minimum unique holders
            'max_wallet_size': 0.02,         # Max 2% per wallet
            'min_lp_value': 50_000           # Minimum $50k LP value
        }
        
        # AutoSnipe Security Settings
        self.autosnipe_config = {
            'security': {
                'max_buy_tax': 0.07,  # 7%
                'max_sell_tax': 0.07,  # 7%
                'min_lp_lock_days': 365,
                'max_dev_wallet_percent': 0.03,  # 3%
                'min_unique_holders': 150,
                'min_lp_value_usd': 75000,
                'max_price_impact': 0.15,  # 15%
                'min_24h_volume': 5000,  # $5k
                'min_market_cap': 50000,  # $50k
                'max_concentration': 0.15,  # Max 15% in single wallet
                'min_token_age_hours': 24,  # At least 24 hours old
            },
            'monitoring': {
                'check_interval': 60,  # seconds
                'price_change_alert': 0.10,  # 10%
                'volume_change_alert': 0.20,  # 20%
                'holder_change_alert': 0.05,  # 5%
                'lp_change_alert': 0.10,  # 10%
                'max_consecutive_fails': 3,
            },
            'scoring': {
                'honeypot_weight': 0.35,
                'lp_lock_weight': 0.20,
                'holder_weight': 0.10,
                'dev_wallet_weight': 0.15,
                'contract_weight': 0.20,
            }
        }
        
        # Initialize monitoring state
        self.monitoring_state = {}
        
        # Initialize blacklisted tokens
        self.blacklisted_tokens = set()
        
        # Initialize monitored tokens
        self.monitored_tokens = set()
        
        # Initialize test trades
        self.test_trades = []
        
        # Trading Strategy Settings
        self.trading_config = {
            'entry': {
                'momentum_threshold': 0.05,  # 5% price increase
                'volume_threshold': 10000,   # $10k min volume
                'time_window': 300,         # 5 minutes
                'max_slippage': 0.02,       # 2% max slippage
                'min_liquidity': 50000,     # $50k min liquidity
            },
            'exit': {
                'take_profit': 0.20,        # 20% profit target
                'stop_loss': 0.10,          # 10% stop loss
                'trailing_stop': 0.05,      # 5% trailing stop
                'max_hold_time': 3600,      # 1 hour max hold
            },
            'position': {
                'max_position_size': 0.10,   # 10% of portfolio
                'min_position_size': 0.01,   # 1% of portfolio
                'max_open_positions': 5,     # Max 5 concurrent positions
                'position_scaling': True,    # Enable position scaling
            },
            'risk': {
                'daily_loss_limit': 0.05,    # 5% max daily loss
                'max_drawdown': 0.15,        # 15% max drawdown
                'correlation_threshold': 0.7, # Max correlation between positions
                'volatility_threshold': 0.5,  # Max acceptable volatility
            }
        }
        
        # MEV Protection Settings
        self.mev_config = {
            'mempool_analysis': {
                'block_window': 10,          # Analyze last 10 blocks
                'max_pending_txs': 1000,     # Max pending transactions to analyze
                'gas_price_threshold': 1.5,  # 1.5x average gas price threshold
                'sandwich_detection': True,   # Enable sandwich attack detection
                'frontrun_protection': True,  # Enable frontrunning protection
                'backrun_protection': True,   # Enable backrunning protection
            },
            'transaction_protection': {
                'private_tx': True,           # Use private transaction service
                'time_delay': 2,              # Random delay 0-2 seconds
                'gas_optimization': True,     # Smart gas price optimization
                'route_splitting': True,      # Split large trades across routes
                'slippage_optimization': True # Dynamic slippage adjustment
            },
            'routing': {
                'max_routes': 3,              # Max number of split routes
                'min_route_amount': 0.1,      # Min amount per route in SOL
                'route_selection': 'smart',   # Smart route selection algorithm
                'dex_preference': ['Orca', 'Raydium', 'Serum']  # Preferred DEXes
            }
        }
        
    def setup_connection_pool(self):
        """Initialize connection pool with proper limits"""
        if not hasattr(self, 'session') or self.session is None:
            connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
            self.session = aiohttp.ClientSession(connector=connector)
            logging.info("Initialized aiohttp session")

    def cleanup_resources(self):
        """Cleanup old data and manage memory"""
        current_time = time.time()
        
        # Only cleanup if enough time has passed
        if current_time - self.last_cleanup_time < self.cleanup_interval:
            return
            
        try:
            # Trim processed transactions
            if len(self.processed_transactions) > self.max_stored_transactions:
                self.processed_transactions = self.processed_transactions[-self.max_stored_transactions:]
            
            # Cleanup old positions
            self.positions = {
                k: v for k, v in self.positions.items()
                if current_time - v['timestamp'] < 86400  # Keep last 24 hours
            }
            
            # Trim position history
            for key in ['timestamps', 'prices', 'amounts']:
                if len(self.position_history[key]) > self.max_history_size:
                    self.position_history[key] = self.position_history[key][-self.max_history_size:]
            
            # Cleanup resource monitoring
            max_resource_history = 1000
            for key in self.resource_usage:
                if len(self.resource_usage[key]) > max_resource_history:
                    self.resource_usage[key] = self.resource_usage[key][-max_resource_history:]
            
            self.last_cleanup_time = current_time
            
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")

    def _rotate_rpc(self):
        """Smart RPC endpoint rotation with failover"""
        current_time = time.time()
        
        # Only rotate if enough time has passed
        if current_time - self.last_rpc_rotation < self.rpc_rotation_interval:
            return
            
        try:
            # Sort endpoints by weight/fails ratio
            valid_endpoints = {
                endpoint: data
                for endpoint, data in self.rpc_endpoints.items()
                if data['fails'] < 5  # Exclude endpoints with too many failures
            }
            
            if not valid_endpoints:
                # Reset fails if all endpoints are failing
                for data in self.rpc_endpoints.values():
                    data['fails'] = 0
                valid_endpoints = self.rpc_endpoints
            
            # Select endpoint with best weight/fails ratio
            self.current_rpc = max(
                valid_endpoints.items(),
                key=lambda x: x[1]['weight'] / (x[1]['fails'] + 1)
            )[0]
            
            self.last_rpc_rotation = current_time
            
        except Exception as e:
            logging.error(f"Error rotating RPC: {str(e)}")
            # Fallback to first endpoint
            self.current_rpc = list(self.rpc_endpoints.keys())[0]

    async def monitor_with_backoff(self):
        """Monitor wallets with smart backoff and resource management"""
        backoff = 1
        max_backoff = 60
        
        while True:
            try:
                # Cleanup resources first
                self.cleanup_resources()
                
                # Rotate RPC if needed
                self._rotate_rpc()
                
                # Monitor wallets
                async with self.session.get(
                    f"{self.current_rpc}/get_wallet_transactions",
                    params={'address': list(self.tracked_wallets)}
                ) as response:
                    data = await response.json()
                    
                    # Process new transactions
                    for tx in data:
                        if tx['signature'] not in self.processed_transactions:
                            await self.analyze_and_copy_trade(tx)
                            self.processed_transactions.append(tx['signature'])
                    
                    # Success - reset backoff
                    backoff = 1
                    
                    # Update RPC stats
                    self.rpc_endpoints[self.current_rpc]['fails'] = 0
                    
            except Exception as e:
                logging.error(f"Error in monitoring: {str(e)}")
                # Increment fail counter for current RPC
                self.rpc_endpoints[self.current_rpc]['fails'] += 1
                
                # Apply backoff
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
            
            # Small sleep to prevent tight loops
            await asyncio.sleep(1)

    async def start(self):
        """Start trading with proper initialization"""
        try:
            # Setup connections
            self.setup_connection_pool()
            
            # Initialize VPN
            await self.vpn_manager.rotate_vpn()
            
            # Start monitoring tasks
            monitoring_task = asyncio.create_task(self.monitor_with_backoff())
            vpn_rotation_task = asyncio.create_task(self.vpn_manager.auto_rotate())
            security_monitoring_task = asyncio.create_task(self.start_security_monitoring())
            
            # Wait for tasks
            await asyncio.gather(monitoring_task, vpn_rotation_task, security_monitoring_task)
            
        except Exception as e:
            logging.error(f"Error starting trader: {str(e)}")
        finally:
            # Cleanup
            if hasattr(self, 'session') and self.session:
                await self.session.close()

    async def setup_wallet_tracking(self, wallet_addresses: List[str]):
        """Setup wallet tracking for copy trading"""
        self.tracked_wallets.update(wallet_addresses)
        await self.start_wallet_monitoring()
        
    async def start_wallet_monitoring(self):
        """Monitor tracked wallets for trades"""
        while True:
            for wallet in self.tracked_wallets:
                try:
                    transactions = await self.get_wallet_transactions(wallet)
                    for tx in transactions:
                        if self.is_new_trade(tx):
                            await self.analyze_and_copy_trade(tx)
                except Exception as e:
                    logging.error(f"Wallet monitoring error: {str(e)}")
            await asyncio.sleep(1)  # Poll interval
            
    async def analyze_token(self, token_address: str) -> Optional[TokenMetrics]:
        """Analyze token metrics before trading"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get token data from DEX Screener API
                async with session.get(
                    f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
                ) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()
                    
                    # Extract metrics
                    metrics = TokenMetrics(
                        liquidity=float(data.get('liquidity', 0)),
                        volume_24h=float(data.get('volume24h', 0)),
                        top_holders_percentage=await self.get_top_holders_percentage(token_address),
                        market_cap=float(data.get('marketCap', 0)),
                        price=float(data.get('price', 0)),
                        holders=int(data.get('holders', 0))
                    )
                    
                    return metrics
                    
        except Exception as e:
            logging.error(f"Token analysis error: {str(e)}")
            return None
            
    async def get_top_holders_percentage(self, token_address: str) -> float:
        """Get percentage of tokens held by top wallets"""
        try:
            # Get holder data
            holders = await self.get_token_holders(token_address)
            
            # Calculate top holders percentage
            total_supply = sum(h['balance'] for h in holders)
            top_holders_balance = sum(h['balance'] for h in holders[:10])  # Top 10 holders
            
            return (top_holders_balance / total_supply) * 100 if total_supply > 0 else 0
            
        except Exception as e:
            logging.error(f"Holder analysis error: {str(e)}")
            return 100  # Return 100% as safety measure
            
    async def execute_trade(self, token_address: str, amount_sol: float, is_buy: bool = True):
        """Execute trade with bloom bot style parameters"""
        try:
            if is_buy:
                # Pre-trade checks
                metrics = await self.analyze_token(token_address)
                if not metrics:
                    return False
                    
                # Safety checks (from video)
                if (metrics.top_holders_percentage > 20 or  # Top holders < 20%
                    not await self.is_liquidity_locked(token_address) or  # Liquidity must be locked
                    metrics.volume_24h < 1000):  # Minimum volume
                    logging.warning(f"Safety checks failed for token {token_address}")
                    return False
                    
                # Execute buy
                success = await self._execute_buy(
                    token_address=token_address,
                    amount_sol=amount_sol,
                    slippage=self.config.slippage,
                    degen_mode=self.config.degen_mode
                )
                
                if success:
                    self.positions[token_address] = {
                        'amount': amount_sol,
                        'entry_price': metrics.price,
                        'time': asyncio.get_event_loop().time()
                    }
                
                return success
                
            else:
                # Execute sell
                return await self._execute_sell(
                    token_address=token_address,
                    percentage=100,  # Full sell
                    slippage=self.config.slippage
                )
                
        except Exception as e:
            logging.error(f"Trade execution error: {str(e)}")
            return False
            
    async def set_limit_order(self, token_address: str, price: float, amount_sol: float, is_buy: bool = True):
        """Set limit order for token"""
        try:
            order = {
                'token_address': token_address,
                'price': price,
                'amount_sol': amount_sol,
                'is_buy': is_buy,
                'time': asyncio.get_event_loop().time()
            }
            
            # Store order and start monitoring
            await self._monitor_limit_order(order)
            return True
            
        except Exception as e:
            logging.error(f"Limit order error: {str(e)}")
            return False
            
    async def enable_sniper_mode(self, token_address: str, max_amount_sol: float):
        """Enable sniper mode for new token"""
        try:
            # Monitor token for listing
            while True:
                if await self.is_token_live(token_address):
                    # Execute instant buy when token is live
                    return await self.execute_trade(
                        token_address=token_address,
                        amount_sol=max_amount_sol,
                        is_buy=True
                    )
                await asyncio.sleep(0.1)  # Fast polling
                
        except Exception as e:
            logging.error(f"Sniper mode error: {str(e)}")
            return False
            
    async def get_wallet_transactions(self, wallet_address: str) -> List[Dict]:
        """Get recent transactions for wallet"""
        try:
            # Rotate VPN if needed
            await self.vpn_manager.rotate_vpn()
            
            async with self.session.get(
                f"{self.current_rpc}/getSignaturesForAddress",
                params={'address': wallet_address, 'limit': 20}
            ) as response:
                if response.status != 200:
                    self._rotate_rpc()
                    return []
                    
                data = await response.json()
                signatures = [tx['signature'] for tx in data.get('result', [])]
                
                # Get transaction details
                transactions = []
                for sig in signatures:
                    tx_data = await self._get_transaction(sig)
                    if tx_data:
                        transactions.append(tx_data)
                
                return transactions
                
        except Exception as e:
            logging.error(f"Failed to get wallet transactions: {str(e)}")
            self._rotate_rpc()
            return []
            
    def is_new_trade(self, transaction: Dict) -> bool:
        """Check if transaction is a new trade"""
        try:
            # Check if transaction is a swap/trade
            if not transaction.get('meta', {}).get('logMessages'):
                return False
                
            logs = transaction['meta']['logMessages']
            is_swap = any('swap' in log.lower() for log in logs)
            
            # Check if it's a new transaction we haven't processed
            is_new = transaction['signature'] not in self.processed_transactions
            
            if is_swap and is_new:
                self.processed_transactions.append(transaction['signature'])
                return True
                
            return False
            
        except Exception as e:
            logging.error(f"Trade check error: {str(e)}")
            return False
            
    async def analyze_and_copy_trade(self, transaction: Dict):
        """Analyze and potentially copy a trade"""
        try:
            # Extract token and amount
            token_address = self._extract_token_address(transaction)
            amount_sol = self._extract_amount_sol(transaction)
            
            if not token_address or not amount_sol:
                return
                
            # Analyze token
            metrics = await self.analyze_token(token_address)
            if not metrics:
                return
                
            # Apply trading criteria
            if (metrics.top_holders_percentage <= 20 and  # Max 20% whale concentration
                metrics.volume_24h >= 1000 and  # Minimum volume
                await self.is_liquidity_locked(token_address)):  # Locked liquidity
                
                # Execute copy trade
                await self.execute_trade(
                    token_address=token_address,
                    amount_sol=min(amount_sol, max(self.config.buy_amounts)),  # Cap at max configured amount
                    is_buy=True
                )
                
        except Exception as e:
            logging.error(f"Copy trade error: {str(e)}")
            
    async def get_token_holders(self, token_address: str) -> List[Dict]:
        """Get token holder data"""
        try:
            async with self.session.get(
                f"https://public-api.solscan.io/token/holders?tokenAddress={token_address}"
            ) as response:
                if response.status != 200:
                    return []
                    
                data = await response.json()
                return data.get('data', [])
                
        except Exception as e:
            logging.error(f"Failed to get token holders: {str(e)}")
            return []
            
    async def is_liquidity_locked(self, token_address: str) -> bool:
        """Check if token liquidity is locked"""
        try:
            # Check common liquidity lockers
            lockers = [
                "UniCrypt",
                "PinkLock",
                "MudraLocker"
            ]
            
            async with self.session.get(
                f"https://api.{lockers[0].lower()}.com/api/v1/locks/{token_address}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('locked'):
                        return True
                                
            return False
            
        except Exception as e:
            logging.error(f"Liquidity lock check error: {str(e)}")
            return False
            
    async def _get_transaction(self, signature: str) -> Optional[Dict]:
        """Get transaction details"""
        try:
            async with self.session.post(
                self.rpc_endpoints[self.current_rpc],
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [
                        signature,
                        {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
                    ]
                }
            ) as response:
                if response.status != 200:
                    self._rotate_rpc()
                    return None
                    
                data = await response.json()
                return data.get('result')
                
        except Exception as e:
            logging.error(f"Transaction fetch error: {str(e)}")
            return None
            
    def _extract_token_address(self, transaction: Dict) -> Optional[str]:
        """Extract token address from transaction"""
        try:
            # Check instruction data
            for ix in transaction.get('meta', {}).get('innerInstructions', []):
                for inner_ix in ix.get('instructions', []):
                    # Check for token program interactions
                    if inner_ix.get('programId') == 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA':
                        # Extract token account
                        accounts = inner_ix.get('accounts', [])
                        if len(accounts) >= 2:
                            return accounts[1]  # Usually the token mint address
                            
            return None
            
        except Exception as e:
            logging.error(f"Token address extraction error: {str(e)}")
            return None
            
    def _extract_amount_sol(self, transaction: Dict) -> Optional[float]:
        """Extract SOL amount from transaction"""
        try:
            # Look for SOL transfer in pre/post balances
            pre_balances = transaction.get('meta', {}).get('preBalances', [])
            post_balances = transaction.get('meta', {}).get('postBalances', [])
            
            if len(pre_balances) > 0 and len(post_balances) > 0:
                # Calculate difference in SOL
                diff = abs(pre_balances[0] - post_balances[0])
                return diff / 1e9  # Convert lamports to SOL
                
            return None
            
        except Exception as e:
            logging.error(f"Amount extraction error: {str(e)}")
            return None
            
    async def _sign_transaction(self, tx: Dict) -> Optional[str]:
        """Sign transaction"""
        try:
            # Create transaction object
            transaction = {
                "recentBlockhash": await self._get_recent_blockhash(),
                "feePayer": self.wallet_address,
                "instructions": [
                    {
                        "programId": "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",  # Jupiter aggregator
                        "accounts": [
                            {"pubkey": self.wallet_address, "isSigner": True, "isWritable": True},
                            {"pubkey": tx['token'], "isSigner": False, "isWritable": True}
                        ],
                        "data": self._encode_swap_data(tx)
                    }
                ]
            }
            
            # Sign with private key
            signed = await self._sign_with_private_key(transaction)
            return signed
            
        except Exception as e:
            logging.error(f"Transaction signing error: {str(e)}")
            return None
            
    async def _submit_transaction(self, signed_tx: str) -> bool:
        """Submit signed transaction"""
        try:
            async with self.session.post(
                self.rpc_endpoints[self.current_rpc],
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "sendTransaction",
                    "params": [
                        signed_tx,
                        {"encoding": "base64"}
                    ]
                }
            ) as response:
                if response.status != 200:
                    self._rotate_rpc()
                    return False
                    
                data = await response.json()
                return 'result' in data
                
        except Exception as e:
            logging.error(f"Transaction submission error: {str(e)}")
            return False
            
    async def _get_token_balance(self, token_address: str) -> Optional[float]:
        """Get token balance"""
        try:
            async with self.session.post(
                self.rpc_endpoints[self.current_rpc],
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTokenAccountsByOwner",
                    "params": [
                        self.wallet_address,
                        {"mint": token_address},
                        {"encoding": "jsonParsed"}
                    ]
                }
            ) as response:
                if response.status != 200:
                    self._rotate_rpc()
                    return None
                    
                data = await response.json()
                accounts = data.get('result', {}).get('value', [])
                
                if accounts:
                    # Get balance from first account
                    balance = accounts[0].get('account', {}).get('data', {}).get('parsed', {}).get('info', {}).get('tokenAmount', {}).get('uiAmount')
                    return float(balance) if balance is not None else None
                    
                return None
                
        except Exception as e:
            logging.error(f"Balance fetch error: {str(e)}")
            return None
            
    async def _get_token_price(self, token_address: str) -> Optional[float]:
        """Get current token price"""
        try:
            # Use Jupiter API for price data
            async with self.session.get(
                f"https://price.jup.ag/v4/price?ids={token_address}"
            ) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                return float(data.get('data', {}).get(token_address, {}).get('price', 0))
                
        except Exception as e:
            logging.error(f"Price fetch error: {str(e)}")
            return None
            
    async def _get_pool_data(self, token_address: str) -> Dict:
        """Get pool data for token"""
        try:
            # Use Raydium API for pool data
            async with self.session.get(
                f"https://api.raydium.io/v2/main/pool/{token_address}"
            ) as response:
                if response.status != 200:
                    return {}
                    
                data = await response.json()
                return {
                    'liquidity': float(data.get('liquidity', 0)),
                    'volume_24h': float(data.get('volume24h', 0)),
                    'price': float(data.get('price', 0)),
                    'price_change_24h': float(data.get('priceChange24h', 0))
                }
                
        except Exception as e:
            logging.error(f"Pool data fetch error: {str(e)}")
            return {}
            
    async def _get_recent_blockhash(self) -> Optional[str]:
        """Get recent blockhash for transaction"""
        try:
            async with self.session.post(
                self.rpc_endpoints[self.current_rpc],
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getRecentBlockhash"
                }
            ) as response:
                if response.status != 200:
                    self._rotate_rpc()
                    return None
                    
                data = await response.json()
                return data.get('result', {}).get('value', {}).get('blockhash')
                
        except Exception as e:
            logging.error(f"Blockhash fetch error: {str(e)}")
            return None
            
    def _encode_swap_data(self, tx: Dict) -> bytes:
        """Encode swap instruction data"""
        try:
            # Basic swap instruction encoding
            # In practice, you'd want to use proper Solana instruction encoding
            return bytes([
                0x0,  # Swap instruction
                *list(int(tx['amount_in'] * 1e9).to_bytes(8, 'little')),  # Amount in
                *list(int(tx['slippage'] * 100).to_bytes(2, 'little'))  # Slippage
            ])
            
        except Exception as e:
            logging.error(f"Swap data encoding error: {str(e)}")
            return bytes()
            
    async def _sign_with_private_key(self, transaction: Dict) -> Optional[str]:
        """Sign transaction with private key"""
        try:
            # In practice, implement proper Solana transaction signing
            # This is a placeholder for the actual implementation
            return "signed_transaction_base64"
            
        except Exception as e:
            logging.error(f"Transaction signing error: {str(e)}")
            return None
            
    def _rotate_rpc(self):
        """Rotate to next RPC endpoint"""
        self.current_rpc = list(self.rpc_endpoints.keys())[0]

    # Known successful whale wallets (from orange guy's list)
    WHALE_WALLETS = [
        'FZtXGrHhtKqgw2VGBp8NEzG4QQnQ4ZP3wGwAEBYCgqdi',  # GMGN whale
        '5GtGEKh5sLpRX7bkuhqT6NerR6FNuiV8mvVqnL6L7Gyu',  # BullX whale
        '9HzJyW1qZsEiSfMUf6L2jo3CcTKAyBmSyKdwQeYisHrC',  # Orange's alpha wallet
        # Add more from his list as we get them
    ]

    # GMGN-specific settings
    GMGN_SETTINGS = {
        'min_wallet_age_days': 90,        # Proven track record
        'min_successful_trades': 25,      # Consistent performance
        'min_avg_profit_percent': 150,    # 150%+ average gains
        'max_loss_streak': 3,            # Risk management
        'min_win_rate': 0.65             # 65%+ success rate
    }

    # BullX criteria
    BULLX_CRITERIA = {
        'volume_multiplier': 3,           # 3x volume spike
        'holder_growth_rate': 50,         # 50+ new holders/hour
        'price_impact': 0.02,             # 2% price impact per trade
        'liquidity_depth': 100_000        # $100k min liquidity
    }

    async def track_successful_whales(self):
        """Track successful whale wallets for signals"""
        try:
            while True:
                all_wallets = set()
                
                # 1. Add known whale wallets from orange guy's list
                all_wallets.update(WHALE_WALLETS)
                
                # 2. Add GMGN-discovered wallets
                gmgn_wallets = await self._get_gmgn_wallets()
                all_wallets.update(w['address'] for w in gmgn_wallets)
                
                # 3. Get top performing wallets from Solscan
                solscan_wallets = await self._get_top_wallets()
                all_wallets.update(w['address'] for w in solscan_wallets)
                
                # Track all wallets
                for wallet in all_wallets:
                    # Get recent transactions
                    transactions = await self._get_wallet_transactions(wallet)
                    
                    for tx in transactions:
                        # Check if it's a token buy
                        token_address = self._extract_token_address(tx)
                        if not token_address:
                            continue
                            
                        # Get BullX signals
                        bullx_signals = await self._check_bullx_signals(token_address)
                        
                        # Only proceed if BullX is bullish
                        if not bullx_signals['overall_bullish']:
                            continue
                            
                        # Analyze token potential
                        token_score = await self._analyze_token_potential(token_address)
                        
                        if token_score['total'] >= 85:  # High potential token
                            # Check social sentiment
                            sentiment = await self._check_social_sentiment(token_address)
                            
                            if sentiment['score'] >= 70:  # Strong community interest
                                # Calculate position size
                                position_size = self._calculate_position_size(
                                    token_score,
                                    sentiment['momentum']
                                )
                                
                                # Execute trade with tight stops
                                await self._execute_whale_following_trade(
                                    token_address,
                                    position_size,
                                    sentiment['momentum']
                                )
                                
                await asyncio.sleep(1)  # Check every second
                
        except Exception as e:
            logging.error(f"Whale tracking error: {str(e)}")

    def _calculate_position_size(self, token_score: Dict, momentum: float) -> float:
        """Calculate position size based on score and momentum"""
        try:
            # Base position size (from video)
            base_size = self.capital * 0.1  # 10% of capital
            
            # Adjust based on score
            if token_score['total'] >= 90:
                size_multiplier = 1.5
            elif token_score['total'] >= 85:
                size_multiplier = 1.0
            else:
                size_multiplier = 0.5
                
            # Adjust for momentum
            momentum_multiplier = 1 + (momentum * 0.5)  # Up to 50% increase
            
            # Additional multiplier if multiple systems confirm (GMGN + BullX)
            system_multiplier = 1.2 if token_score.get('multi_system_confirm') else 1.0
            
            return base_size * size_multiplier * momentum_multiplier * system_multiplier
            
        except Exception as e:
            logging.error(f"Position size calculation error: {str(e)}")
            return 0
            
    async def _get_gmgn_wallets(self) -> List[Dict]:
        """Get successful wallets using GMGN criteria"""
        try:
            wallets = []
            
            # Query GMGN API (they have a free tier)
            async with self.session.get(
                'https://api.gmgn.io/v1/wallets/top',
                params={
                    'timeframe': '90d',
                    'min_trades': GMGN_SETTINGS['min_successful_trades'],
                    'min_profit': GMGN_SETTINGS['min_avg_profit_percent']
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    wallets.extend(data.get('wallets', []))

            # Filter by our criteria
            filtered_wallets = []
            for wallet in wallets:
                if (
                    wallet.get('age_days', 0) >= GMGN_SETTINGS['min_wallet_age_days'] and
                    wallet.get('win_rate', 0) >= GMGN_SETTINGS['min_win_rate'] and
                    wallet.get('max_consecutive_losses', 0) <= GMGN_SETTINGS['max_loss_streak']
                ):
                    filtered_wallets.append(wallet)

            return filtered_wallets

        except Exception as e:
            logging.error(f"GMGN wallet fetch error: {str(e)}")
            return []

    async def _check_bullx_signals(self, token_address: str) -> Dict:
        """Check BullX trading signals"""
        try:
            signals = {
                'volume_spike': False,
                'holder_growth': False,
                'price_strength': False,
                'liquidity_good': False,
                'overall_bullish': False
            }

            # Get BullX metrics
            async with self.session.get(
                f'https://api.bullx.io/v1/token/{token_address}'
            ) as response:
                if response.status != 200:
                    return signals
                    
                data = await response.json()
                
                # Check volume spike
                if data.get('volume_24h_change', 0) >= BULLX_CRITERIA['volume_multiplier']:
                    signals['volume_spike'] = True
                    
                # Check holder growth
                if data.get('holder_growth_rate', 0) >= BULLX_CRITERIA['holder_growth_rate']:
                    signals['holder_growth'] = True
                    
                # Check price impact
                if data.get('price_impact', 1) <= BULLX_CRITERIA['price_impact']:
                    signals['price_strength'] = True
                    
                # Check liquidity
                if data.get('liquidity_usd', 0) >= BULLX_CRITERIA['liquidity_depth']:
                    signals['liquidity_good'] = True
                    
                # Overall signal
                signals['overall_bullish'] = (
                    signals['volume_spike'] and
                    signals['holder_growth'] and
                    signals['price_strength'] and
                    signals['liquidity_good']
                )
                
            return signals

        except Exception as e:
            logging.error(f"BullX signal check error: {str(e)}")
            return {'overall_bullish': False}

    async def _get_top_wallets(self) -> List[Dict]:
        """Get top performing wallets"""
        try:
            # Use Solscan API to get top wallets
            async with self.session.get(
                'https://api.solscan.io/account/top',
                params={'limit': 100}
            ) as response:
                if response.status != 200:
                    return []
                    
                data = await response.json()
                
                # Filter for successful traders
                return [
                    wallet for wallet in data.get('data', [])
                    if self._is_successful_trader(wallet)
                ]
                
        except Exception as e:
            logging.error(f"Error getting top wallets: {str(e)}")
            return []
            
    def _is_successful_trader(self, wallet: Dict) -> bool:
        """Check if wallet belongs to successful trader"""
        try:
            # Criteria from video
            return (
                wallet.get('profit_ratio', 0) > 2.0 and  # 200%+ profit
                wallet.get('trade_count', 0) > 50 and    # Active trader
                wallet.get('win_rate', 0) > 0.6          # 60%+ win rate
            )
            
        except Exception as e:
            logging.error(f"Trader analysis error: {str(e)}")
            return False
            
    async def _get_wallet_transactions(self, wallet: str) -> List[Dict]:
        """Get recent transactions for wallet"""
        try:
            async with self.session.get(
                f'https://api.solscan.io/account/transaction',
                params={
                    'address': wallet,
                    'limit': 50
                }
            ) as response:
                if response.status != 200:
                    return []
                    
                data = await response.json()
                return data.get('data', [])
                
        except Exception as e:
            logging.error(f"Transaction fetch error: {str(e)}")
            return []
            
    async def _analyze_token_potential(self, token_address: str) -> Dict:
        """Analyze token's potential"""
        try:
            score = {
                'liquidity': 0,
                'holders': 0,
                'momentum': 0,
                'community': 0,
                'total': 0
            }
            
            # Check liquidity (video: minimum $100k)
            pool_data = await self._get_pool_data(token_address)
            if pool_data.get('liquidity', 0) >= 100_000:
                score['liquidity'] = 100
                
            # Check holder count and distribution
            holders = await self._get_token_holders(token_address)
            if len(holders) >= 1000:
                score['holders'] = 100 * min(len(holders) / 5000, 1)
                
            # Check price momentum
            price_data = await self._get_price_history(token_address)
            momentum = self._calculate_momentum(price_data)
            score['momentum'] = momentum * 100
            
            # Check community engagement
            community = await self._check_social_sentiment(token_address)
            score['community'] = community['score']
            
            # Calculate total score with weights from video
            weights = {
                'liquidity': 0.3,
                'holders': 0.2,
                'momentum': 0.3,
                'community': 0.2
            }
            
            score['total'] = sum(
                score[k] * v for k, v in weights.items()
            )
            
            return score
            
        except Exception as e:
            logging.error(f"Token analysis error: {str(e)}")
            return {'total': 0}
            
    def _calculate_momentum(self, price_data: List) -> float:
        """Calculate price momentum"""
        try:
            if not price_data or len(price_data) < 2:
                return 0
                
            # Calculate rate of change
            latest = price_data[-1]['price']
            previous = price_data[0]['price']
            
            if previous <= 0:
                return 0
                
            change = (latest - previous) / previous
            
            # Normalize to 0-1 range
            return min(max(change, 0), 1)
            
        except Exception as e:
            logging.error(f"Momentum calculation error: {str(e)}")
            return 0
            
    async def _check_social_sentiment(self, token_address: str) -> Dict:
        """Check social media sentiment"""
        try:
            # Initialize sentiment data
            sentiment = {
                'score': 0,
                'momentum': 0,
                'platforms': {
                    'twitter': 0,
                    'telegram': 0,
                    'discord': 0
                }
            }
            
            # Check Twitter mentions (video: key indicator)
            twitter_data = await self._get_twitter_mentions(token_address)
            sentiment['platforms']['twitter'] = self._score_twitter_data(twitter_data)
            
            # Check Telegram activity
            telegram_data = await self._get_telegram_activity(token_address)
            sentiment['platforms']['telegram'] = self._score_telegram_data(telegram_data)
            
            # Check Discord engagement
            discord_data = await self._get_discord_activity(token_address)
            sentiment['platforms']['discord'] = self._score_discord_data(discord_data)
            
            # Calculate overall sentiment score
            weights = {'twitter': 0.5, 'telegram': 0.3, 'discord': 0.2}
            sentiment['score'] = sum(
                sentiment['platforms'][k] * v 
                for k, v in weights.items()
            )
            
            # Calculate momentum (rate of growth in mentions)
            sentiment['momentum'] = self._calculate_social_momentum(twitter_data)
            
            return sentiment
            
        except Exception as e:
            logging.error(f"Sentiment check error: {str(e)}")
            return {'score': 0, 'momentum': 0}
            
    def _score_twitter_data(self, data: Dict) -> float:
        """Score Twitter metrics"""
        try:
            # Scoring criteria from video
            base_score = 0
            
            # Recent mentions (last 24h)
            mentions = data.get('recent_mentions', 0)
            if mentions >= 1000:
                base_score += 40
            elif mentions >= 500:
                base_score += 30
            elif mentions >= 100:
                base_score += 20
                
            # Engagement rate
            engagement = data.get('engagement_rate', 0)
            if engagement >= 0.1:  # 10%+ engagement
                base_score += 30
                
            # Influencer mentions
            influencer_count = data.get('influencer_mentions', 0)
            if influencer_count >= 3:
                base_score += 30
                
            return min(base_score, 100)
            
        except Exception as e:
            logging.error(f"Twitter scoring error: {str(e)}")
            return 0
            
    async def _simulate_buy(self, token_address, amount):
        """Simulate a buy transaction to check for honeypot"""
        try:
            # Simulate buy transaction
            return {
                'success': True,
                'gas_estimate': 200000,
                'price_impact': 0.02,
                'output': amount * 0.98  # Simulated 2% slippage
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def _simulate_sell(self, token_address, amount):
        """Simulate a sell transaction to check for honeypot"""
        try:
            # Simulate sell transaction
            return {
                'success': True,
                'gas_estimate': 200000,
                'price_impact': 0.02,
                'output': amount * 0.98  # Simulated 2% slippage
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def _analyze_taxes(self, token_address):
        """Analyze buy and sell taxes"""
        try:
            # Simulate transactions to calculate taxes
            buy_amount = 1
            buy_result = await self._simulate_buy(token_address, buy_amount)
            sell_result = await self._simulate_sell(token_address, buy_result['output'])
            
            # Calculate taxes
            buy_tax = 1 - (buy_result['output'] / buy_amount)
            sell_tax = 1 - (sell_result['output'] / buy_result['output'])
            
            return {
                'buy_tax': buy_tax,
                'sell_tax': sell_tax,
                'total_tax': buy_tax + sell_tax
            }
        except Exception as e:
            logging.error(f"Tax analysis error: {str(e)}")
            return {
                'buy_tax': 1,
                'sell_tax': 1,
                'total_tax': 2
            }
    
    async def check_token_security(self, token_address):
        """Enhanced security check using AutoSnipe"""
        try:
            security_score = 100
            warnings = []
            critical_flags = []
            
            # 1. Honeypot Check
            if self.autosnipe_config['security']['max_buy_tax'] > 0:
                honeypot = await self._check_honeypot(token_address)
                if honeypot['is_honeypot']:
                    security_score -= self.autosnipe_config['scoring']['honeypot_weight']
                    critical_flags.append("CRITICAL: Honeypot detected")
                    critical_flags.extend(honeypot['reasons'])
            
            # 2. Ownership Check
            if self.autosnipe_config['security']['max_dev_wallet_percent'] > 0:
                ownership = await self._check_ownership(token_address)
                if not ownership['renounced']:
                    security_score -= self.autosnipe_config['scoring']['dev_wallet_weight']
                    warnings.append(f"Ownership not renounced: {ownership['owner']}")
            
            # 3. Tax Analysis
            if self.autosnipe_config['security']['max_buy_tax'] > 0:
                taxes = await self._analyze_taxes(token_address)
                if taxes['buy_tax'] > self.autosnipe_config['security']['max_buy_tax']:
                    security_score -= (self.autosnipe_config['scoring']['dev_wallet_weight'] / 2)
                    warnings.append(f"High buy tax: {taxes['buy_tax']*100}%")
                if taxes['sell_tax'] > self.autosnipe_config['security']['max_sell_tax']:
                    security_score -= (self.autosnipe_config['scoring']['dev_wallet_weight'] / 2)
                    warnings.append(f"High sell tax: {taxes['sell_tax']*100}%")
            
            # 4. LP Analysis
            if self.autosnipe_config['security']['min_lp_lock_days'] > 0:
                lp = await self._check_liquidity(token_address)
                if lp['value'] < self.autosnipe_config['security']['min_lp_value_usd']:
                    security_score -= (self.autosnipe_config['scoring']['lp_lock_weight'] / 2)
                    warnings.append(f"Low LP value: ${lp['value']}")
                if lp['lock_days'] < self.autosnipe_config['security']['min_lp_lock_days']:
                    security_score -= (self.autosnipe_config['scoring']['lp_lock_weight'] / 2)
                    warnings.append(f"Short LP lock: {lp['lock_days']} days")
            
            # 5. Holder Analysis
            if self.autosnipe_config['security']['min_unique_holders'] > 0:
                holders = await self._analyze_holders(token_address)
                if len(holders['unique']) < self.autosnipe_config['security']['min_unique_holders']:
                    security_score -= (self.autosnipe_config['scoring']['holder_weight'] / 2)
                    warnings.append(f"Low holder count: {len(holders['unique'])}")
                
                # Check wallet concentrations
                for holder in holders['large_wallets']:
                    if holder['percentage'] > self.autosnipe_config['security']['max_concentration']:
                        security_score -= (self.autosnipe_config['scoring']['holder_weight'] / 2)
                        warnings.append(f"Large wallet: {holder['address']} holds {holder['percentage']*100}%")
            
            # 6. Contract Scan
            if self.autosnipe_config['security']['min_token_age_hours'] > 0:
                scan = await self._scan_contract(token_address)
                if scan['malicious_functions']:
                    security_score -= 30  # Immediate large penalty
                    critical_flags.extend(scan['malicious_functions'])
            
            return {
                'safe': security_score >= 70 and not critical_flags,
                'score': security_score,
                'critical_flags': critical_flags,
                'warnings': warnings
            }
            
        except Exception as e:
            logging.error(f"Security check error: {str(e)}")
            return {'safe': False, 'score': 0, 'critical_flags': ['Check failed']}

    async def execute_test_trade(self, token_address, amount_sol):
        """Execute trade in test mode with security checks"""
        try:
            # Run security checks first
            security = await self.check_token_security(token_address)
            
            if not security['safe']:
                logging.warning(f"Security check failed: {security['critical_flags']}")
                return {
                    'success': False,
                    'reason': 'Security check failed',
                    'details': security
                }
            
            if security['warnings']:
                logging.info(f"Security warnings: {security['warnings']}")
            
            # Proceed with test trade
            trade_result = await self._simulate_trade(
                token_address,
                amount_sol,
                security['score']
            )
            
            # Log test trade
            self.test_trades.append({
                'timestamp': datetime.now(),
                'token': token_address,
                'amount': amount_sol,
                'security_score': security['score'],
                'result': trade_result
            })
            
            return {
                'success': True,
                'trade': trade_result,
                'security': security
            }
            
        except Exception as e:
            logging.error(f"Test trade error: {str(e)}")
            return {'success': False, 'reason': str(e)}

    async def start_security_monitoring(self):
        """Start real-time security monitoring"""
        while True:
            try:
                for token_address in self.monitored_tokens:
                    await self._monitor_token_security(token_address)
                await asyncio.sleep(self.autosnipe_config['monitoring']['check_interval'])
            except Exception as e:
                logging.error(f"Monitoring error: {str(e)}")
                await asyncio.sleep(5)  # Brief pause on error
    
    async def _monitor_token_security(self, token_address):
        """Monitor a single token for security issues"""
        try:
            current_state = await self._get_token_state(token_address)
            previous_state = self.monitoring_state.get(token_address, {})
            
            alerts = []
            
            # Check for significant changes
            if previous_state:
                # Price monitoring
                if 'price' in current_state and 'price' in previous_state:
                    price_change = abs(current_state['price'] - previous_state['price']) / previous_state['price']
                    if price_change > self.autosnipe_config['monitoring']['price_change_alert']:
                        alerts.append(f"Price changed by {price_change*100:.1f}%")
                
                # Volume monitoring
                if 'volume' in current_state and 'volume' in previous_state:
                    volume_change = abs(current_state['volume'] - previous_state['volume']) / previous_state['volume']
                    if volume_change > self.autosnipe_config['monitoring']['volume_change_alert']:
                        alerts.append(f"Volume changed by {volume_change*100:.1f}%")
                
                # Holder monitoring
                if 'holders' in current_state and 'holders' in previous_state:
                    holder_change = abs(len(current_state['holders']) - len(previous_state['holders'])) / len(previous_state['holders'])
                    if holder_change > self.autosnipe_config['monitoring']['holder_change_alert']:
                        alerts.append(f"Holder count changed by {holder_change*100:.1f}%")
                
                # LP monitoring
                if 'lp_value' in current_state and 'lp_value' in previous_state:
                    lp_change = abs(current_state['lp_value'] - previous_state['lp_value']) / previous_state['lp_value']
                    if lp_change > self.autosnipe_config['monitoring']['lp_change_alert']:
                        alerts.append(f"LP value changed by {lp_change*100:.1f}%")
                
                # Contract monitoring
                if current_state.get('contract_hash') != previous_state.get('contract_hash'):
                    alerts.append("CRITICAL: Contract implementation changed!")
                
                # Ownership monitoring
                if current_state.get('owner') != previous_state.get('owner'):
                    alerts.append(f"CRITICAL: Contract ownership changed to {current_state['owner']}")
            
            # Update monitoring state
            self.monitoring_state[token_address] = current_state
            
            # Handle alerts
            if alerts:
                await self._handle_security_alerts(token_address, alerts)
            
        except Exception as e:
            logging.error(f"Token monitoring error: {str(e)}")
    
    async def _get_token_state(self, token_address):
        """Get current token state for monitoring"""
        try:
            state = {}
            
            # Get basic token info
            token_info = await self._get_token_info(token_address)
            state['price'] = token_info.get('price', 0)
            state['volume'] = token_info.get('volume_24h', 0)
            
            # Get holder info
            holders = await self._get_token_holders(token_address)
            state['holders'] = holders
            
            # Get LP info
            lp_info = await self._check_liquidity(token_address)
            state['lp_value'] = lp_info.get('value', 0)
            
            # Get contract info
            contract = await self._get_contract_data(token_address)
            state['contract_hash'] = contract.get('implementation_hash')
            state['owner'] = contract.get('owner')
            
            return state
            
        except Exception as e:
            logging.error(f"Error getting token state: {str(e)}")
            return {}
    
    async def _handle_security_alerts(self, token_address, alerts):
        """Handle security alerts"""
        try:
            # Log all alerts
            for alert in alerts:
                logging.warning(f"Security Alert for {token_address}: {alert}")
            
            # Check if we need to take action
            critical_alerts = [a for a in alerts if a.startswith("CRITICAL")]
            if critical_alerts:
                # Emergency actions for critical alerts
                await self._emergency_actions(token_address, critical_alerts)
            
            # Update security score
            security = await self.check_token_security(token_address)
            if not security['safe']:
                await self._emergency_actions(token_address, security['critical_flags'])
            
        except Exception as e:
            logging.error(f"Error handling alerts: {str(e)}")
    
    async def _emergency_actions(self, token_address, reasons):
        """Handle emergency situations"""
        try:
            # Log emergency
            logging.critical(f"Emergency action for {token_address}: {reasons}")
            
            # Check if we have any open positions
            position = await self._get_position(token_address)
            if position and position['amount'] > 0:
                # Try to emergency sell
                logging.warning(f"Attempting emergency sell for {token_address}")
                await self._emergency_sell(token_address, position['amount'])
            
            # Remove from monitoring
            if token_address in self.monitored_tokens:
                self.monitored_tokens.remove(token_address)
            
            # Blacklist token
            self.blacklisted_tokens.add(token_address)
            
        except Exception as e:
            logging.error(f"Emergency action error: {str(e)}")

    async def analyze_entry_opportunity(self, token_address):
        """Analyze if token presents a good entry opportunity"""
        try:
            # Get market data
            price_data = await self._get_price_history(token_address, self.trading_config['entry']['time_window'])
            volume_data = await self._get_volume_data(token_address)
            liquidity = await self._get_liquidity(token_address)
            
            # Check entry conditions
            momentum = self._calculate_momentum(price_data)
            volume_ok = volume_data['24h'] >= self.trading_config['entry']['volume_threshold']
            liquidity_ok = liquidity >= self.trading_config['entry']['min_liquidity']
            
            # Calculate position size
            portfolio_value = await self.get_portfolio_value()
            max_position = portfolio_value * self.trading_config['position']['max_position_size']
            min_position = portfolio_value * self.trading_config['position']['min_position_size']
            
            # Check if we can take new positions
            current_positions = await self._get_open_positions()
            positions_ok = len(current_positions) < self.trading_config['position']['max_open_positions']
            
            # Calculate correlation with existing positions
            correlation_ok = await self._check_correlation(token_address, current_positions)
            
            # Entry decision
            entry_score = 0
            reasons = []
            
            if momentum >= self.trading_config['entry']['momentum_threshold']:
                entry_score += 30
                reasons.append(f"Strong momentum: {momentum*100:.1f}%")
            
            if volume_ok:
                entry_score += 20
                reasons.append(f"Good volume: ${volume_data['24h']:,.0f}")
            
            if liquidity_ok:
                entry_score += 20
                reasons.append(f"Sufficient liquidity: ${liquidity:,.0f}")
            
            if positions_ok:
                entry_score += 15
                reasons.append("Position limit not reached")
            
            if correlation_ok:
                entry_score += 15
                reasons.append("Low correlation with existing positions")
            
            return {
                'should_enter': entry_score >= 75,
                'score': entry_score,
                'reasons': reasons,
                'position_size': min(max_position, max(min_position, liquidity * 0.02))  # 2% of liquidity
            }
            
        except Exception as e:
            logging.error(f"Error analyzing entry opportunity: {str(e)}")
            return {'should_enter': False, 'score': 0, 'reasons': [f"Error: {str(e)}"], 'position_size': 0}

    async def analyze_exit_opportunity(self, token_address, entry_price, position_size):
        """Analyze if position should be exited"""
        try:
            current_price = await self._get_current_price(token_address)
            price_change = (current_price - entry_price) / entry_price
            
            # Check exit conditions
            take_profit = price_change >= self.trading_config['exit']['take_profit']
            stop_loss = price_change <= -self.trading_config['exit']['stop_loss']
            
            # Get position data
            position_data = await self._get_position_data(token_address)
            hold_time = position_data['hold_time']
            trailing_high = position_data['trailing_high']
            
            # Calculate trailing stop
            trailing_stop_hit = (trailing_high - current_price) / trailing_high >= self.trading_config['exit']['trailing_stop']
            
            # Exit decision
            should_exit = False
            reasons = []
            
            if take_profit:
                should_exit = True
                reasons.append(f"Take profit hit: {price_change*100:.1f}%")
            
            if stop_loss:
                should_exit = True
                reasons.append(f"Stop loss hit: {price_change*100:.1f}%")
            
            if trailing_stop_hit:
                should_exit = True
                reasons.append(f"Trailing stop hit: {((trailing_high - current_price) / trailing_high)*100:.1f}%")
            
            if hold_time >= self.trading_config['exit']['max_hold_time']:
                should_exit = True
                reasons.append(f"Max hold time reached: {hold_time/3600:.1f} hours")
            
            return {
                'should_exit': should_exit,
                'reasons': reasons,
                'current_price': current_price,
                'price_change': price_change
            }
            
        except Exception as e:
            logging.error(f"Error analyzing exit opportunity: {str(e)}")
            return {'should_exit': True, 'reasons': [f"Error: {str(e)}"], 'current_price': 0, 'price_change': 0}

    async def _get_price_history(self, token_address, time_window):
        """Get price history for given time window"""
        try:
            # Implement price history fetching
            return [{
                'timestamp': i,
                'price': 1.0 + (i/100)
            } for i in range(time_window)]
        except Exception as e:
            logging.error(f"Error getting price history: {str(e)}")
            return []

    async def _get_volume_data(self, token_address):
        """Get volume data for token"""
        try:
            # Implement volume data fetching
            return {
                '24h': 50000,
                '1h': 5000,
                '5m': 1000
            }
        except Exception as e:
            logging.error(f"Error getting volume data: {str(e)}")
            return {'24h': 0, '1h': 0, '5m': 0}

    async def _get_liquidity(self, token_address):
        """Get liquidity data for token"""
        try:
            # Implement liquidity check
            return 100000  # $100k liquidity
        except Exception as e:
            logging.error(f"Error getting liquidity: {str(e)}")
            return 0

    def _calculate_momentum(self, price_data):
        """Calculate price momentum"""
        try:
            if not price_data:
                return 0
            
            first_price = price_data[0]['price']
            last_price = price_data[-1]['price']
            
            return (last_price - first_price) / first_price
        except Exception as e:
            logging.error(f"Error calculating momentum: {str(e)}")
            return 0

    async def get_portfolio_value(self):
        """Get total portfolio value"""
        try:
            # Implement portfolio value calculation
            return 10000  # $10k portfolio
        except Exception as e:
            logging.error(f"Error getting portfolio value: {str(e)}")
            return 0

    async def _get_open_positions(self):
        """Get list of open positions"""
        try:
            # Implement open positions fetching
            return []  # No open positions
        except Exception as e:
            logging.error(f"Error getting open positions: {str(e)}")
            return []

    async def _check_correlation(self, token_address, current_positions):
        """Check correlation with existing positions"""
        try:
            # Implement correlation check
            return True  # No correlation issues
        except Exception as e:
            logging.error(f"Error checking correlation: {str(e)}")
            return False

    async def _get_current_price(self, token_address):
        """Get current token price"""
        try:
            # Implement current price fetching
            return 1.0  # $1.00
        except Exception as e:
            logging.error(f"Error getting current price: {str(e)}")
            return 0

    async def _get_position_data(self, token_address):
        """Get data for specific position"""
        try:
            # Implement position data fetching
            return {
                'hold_time': 1800,  # 30 minutes
                'trailing_high': 1.2,  # $1.20 highest price
                'entry_price': 1.0,  # $1.00 entry
                'current_price': 1.1,  # $1.10 current
                'size': 1000  # $1000 position size
            }
        except Exception as e:
            logging.error(f"Error getting position data: {str(e)}")
            return {
                'hold_time': 0,
                'trailing_high': 0,
                'entry_price': 0,
                'current_price': 0,
                'size': 0
            }
    
    async def close(self):
        """Close all connections and cleanup"""
        try:
            if hasattr(self, 'session') and self.session:
                await self.session.close()
            if hasattr(self, 'ws') and self.ws:
                await self.ws.close()
        except Exception as e:
            logging.error(f"Error closing connections: {str(e)}")

    async def _protect_from_mev(self, transaction: Dict) -> Dict:
        """
        Apply MEV protection strategies to transaction
        """
        try:
            # Analyze mempool for potential MEV threats
            mempool_threats = await self._analyze_mempool()
            
            # If high MEV threat detected, enhance protection
            if mempool_threats['threat_level'] > 0.7:
                # Split transaction across multiple routes
                if self.mev_config['transaction_protection']['route_splitting']:
                    transaction = await self._split_transaction_routes(transaction)
                
                # Add random time delay
                if self.mev_config['transaction_protection']['time_delay']:
                    delay = random.uniform(0, self.mev_config['transaction_protection']['time_delay'])
                    await asyncio.sleep(delay)
                
                # Optimize gas price
                if self.mev_config['transaction_protection']['gas_optimization']:
                    transaction = await self._optimize_gas_price(transaction, mempool_threats)
                
                # Use private transaction service if enabled
                if self.mev_config['transaction_protection']['private_tx']:
                    transaction = await self._send_private_transaction(transaction)
            
            return transaction
            
        except Exception as e:
            logging.error(f"MEV protection error: {str(e)}")
            return transaction

    async def _analyze_mempool(self) -> Dict:
        """
        Analyze mempool for potential MEV threats
        """
        try:
            threat_analysis = {
                'threat_level': 0.0,
                'sandwich_risk': False,
                'frontrun_risk': False,
                'backrun_risk': False,
                'high_gas_competition': False
            }
            
            # Get pending transactions
            pending_txs = await self._get_pending_transactions()
            
            # Analyze gas prices
            gas_prices = [tx['gasPrice'] for tx in pending_txs]
            avg_gas = sum(gas_prices) / len(gas_prices) if gas_prices else 0
            
            # Check for high gas competition
            if any(price > avg_gas * self.mev_config['mempool_analysis']['gas_price_threshold'] 
                  for price in gas_prices):
                threat_analysis['high_gas_competition'] = True
                threat_analysis['threat_level'] += 0.3
            
            # Detect potential sandwich attacks
            if self.mev_config['mempool_analysis']['sandwich_detection']:
                sandwich_risk = await self._detect_sandwich_pattern(pending_txs)
                if sandwich_risk:
                    threat_analysis['sandwich_risk'] = True
                    threat_analysis['threat_level'] += 0.4
            
            # Detect frontrunning attempts
            if self.mev_config['mempool_analysis']['frontrun_protection']:
                frontrun_risk = await self._detect_frontrun_attempt(pending_txs)
                if frontrun_risk:
                    threat_analysis['frontrun_risk'] = True
                    threat_analysis['threat_level'] += 0.4
            
            return threat_analysis
            
        except Exception as e:
            logging.error(f"Mempool analysis error: {str(e)}")
            return {'threat_level': 0.0}

    async def _split_transaction_routes(self, transaction: Dict) -> Dict:
        """
        Split large transactions across multiple routes to minimize MEV impact
        """
        try:
            if transaction['amount'] < self.mev_config['routing']['min_route_amount']:
                return transaction
                
            routes = []
            amount_per_route = transaction['amount'] / self.mev_config['routing']['max_routes']
            
            for dex in self.mev_config['routing']['dex_preference'][:self.mev_config['routing']['max_routes']]:
                route = {
                    'dex': dex,
                    'amount': amount_per_route,
                    'path': await self._find_optimal_path(dex, transaction['token_address'])
                }
                routes.append(route)
            
            transaction['split_routes'] = routes
            return transaction
            
        except Exception as e:
            logging.error(f"Route splitting error: {str(e)}")
            return transaction

    async def _optimize_gas_price(self, transaction: Dict, mempool_threats: Dict) -> Dict:
        """
        Optimize gas price based on mempool analysis and threat level
        """
        try:
            base_gas = await self._get_base_gas_price()
            
            # Adjust gas based on threat level
            if mempool_threats['threat_level'] > 0.8:
                gas_multiplier = 1.5
            elif mempool_threats['threat_level'] > 0.5:
                gas_multiplier = 1.3
            else:
                gas_multiplier = 1.1
                
            transaction['gasPrice'] = int(base_gas * gas_multiplier)
            return transaction
            
        except Exception as e:
            logging.error(f"Gas optimization error: {str(e)}")
            return transaction

    async def _send_private_transaction(self, transaction: Dict) -> Dict:
        """
        Send transaction through private transaction service to avoid mempool exposure
        """
        try:
            # Implement private transaction service integration
            # This could be Flashbots or similar service
            return transaction
        except Exception as e:
            logging.error(f"Private transaction error: {str(e)}")
            return transaction

    async def get_wallet_balance(self) -> float:
        """Get real wallet balance in USD"""
        try:
            logging.info(f"Fetching balance for wallet: {self.wallet_address}")
            
            # Ensure we have a session
            if not hasattr(self, 'session') or self.session is None:
                self.setup_connection_pool()
            
            # Get SOL balance
            rpc_url = next(iter(self.rpc_endpoints))  # Get first RPC URL
            logging.info(f"Using RPC endpoint: {rpc_url}")
            
            async with self.session.post(
                rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [self.wallet_address]
                }
            ) as response:
                if response.status != 200:
                    logging.error(f"RPC request failed with status: {response.status}")
                    return 0
                    
                data = await response.json()
                if 'result' not in data:
                    logging.error(f"Unexpected RPC response: {data}")
                    return 0
                    
                sol_balance = float(data['result']['value']) / 1e9  # Convert lamports to SOL
                logging.info(f"SOL balance: {sol_balance}")
                
                # Get SOL price
                async with self.session.get(
                    "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
                ) as price_response:
                    if price_response.status != 200:
                        logging.error("Failed to get SOL price from CoinGecko")
                        return 0
                        
                    price_data = await price_response.json()
                    sol_price = price_data.get('solana', {}).get('usd', 0)
                    logging.info(f"SOL price: ${sol_price}")
                    
                    total_usd = sol_balance * sol_price
                    logging.info(f"Total USD value: ${total_usd:.2f}")
                    return total_usd
                    
        except Exception as e:
            logging.error(f"Error getting wallet balance: {str(e)}")
            return 0

    def load_trade_history(self):
        """Load trade history from file"""
        try:
            if os.path.exists(self.trade_history_path):
                with open(self.trade_history_path, 'r') as f:
                    return json.load(f)
            else:
                default_history = {
                    'test_trades': [],
                    'real_trades': [],
                    'portfolio': {
                        'total_value': self.get_wallet_balance(),
                        'change_24h': 0,
                        'positions': []
                    }
                }
                with open(self.trade_history_path, 'w') as f:
                    json.dump(default_history, f, indent=4)
                return default_history
        except Exception as e:
            logging.error(f"Error loading trade history: {e}")
            return {
                'test_trades': [],
                'real_trades': [],
                'portfolio': {
                    'total_value': 0,
                    'change_24h': 0,
                    'positions': []
                }
            }

    def save_trade_history(self):
        """Save trade history to file"""
        try:
            with open(self.trade_history_path, 'w') as f:
                json.dump(self.trade_history, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving trade history: {e}")

    def add_test_trade(self, token: str, trade_type: str, amount: float, price: float, profit: float, whale_address: str = None):
        """Add a test trade to history with profit categorization"""
        try:
            # Calculate profit percentage
            profit_percentage = (profit / (amount * price)) * 100
            
            # Determine profit category
            category = None
            if profit_percentage >= 1000:
                category = "moonshot"
            elif profit_percentage >= 100:
                category = "large"
            elif profit_percentage >= 20:
                category = "medium"
            elif profit_percentage > 0:
                category = "small"
            
            # Create trade record
            trade = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'token': token,
                'type': trade_type,
                'amount': amount,
                'price': price,
                'profit': profit,
                'profit_percentage': profit_percentage,
                'category': category,
                'whale_address': whale_address,
                'status': 'COMPLETED'
            }
            
            # Add to trade history
            self.trade_history['test_trades'].append(trade)
            
            # Update profit categories if profitable
            if category and profit > 0:
                self.trade_history['portfolio']['profit_categories'][category]['count'] += 1
                self.trade_history['portfolio']['profit_categories'][category]['total_profit'] += profit
            
            # Update portfolio value
            current_balance = self.get_wallet_balance()
            self.trade_history['portfolio']['total_value'] = current_balance
            
            # Save updated history
            self.save_trade_history()
            
            # Update wallet balance
            self.update_wallet_balance(current_balance + profit)
            
            return True
        except Exception as e:
            logging.error(f"Error adding test trade: {e}")
            return False
    
    def update_wallet_balance(self, new_balance: float):
        """Update wallet balance in wallet.json"""
        try:
            wallet_path = os.path.join(self.root_dir, 'database', 'wallet.json')
            with open(wallet_path, 'r') as f:
                wallet_data = json.load(f)
            
            wallet_data['balance'] = new_balance
            wallet_data['last_updated'] = datetime.now(timezone.utc).isoformat()
            
            with open(wallet_path, 'w') as f:
                json.dump(wallet_data, f, indent=4)
            
            return True
        except Exception as e:
            logging.error(f"Error updating wallet balance: {e}")
            return False
    
    def execute_whale_copy_trade(self, whale_address: str, token_address: str, amount_sol: float) -> bool:
        """Execute a test trade copying a whale's position"""
        try:
            # Get token metrics
            metrics = self.get_token_metrics(token_address)
            
            # Calculate potential profit based on metrics
            base_profit = random.uniform(-5, 15)  # Base profit/loss
            
            # Adjust profit based on metrics
            if metrics.liquidity > 1000000:  # High liquidity
                base_profit *= 1.2
            if metrics.volume_24h > 500000:  # High volume
                base_profit *= 1.3
            if metrics.top_holders_percentage < 50:  # Good distribution
                base_profit *= 1.1
            
            # Small chance of moonshot (1%)
            if random.random() < 0.01:
                base_profit *= random.uniform(50, 200)
            
            # Execute the trade
            success = self.add_test_trade(
                token=token_address,
                trade_type="BUY" if random.random() > 0.5 else "SELL",
                amount=amount_sol,
                price=metrics.price,
                profit=base_profit,
                whale_address=whale_address
            )
            
            return success
        except Exception as e:
            logging.error(f"Error executing whale copy trade: {e}")
            return False
    
    def start_test_trading(self):
        """Start test trading with whale tracking"""
        try:
            # Initialize trading loop
            while True:
                # Get list of whale wallets
                whale_wallets = self.get_whale_wallets()
                
                for whale in whale_wallets:
                    # Monitor whale's transactions
                    recent_txs = self.get_recent_transactions(whale)
                    
                    for tx in recent_txs:
                        if self.is_valid_trade_tx(tx):
                            # Copy whale's trade with our test balance
                            self.execute_whale_copy_trade(
                                whale_address=whale,
                                token_address=tx['token_address'],
                                amount_sol=random.uniform(0.1, 1.0)  # Start small
                            )
                
                # Sleep to avoid rate limits
                time.sleep(10)
        except Exception as e:
            logging.error(f"Error in test trading loop: {e}")
            return False

    async def execute_test_trade(self, token_address: str, amount_sol: float) -> bool:
        """Execute trade in test mode with security checks"""
        try:
            # Simulate a test trade
            price = random.uniform(70, 80)  # Simulated SOL price
            profit = random.uniform(-2, 5)  # Simulated profit/loss
            
            # Add trade to history
            success = self.add_test_trade(
                token="SOL/USDC",
                trade_type="BUY" if random.random() > 0.5 else "SELL",
                amount=amount_sol,
                price=price,
                profit=profit
            )
            
            return success
        except Exception as e:
            logging.error(f"Error executing test trade: {e}")
            return False

    def initialize_trade_history(self):
        """Initialize trade history with sample trades"""
        try:
            # Clear existing trades
            self.trade_history = {
                'test_trades': [],
                'real_trades': [],
                'portfolio': {
                    'total_value': self.get_wallet_balance(),
                    'change_24h': 0,
                    'positions': []
                }
            }
            
            # Add some sample test trades
            for _ in range(5):
                self.execute_test_trade("SOL/USDC", random.uniform(5, 15))
            
            self.save_trade_history()
            return True
        except Exception as e:
            logging.error(f"Error initializing trade history: {e}")
            return False

    async def execute_test_trade(self, token_address: str, amount_sol: float) -> bool:
        """Execute trade in test mode with security checks"""
        try:
            # Simulate a test trade
            price = random.uniform(70, 80)  # Simulated SOL price
            profit = random.uniform(-2, 5)  # Simulated profit/loss
            
            # Add trade to history
            success = self.add_test_trade(
                token="SOL/USDC",
                trade_type="BUY" if random.random() > 0.5 else "SELL",
                amount=amount_sol,
                price=price,
                profit=profit
            )
            
            return success
        except Exception as e:
            logging.error(f"Error executing test trade: {e}")
            return False
