from solana.rpc.api import Client
import time

def airdrop_sol(wallet_address, amount_sol=2):
    """Airdrop SOL to wallet on devnet"""
    print(f"Requesting airdrop for {wallet_address}")
    
    # Connect to devnet
    client = Client("https://api.devnet.solana.com")
    
    try:
        # Request airdrop (amount in lamports, 1 SOL = 1B lamports)
        result = client.request_airdrop(wallet_address, int(amount_sol * 1000000000))
        print(f"Airdrop requested: {result['result']}")
        
        # Wait for confirmation
        print("Waiting for confirmation...")
        time.sleep(20)  # Devnet needs time to process
        
        # Check balance
        balance = client.get_balance(wallet_address)
        print(f"New balance: {balance['result']['value'] / 1000000000:.2f} SOL")
        
        return True
    except Exception as e:
        print(f"Error during airdrop: {str(e)}")
        return False

if __name__ == "__main__":
    # Your devnet wallet
    WALLET = "G2xZUKwoBE8DjYAvPVbaJozFVZedRYoGeQFaguncELLi"
    
    # Request 2 SOL
    success = airdrop_sol(WALLET, 2)
    if success:
        print("Airdrop successful! Check your Phantom wallet.")
    else:
        print("Airdrop failed. Try using https://solfaucet.com instead.")
