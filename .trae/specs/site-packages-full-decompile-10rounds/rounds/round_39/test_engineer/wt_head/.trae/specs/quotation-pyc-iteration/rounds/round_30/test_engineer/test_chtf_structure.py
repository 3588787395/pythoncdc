"""R30-6: Test which source structure produces the observed bytecode pattern.

Observed pyc pattern (NO JUMP_FORWARD between D's pass and E's condition):
    B false -> E condition
    C false -> D condition
    D false -> E condition
    D true  -> pass (NOP), fall through to E condition

Question: Does `elif B: if C: continue; elif D: pass` (nested) produce this,
          or does `elif B: if C: continue` + `elif D: pass` (sibling) produce this?
"""
import dis


def compile_and_show(src, label):
    code = compile(src, f'<{label}>', 'exec')
    for c in code.co_consts:
        if hasattr(c, 'co_name') and c.co_name == 'test_fn':
            fn = c
            break
    print(f"\n=== {label} ===")
    instrs = list(dis.get_instructions(fn))
    for i, ins in enumerate(instrs):
        print(f"  [{i:3d}] off={ins.offset:4d} {ins.opname:30s} {repr(ins.argval)[:50]}")


# Structure 1: nested (what decompiler outputs)
src_nested = """
def test_fn(a, b, c, d, e):
    for n in [1,2,3]:
        if a:
            continue
        elif b:
            if c:
                continue
            elif d:
                pass
        elif e:
            x = 1
"""

# Structure 2: D as sibling of B
src_sibling = """
def test_fn(a, b, c, d, e):
    for n in [1,2,3]:
        if a:
            continue
        elif b:
            if c:
                continue
        elif d:
            pass
        elif e:
            x = 1
"""

# Structure 3: D nested, but B body has only if-elif (no trailing content)
src_nested2 = """
def test_fn(a, b, c, d, e):
    for n in [1,2,3]:
        if a:
            continue
        elif b:
            if c:
                continue
            elif d:
                pass
            else:
                pass
        elif e:
            x = 1
"""

compile_and_show(src_nested, 'nested (decompiler output)')
compile_and_show(src_sibling, 'sibling (D sibling of B)')
