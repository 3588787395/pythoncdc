"""Round 33 test_engineer: 严格验证 ptradeAccount 全部函数。

口径：co_code/co_consts/co_names/co_varnames 全等（同 verify_ptrade_full.py）。
用 py_compile 编译 OK.py（避免 import 依赖）。
"""
import sys, marshal, types, py_compile, inspect

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

PYC = ROOT + r'\site-packages\fly\simtradding\ptradeAccount.pyc'
OK  = ROOT + r'\site-packages\fly\simtradding\ptradeAccountOK.py'


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def walk_code(co, pf, out):
    """收集全部嵌套 code 对象，name 用点路径（含类体、模块内函数）。"""
    if co.co_name != '<module>':
        out[pf + co.co_name] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            walk_code(c, pf + co.co_name + '.', out)


def func_code_equal(a, b):
    diffs = []
    if a.co_code != b.co_code:
        # 定位第一个不同字节
        for i in range(min(len(a.co_code), len(b.co_code))):
            if a.co_code[i] != b.co_code[i]:
                diffs.append('co_code 首个差异 @byte %d: 0x%02x vs 0x%02x (len %d vs %d)' %
                             (i, a.co_code[i], b.co_code[i], len(a.co_code), len(b.co_code)))
                break
        else:
            diffs.append('co_code 长度不同: %d vs %d' % (len(a.co_code), len(b.co_code)))
    if a.co_consts != b.co_consts:
        for i in range(min(len(a.co_consts), len(b.co_consts))):
            if a.co_consts[i] != b.co_consts[i]:
                diffs.append('co_consts[%d]: %r vs %r' % (i, a.co_consts[i], b.co_consts[i]))
                break
        else:
            diffs.append('co_consts 长度不同: %d vs %d' % (len(a.co_consts), len(b.co_consts)))
    if a.co_names != b.co_names:
        diffs.append('co_names differ')
    if a.co_varnames != b.co_varnames:
        diffs.append('co_varnames differ')
    return not diffs, '; '.join(diffs)


def main():
    pyc = load_code(PYC)
    cfile = py_compile.compile(OK, doraise=True, quiet=2)
    ok = load_code(cfile)

    pyc_funcs = {}
    walk_code(pyc, '', pyc_funcs)
    ok_funcs = {}
    walk_code(ok, '', ok_funcs)

    # 去掉模块级顶层（仅保留函数与类体，便于对照；<module> 已排除）
    print('pyc code 对象数: %d, OK code 对象数: %d' % (len(pyc_funcs), len(ok_funcs)))

    matched = 0
    mismatched = []
    for name, pc in sorted(pyc_funcs.items()):
        if name not in ok_funcs:
            mismatched.append((name, 'OK 中缺失', ''))
            continue
        eq, diff = func_code_equal(pc, ok_funcs[name])
        if eq:
            matched += 1
        else:
            mismatched.append((name, diff, ''))
    for name in ok_funcs:
        if name not in pyc_funcs:
            mismatched.append((name, 'pyc 中缺失', ''))

    print('严格匹配: %d/%d' % (matched, len(pyc_funcs)))
    for name, diff, _ in mismatched:
        print('  MISMATCH: %s | %s' % (name, diff))
    return mismatched


if __name__ == '__main__':
    sys.exit(0 if not main() else 1)
