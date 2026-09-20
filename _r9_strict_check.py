"""严格结构化比对：非跳转部分逐位相同 + 跳转目标落到相同的指令序号。

与 testqouter.round1.base.compare_bytecode 的区别：
  后者只要没有 true_diffs 就判 matched，跳转目标差异（jump_diffs）被整体忽略。
  本脚本用「跳转目标的指令序号」做结构判定 —— 与布局无关（指令数变化不影响），
  但能抓住「跳转落到不同块」这种真正的语义差异。

用法：
  python _r9_strict_check.py <pyc> [<pyc> ...]
  或   python _r9_strict_check.py --manifest <清单文件>
"""
import bisect
import dis
import marshal
import py_compile
import sys
import types
from pathlib import Path
NOISE = {'NOP', 'CACHE', 'PRECALL', 'EXTENDED_ARG'}
JUMPISH = ('JUMP', 'POP_JUMP', 'FOR_ITER', 'SEND', 'SETUP')


def _is_jump(op):
    return op in ('FOR_ITER', 'SEND', 'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP',
                  'SETUP_FINALLY', 'SETUP_WITH', 'SETUP_CLEANUP',
                  ) or ('JUMP' in op)


def _norm_arg(i):
    op = i.opname
    if _is_jump(op):
        return None            # 跳转目标单独按序号比较
    av = i.argval
    if isinstance(av, types.CodeType):
        return ('CODE', av.co_name)
    try:
        return repr(av)
    except Exception:
        return str(type(av))


def filtered(code):
    out = []
    for i in dis.get_instructions(code):
        if i.opname in NOISE:
            continue
        out.append(i)
    return out


def load_map(path):
    with open(path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    out = {}

    def walk(c, prefix=''):
        key = prefix + c.co_name
        out.setdefault(key, c)
        for k in c.co_consts:
            if hasattr(k, 'co_name'):
                walk(k, key + '.')

    walk(code)
    return out


def compile_map(py_path):
    cfile = py_compile.compile(py_path, doraise=True, quiet=2)
    with open(cfile, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    out = {}

    def walk(c, prefix=''):
        key = prefix + c.co_name
        out.setdefault(key, c)
        for k in c.co_consts:
            if hasattr(k, 'co_name'):
                walk(k, key + '.')

    walk(code)
    return out


def strict_compare(orig, decomp):
    o = filtered(orig)
    d = filtered(decomp)
    so = [(_norm_arg(i), i.opname) if not _is_jump(i.opname) else ('<JUMP>', i.opname) for i in o]
    sd = [(_norm_arg(i), i.opname) if not _is_jump(i.opname) else ('<JUMP>', i.opname) for i in d]
    if len(so) != len(sd):
        return 'seq_len', f'orig={len(so)} decomp={len(sd)}', None
    for n, (a, b) in enumerate(zip(so, sd)):
        if a != b:
            return 'seq_diff', f'#{n}: orig={a} decomp={b}', None
    # 非跳转部分完全一致 -> 比较跳转**目标处的指令内容**。
    # 不用「目标序号」比较：两个语义相同的块（例如两块都是 LOAD_CONST None +
    # RETURN_VALUE）被编译器交换次序时序号会不同，但那不是语义差异。
    # 用目标指令内容比较，既能抓住 not_none_string（目标从 LOAD_CONST False
    # 变成 LOAD_CONST True），又不会误报等价的 return None 块交换。
    def off2instr(all_instrs, filt):
        f_offs = [i.offset for i in filt]
        m = {}
        for i in all_instrs:
            n = bisect.bisect_left(f_offs, i.offset)
            m[i.offset] = filt[n] if n < len(filt) else None
        return m

    o_off2instr = off2instr(list(dis.get_instructions(orig)), o)
    d_off2instr = off2instr(list(dis.get_instructions(decomp)), d)
    for n, (oi, di) in enumerate(zip(o, d)):
        if not _is_jump(oi.opname):
            continue
        o_t = o_off2instr.get(getattr(oi, 'argval', None))
        d_t = d_off2instr.get(getattr(di, 'argval', None))
        sig = lambda t: None if t is None else (_norm_arg(t), t.opname)
        if sig(o_t) != sig(d_t):
            return 'target_diff', (
                f'#{n} {oi.opname}: orig目标={sig(o_t)} '
                f'(off={getattr(oi,"argval",None)}) decomp目标={sig(d_t)} '
                f'(off={getattr(di,"argval",None)})'), n
    return None, 'ok', None


def check_pyc(pyc_path):
    pyc = Path(pyc_path)
    ok_py = Path(str(pyc)[:-4] + 'OK.py')
    if not ok_py.exists():
        return None
    origs = load_map(str(pyc))
    try:
        decs = compile_map(str(ok_py))
    except Exception as e:
        return {'error': f'compile failed: {e}'}
    res = {'file': str(pyc), 'functions': 0, 'ok': 0, 'bad': []}
    for name in sorted(set(origs) & set(decs)):
        res['functions'] += 1
        kind, msg, idx = strict_compare(origs[name], decs[name])
        if kind is None:
            res['ok'] += 1
        else:
            res['bad'].append((name, kind, msg))
    return res


def main():
    args = sys.argv[1:]
    if args and args[0] == '--manifest':
        paths = [l.strip() for l in Path(args[1]).read_text(encoding='utf-8').splitlines() if l.strip()]
    else:
        paths = args
    tot_f = tot_ok = 0
    for p in paths:
        r = check_pyc(p)
        if r is None:
            print(f'  [skip] {p}')
            continue
        if 'error' in r:
            print(f'  [ERR ] {p}: {r["error"]}')
            continue
        tot_f += r['functions']
        tot_ok += r['ok']
        short = p.split('site-packages/')[-1]
        print(f'  {r["ok"]:3d}/{r["functions"]:<3d}  {short}')
        for nm, kind, msg in r['bad'][:12]:
            print(f'          - {nm}: [{kind}] {msg}')
    print(f'\n合计 严格匹配 {tot_ok}/{tot_f}')


if __name__ == '__main__':
    main()
