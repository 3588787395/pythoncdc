"""[R30-7 minimal repro] if-elif chain followed by a separate `if` (not `elif`).

When the then body of an elif contains an inner if-elif chain whose last
branch is `pass` (no else), the inner merge falls through to the next
statement. If that next statement is `if E: ... else: ...`, the decompiler
incorrectly treats it as `elif E: ... else: ...`, generating an extra
JUMP_FORWARD (to skip the else body of the elif chain), causing bytecode
diff=+2.

Pattern (original source):
    if A: continue
    elif B:
        if C: continue
        elif D: pass       # D's pass falls through to E
    if E: ...              # E is a SEPARATE if, NOT elif E
    else: ...

Control flow:
    B false -> E (conditional jump)
    D false -> E (conditional jump)
    D true  -> E (fall-through)

E's predecessors include D's blocks (from B's then body). In a normal
elif chain, the next elif condition has only ONE predecessor (the
previous elif condition). When E has predecessors from the then body,
it's a merge point (separate if), not an elif condition.

With the fix, the decompiler correctly generates `if E:` (separate),
producing exact bytecode match (diff=0).
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
    print(f"  {label}: instrs={len(instrs)} JUMP_FORWARD={jf_count}")
    return len(instrs), jf_count


# Correct structure: if-elif + separate if (NOT elif)
src_correct = """
def test_fn(a, b, c, d, e):
    for n in [1, 2, 3]:
        if a:
            continue
        elif b:
            if c:
                continue
            elif d:
                pass
        if e:
            x = 1
        else:
            x = 2
        y = 3
"""

# Buggy structure: if-elif-elif-else (E treated as elif)
src_buggy = """
def test_fn(a, b, c, d, e):
    for n in [1, 2, 3]:
        if a:
            continue
        elif b:
            if c:
                continue
            elif d:
                pass
        elif e:
            x = 1
        else:
            x = 2
        y = 3
"""

print("=== Minimal repro: separate if vs elif after if-elif chain ===")
n_correct, jf_correct = _compile_and_check(src_correct, 'correct (separate if)')
n_buggy, jf_buggy = _compile_and_check(src_buggy, 'buggy (elif)')

if n_buggy > n_correct:
    print(f"\n  BUG CONFIRMED: buggy has {n_buggy - n_correct} extra instruction(s)")
    print(f"  correct={n_correct}, buggy={n_buggy}")
    print(f"  The extra instruction is JUMP_FORWARD (skip else body of elif chain)")
else:
    print(f"\n  No diff (correct={n_correct}, buggy={n_buggy})")
