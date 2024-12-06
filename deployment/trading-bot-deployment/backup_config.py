import shutil
import json
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

def create_backup():
    """Create a backup of all configuration and database files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backups/backup_{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to backup
    files_to_backup = [
        "config/trading_config.json",
        "database/wallet.json",
        "database/trade_history.json",
        "trading/engine.py",
        "app.py",
        "ocean_runner.py"
    ]
    
    for file_path in files_to_backup:
        src = Path(file_path)
        if src.exists():
            dst = backup_dir / src.name
            shutil.copy2(src, dst)
            logging.info(f"Backed up {src} to {dst}")
    
    logging.info(f"Backup completed: {backup_dir}")

if __name__ == "__main__":
    create_backup()
