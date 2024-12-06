import websockets
import json
import asyncio
import time

async def test_websocket():
    # Load config
    with open('config/rpc_config.json', 'r') as f:
        config = json.load(f)
    
    ws_url = config['websocket']['primary']
    
    try:
        print("Testing WebSocket connection...")
        async with websockets.connect(ws_url) as websocket:
            # Subscribe to slot updates
            subscribe_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "slotSubscribe"
            }
            
            await websocket.send(json.dumps(subscribe_message))
            response = await websocket.recv()
            print(f"Subscription response: {response}")
            
            # Wait for a few updates
            print("\nWaiting for slot updates (5 seconds)...")
            for _ in range(3):
                update = await websocket.recv()
                print(f"Received update: {update}")
                await asyncio.sleep(1)
            
            print("\nWebSocket Test: SUCCESS")
            return True
            
    except Exception as e:
        print(f"\nWebSocket Test: FAILED")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_websocket())
