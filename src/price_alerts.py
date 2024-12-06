import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
import aiohttp
from dataclasses import dataclass
import numpy as np
import winsound
import os
from pathlib import Path

@dataclass
class PriceAlert:
    pair: str
    condition: str  # 'above' or 'below'
    price: float
    notification_type: str  # 'sound', 'popup', 'both'
    created_at: datetime
    expires_at: Optional[datetime] = None
    triggered: bool = False

class PriceAlertManager:
    def __init__(self):
        self.alerts: List[PriceAlert] = []
        self.triggered_alerts: Set[int] = set()
        self.sound_enabled = True
        
        # Create sounds directory if it doesn't exist
        self.sounds_dir = Path("sounds")
        self.sounds_dir.mkdir(exist_ok=True)
        
        # Default sound files
        self.sounds = {
            'opportunity': str(self.sounds_dir / 'opportunity.wav'),
            'alert': str(self.sounds_dir / 'alert.wav'),
            'warning': str(self.sounds_dir / 'warning.wav')
        }
        
        # Create default sound files if they don't exist
        self.create_default_sounds()
    
    def create_default_sounds(self):
        """Create default sound files using Windows beeps"""
        try:
            import wave
            import struct
            
            for sound_type, filename in self.sounds.items():
                if not os.path.exists(filename):
                    # Create a simple WAV file with a beep
                    with wave.open(filename, 'w') as wav_file:
                        # Set parameters
                        nchannels = 1
                        sampwidth = 2
                        framerate = 44100
                        nframes = framerate  # 1 second
                        
                        # Set WAV file parameters
                        wav_file.setnchannels(nchannels)
                        wav_file.setsampwidth(sampwidth)
                        wav_file.setframerate(framerate)
                        
                        # Generate different frequencies for different alerts
                        if sound_type == 'opportunity':
                            freq = 1000
                        elif sound_type == 'alert':
                            freq = 800
                        else:
                            freq = 600
                        
                        # Generate sound wave
                        for i in range(nframes):
                            value = int(32767.0 * np.sin(2.0 * np.pi * freq * i / framerate))
                            data = struct.pack('<h', value)
                            wav_file.writeframes(data)
        except Exception as e:
            logging.error(f"Error creating sound files: {str(e)}")
    
    def add_alert(
        self,
        pair: str,
        condition: str,
        price: float,
        notification_type: str = 'both',
        duration_hours: Optional[float] = None
    ) -> bool:
        """Add a new price alert"""
        try:
            now = datetime.now()
            expires_at = None
            if duration_hours:
                expires_at = now.timestamp() + (duration_hours * 3600)
            
            alert = PriceAlert(
                pair=pair,
                condition=condition,
                price=price,
                notification_type=notification_type,
                created_at=now,
                expires_at=expires_at,
                triggered=False
            )
            
            self.alerts.append(alert)
            return True
            
        except Exception as e:
            logging.error(f"Error adding alert: {str(e)}")
            return False
    
    def remove_alert(self, alert_id: int) -> bool:
        """Remove an alert by its ID"""
        try:
            if 0 <= alert_id < len(self.alerts):
                self.alerts.pop(alert_id)
                return True
            return False
        except Exception as e:
            logging.error(f"Error removing alert: {str(e)}")
            return False
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts = []
        self.triggered_alerts.clear()
    
    async def check_alerts(self, current_prices: Dict[str, float]):
        """Check all active alerts against current prices"""
        now = datetime.now().timestamp()
        triggered = []
        
        for i, alert in enumerate(self.alerts):
            if i in self.triggered_alerts:
                continue
                
            if alert.expires_at and now > alert.expires_at:
                continue
                
            current_price = current_prices.get(alert.pair)
            if not current_price:
                continue
                
            is_triggered = False
            if alert.condition == 'above' and current_price > alert.price:
                is_triggered = True
            elif alert.condition == 'below' and current_price < alert.price:
                is_triggered = True
                
            if is_triggered:
                triggered.append((i, alert))
                self.triggered_alerts.add(i)
        
        return triggered
    
    async def process_triggered_alerts(self, triggered_alerts: List[tuple]):
        """Process triggered alerts"""
        for alert_id, alert in triggered_alerts:
            message = f"🚨 Price Alert: {alert.pair} is {alert.condition} {alert.price}"
            
            if alert.notification_type in ['sound', 'both']:
                self.play_alert_sound('alert')
            
            if alert.notification_type in ['popup', 'both']:
                # In a full implementation, this would show a system notification
                print(message)
    
    def play_alert_sound(self, sound_type: str = 'alert'):
        """Play alert sound"""
        try:
            if self.sound_enabled:
                sound_file = self.sounds.get(sound_type)
                if sound_file and os.path.exists(sound_file):
                    winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            logging.error(f"Error playing sound: {str(e)}")
    
    def toggle_sound(self, enabled: bool):
        """Toggle sound notifications"""
        self.sound_enabled = enabled
    
    def get_active_alerts(self) -> List[PriceAlert]:
        """Get list of active alerts"""
        now = datetime.now().timestamp()
        return [
            alert for i, alert in enumerate(self.alerts)
            if i not in self.triggered_alerts
            and (not alert.expires_at or now <= alert.expires_at)
        ]
    
    def get_triggered_alerts(self) -> List[PriceAlert]:
        """Get list of triggered alerts"""
        return [
            alert for i, alert in enumerate(self.alerts)
            if i in self.triggered_alerts
        ]
    
    def export_alerts(self, filename: str = 'alerts.json'):
        """Export alerts to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(
                    [{
                        'pair': alert.pair,
                        'condition': alert.condition,
                        'price': alert.price,
                        'notification_type': alert.notification_type,
                        'created_at': alert.created_at.isoformat(),
                        'expires_at': alert.expires_at.isoformat() if alert.expires_at else None,
                        'triggered': alert.triggered
                    } for alert in self.alerts],
                    f,
                    indent=2
                )
        except Exception as e:
            logging.error(f"Error exporting alerts: {str(e)}")
    
    def import_alerts(self, filename: str = 'alerts.json'):
        """Import alerts from JSON file"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)
                    self.alerts = [
                        PriceAlert(
                            pair=alert['pair'],
                            condition=alert['condition'],
                            price=alert['price'],
                            notification_type=alert['notification_type'],
                            created_at=datetime.fromisoformat(alert['created_at']),
                            expires_at=datetime.fromisoformat(alert['expires_at']) if alert['expires_at'] else None,
                            triggered=alert['triggered']
                        )
                        for alert in data
                    ]
        except Exception as e:
            logging.error(f"Error importing alerts: {str(e)}")
            
class OpportunityAlertManager(PriceAlertManager):
    """Specialized alert manager for arbitrage opportunities"""
    
    def __init__(self):
        super().__init__()
        self.min_profit_threshold = 1.0  # 1% minimum profit
        self.opportunity_history = []
        
    def set_profit_threshold(self, threshold: float):
        """Set minimum profit threshold for opportunities"""
        self.min_profit_threshold = threshold
    
    async def check_opportunity(self, opportunity: Dict) -> bool:
        """Check if an opportunity meets alert criteria"""
        try:
            profit_percentage = opportunity.get('profit_percentage', 0)
            
            if profit_percentage >= self.min_profit_threshold:
                # Record opportunity
                self.opportunity_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'opportunity': opportunity
                })
                
                # Play opportunity sound
                self.play_alert_sound('opportunity')
                
                return True
                
            return False
            
        except Exception as e:
            logging.error(f"Error checking opportunity: {str(e)}")
            return False
    
    def get_opportunity_history(
        self,
        limit: Optional[int] = None,
        min_profit: Optional[float] = None
    ) -> List[Dict]:
        """Get history of opportunities"""
        history = self.opportunity_history
        
        if min_profit is not None:
            history = [
                h for h in history
                if h['opportunity']['profit_percentage'] >= min_profit
            ]
        
        if limit:
            history = history[-limit:]
            
        return history
    
    def clear_history(self):
        """Clear opportunity history"""
        self.opportunity_history = []
