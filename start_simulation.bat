@echo off
echo Starting Flash Trading Bot Simulation...

REM Start the simulation in a new window with proper input handling
start "Flash Simulation" /B python test_live_simulation.py

REM Wait a moment for the simulation to initialize
timeout /t 2

REM Start the dashboard in a new window with proper input handling
start "Flash Dashboard" /B python run_dashboard.py

echo Started! Opening dashboard in your browser...
timeout /t 2
start http://localhost:5000

echo Done! The white trading dashboard should open in your browser.
