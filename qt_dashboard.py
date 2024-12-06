import sys
import asyncio
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
                           QHeaderView)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor
from trading.engine import TradingEngine
from datetime import datetime
import json
import qasync
import gc

class TradingDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MemeHunter Trading Bot')
        self.setGeometry(100, 100, 1200, 800)  # Smaller window
        self.setStyleSheet("background-color: white;")

        # Initialize trading engine
        self.trading_engine = TradingEngine()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)  # Reduce spacing

        # Create metrics section
        metrics_widget = QWidget()
        metrics_layout = QHBoxLayout(metrics_widget)
        metrics_layout.setSpacing(10)  # Reduce spacing
        
        # Style for metric cards (simplified)
        metric_style = """
            QWidget#metric_card {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
            QLabel#value_label {
                font-size: 24px;
                color: #1E88E5;
                font-weight: bold;
            }
            QLabel#label_label {
                font-size: 16px;
                color: #666;
            }
        """

        # Create metric cards
        self.wallet_balance = self.create_metric_card("Wallet Balance", "$0.00", metric_style)
        self.win_rate = self.create_metric_card("Win Rate", "0.0%", metric_style)
        self.total_trades = self.create_metric_card("Total Trades", "0", metric_style)
        self.moonshots = self.create_metric_card("Moonshots", "0", metric_style)

        metrics_layout.addWidget(self.wallet_balance)
        metrics_layout.addWidget(self.win_rate)
        metrics_layout.addWidget(self.total_trades)
        metrics_layout.addWidget(self.moonshots)
        layout.addWidget(metrics_widget)

        # Create trades table (optimized)
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(6)  # Removed 'Status' column
        self.trades_table.setHorizontalHeaderLabels([
            'Time', 'Token', 'Type', 'Amount', 'Price', 'Profit'
        ])
        
        # Set table style (simplified)
        self.trades_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                padding: 5px;
            }
            QHeaderView::section {
                background-color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Auto-resize columns to content
        header = self.trades_table.horizontalHeader()
        for i in range(6):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.trades_table)

        # Create update timer (reduced frequency)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(5000)  # Update every 5 seconds instead of 2

        # Memory optimization
        self.last_trades = []
        gc.collect()  # Force garbage collection

    def create_metric_card(self, label_text, value_text, style):
        """Create a metric card (optimized)"""
        card = QWidget()
        card.setObjectName("metric_card")
        card.setStyleSheet(style)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        value = QLabel(value_text)
        value.setObjectName("value_label")
        value.setAlignment(Qt.AlignCenter)
        
        label = QLabel(label_text)
        label.setObjectName("label_label")
        label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(value)
        layout.addWidget(label)
        
        return card

    def update_dashboard(self):
        """Update dashboard (optimized)"""
        try:
            # Get trading data
            data = self.trading_engine.get_trading_metrics()
            if not data:
                return

            # Update metrics (only if changed)
            balance = f"${data['wallet_balance']:.2f}"
            if self.wallet_balance.findChild(QLabel, "value_label").text() != balance:
                self.wallet_balance.findChild(QLabel, "value_label").setText(balance)

            win_rate = f"{data['win_rate']:.1f}%"
            if self.win_rate.findChild(QLabel, "value_label").text() != win_rate:
                self.win_rate.findChild(QLabel, "value_label").setText(win_rate)

            trades = str(data['total_trades'])
            if self.total_trades.findChild(QLabel, "value_label").text() != trades:
                self.total_trades.findChild(QLabel, "value_label").setText(trades)

            moonshots = str(data['moonshots'])
            if self.moonshots.findChild(QLabel, "value_label").text() != moonshots:
                self.moonshots.findChild(QLabel, "value_label").setText(moonshots)

            # Update trades table (only if new trades)
            new_trades = data['recent_trades']
            if new_trades != self.last_trades:
                self.trades_table.setRowCount(len(new_trades))
                
                for i, trade in enumerate(new_trades):
                    # Time
                    self.trades_table.setItem(i, 0, QTableWidgetItem(trade['timestamp']))
                    # Token
                    self.trades_table.setItem(i, 1, QTableWidgetItem(trade['token']))
                    # Type
                    self.trades_table.setItem(i, 2, QTableWidgetItem(trade['type']))
                    # Amount
                    self.trades_table.setItem(i, 3, QTableWidgetItem(f"{trade['amount']:.2f}"))
                    # Price
                    self.trades_table.setItem(i, 4, QTableWidgetItem(f"${trade['price']:.4f}"))
                    
                    # Profit with color
                    profit_item = QTableWidgetItem(f"{trade['profit']:.2f}%")
                    if trade['profit'] > 0:
                        profit_item.setForeground(QColor('#4CAF50'))
                    else:
                        profit_item.setForeground(QColor('#f44336'))
                    self.trades_table.setItem(i, 5, profit_item)
                
                self.last_trades = new_trades

            # Force cleanup
            gc.collect()

        except Exception as e:
            print(f"Error updating dashboard: {e}")

    async def start_trading_engine(self):
        """Start the trading engine in the background"""
        try:
            await self.trading_engine.start()
        except Exception as e:
            print(f"Error starting trading engine: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set application-wide font (system default for better performance)
    app.setStyle('Fusion')  # Use Fusion style for better performance
    
    window = TradingDashboard()
    window.show()
    
    # Create event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Start trading engine
    loop.create_task(window.start_trading_engine())
    
    # Run event loop
    with loop:
        loop.run_forever()
