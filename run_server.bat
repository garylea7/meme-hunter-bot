@echo off
echo Starting Flask server...
set FLASK_APP=src.flask_dashboard
set FLASK_ENV=development
set FLASK_DEBUG=1
python -m flask run --host=127.0.0.1 --port=5000
pause
