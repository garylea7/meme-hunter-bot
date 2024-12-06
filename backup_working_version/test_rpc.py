from solana.rpc.api import Client
import json
import time

def test_rpc_connection():
    # Load config
    with open('config/rpc_config.json', 'r') as f:
        config = json.load(f)
    
    # Create RPC client
    client = Client(config['rpc_endpoints']['primary'])
    
    try:
        # Test basic connection
        print("Testing RPC connection...")
        version = client.get_version()
        print(f"Connected to Solana version: {version}")
        
        # Get recent block height
        block_height = client.get_block_height()
        print(f"Current block height: {block_height}")
        
        # Test transaction count
        slot = client.get_slot()
        count = client.get_block_production()
        print(f"Recent block production info received")
        
        print("\nRPC Connection Test: SUCCESS")
        return True
        
    except Exception as e:
        print(f"\nRPC Connection Test: FAILED")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_rpc_connection()
