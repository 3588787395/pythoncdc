#!/usr/bin/env python3
"""Fix LOAD_GLOBAL to handle Python 3.11 push_null flag (arg & 1 == 1)"""

filepath = 'core/cfg/ast_generator_v2.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """        # 加载变量
        elif opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DEREF', 'LOAD_CLOSURE'):
            self.stack.append({
                'type': 'Name',
                'id': instr.argval,
                'ctx': 'Load',
                'lineno': instr.starts_line
            })"""

new = """        # 加载变量
        elif opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DEREF', 'LOAD_CLOSURE'):
            # Python 3.11+: LOAD_GLOBAL with arg & 1 == 1 pushes NULL before
            # the value (marks callable for CALL instruction). Without this,
            # CALL 0 with multiple Name funcs on stack is misidentified as
            # decorator pattern (e.g. gather(sc(), sc(), sc()) fails).
            if opname == 'LOAD_GLOBAL' and instr.arg is not None and (instr.arg & 1) == 1:
                self.stack.append({
                    'type': 'PUSH_NULL',
                    'lineno': instr.starts_line
                })
            self.stack.append({
                'type': 'Name',
                'id': instr.argval,
                'ctx': 'Load',
                'lineno': instr.starts_line
            })"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Edit applied successfully')
else:
    print('ERROR: Old string not found')
