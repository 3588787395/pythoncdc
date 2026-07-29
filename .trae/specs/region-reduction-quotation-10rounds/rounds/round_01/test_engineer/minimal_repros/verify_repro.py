"""minimal_repros 验证辅助：编译 repro.py → 反编译 → 比较字节码。

用法：
    python verify_repro.py <repro.py>
输出：matched / total / first_diff（用于确认 repro 复现了缺陷）。
"""
import sys
import os
import py_compile
import tempfile
import types
import dis

sys.path.insert(0, '/workspace')

SKIP_OPS = ('EXTENDED_ARG', 'CACHE')


def get_instr_list(co):
    return [(i.offset, i.opname, i.argval) for i in dis.get_instructions(co)
            if i.opname not in SKIP_OPS]


def instr_equal(a, b):
    if a[1] != b[1]:
        return False
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        ia, ib = get_instr_list(av_a), get_instr_list(av_b)
        if len(ia) != len(ib):
            return False
        return all(instr_equal(x, y) for x, y in zip(ia, ib))
    if isinstance(av_a, types.CodeType) or isinstance(av_b, types.CodeType):
        return False
    return av_a == av_b


def walk_code(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
    sink[name] = co
    sub = '' if name == '<module>' else name + '.'
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            walk_code(c, sub, sink)
    return sink


def verify(repro_py):
    with open(repro_py, 'r', encoding='utf-8') as f:
        orig_src = f.read()
    with tempfile.TemporaryDirectory() as d:
        pyc = os.path.join(d, 'repro.pyc')
        py_compile.compile(repro_py, pyc, doraise=True)

        from pycdc import decompile_pyc
        src = decompile_pyc(pyc, use_cfg=False, cfg_hybrid=False)

        try:
            new_code = compile(src, '<decompiled>', 'exec')
            compile_ok = True
        except SyntaxError as e:
            return {'compile_ok': False, 'err': str(e), 'src_snippet': src[:500]}

        orig_code = compile(orig_src, repro_py, 'exec')
        orig_cos = walk_code(orig_code)
        new_cos = walk_code(new_code)

        matched = 0
        total = len(orig_cos)
        details = []
        for name, oc in orig_cos.items():
            if name not in new_cos:
                details.append((name, 'missing', None))
                continue
            oa, na = get_instr_list(oc), get_instr_list(new_cos[name])
            if len(oa) != len(na):
                details.append((name, 'len_diff', f'orig={len(oa)} new={len(na)}'))
                continue
            fd = -1
            for i, (x, y) in enumerate(zip(oa, na)):
                if not instr_equal(x, y):
                    fd = i
                    break
            if fd < 0:
                matched += 1
                details.append((name, 'match', None))
            else:
                details.append((name, 'instr_diff', f'idx={fd} orig={oa[fd]} new={na[fd]}'))

        return {
            'compile_ok': True,
            'total': total,
            'matched': matched,
            'mismatched': total - matched,
            'success_rate': round(matched / total * 100, 2) if total else 0,
            'details': details,
            'src': src,
        }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: verify_repro.py <repro.py>')
        sys.exit(2)
    r = verify(sys.argv[1])
    print(f"file: {sys.argv[1]}")
    print(f"compile_ok: {r.get('compile_ok')}")
    if r.get('compile_ok'):
        print(f"total={r['total']} matched={r['matched']} mismatched={r['mismatched']} success_rate={r['success_rate']}%")
        for name, status, extra in r['details']:
            tag = 'OK ' if status == 'match' else 'BAD'
            print(f"  [{tag}] {name}: {status} {extra or ''}")
    else:
        print(f"compile FAILED: {r.get('err')}")
        print(f"src snippet:\n{r.get('src_snippet')}")
