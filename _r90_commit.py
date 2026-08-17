#!/usr/bin/env python3
"""R90 commit script"""
import subprocess

msg = """R90: fix UNPACK_SEQUENCE tuple unpack lost in entry block of IfRegion/BoolOpRegion

Root cause: generate() inline entry block loop did not handle UNPACK_SEQUENCE.
When entry block contains tuple unpacking (a, b = f()) + if condition,
UNPACK_SEQUENCE was passed to _build_store_statement as part of value expr,
causing tuple target to collapse to single target and second store lost.

Fix: Added UNPACK_SEQUENCE/UNPACK_EX state machine to entry block loop,
mirroring _if_extract_cond_instructions logic. Verification:
- klinedata.pyc get_kline_by_count_new: 430 to 49 true_diffs
- 3 minimal reproduction cases: all bytecode match
- 112 existing tests pass, 0 regressions"""

result = subprocess.run(['git', 'add', 'core/cfg/region_ast_generator.py'], capture_output=True, text=True)
print(f"git add: {result.returncode}")
if result.stderr:
    print(result.stderr)

result = subprocess.run(['git', 'commit', '-m', msg], capture_output=True, text=True)
print(f"git commit: {result.returncode}")
print(result.stdout)
if result.stderr:
    print(result.stderr)
