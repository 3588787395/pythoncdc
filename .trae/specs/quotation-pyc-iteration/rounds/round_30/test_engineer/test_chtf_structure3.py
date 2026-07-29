"""R30-6: Test if E is a separate if (not elif) - matching quotation.pyc pattern."""
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


# Structure: E is a SEPARATE if (not elif)
src_separate_if = """
def test_fn(a, b, c, d, e):
    for n in [1,2,3]:
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

# Structure: E is elif (what decompiler outputs - WRONG)
src_elif_e = """
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
        else:
            x = 2
        y = 3
"""

compile_and_show(src_separate_if, 'SEPARATE if E (correct)')
compile_and_show(src_elif_e, 'elif E (decompiler output - WRONG)')
