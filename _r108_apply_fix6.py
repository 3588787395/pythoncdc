"""Apply fix to _filter_trailing_return_none: don't filter return None after Try"""
path = r'f:\Downloads\pythoncdc-main\core\cfg\code_generator.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = """            if _is_return_none:
                if not has_while_loop:
                    if len(nodes) == 1:
                        pass
                    elif len(nodes) >= 2:
                        _second_last = nodes[-2]
                        _is_pass = (isinstance(_second_last, ASTPass)
                                    or (isinstance(_second_last, dict) and _second_last.get('type') == 'Pass'))
                        if _is_pass:
                            pass
                        else:
                            nodes = nodes[:-1]"""

new = """            if _is_return_none:
                if not has_while_loop:
                    if len(nodes) == 1:
                        pass
                    elif len(nodes) >= 2:
                        _second_last = nodes[-2]
                        _is_pass = (isinstance(_second_last, ASTPass)
                                    or (isinstance(_second_last, dict) and _second_last.get('type') == 'Pass'))
                        # [dtc-r08 fix] 区域归约算法原则 2（每块唯一归属）：
                        # 当 return None 紧跟在 Try 节点之后时，它是
                        # try-except-else-finally 结构之后的显式返回语句，
                        # 不是隐式的函数末尾返回 None。CPython 编译器为
                        # try-except-else-finally 生成 finally 正常路径副本，
                        # 该副本以 JUMP_FORWARD 跳到 return None 块。过滤掉
                        # 这个 return None 会导致字节码不一致（缺少
                        # LOAD_CONST None + RETURN_VALUE 指令序列）。
                        _is_after_try = (isinstance(_second_last, ASTTry)
                                         or (isinstance(_second_last, dict) and _second_last.get('type') == 'Try'))
                        if _is_pass:
                            pass
                        elif _is_after_try:
                            pass
                        else:
                            nodes = nodes[:-1]"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
else:
    print("ERROR: Old text not found!")
