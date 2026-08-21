"""Check what bytecode 'else: pass' produces."""
import dis

# Case 1: if not cond: body else: pass
code1 = compile("""
if not a < b <= c:
    x = 1
else:
    pass
y = 2
""", '<test>', 'exec')
print("=== if not a < b <= c: x=1 else: pass ===")
dis.dis(code1)
print()

# Case 2: without else: pass
code2 = compile("""
if not a < b <= c:
    x = 1
y = 2
""", '<test>', 'exec')
print("=== if not a < b <= c: x=1 (no else) ===")
dis.dis(code2)
