import dis
src = '''match x:
    case {"key": val}:
        y = val
    case _:
        y = 0'''
code = compile(src, '<test>', 'exec')
dis.dis(code)
