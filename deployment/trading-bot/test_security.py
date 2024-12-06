import asyncio
from src.solana_trader import SolanaTrader
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_security_features():
    """Test all security features of the trading bot"""
    
    # Load config
    with open('config/rpc_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize trader with test wallet
    trader = SolanaTrader(
        wallet_address="G2xZUKwoBE8DjYAvPVbaJozFVZedRYoGeQFaguncELLi",
        private_key="YOUR_PRIVATE_KEY",  # Will be used only for test transactions
        ocean_config_path="config/rpc_config.json"
    )
    
    # Test tokens
    test_tokens = {
        'good_token': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
        'suspicious_token': 'YOUR_SUSPICIOUS_TOKEN',
    }
    
    print("\n=== Starting Security Tests ===\n")
    
    try:
        # 1. Basic Security Check
        print("Testing comprehensive security checks...")
        for name, token in test_tokens.items():
            security = await trader.check_token_security(token)
            print(f"\n{name.upper()} Security Check:")
            print(f"Safe: {security['safe']}")
            print(f"Score: {security['score']}")
            
            if security['critical_flags']:
                print(f"Critical Flags: {security['critical_flags']}")
            if security['warnings']:
                print(f"Warnings: {security['warnings']}")
            
            # Print detailed analysis
            print("\nDetailed Analysis:")
            print(f"Honeypot Check: {'Failed' if security['details']['honeypot']['is_honeypot'] else 'Passed'}")
            print(f"Ownership: {'Renounced' if security['details']['ownership']['renounced'] else 'Not Renounced'}")
            print(f"Max Tax: {max(security['details']['taxes']['buy_tax'], security['details']['taxes']['sell_tax'])*100:.1f}%")
            print(f"Liquidity Score: {security['details']['liquidity']['score']}")
        
        # 2. Test Entry Analysis
        print("\nTesting entry analysis...")
        entry = await trader.analyze_entry_opportunity(test_tokens['good_token'])
        print(f"\nEntry Analysis:")
        print(f"Should Enter: {entry['should_enter']}")
        print(f"Score: {entry['score']}")
        print(f"Reasons: {entry['reasons']}")
        print(f"Suggested Position Size: ${entry['position_size']:,.2f}")
        
        # 3. Test Exit Analysis
        print("\nTesting exit analysis...")
        exit_analysis = await trader.analyze_exit_opportunity(
            test_tokens['good_token'],
            entry_price=1.0,
            position_size=1000
        )
        print(f"\nExit Analysis:")
        print(f"Should Exit: {exit_analysis['should_exit']}")
        print(f"Reasons: {exit_analysis['reasons']}")
        print(f"Price Change: {exit_analysis['price_change']*100:.1f}%")
        
        # 4. Test Real-time Monitoring
        print("\nTesting real-time monitoring...")
        await trader._monitor_token_security(test_tokens['good_token'])
        print("Monitoring test complete")
        
        print("\n=== Security Tests Complete ===\n")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    
    finally:
        # Cleanup
        await trader.close()

if __name__ == "__main__":
    asyncio.run(test_security_features())
