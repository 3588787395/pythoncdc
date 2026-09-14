import dis

src = "def f(direction): x = f\"{'IN' if direction == '0' else 'OUT'}END\"; return x"
code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_code'):
        print(f'=== {c.co_name} ===')
        dis.dis(c)

print()
print("=== Without tail ===")
src2 = "def g(direction): x = f\"{'IN' if direction == '0' else 'OUT'}\"; return x"
code2 = compile(src2, '<test>', 'exec')
for c in code2.co_consts:
    if hasattr(c, 'co_code'):
        print(f'=== {c.co_name} ===')
        dis.dis(c)
