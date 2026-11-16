# g2c REAL46-046 min: module globals derived from __file__ (placement-dependent).
from pathlib import Path
ROOT = Path(__file__).resolve().parent
GEN_DIRS = (ROOT / 'core', ROOT / 'parsers')
OUT = ROOT / 'docs' / 'syntax-coverage.json'
print(GEN_DIRS, OUT)
