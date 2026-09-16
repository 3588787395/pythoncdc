import dis, py_compile, marshal, types

# Test 1: try-except without else
code1 = compile('''
try:
    x = 1
except BaseException:
    x = 2
x = 3
''', '<test1>', 'exec')

# Test 2: try-except with else
code2 = compile('''
try:
    x = 1
except BaseException:
    x = 2
else:
    x = 3
''', '<test2>', 'exec')

# Compare the bytecode of the top-level code
print('=== try-except without else ===')
dis.dis(code1)
print()

print('=== try-except with else ===')
dis.dis(code2)
