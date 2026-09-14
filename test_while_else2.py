import sys
sys.path.insert(0, '.')
from core.cfg import decompile

# while-else with break that goes to after-while
# The break should skip the else block
src1 = '''
def while_else_break2(n):
    i = 0
    while i < n:
        if i == 5:
            break
        i += 1
    else:
        result = 'no break'
    result = 'done'
    return result
'''
print('=== while-else break 2 ===')
try:
    result = decompile(src1)
    print(result)
except Exception as e:
    print(f'ERROR: {e}')

# while-else where break is inside nested if
src2 = '''
def while_else_nested_break(items):
    while items:
        item = items.pop()
        if item == 'stop':
            break
    else:
        items.append('done')
    return items
'''
print()
print('=== while-else nested break ===')
try:
    result = decompile(src2)
    print(result)
except Exception as e:
    print(f'ERROR: {e}')

# The actual problem from the task description:
# while-else with break - else block is misunderstood as while-out code
# and break is incorrectly replaced with return None or continue
src3 = '''
def while_else_break_issue(data):
    found = None
    while data:
        item = data.pop()
        if item > 0:
            found = item
            break
    else:
        found = -1
    return found
'''
print()
print('=== while-else break issue ===')
try:
    result = decompile(src3)
    print(result)
except Exception as e:
    print(f'ERROR: {e}')
