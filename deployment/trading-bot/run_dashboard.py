import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from streamlit_interface import run_dashboard

if __name__ == "__main__":
    run_dashboard()
