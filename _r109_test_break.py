"""Test: does Python 3.11.7 compile break in try-for as JUMP_FORWARD or RETURN_VALUE?"""
import dis

# Simple case: break in try-for
src1 = '''
def f(data):
    try:
        for item in data:
            if item > 100:
                break
    except Exception:
        pass
'''

code1 = compile(src1, '<test>', 'exec')
for c in code1.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'f':
        print("=== break in try-for ===")
        dis.dis(c)
        print(f"Exception table: {c.co_exceptiontable}")
        break

# Case without try
src2 = '''
def g(data):
    for item in data:
        if item > 100:
            break
'''

code2 = compile(src2, '<test>', 'exec')
for c in code2.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'g':
        print("\n=== break in for (no try) ===")
        dis.dis(c)
        break
