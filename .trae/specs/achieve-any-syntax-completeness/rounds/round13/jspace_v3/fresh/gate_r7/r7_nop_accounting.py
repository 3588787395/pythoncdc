# -*- coding: utf-8 -*-
"""NOP accounting: which source statements leave a NOP in co_code.

Feeds the T3 analysis: the protected-field differences are dominated by NOP
placement, so we need to know which statements produce one.
"""
import dis
import json

CASES = [
    ('if0_pass', 'def f():\n    if 0:\n        pass\n'),
    ('if0_raise', 'def f():\n    if 0:\n        raise ValueError("x")\n'),
    ('if0_then_for', 'def f():\n    if 0:\n        raise ValueError("x")\n    for i in range(2):\n        pass\n'),
    ('while1_break', 'def f():\n    while 1:\n        break\n'),
    ('while_true_break', 'def f():\n    while True:\n        break\n'),
    ('pass_then_return', 'def f():\n    pass\n    return None\n'),
    ('return_only', 'def f():\n    return None\n'),
    ('if_true_body', 'def f():\n    if True:\n        x = 1\n    return x\n'),
]

rows = []
for name, src in CASES:
    code = compile(src, 'x', 'exec', dont_inherit=True).co_consts[0]
    instrs = [(i.offset, i.opname, i.arg) for i in dis.get_instructions(code)]
    rows.append({'case': name, 'source': src,
                 'consts': [(type(v).__name__, repr(v)) for v in code.co_consts],
                 'names': list(code.co_names),
                 'nops': [o for o, op, _a in instrs if op == 'NOP'],
                 'n_instr': len(instrs), 'code_len': len(code.co_code)})
    print('%-18s consts=%-40s names=%-18s NOPs=%-10s len=%d'
          % (name, rows[-1]['consts'], rows[-1]['names'], rows[-1]['nops'],
             rows[-1]['code_len']))

json.dump(rows, open(r'D:\temp\opencode\cl_layout\r7\nop_accounting.json', 'w',
                     encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
