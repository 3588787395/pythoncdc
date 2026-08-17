#!/usr/bin/env python3
"""Fix CALL handler: only treat Call on stack as decorator for __build_class__ or is_decorator,
not for regular function call arguments (e.g. gather(sc(), sc(), sc()))."""

filepath = 'core/cfg/ast_generator_v2.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                    elif func.get('type') == 'Name':
                        # [关键修复] 处理类装饰器的情况
                        # 类装饰器的特征：func是Name（如dataclass），栈上有Call节点（如__build_class__调用）
                        if self.stack and self.stack[-1].get('type') == 'Call':
                            inner_obj = self.stack.pop()
                            # 检查inner_obj是否是类定义调用
                            is_class_def = False
                            if inner_obj.get('type') == 'Call':
                                inner_func = inner_obj.get('func', {})
                                if inner_func.get('type') == 'Name' and inner_func.get('id') == '__build_class__':
                                    is_class_def = True
                            # 创建新的Call节点，将装饰器应用于内层对象
                            call_node = {
                                'type': 'Call',
                                'func': func,
                                'args': [inner_obj],
                                'kwargs': kwargs,
                                'lineno': instr.starts_line
                            }
                            if is_class_def:
                                call_node['is_class_decorator'] = True  # 标记为类装饰器调用
                            self.stack.append(call_node)"""

new = """                    elif func.get('type') == 'Name':
                        # [关键修复] 处理类装饰器的情况
                        # 类装饰器的特征：func是Name（如dataclass），栈上有Call节点（如__build_class__调用）
                        # 注意：不能将所有栈顶Call都视为装饰器参数 ——
                        # gather(sc(), sc(), sc()) 中 CALL 0 后栈顶是 Call(sc,[])，
                        # 但 sc() 是 gather 的参数，不是装饰器。
                        # 仅当 inner Call 是 __build_class__ 或带 is_decorator 标记时才视为装饰器。
                        if (self.stack and self.stack[-1].get('type') == 'Call'
                                and (self.stack[-1].get('is_decorator') is True
                                     or self.stack[-1].get('is_class_decorator') is True
                                     or (isinstance(self.stack[-1].get('func'), dict)
                                         and self.stack[-1]['func'].get('type') == 'Name'
                                         and self.stack[-1]['func'].get('id') == '__build_class__'))):
                            inner_obj = self.stack.pop()
                            # 检查inner_obj是否是类定义调用
                            is_class_def = False
                            if inner_obj.get('type') == 'Call':
                                inner_func = inner_obj.get('func', {})
                                if inner_func.get('type') == 'Name' and inner_func.get('id') == '__build_class__':
                                    is_class_def = True
                            # 创建新的Call节点，将装饰器应用于内层对象
                            call_node = {
                                'type': 'Call',
                                'func': func,
                                'args': [inner_obj],
                                'kwargs': kwargs,
                                'lineno': instr.starts_line
                            }
                            if is_class_def:
                                call_node['is_class_decorator'] = True  # 标记为类装饰器调用
                            self.stack.append(call_node)"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Edit applied successfully')
else:
    print('ERROR: Old string not found')
