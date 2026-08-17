#!/usr/bin/env python3
"""Fix LOAD_ATTR to push PUSH_NULL for method form (arg & 1 == 1) in Python 3.11+"""

filepath = 'core/cfg/ast_generator_v2.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """        # 加载属性
        elif opname == 'LOAD_ATTR':
            if self.stack:
                value = self.stack.pop()
                # [关键修复] Python 3.11+ LOAD_ATTR 参数包含标志位
                # arg & 1 == 1 表示方法形式（会压入 null 和 bound method）
                # arg & 1 == 0 表示属性访问（只压入属性值）
                is_method_form = (instr.arg & 1) == 1 if instr.arg is not None else False
                self.stack.append({
                    'type': 'Attribute',
                    'value': value,
                    'attr': instr.argval,
                    'ctx': 'Load',
                    'lineno': instr.starts_line,
                    'is_method_form': is_method_form  # 保存标志位信息
                })"""

new = """        # 加载属性
        elif opname == 'LOAD_ATTR':
            if self.stack:
                value = self.stack.pop()
                # [关键修复] Python 3.11+ LOAD_ATTR 参数包含标志位
                # arg & 1 == 1 表示方法形式（会压入 null 和 bound method）
                # arg & 1 == 0 表示属性访问（只压入属性值）
                is_method_form = (instr.arg & 1) == 1 if instr.arg is not None else False
                # Python 3.11+: method form pushes NULL before the attribute,
                # marking it as callable for CALL instruction. Without this,
                # CALL with multiple args is misidentified as decorator pattern.
                if is_method_form:
                    # Pop PUSH_NULL if the value was preceded by one (from LOAD_GLOBAL push_null)
                    # LOAD_ATTR method form replaces [NULL, obj] with [NULL, NULL, attr]
                    if self.stack and self.stack[-1].get('type') == 'PUSH_NULL':
                        pass  # Keep existing NULL, will add another below
                    self.stack.append({
                        'type': 'PUSH_NULL',
                        'lineno': instr.starts_line
                    })
                self.stack.append({
                    'type': 'Attribute',
                    'value': value,
                    'attr': instr.argval,
                    'ctx': 'Load',
                    'lineno': instr.starts_line,
                    'is_method_form': is_method_form  # 保存标志位信息
                })"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Edit applied successfully')
else:
    print('ERROR: Old string not found')
