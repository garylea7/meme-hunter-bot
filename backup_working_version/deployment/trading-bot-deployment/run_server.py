import sys
import os

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Read environment variables directly
env_path = os.path.join(project_root, '.env')
env_vars = {}
with open(env_path, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()

print(f"Wallet Address: {os.environ.get('WALLET_ADDRESS')}")

# Import and run the Flask app
from src.flask_dashboard import app
from hypercorn.config import Config
from hypercorn.asyncio import serve
import asyncio

if __name__ == '__main__':
    config = Config()
    config.bind = ["localhost:5000"]
    asyncio.run(serve(app, config))
