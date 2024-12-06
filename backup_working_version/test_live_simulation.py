import asyncio
import logging
from datetime import datetime
import json
from src.simulation.sim_trader import SimulatedTrader
from src.market_analysis import MarketAnalyzer
from src.profit_hunter import ProfitHunter

async def run_live_simulation():
    """Run trading simulation with real-time market data"""
    
    # Initialize components
    sim_trader = SimulatedTrader(initial_balance=500.0)
    market_analyzer = MarketAnalyzer()
    profit_hunter = ProfitHunter(initial_capital=500.0)
    
    logging.info(f"Starting live simulation at {datetime.utcnow().isoformat()}")
    logging.info(f"Initial balance: ${sim_trader.initial_balance}")
    
    try:
        while True:
            # Get real-time market data
            opportunities = await profit_hunter.scan_new_tokens()
            
            for token in opportunities:
                # Get detailed market data
                market_data = await market_analyzer.get_realtime_data(token['address'])
                
                # Update existing positions
                await sim_trader.update_positions({token['address']: market_data})
                
                # Analyze for new trades
                if profit_hunter.should_enter_trade(market_data):
                    # Calculate position size
                    price = float(market_data['price_data']['price'])
                    amount = min(
                        sim_trader.max_position_size / price,
                        float(market_data['price_data']['liquidity']) * 0.01  # Max 1% of liquidity
                    )
                    
                    # Execute simulated trade
                    result = await sim_trader.execute_trade(
                        token['address'],
                        'BUY',
                        amount,
                        price
                    )
                    
                    if result['success']:
                        logging.info(f"Opened position in {token['symbol']} at ${price}")
                    
            # Get and log performance metrics
            metrics = sim_trader.get_performance_metrics()
            logging.info(f"Current Balance: ${metrics['current_balance']:.2f}")
            logging.info(f"Win Rate: {metrics['win_rate']:.2f}%")
            logging.info(f"ROI: {metrics['roi']:.2f}%")
            
            # Save results periodically
            sim_trader.save_results('simulation_results.json')
            
            # Wait before next iteration
            await asyncio.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        logging.info("Simulation stopped by user")
        sim_trader.save_results('final_simulation_results.json')
    except Exception as e:
        logging.error(f"Simulation error: {str(e)}")
        sim_trader.save_results('error_simulation_results.json')

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create simulation directory if it doesn't exist
    import os
    os.makedirs('simulation_results', exist_ok=True)
    
    # Run the simulation
    asyncio.run(run_live_simulation())
