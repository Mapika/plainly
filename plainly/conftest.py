import sys
from pathlib import Path

# Make the `plainly` package under scripts/ importable in tests.
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
