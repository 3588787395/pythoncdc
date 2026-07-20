"""Bytecode dump for R6 bugs."""
import dis

CASES = {
    'R6-09 unpack': "x, y = (a if c else b), (d if e else f)",
    'R6-18 lambda': "f = lambda: (a if c else b) + (d if e else g)",
    'R6-19 call_args': "f(a if c else b, d if e else g, h if i else j)",
    'R6-20 subscript_store': "x[a if c else b][d if e else f] = 1",
    'R6-10 listcomp': "z = [a if c else b for x in ys if x > 0]",
    'R6-12 setcomp': "z = {a if c else b for x in ys if x}",
    'R6-13 genexp': "z = list(a if c else b for x in ys if x > 0)",
    'R6-17 annotation': "x: T = a if c else b",
    'R6-06 except_handler': "try:\n    pass\nexcept E:\n    x = a if c else b",
    'R6-02 while_body': "while x:\n    y = a if c else b",
}


def show(name, code_obj, indent=0):
    pad = '  ' * indent
    print(f"{pad}=== {name} (code: {code_obj.co_name}) ===")
    dis.dis(code_obj)
    print()
    for const in code_obj.co_consts:
        if hasattr(const, 'co_code'):
            show(name + ' [nested]', const, indent + 1)


for name, src in CASES.items():
    code = compile(src, '<test>', 'exec')
    show(name, code)
