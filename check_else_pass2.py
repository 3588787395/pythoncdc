"""Check what bytecode 'else: pass' produces inside a for loop."""
import dis

# Case 1: for + if not + else: pass
code1 = compile("""
for x in range(10):
    if not a < x <= b:
        y = 1
    else:
        pass
""", '<test>', 'exec')
print("=== for + if not + else: pass ===")
dis.dis(code1)
print()

# Case 2: without else: pass
code2 = compile("""
for x in range(10):
    if not a < x <= b:
        y = 1
""", '<test>', 'exec')
print("=== for + if not (no else) ===")
dis.dis(code2)
