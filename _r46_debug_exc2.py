"""Debug the exception handling for repro_21 - find structures."""
import sys, dis, marshal, types
sys.path.insert(0, '.')

from core.cfg.cfg_builder import build_cfg
from core.cfg.structured_analyzer import StructuredAnalyzer
from core.cfg.exception_handler import identify_try_except_simplified

REPRO_DIR = ".trae/specs/region-comment-multi-pyc-iteration/rounds/round_46/test_engineer/minimal_repros"

with open(f'{REPRO_DIR}/repro_21_try_except_format.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func = None
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'func':
        func = const
        break

cfg = build_cfg(func)
analyzer = StructuredAnalyzer(cfg)
analyzer.analyze()
identify_try_except_simplified(analyzer, set())

# Find structures
print("=== Analyzer attributes ===")
for attr in dir(analyzer):
    if not attr.startswith('_'):
        val = getattr(analyzer, attr)
        if not callable(val):
            print(f"  {attr}: {type(val).__name__} = {val if not hasattr(val, '__len__') or len(str(val)) < 200 else '...'}")

# Check for try-except structures
print("\n=== Looking for structures ===")
for attr in dir(analyzer):
    if 'struct' in attr.lower() or 'try' in attr.lower() or 'except' in attr.lower():
        val = getattr(analyzer, attr)
        print(f"  {attr}: {type(val).__name__}")
        if hasattr(val, '__iter__'):
            for item in val:
                print(f"    {item}")
