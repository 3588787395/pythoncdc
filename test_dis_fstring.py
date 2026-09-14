import dis
src = '''
def fstring_ternary(direction):
    return f"{'IN' if direction == '0' else 'OUT'}END"
'''
code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_code'):
        dis.dis(c)
