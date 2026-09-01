"""R23: check Python version and return None bytecode"""
import sys, dis
print(f'Python version: {sys.version}')
print(f'RETURN_CONST opcode: {dis.opmap.get("RETURN_CONST", "NOT FOUND")}')
print(f'LOAD_CONST opcode: {dis.opmap.get("LOAD_CONST", "NOT FOUND")}')
print(f'RETURN_VALUE opcode: {dis.opmap.get("RETURN_VALUE", "NOT FOUND")}')

# Test: compile a function with implicit return None
src = """
def f():
    pass
"""
code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_code'):
        print(f'\nImplicit return None bytecode:')
        dis.dis(c)
        print(f'co_code bytes: {c.co_code.hex()}')
        print(f'co_code len: {len(c.co_code)}')
