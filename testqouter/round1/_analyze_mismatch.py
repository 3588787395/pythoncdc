import py_compile, sys, os

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from pycdc import decompile_pyc

mismatched = ['test_b05_expr_stmt.py', 'test_b08_pass.py', 'test_e01_try_except.py', 'test_e02_multi_except.py',
              'test_e03_try_else_finally.py', 'test_e04_try_finally.py', 'test_e05_try_except_finally.py',
              'test_e06_full_combination.py', 'test_e07_except_as.py', 'test_e08_bare_except.py',
              'test_e09_nested_try.py', 'test_e10_try_with_loop.py', 'test_e11_loop_with_try.py',
              'test_e12_try_with_if.py', 'test_e13_if_with_try.py', 'test_l01_for_break.py',
              'test_l02_for_continue.py', 'test_l03_for_else.py', 'test_l04_while_break.py',
              'test_l06_for.py', 'test_l09_for_break_else.py', 'test_l10_while_break_else.py',
              'test_l11_for_break_continue.py', 'test_l12_while_break_continue.py',
              'test_l13_nested_for.py', 'test_l15_nested_for_break.py', 'test_l16_nested_for_continue.py',
              'test_l17_for_with_while.py', 'test_n10_try_for_break.py', 'test_n11_try_while_continue.py',
              'test_n12_for_try_except.py', 'test_n13_while_try_except.py', 'test_n14_for_for_if_break.py',
              'test_n15_while_if_while_break.py', 'test_n16_for_if_try_except.py', 'test_n17_if_for_break.py',
              'test_n18_if_while_break.py', 'test_w01_with.py', 'test_w02_with_no_as.py',
              'test_w03_multi_with.py', 'test_w04_nested_with.py', 'test_w05_with_with_try.py',
              'test_w06_try_with_with.py']


def extract_body(src):
    lines = src.strip().split('\n')
    body_lines = []
    in_func = False
    for line in lines:
        if line.startswith('def '):
            in_func = True
            continue
        if in_func and line.strip():
            body_lines.append(line)
    return '\n'.join(body_lines)


for tf in mismatched[:6]:
    test_path = os.path.join(HERE, tf)
    with open(test_path) as f:
        orig_src = f.read()

    pyc_path = tf + 'c'
    py_compile.compile(test_path, cfile=pyc_path, doraise=True)
    deco_src = decompile_pyc(pyc_path)
    os.remove(pyc_path)

    orig_body = extract_body(orig_src)
    deco_body = extract_body(deco_src)

    print(f"\n{'='*60}")
    print(f"FILE: {tf}")
    print(f"ORIGINAL:\n{orig_body}")
    print(f"\nDECOMPILED:\n{deco_body}")
    if orig_body != deco_body:
        print(f"\nDIFF DETECTED")
