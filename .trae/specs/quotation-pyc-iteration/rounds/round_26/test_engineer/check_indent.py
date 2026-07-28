"""R26: 精确对比get_option_info源码编译后的字节码结构"""
import sys
import types
import dis
import ast

sys.path.insert(0, '/workspace')

with open('/tmp/r26_decompiled.py') as f:
    src = f.read()

tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'get_option_info':
        start = node.lineno
        end = node.end_lineno
        lines = src.split('\n')[start-1:end]
        print("=== get_option_info source (lines {}-{}) ===".format(start, end))
        for i, line in enumerate(lines):
            indent = len(line) - len(line.lstrip())
            print(f"  {start+i:>4} [{indent:>2}sp] {line}")
        break

# Now compile and check bytecode around 720-740
sco = compile(src, '<x>', 'exec')
def find_co(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find_co(c, name)
            if r:
                return r
    return None

co = find_co(sco, 'get_option_info')
print("\n=== SRC bytecode 720-760 ===")
for ins in dis.get_instructions(co):
    if ins.opname in ('EXTENDED_ARG', 'CACHE'):
        continue
    if 720 <= ins.offset <= 760:
        print(f"  {ins.offset:>4} {ins.opname:<35} {ins.argrepr}")
