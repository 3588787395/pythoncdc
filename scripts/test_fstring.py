import dis
code = compile("f'{x}'", '<test>', 'eval')
print("f'{x}':")
dis.dis(code)
print()
code2 = compile("f'{x!s}'", '<test>', 'eval')
print("f'{x!s}':")
dis.dis(code2)
print()
# Check with attribute
code3 = compile("f'{x.y}'", '<test>', 'eval')
print("f'{x.y}':")
dis.dis(code3)
