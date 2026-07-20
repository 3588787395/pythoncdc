"""Compare bytecode of bool11 (true condition chain) vs if87 (sequential if+while)."""
import dis

print("=== CASE 1: while not done and has_data(): (TRUE condition chain) ===")
source1 = """while not done and has_data():
    process()"""
code1 = compile(source1, '<test>', 'exec')
dis.dis(code1)

print()
print("=== CASE 2: if a > 0: while a > 10: (SEQUENTIAL if+while) ===")
source2 = """if a > 0:
    while a > 10:
        a = a - 1"""
code2 = compile(source2, '<test>', 'exec')
dis.dis(code2)
