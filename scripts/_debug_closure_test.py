import sys, marshal, types

sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode, _filter_noise_instrs, get_bytecode_instructions

# Test with a simple code object
code = compile('''
def outer():
    x = 1
    def inner():
        return x
    return inner
''', '<test>', 'exec')

# Get inner's code object
inner_code = None
for c in code.co_consts:
    if isinstance(c, types.CodeType):
        for c2 in c.co_consts:
            if isinstance(c2, types.CodeType):
                inner_code = c2

if inner_code:
    print("inner freevars:", inner_code.co_freevars)
    print("inner cellvars:", inner_code.co_cellvars)
    
    # Test compare_bytecode with itself
    result = compare_bytecode(inner_code, inner_code)
    print("self-compare:", result)
    
    # Now test the normalization by creating a fake LOAD_GLOBAL version
    # Let's just check if the closure_vars check works
    closure_vars = set(inner_code.co_freevars) | set(inner_code.co_cellvars)
    print("closure_vars:", closure_vars)
