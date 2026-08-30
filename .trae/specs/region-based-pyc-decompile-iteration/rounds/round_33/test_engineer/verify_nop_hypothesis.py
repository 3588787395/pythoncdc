"""Round 33: 决定性验证——在 OK.py 4 个 NOP 边界插入裸字符串，重编译对比类体。"""
import sys, marshal, types, py_compile, dis

ROOT = r"F:\Downloads\pythoncdc-main"
PYC = ROOT + r'\site-packages\fly\simtradding\ptradeAccount.pyc'
OK  = ROOT + r'\site-packages\fly\simtradding\ptradeAccountOK.py'


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def find_cls(code, name):
    return [c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name == name][0]


def instr_sig(code):
    return [(ins.offset, ins.opname, ins.argval) for ins in dis.get_instructions(code)]


def main():
    # 1) 读取 OK.py，在 4 个位置插入裸字符串（副本）
    with open(OK, 'r', encoding='utf-8') as f:
        src = f.read()
    lines = src.split('\n')
    # 边界标记：在指定 def 行之前插入裸字符串（插到前一个函数体末行之后）
    targets = [
        (143, 'login_account'),      # get_operator 之后
        (597, 'update_ptaccount_info'),
        (781, 'auth_bind_station'),
        (795, 'reconnect'),
    ]
    # 从后往前插入，避免行号偏移
    marks = ['"<round33-nop-marker-1>"', '"<round33-nop-marker-2>"',
             '"<round33-nop-marker-3>"', '"<round33-nop-marker-4>"']
    for (lineno, name), mark in sorted(zip(targets, marks), key=lambda x: -x[0][0]):
        # 找到 def {name} 的行号
        def_idx = None
        for i, ln in enumerate(lines):
            if ln.strip().startswith('def %s' % name):
                def_idx = i
                break
        # 向前找前一个 def 的函数体末行（缩进比 def 深的最后一行）
        def_indent = len(lines[def_idx]) - len(lines[def_idx].lstrip())
        insert_at = def_idx
        j = def_idx - 1
        while j >= 0:
            ln = lines[j]
            if not ln.strip():
                j -= 1
                continue
            # 类体顶层语句（缩进 == def 缩进）如 @property、前一个 def、pass 等
            ind = len(ln) - len(ln.lstrip())
            if ln.lstrip().startswith('@'):
                j -= 1
                continue
            if ind <= def_indent:
                # 这是类体顶层语句（可能是前一个 def 或装饰器）
                if ln.lstrip().startswith('def '):
                    # 前一个 def 的函数体末行 = 其 def 行之后缩进更深的最后一行
                    k = j + 1
                    last_body = None
                    while k < def_idx:
                        l2 = lines[k]
                        if l2.strip() and (len(l2) - len(l2.lstrip())) > def_indent:
                            last_body = k
                        k += 1
                    insert_at = (last_body + 1) if last_body is not None else (j + 1)
                    break
                else:
                    insert_at = j + 1
                    break
            j -= 1
        lines.insert(insert_at, '    ' + mark)
    new_src = '\n'.join(lines)
    test_py = OK[:-3] + '_marker_test.py'
    with open(test_py, 'w', encoding='utf-8') as f:
        f.write(new_src)

    # 2) 编译对比
    pyc = load_code(PYC)
    test_pyc = test_py + 'c'
    cfile = py_compile.compile(test_py, cfile=test_pyc, doraise=True, quiet=2)
    ok = load_code(cfile)
    a = find_cls(pyc, 'PtradeAccount')
    b = find_cls(ok, 'PtradeAccount')
    print('pyc 类体 co_code len:', len(a.co_code))
    print('ok  类体 co_code len:', len(b.co_code))
    print('co_code 全等:', a.co_code == b.co_code)
    if a.co_code != b.co_code:
        # 找第一个不同点
        for i in range(min(len(a.co_code), len(b.co_code))):
            if a.co_code[i] != b.co_code[i]:
                print('首个差异 @byte %d: pyc=0x%02x ok=0x%02x' % (i, a.co_code[i], b.co_code[i]))
                break
        print('长度差: %d vs %d' % (len(a.co_code), len(b.co_code)))
    else:
        print('co_consts 对比:')
        ca = [c for c in a.co_consts if not isinstance(c, types.CodeType)]
        cb = [c for c in b.co_consts if not isinstance(c, types.CodeType)]
        print('  pyc 非code consts:', [repr(x) for x in ca])
        print('  ok  非code consts:', [repr(x) for x in cb])
        print('co_names 全等:', a.co_names == b.co_names)
        print('co_varnames 全等:', a.co_varnames == b.co_varnames)


if __name__ == '__main__':
    main()
