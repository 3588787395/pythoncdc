"""批量验证所有 minimal_repros，输出 repro_verify_summary.txt。

对每个 repro_NN_*.py：
  1. py_compile 通过性
  2. decompile_pyc 反编译
  3. 编译反编译产物
  4. 字节码递归比较
  5. 记录 matched / total / success_rate / 首处不一致
"""
import sys
import os
import glob
import py_compile
import tempfile
import types
import dis
import json

sys.path.insert(0, '/workspace')

REPRO_DIR = os.path.dirname(os.path.abspath(__file__))
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


def verify_one(repro_py):
    result = {'file': os.path.basename(repro_py), 'py_compile_ok': False,
              'decompile_ok': False, 'compile_ok': False,
              'total': 0, 'matched': 0, 'mismatched': 0, 'success_rate': 0.0,
              'first_mismatch': None, 'reproduces_defect': False}
    # 1. py_compile
    try:
        with tempfile.TemporaryDirectory() as d:
            pyc = os.path.join(d, 'r.pyc')
            py_compile.compile(repro_py, pyc, doraise=True)
        result['py_compile_ok'] = True
    except Exception as e:
        result['py_compile_err'] = str(e)
        return result

    with open(repro_py, 'r', encoding='utf-8') as f:
        orig_src = f.read()
    with tempfile.TemporaryDirectory() as d:
        pyc = os.path.join(d, 'r.pyc')
        py_compile.compile(repro_py, pyc, doraise=True)
        # 2. decompile
        try:
            from pycdc import decompile_pyc
            src = decompile_pyc(pyc, use_cfg=False, cfg_hybrid=False)
            result['decompile_ok'] = True
        except Exception as e:
            result['decompile_err'] = str(e)
            return result
        # 3. compile decompiled
        try:
            new_code = compile(src, '<d>', 'exec')
            result['compile_ok'] = True
        except SyntaxError as e:
            result['compile_err'] = str(e)
            return result
        # 4. compare
        orig_cos = walk_code(compile(orig_src, repro_py, 'exec'))
        new_cos = walk_code(new_code)
        matched = 0
        first_mm = None
        for name, oc in orig_cos.items():
            if name not in new_cos:
                if first_mm is None and name != '<module>':
                    first_mm = f"{name}: missing"
                continue
            oa, na = get_instr_list(oc), get_instr_list(new_cos[name])
            if len(oa) != len(na):
                if first_mm is None and name != '<module>':
                    first_mm = f"{name}: len_diff orig={len(oa)} new={len(na)}"
                continue
            fd = -1
            for i, (x, y) in enumerate(zip(oa, na)):
                if not instr_equal(x, y):
                    fd = i
                    break
            if fd < 0:
                matched += 1
            elif first_mm is None and name != '<module>':
                first_mm = f"{name}: instr_diff idx={fd} orig={oa[fd]} new={na[fd]}"
        total = len(orig_cos)
        mismatched = total - matched
        result['total'] = total
        result['matched'] = matched
        result['mismatched'] = mismatched
        result['success_rate'] = round(matched / total * 100, 2) if total else 0
        result['first_mismatch'] = first_mm
        # 排除 <module> 的 code-object argval 差异（那是函数内部差异的副作用）
        # 只要任一非 <module> 函数不一致，即视为复现缺陷
        result['reproduces_defect'] = mismatched > 0 and any(
            name != '<module>' and (
                name not in new_cos or
                len(get_instr_list(oc)) != len(get_instr_list(new_cos[name])) or
                any(not instr_equal(x, y) for x, y in zip(
                    get_instr_list(oc), get_instr_list(new_cos[name])))
            )
            for name, oc in orig_cos.items()
        )
    return result


def main():
    repros = sorted(glob.glob(os.path.join(REPRO_DIR, 'repro_*.py')))
    lines = []
    lines.append("=" * 80)
    lines.append("Round 1 minimal_repros 验证摘要")
    lines.append("=" * 80)
    lines.append(f"repro 目录: {REPRO_DIR}")
    lines.append(f"repro 总数: {len(repros)}")
    lines.append("")
    lines.append(f"{'文件':<50} {'compile':<8} {'total':>6} {'match':>6} {'bad':>5} {'rate%':>7} {'复现':>5}")
    lines.append("-" * 95)

    summary = []
    reproduced = 0
    for rp in repros:
        r = verify_one(rp)
        summary.append(r)
        if r['reproduces_defect']:
            reproduced += 1
        comp = 'OK' if r.get('compile_ok') else 'FAIL'
        lines.append(f"{r['file']:<50} {comp:<8} {r['total']:>6} {r['matched']:>6} "
                     f"{r['mismatched']:>5} {r['success_rate']:>7.2f} "
                     f"{'是' if r['reproduces_defect'] else '否':>5}")

    lines.append("-" * 95)
    lines.append(f"复现缺陷的 repro 数: {reproduced} / {len(repros)}")
    lines.append("")
    lines.append("=== 各 repro 首处不一致详情 ===")
    for r in summary:
        lines.append(f"\n[{r['file']}]")
        lines.append(f"  py_compile_ok: {r['py_compile_ok']}")
        lines.append(f"  decompile_ok: {r.get('decompile_ok')}")
        lines.append(f"  compile_ok:   {r.get('compile_ok')}")
        if r.get('compile_ok'):
            lines.append(f"  total={r['total']} matched={r['matched']} mismatched={r['mismatched']} rate={r['success_rate']}%")
        lines.append(f"  reproduces_defect: {r['reproduces_defect']}")
        if r.get('first_mismatch'):
            lines.append(f"  first_mismatch: {r['first_mismatch']}")
        if r.get('py_compile_err'):
            lines.append(f"  py_compile_err: {r['py_compile_err']}")
        if r.get('decompile_err'):
            lines.append(f"  decompile_err: {r['decompile_err']}")
        if r.get('compile_err'):
            lines.append(f"  compile_err: {r['compile_err']}")

    out = "\n".join(lines) + "\n"
    out_path = os.path.join(REPRO_DIR, 'repro_verify_summary.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f"[verify_summary] wrote {out_path}")
    print(f"[verify_summary] reproduced {reproduced} / {len(repros)}")
    # 也写一份 json
    with open(os.path.join(REPRO_DIR, 'repro_verify_summary.json'), 'w', encoding='utf-8') as f:
        json.dump({'reproduced': reproduced, 'total': len(repros), 'results': summary}, f, indent=2, default=str)
    print(f"[verify_summary] wrote repro_verify_summary.json")


if __name__ == '__main__':
    main()
