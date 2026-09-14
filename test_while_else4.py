import sys
sys.path.insert(0, '.')
from core.cfg import decompile

# Test: while-else with break, where the else block has actual code
# and the break target is after the else block
src = '''
def test_while_else_break(n):
    i = 0
    while i < n:
        if i == 5:
            break
        i += 1
    else:
        x = 'no break'
    return i
'''
print('=== while-else break basic ===')
try:
    result = decompile(src)
    print(result)
except Exception as e:
    print(f'ERROR: {e}')

# Test: while-else with break inside a nested structure
src2 = '''
def test_while_else_nested_break(data):
    while data:
        item = data[0]
        if item < 0:
            data.pop(0)
            continue
        if item == 0:
            break
        data.pop(0)
    else:
        data.append(-1)
    return data
'''
print()
print('=== while-else nested break ===')
try:
    result = decompile(src2)
    print(result)
except Exception as e:
    print(f'ERROR: {e}')

# Test: while-else with break where break jumps past else
src3 = '''
def test_while_else_break_jump():
    x = 0
    while x < 10:
        if x == 5:
            break
        x += 1
    else:
        x = 100
    return x
'''
print()
print('=== while-else break jump ===')
try:
    result = decompile(src3)
    print(result)
except Exception as e:
    print(f'ERROR: {e}')

# Test: for-else with break for comparison
src4 = '''
def test_for_else_break(items):
    for item in items:
        if item < 0:
            break
    else:
        items.append(0)
    return items
'''
print()
print('=== for-else break ===')
try:
    result = decompile(src4)
    print(result)
except Exception as e:
    print(f'ERROR: {e}')
