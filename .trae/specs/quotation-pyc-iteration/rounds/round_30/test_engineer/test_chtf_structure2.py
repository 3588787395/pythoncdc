"""R30-6: Test nested structure with code after the if-elif chain (like quotation.pyc)."""
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


# Nested structure with code after if-elif (matches quotation.pyc pattern)
src_nested_after = """
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

compile_and_show(src_nested_after, 'nested with code after if-elif')
