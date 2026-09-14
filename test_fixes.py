import sys
sys.path.insert(0, '.')
from core.cfg import decompile

# Test 1: while-else with break
src1 = '''
def while_else_break(n):
    i = 0
    while i < n:
        if i == 5:
            break
        i += 1
    else:
        print('no break')
    print('after while')
'''
print('=== Test 1: while-else with break ===')
try:
    result = decompile(src1)
    print(result)
except Exception as e:
    print(f'ERROR: {e}')

# Test 2: while-else no break
src2 = '''
def while_else_no_break(n):
    i = 0
    while i < n:
        i += 1
    else:
        print('no break')
    print('after while')
'''
print()
print('=== Test 2: while-else no break ===')
try:
    result = decompile(src2)
    print(result)
except Exception as e:
    print(f'ERROR: {e}')

# Test 3: f-string with ternary - use compile to avoid quoting issues
import types
src3 = "def fstring_ternary(direction):\n x = f\"{'IN' if direction == '0' else 'OUT'}END\"\n return x\n"
print()
print('=== Test 3: f-string ternary ===')
try:
    result = decompile(src3)
    print(result)
except Exception as e:
    print(f'ERROR: {e}')

# Test 3b: f-string with ternary - alternative
src3b = '''def fstring_ternary_alt(direction):
    x = f"{'yes' if direction else 'no'}tail"
    return x
'''
print()
print('=== Test 3b: f-string ternary alt ===')
try:
    result = decompile(src3b)
    print(result)
except Exception as e:
    print(f'ERROR: {e}')

# Test 4: while-else with break and nested code
src4 = '''
def while_else_break2(items):
    for item in items:
        while item > 0:
            if item == 3:
                break
            item -= 1
        else:
            print('completed')
'''
print()
print('=== Test 4: while-else break2 ===')
try:
    result = decompile(src4)
    print(result)
except Exception as e:
    print(f'ERROR: {e}')
