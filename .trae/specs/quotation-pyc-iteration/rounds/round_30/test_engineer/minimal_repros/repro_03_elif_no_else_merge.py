"""[R30-6 minimal repro] if-elif-elif chain where last elif body has a nested
if whose FALSE path converges at the chain merge (no else).

Pattern:
    if A: return           # sink
    elif B: return         # sink
    elif C:                # condition
        n = ...            # elif body entry (conditional block)
        if D:              # nested condition (same block)
            ...
            return         # sink
        # D's FALSE → merge (direct jump, no JUMP_FORWARD)
    # C's FALSE → merge (same merge point)
    post_code              # merge

C's FALSE and D's FALSE both jump directly to merge (post-if code).
The region analyzer should detect this and treat merge as the chain merge
(NOT as else body). Otherwise, it generates:
    elif C:
        ...
    else:
        post_code
which produces an extra JUMP_FORWARD (to skip the else body), causing
bytecode diff=+1.

With the fix, the decompiler generates:
    elif C:
        ...
    post_code
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
    jf_count = sum(1 for i in instrs if i.opname == 'JUMP_FORWARD')
    print(f"  {label}: JUMP_FORWARD count={jf_count}")
    return jf_count


# Original pattern: if-elif-elif (NO else), post-if code
src_original = """
def test_fn(a, b):
    if a == 1:
        return 0
    elif a == 2:
        return 1
    elif a == 3:
        n = b
        if n == 0:
            b = b + 1
            return round(b, 2)
    preindex = None
    tmpdata = None
    if b > 0:
        tmpstartindex = b
    else:
        tmpstartindex = 0
    return preindex
"""


# Buggy pattern (before fix): if-elif-elif-else (with else wrapping post-if code)
src_buggy = """
def test_fn(a, b):
    if a == 1:
        return 0
    elif a == 2:
        return 1
    elif a == 3:
        n = b
        if n == 0:
            b = b + 1
            return round(b, 2)
    else:
        preindex = None
        tmpdata = None
        if b > 0:
            tmpstartindex = b
        else:
            tmpstartindex = 0
    return preindex
"""


print("=== Minimal repro: if-elif-elif with nested if, no else ===")
jf_orig = _compile_and_check(src_original, 'original (no else)')
jf_buggy = _compile_and_check(src_buggy, 'buggy (with else)')

if jf_buggy > jf_orig:
    print(f"\n  BUG CONFIRMED: buggy has {jf_buggy - jf_orig} extra JUMP_FORWARD(s)")
    print(f"  original={jf_orig}, buggy={jf_buggy}")
else:
    print(f"\n  No diff detected (original={jf_orig}, buggy={jf_buggy})")
