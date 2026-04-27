import sys
from pathlib import Path

# Make the project root importable from inside the tests/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

