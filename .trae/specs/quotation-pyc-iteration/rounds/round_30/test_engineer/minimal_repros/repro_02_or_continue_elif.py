"""[R30-5 minimal repro] `if A or B: continue` in for loop with elif chain.

Pattern: Inside a for loop, `if A or B: continue` followed by `elif C: ...; else: ...`
compiles to a shared continue block:
  A; POP_JUMP_IF_TRUE to <shared_continue>
  B; POP_JUMP_IF_FALSE to <after>
  <shared_continue>: JUMP_BACKWARD to loop_header
  <after>: ...

The region analyzer models this as two IfRegions:
  - IfRegion@A type=IF_THEN merge=loop_header then=[B_block, ...] else=[]
    (TRUE path jumps to shared_continue -> loop_header; FALSE falls through)
  - IfRegion@B type=IF_ELIF_CHAIN merge=loop_header then=[shared_continue] else=[...]

Without the fix, the decompiler generates:
  if not A:
      if B: continue
      elif C: ...
      else: ...
This produces an extra JUMP_BACKWARD (implicit continue when A is True),
causing bytecode diff=+1.

With the fix, the decompiler generates:
  if A or B: continue
  elif C: ...
  else: ...
which matches the original bytecode exactly (diff=0).
"""
import dis


def _compile_and_check(src, label):
    code = compile(src, f'<{label}>', 'exec')
    for c in code.co_consts:
        if hasattr(c, 'co_name') and c.co_name == 'test_fn':
            fn = c
            break
    instrs = list(dis.get_instructions(fn))
    # Find POP_JUMP_FORWARD_IF_TRUE and check for shared continue pattern
    has_if_true = any(i.opname == 'POP_JUMP_FORWARD_IF_TRUE' for i in instrs)
    # Count JUMP_BACKWARD instructions inside the loop (before data_out.append)
    jb_count = sum(1 for i in instrs if i.opname == 'JUMP_BACKWARD')
    print(f"  {label}: POP_JUMP_IF_TRUE={has_if_true}, JUMP_BACKWARD count={jb_count}")
    return has_if_true, jb_count


# Original pattern: if A or B: continue; elif C: ...; else: ...
src_original = """
def test_fn():
    data = []
    dict1 = {}
    data_out = []
    for i in data:
        for key, value in i.items():
            if key == 'price_change_ratio' or key == 'trading_time_desc':
                continue
            elif isinstance(value, dict):
                dict1.update(value)
                continue
            else:
                dict1[key] = value
                continue
    data_out.append(dict1)
"""

# Buggy pattern (before fix): if not A: if B: continue; elif...
src_buggy = """
def test_fn():
    data = []
    dict1 = {}
    data_out = []
    for i in data:
        for key, value in i.items():
            if not key == 'price_change_ratio':
                if key == 'trading_time_desc':
                    continue
                elif isinstance(value, dict):
                    dict1.update(value)
                    continue
                else:
                    dict1[key] = value
                    continue
    data_out.append(dict1)
"""

print("=== Minimal repro: if A or B: continue with elif chain ===")
_, jb_orig = _compile_and_check(src_original, 'original (A or B)')
_, jb_buggy = _compile_and_check(src_buggy, 'buggy (if not A)')

if jb_buggy > jb_orig:
    print(f"\n  BUG CONFIRMED: buggy has {jb_buggy - jb_orig} extra JUMP_BACKWARD(s)")
    print(f"  original={jb_orig}, buggy={jb_buggy}")
else:
    print(f"\n  No diff detected (original={jb_orig}, buggy={jb_buggy})")
