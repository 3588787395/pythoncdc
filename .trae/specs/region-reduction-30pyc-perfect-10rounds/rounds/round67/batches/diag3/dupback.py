# -*- coding: utf-8 -*-
"""scratch: report functions whose 3.11 bytecode contains two adjacent
unconditional backward jumps (the klinedata get_all_real_daily_kline layout)."""
import dis
import io
import marshal
import sys
import types

sys.stdout.reconfigure(encoding='utf-8')


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


path = sys.argv[1]
data = io.open(path, 'rb').read()
co = marshal.loads(data[16:])
names = set(sys.argv[2:])
for c in walk(co, []):
    if names and c.co_name not in names:
        continue
    ins = [i for i in dis.get_instructions(c) if i.opname != 'CACHE']
    core = [i for i in ins if i.opname != 'EXTENDED_ARG']
    dup = [(core[k - 1].offset, core[k].offset, core[k].argrepr)
           for k in range(1, len(core))
           if core[k].opname.startswith('JUMP_BACKWARD')
           and core[k - 1].opname.startswith('JUMP_BACKWARD')
           and core[k].argrepr == core[k - 1].argrepr]
    print('%-6s n=%-4d adj-dup-backward-jumps=%s' % (c.co_name, len(core), dup))
