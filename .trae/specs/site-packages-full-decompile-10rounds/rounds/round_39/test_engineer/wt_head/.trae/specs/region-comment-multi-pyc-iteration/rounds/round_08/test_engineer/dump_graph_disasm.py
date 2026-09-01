"""Dump graph.pyc disassembly, focused on create_full_graph."""
import dis, marshal, sys

PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/graph.pyc'
with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

print('TOP:', code.co_name, 'consts:')
for i, c in enumerate(code.co_consts):
    if hasattr(c, 'co_code'):
        print(f'  [{i}] {c.co_name}  firstlineno={c.co_firstlineno}')

# Find ModelGraph class
for c in code.co_consts:
    if hasattr(c, 'co_code') and c.co_name == 'ModelGraph':
        print('\n=== ModelGraph class consts ===')
        for i, cc in enumerate(c.co_consts):
            if hasattr(cc, 'co_code'):
                print(f'  [{i}] {cc.co_name}  firstlineno={cc.co_firstlineno}')
        # Find create_full_graph
        for cc in c.co_consts:
            if hasattr(cc, 'co_code') and cc.co_name == 'create_full_graph':
                print(f'\n=== create_full_graph disasm (firstlineno={cc.co_firstlineno}) ===')
                dis.dis(cc)
                break
        break
