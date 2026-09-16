from core.decompiler import Decompiler
d = Decompiler()
result = d.decompile_file(r'F:\Downloads\pythoncdc-main\site-packages\IQData\utils\common_func.pyc')
lines = result.split('\n')
in_func = False
for i, line in enumerate(lines):
    if 'def handle_exrights' in line:
        in_func = True
    if in_func:
        print(line)
        if line and not line.startswith(' ') and not line.startswith('def') and i > 0:
            break
