import os
import sys
import subprocess

def run_server():
    try:
        # Set environment variables
        os.environ['FLASK_APP'] = 'src.flask_dashboard'
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
        
        # Get the Python executable path
        python_exe = sys.executable
        
        # Run Flask
        subprocess.run([python_exe, "-m", "flask", "run", "--host=127.0.0.1", "--port=5000"])
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")

if __name__ == '__main__':
    run_server()
