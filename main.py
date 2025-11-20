#!/usr/bin/env python3
"""
Main entry point for the voice recognition server.
This wrapper allows running from the project root or src directory.
"""

import sys
from pathlib import Path

# Add src directory to Python path if not already there
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
