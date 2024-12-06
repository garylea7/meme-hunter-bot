from web3 import Web3
import json
import logging
from decimal import Decimal
from typing import Dict, Tuple
import asyncio
from eth_typing import Address
import os
from dotenv import load_dotenv

class YieldFarmingStrategy:
    def __init__(self):
        load_dotenv('.env.private')
        
        # Connect to Base network (Ethereum L2)
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('BASE_RPC_URL')))
        
        # Contract addresses on Base
        self.moonwell_address = os.getenv('MOONWELL_ADDRESS')
        self.usdc_address = os.getenv('USDC_ADDRESS')
        self.well_token_address = os.getenv('WELL_TOKEN_ADDRESS')
        self.balancer_vault = os.getenv('BALANCER_VAULT_BASE')
        
        # Load contract ABIs
        self.moonwell_contract = self.load_contract('Moonwell.json', self.moonwell_address)
        self.usdc_contract = self.load_contract('USDC.json', self.usdc_address)
        self.balancer_contract = self.load_contract('BalancerVault.json', self.balancer_vault)
        
        # Strategy parameters
        self.leverage_ratio = 3  # 3x leverage as shown in video
        self.min_collateral_ratio = 1.5  # Safety buffer
        self.auto_compound_interval = 24  # Hours
        self.flash_loan_fee = 0.0001  # Balancer's 0.01% fee
        
    def load_contract(self, abi_file: str, address: str):
        """Load contract from ABI file"""
        try:
            with open(f'artifacts/{abi_file}') as f:
                contract_json = json.load(f)
            return self.w3.eth.contract(
                address=self.w3.to_checksum_address(address),
                abi=contract_json['abi']
            )
        except Exception as e:
            logging.error(f"Error loading contract: {str(e)}")
            return None
    
    async def calculate_potential_yield(self, deposit_amount: float) -> Dict:
        """Calculate potential yield with 3x leverage"""
        try:
            # Get current APYs
            base_apy = await self.get_moonwell_apy()
            well_token_apy = await self.get_well_token_apy()
            total_base_apy = base_apy + well_token_apy
            
            # Calculate leveraged amounts (3x as shown in video)
            flash_loan_amount = deposit_amount * 2  # For 3x total
            total_deposit = deposit_amount * 3
            
            # Calculate yearly yields
            base_yearly_yield = deposit_amount * (total_base_apy / 100)
            leveraged_yearly_yield = total_deposit * (total_base_apy / 100)
            
            # Calculate costs
            flash_loan_fee = self.flash_loan_fee * flash_loan_amount
            gas_costs = await self.estimate_gas_costs()
            
            # Net yields
            net_leveraged_yield = leveraged_yearly_yield - flash_loan_fee - gas_costs
            
            return {
                'deposit_amount': deposit_amount,
                'flash_loan_amount': flash_loan_amount,
                'total_deposit': total_deposit,
                'base_apy': total_base_apy,
                'base_yearly_yield': base_yearly_yield,
                'leveraged_yearly_yield': leveraged_yearly_yield,
                'net_leveraged_yield': net_leveraged_yield,
                'flash_loan_fee': flash_loan_fee,
                'gas_costs': gas_costs,
                'effective_apy': (net_leveraged_yield / deposit_amount) * 100
            }
            
        except Exception as e:
            logging.error(f"Error calculating yield: {str(e)}")
            return None
    
    async def execute_leveraged_deposit(
        self,
        deposit_amount: float,
        flash_loan_amount: float,
        wallet_address: str
    ) -> bool:
        """Execute leveraged deposit strategy exactly as shown in video"""
        try:
            # 1. Approve USDC spending
            await self.check_and_approve_usdc(deposit_amount, wallet_address)
            
            # 2. Request flash loan from Balancer
            flash_loan_params = self.encode_flash_loan_params(
                deposit_amount,
                flash_loan_amount,
                'DEPOSIT'
            )
            
            # 3. Execute the flash loan transaction which will:
            # - Borrow flash loan
            # - Deposit total amount to Moonwell
            # - Borrow USDC from Moonwell
            # - Repay flash loan
            tx_hash = await self.balancer_contract.functions.flashLoan(
                self.flash_loan_contract.address,
                [self.usdc_address],
                [Web3.to_wei(flash_loan_amount, 'ether')],
                flash_loan_params
            ).transact({'from': wallet_address})
            
            # Wait for confirmation
            receipt = await self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                logging.info(f"Successfully executed 3x leveraged deposit of {deposit_amount} USDC")
                return True
            else:
                logging.error("Leveraged deposit failed")
                return False
                
        except Exception as e:
            logging.error(f"Error executing leveraged deposit: {str(e)}")
            return False
    
    async def execute_leveraged_withdrawal(
        self,
        withdraw_amount: float,
        wallet_address: str
    ) -> bool:
        """Execute leveraged withdrawal strategy"""
        try:
            # Calculate flash loan needed to unwind position
            flash_loan_amount = withdraw_amount * (self.leverage_ratio - 1)
            
            # Prepare withdrawal data
            withdrawal_data = self.prepare_withdrawal_data(
                withdraw_amount,
                flash_loan_amount
            )
            
            # Execute flash loan for withdrawal
            tx_hash = await self.execute_flash_loan(withdrawal_data)
            
            # Wait for confirmation
            receipt = await self.wait_for_transaction(tx_hash)
            
            return receipt['status'] == 1
            
        except Exception as e:
            logging.error(f"Error executing leveraged withdrawal: {str(e)}")
            return False
    
    async def auto_compound(self, wallet_address: str) -> bool:
        """Reinvest accumulated rewards using flash loan leverage"""
        try:
            # 1. Get accumulated rewards
            well_rewards = await self.get_well_token_rewards(wallet_address)
            usdc_rewards = await self.get_usdc_rewards(wallet_address)
            
            # Skip if no rewards to compound
            if well_rewards == 0 and usdc_rewards == 0:
                logging.info("No rewards to compound")
                return False
            
            # 2. Convert WELL tokens to USDC if needed
            total_usdc = usdc_rewards
            if well_rewards > 0:
                await self.claim_well_rewards(wallet_address)
                well_price = await self.get_well_usdc_price()
                total_usdc += well_rewards * well_price
            
            # 3. Calculate flash loan amount for 3x leverage
            # Using 70% as shown in video for safety
            flash_loan_amount = total_usdc * 2  # 2x for 3x total leverage
            
            # 4. Execute leveraged deposit with flash loan
            # This is atomic - either succeeds completely or reverts
            success = await self.execute_leveraged_deposit(
                deposit_amount=total_usdc,
                flash_loan_amount=flash_loan_amount,
                wallet_address=wallet_address
            )
            
            if success:
                logging.info(
                    f"Successfully reinvested ${total_usdc:.2f} "
                    f"with ${flash_loan_amount:.2f} flash loan"
                )
            else:
                logging.error("Flash loan leverage failed - transaction reverted")
            
            return success
            
        except Exception as e:
            logging.error(f"Error in auto-compound: {str(e)}")
            return False

    async def execute_leveraged_deposit(
        self,
        deposit_amount: float,
        flash_loan_amount: float,
        wallet_address: str
    ) -> bool:
        """Execute leveraged deposit using flash loan - atomic transaction"""
        try:
            # 1. Verify we have enough USDC
            balance = await self.usdc_contract.functions.balanceOf(wallet_address).call()
            if balance < Web3.to_wei(deposit_amount, 'ether'):
                logging.error(f"Insufficient USDC balance for deposit")
                return False
            
            # 2. Check protocol conditions
            utilization = await self.get_market_utilization()
            if utilization > 90:
                logging.error("Market utilization too high")
                return False
                
            # 3. Prepare flash loan parameters
            flash_loan_params = self.encode_flash_loan_params(
                deposit_amount,
                flash_loan_amount,
                'DEPOSIT'
            )
            
            # 4. Execute flash loan transaction
            # This is atomic - either succeeds or reverts
            tx_hash = await self.balancer_contract.functions.flashLoan(
                self.flash_loan_contract.address,
                [self.usdc_address],
                [Web3.to_wei(flash_loan_amount, 'ether')],
                flash_loan_params
            ).transact({'from': wallet_address})
            
            # 5. Wait for confirmation
            receipt = await self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt['status'] == 1
            
        except Exception as e:
            logging.error(f"Error executing leveraged deposit: {str(e)}")
            return False

    async def estimate_compound_gas(self) -> int:
        """Estimate gas needed for compounding"""
        try:
            # Base gas for transactions
            claim_gas = 100000
            swap_gas = 150000
            deposit_gas = 250000
            
            return claim_gas + swap_gas + deposit_gas
            
        except Exception as e:
            logging.error(f"Error estimating compound gas: {str(e)}")
            return 500000  # Safe default

    async def convert_gas_to_usd(self, gas_wei: int) -> float:
        """Convert gas cost to USD"""
        try:
            eth_price = await self.get_eth_price()
            return (gas_wei * eth_price) / 1e18
            
        except Exception as e:
            logging.error(f"Error converting gas to USD: {str(e)}")
            return 0
    
    async def monitor_health_factor(self, wallet_address: str) -> float:
        """Monitor account health factor"""
        try:
            health_factor = await self.moonwell_contract.functions.getHealthFactor(
                wallet_address
            ).call()
            
            return float(health_factor) / 1e18
            
        except Exception as e:
            logging.error(f"Error getting health factor: {str(e)}")
            return 0
    
    async def get_moonwell_apy(self) -> float:
        """Get current Moonwell supply APY"""
        try:
            supply_rate = await self.moonwell_contract.functions.supplyRatePerBlock().call()
            blocks_per_year = 2_102_400  # Approximate blocks per year
            return (((1 + (supply_rate / 1e18)) ** blocks_per_year) - 1) * 100
        except Exception as e:
            logging.error(f"Error getting Moonwell APY: {str(e)}")
            return 0
    
    async def get_well_token_apy(self) -> float:
        """Get current WELL token rewards APY"""
        try:
            # This would need actual implementation based on Moonwell's reward distribution
            return 5.0  # Example return
        except Exception as e:
            logging.error(f"Error getting WELL token APY: {str(e)}")
            return 0
    
    def calculate_flash_loan_fee(self, amount: float) -> float:
        """Calculate flash loan fee"""
        # Balancer charges 0.01% flash loan fee
        return amount * 0.0001
    
    async def estimate_gas_costs(self) -> float:
        """Estimate gas costs for transactions"""
        try:
            gas_price = self.w3.eth.gas_price
            estimated_gas = 500000  # Approximate gas used
            eth_price = await self.get_eth_price()
            
            return (gas_price * estimated_gas * eth_price) / 1e18
            
        except Exception as e:
            logging.error(f"Error estimating gas costs: {str(e)}")
            return 0
    
    async def get_eth_price(self) -> float:
        """Get current ETH price"""
        try:
            # Implementation would fetch from price feed
            return 2000.0  # Example price
        except Exception as e:
            logging.error(f"Error getting ETH price: {str(e)}")
            return 0
    
    async def get_well_usdc_price(self) -> float:
        """Get WELL/USDC price"""
        try:
            # Implementation would fetch from DEX or price feed
            return 1.0  # Example price
        except Exception as e:
            logging.error(f"Error getting WELL/USDC price: {str(e)}")
            return 0

    async def calculate_detailed_profits(self, deposit_amount: float) -> Dict:
        """Calculate detailed profit projections with safety margins"""
        try:
            # Get current rates
            base_apy = await self.get_moonwell_apy()
            well_token_apy = await self.get_well_token_apy()
            total_apy = base_apy + well_token_apy
            
            # Get collateral factor (83% as shown in video)
            collateral_factor = await self.moonwell_contract.functions.collateralFactor().call()
            safe_borrow_factor = 0.7  # 70% as shown in video for safety
            
            # Calculate leveraged position
            flash_loan_amount = deposit_amount * (safe_borrow_factor / (1 - safe_borrow_factor))
            total_deposit = deposit_amount + flash_loan_amount
            
            # Calculate yields
            daily_yield = total_deposit * (total_apy / 365 / 100)
            monthly_yield = daily_yield * 30
            yearly_yield = daily_yield * 365
            
            # Calculate costs
            flash_loan_fee = flash_loan_amount * self.flash_loan_fee
            estimated_gas = await self.estimate_gas_costs()
            borrow_rate = await self.moonwell_contract.functions.borrowRatePerBlock().call()
            borrow_cost = flash_loan_amount * (borrow_rate / 1e18) * 2102400  # blocks per year
            
            # Calculate net yields
            net_daily = daily_yield - (borrow_cost / 365) - (flash_loan_fee / 365)
            net_monthly = monthly_yield - (borrow_cost / 12) - flash_loan_fee
            net_yearly = yearly_yield - borrow_cost - (flash_loan_fee * 12)
            
            # Calculate time to double investment
            if net_daily > 0:
                days_to_double = (deposit_amount / net_daily) if net_daily > 0 else float('inf')
            else:
                days_to_double = float('inf')
            
            # Safety metrics
            utilization_rate = await self.get_market_utilization()
            health_factor = await self.calculate_health_factor(total_deposit, flash_loan_amount)
            
            return {
                'initial_deposit': deposit_amount,
                'flash_loan_amount': flash_loan_amount,
                'total_position': total_deposit,
                'leverage_ratio': total_deposit / deposit_amount,
                'collateral_factor': collateral_factor / 1e18,
                'safe_borrow_factor': safe_borrow_factor,
                'yields': {
                    'base_apy': base_apy,
                    'well_token_apy': well_token_apy,
                    'total_apy': total_apy,
                    'daily': daily_yield,
                    'monthly': monthly_yield,
                    'yearly': yearly_yield
                },
                'costs': {
                    'flash_loan_fee': flash_loan_fee,
                    'gas_cost': estimated_gas,
                    'borrow_cost': borrow_cost
                },
                'net_yields': {
                    'daily': net_daily,
                    'monthly': net_monthly,
                    'yearly': net_yearly
                },
                'safety_metrics': {
                    'health_factor': health_factor,
                    'utilization_rate': utilization_rate,
                    'days_to_double': days_to_double
                }
            }
            
        except Exception as e:
            logging.error(f"Error calculating detailed profits: {str(e)}")
            return None

    async def get_market_utilization(self) -> float:
        """Get current market utilization rate"""
        try:
            total_supply = await self.moonwell_contract.functions.getMarketTotalSupply(
                self.usdc_address
            ).call()
            total_borrow = await self.moonwell_contract.functions.getMarketTotalBorrow(
                self.usdc_address
            ).call()
            
            return (total_borrow * 100) / total_supply if total_supply > 0 else 0
            
        except Exception as e:
            logging.error(f"Error getting market utilization: {str(e)}")
            return 0

    async def calculate_health_factor(
        self,
        total_deposit: float,
        borrowed_amount: float
    ) -> float:
        """Calculate position health factor"""
        try:
            collateral_factor = await self.moonwell_contract.functions.collateralFactor().call()
            max_borrow = total_deposit * (collateral_factor / 1e18)
            return (max_borrow / borrowed_amount) if borrowed_amount > 0 else float('inf')
            
        except Exception as e:
            logging.error(f"Error calculating health factor: {str(e)}")
            return 0

    async def check_position_safety(self, wallet_address: str) -> Dict:
        """Comprehensive safety check for yield farming position"""
        try:
            # 1. Check protocol health
            utilization = await self.get_market_utilization()
            supply_rate = await self.moonwell_contract.functions.supplyRatePerBlock().call()
            borrow_rate = await self.moonwell_contract.functions.borrowRatePerBlock().call()
            
            # 2. Check position health
            position = await self.get_position_info(wallet_address)
            health_factor = await self.calculate_health_factor(
                position['total_deposit'],
                position['borrowed_amount']
            )
            
            # 3. Check USDC stability
            usdc_price = await self.get_usdc_price()
            usdc_deviation = abs(1 - usdc_price)  # How far from $1
            
            # 4. Calculate risk scores
            protocol_risk = self._calculate_protocol_risk(utilization, supply_rate, borrow_rate)
            position_risk = self._calculate_position_risk(health_factor)
            market_risk = self._calculate_market_risk(usdc_deviation)
            
            total_risk_score = (
                protocol_risk * 0.4 +
                position_risk * 0.4 +
                market_risk * 0.2
            )
            
            # 5. Generate safety recommendations
            recommendations = []
            if health_factor < 1.8:  # Below 1.8x safety margin
                recommendations.append("Consider reducing leverage to increase safety margin")
            if utilization > 85:
                recommendations.append("High utilization - monitor closely for potential issues")
            if usdc_deviation > 0.001:  # 0.1% deviation
                recommendations.append("USDC showing slight price instability")
            
            return {
                'protocol_health': {
                    'utilization_rate': utilization,
                    'supply_rate': supply_rate / 1e18,
                    'borrow_rate': borrow_rate / 1e18,
                    'protocol_risk_score': protocol_risk
                },
                'position_health': {
                    'health_factor': health_factor,
                    'current_leverage': position['leverage_ratio'],
                    'position_risk_score': position_risk
                },
                'market_health': {
                    'usdc_price': usdc_price,
                    'usdc_deviation': usdc_deviation,
                    'market_risk_score': market_risk
                },
                'overall_risk_score': total_risk_score,
                'status': 'SAFE' if total_risk_score < 50 else 'CAUTION' if total_risk_score < 75 else 'DANGER',
                'recommendations': recommendations
            }
            
        except Exception as e:
            logging.error(f"Error checking position safety: {str(e)}")
            return None

    def _calculate_protocol_risk(
        self,
        utilization: float,
        supply_rate: int,
        borrow_rate: int
    ) -> float:
        """Calculate protocol risk score (0-100)"""
        # Higher score = higher risk
        utilization_score = (utilization / 100) * 40  # Max 40 points
        
        # Rate spread risk (higher spread = higher risk)
        rate_spread = (borrow_rate - supply_rate) / 1e18
        spread_score = min((rate_spread * 100), 30)  # Max 30 points
        
        # TVL and history would be considered here
        base_risk = 20  # Base protocol risk
        
        return min(utilization_score + spread_score + base_risk, 100)

    def _calculate_position_risk(self, health_factor: float) -> float:
        """Calculate position risk score (0-100)"""
        if health_factor <= 1:
            return 100
        elif health_factor >= 2:
            return 0
        else:
            # Linear interpolation between health factors 1 and 2
            return 100 * (2 - health_factor)

    def _calculate_market_risk(self, usdc_deviation: float) -> float:
        """Calculate market risk score (0-100)"""
        # USDC deviation risk
        if usdc_deviation <= 0.0001:  # 0.01% deviation
            return 0
        elif usdc_deviation >= 0.01:  # 1% deviation
            return 100
        else:
            # Exponential risk increase
            return min(usdc_deviation * 10000, 100)

    async def get_usdc_price(self) -> float:
        """Get current USDC price from reliable oracle"""
        try:
            # Implementation would use Chainlink or other reliable oracle
            return 1.0  # Example return
        except Exception as e:
            logging.error(f"Error getting USDC price: {str(e)}")
            return 0

    async def get_position_info(self, wallet_address: str) -> Dict:
        """Get current position information"""
        try:
            supplied = await self.moonwell_contract.functions.getSupplyBalance(
                wallet_address,
                self.usdc_address
            ).call()
            
            borrowed = await self.moonwell_contract.functions.getBorrowBalance(
                wallet_address,
                self.usdc_address
            ).call()
            
            return {
                'total_deposit': supplied / 1e18,
                'borrowed_amount': borrowed / 1e18,
                'leverage_ratio': (supplied / (supplied - borrowed)) if supplied > borrowed else 0
            }
            
        except Exception as e:
            logging.error(f"Error getting position info: {str(e)}")
            return None
