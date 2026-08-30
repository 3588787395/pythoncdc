"""Round 33: 实测 3.11.7 各种条件写法的编译形态，寻找与 pyc 匹配的源码写法。

pyc 形态（1783 行）：
  500 CONTAINS_OP 0
  502 POP_JUMP_FORWARD_IF_TRUE 43 (to 590)   # in 为真 -> 跳 590（and 短路出口）
  504 LOAD_GLOBAL len ...
  588 POP_JUMP_FORWARD_IF_FALSE 71 (to 732)  # 后半为假 -> 跳 732（elif）
"""
import dis, sys

VARIANTS = {
    # A: not x in y and z  （源码候选 1）
    'A_not_in_and': '''def f(error_info, password_re, token_re):
    if not '客户交易密码错误' in error_info and len(re.findall(password_re, error_info)) > 0:
        if error_info is not None:
            raise
        error_info = error_info.replace('错误', '错误，交易即将关闭')
    elif len(re.findall(token_re, error_info)) > 0:
        error_info = error_info + '，交易即将关闭'
    return error_info
''',
    # B: (x not in y) and z
    'B_paren_notin_and': '''def f(error_info, password_re, token_re):
    if ('客户交易密码错误' not in error_info) and len(re.findall(password_re, error_info)) > 0:
        if error_info is not None:
            raise
        error_info = error_info.replace('错误', '错误，交易即将关闭')
    elif len(re.findall(token_re, error_info)) > 0:
        error_info = error_info + '，交易即将关闭'
    return error_info
''',
    # C: not (x in y) and z
    'C_not_paren_in_and': '''def f(error_info, password_re, token_re):
    if not ('客户交易密码错误' in error_info) and len(re.findall(password_re, error_info)) > 0:
        if error_info is not None:
            raise
        error_info = error_info.replace('错误', '错误，交易即将关闭')
    elif len(re.findall(token_re, error_info)) > 0:
        error_info = error_info + '，交易即将关闭'
    return error_info
''',
    # D: 嵌套 if（当前 OK.py 写法）
    'D_nested': '''def f(error_info, password_re, token_re):
    if not '客户交易密码错误' in error_info:
        if len(re.findall(password_re, error_info)) > 0:
            if error_info is not None:
                raise
            error_info = error_info.replace('错误', '错误，交易即将关闭')
        elif len(re.findall(token_re, error_info)) > 0:
            error_info = error_info + '，交易即将关闭'
    return error_info
''',
}

for name, src in VARIANTS.items():
    ns = {}
    exec(compile(src, '<t>', 'exec'), ns)
    fn = ns['f']
    print('=' * 60)
    print('### %s' % name)
    out = []
    dis.dis(fn, file=sys.stdout)
