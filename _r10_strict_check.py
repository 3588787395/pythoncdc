"""Round 10 判定尺子（唯一真值）。

与 _r9_strict_check.py 的区别 —— 修复了它的假阳性根源：

  _r9 用「跳转目标**处**的指令」比较落点。但 CPython 3.11 各小版本对同一份
  源码生成的「假出口」形态不同：
      旧版：POP_JUMP_FORWARD_IF_FALSE -> 114(桩: JUMP_BACKWARD -> 8)
      新版：POP_JUMP_BACKWARD_IF_FALSE -> 8
  这在 site-packages 上大量出现（and 链 genexpr 等），_r9 会把它们全部
  误判成 target_diff，制造出「36 个假 ok」的假象。

  本尺子把这种**编译器版本选择**归一化掉，只保留真正的语义判定：

  1. 过滤纯编译噪声 NOP / CACHE / PRECALL / EXTENDED_ARG（无任何语义）。
  2. 非跳转指令序列必须**逐位相同** —— 不做任何裁剪、替换、对齐。
  3. 跳转指令只比较「归一化助记符 + 追踪无条件跳转桩后的**终点指令**」。
     * 助记符按方向归一：_FORWARD/_BACKWARD/_ABSOLUTE 去掉（方向是编译器
       按目标位置选的，语义相同）；**极性不改**（IF_FALSE vs IF_TRUE 是
       真差异，必须报）。
     * 终点追踪：目标若是一条无条件 JUMP，继续追它的目标，直到非 JUMP。
       这样「F->桩->X」与「B->X」等价；而 aes_encrypt 那种「F->isinstance
       块」vs「F->AES 块」终点不同 —— 仍会被抓住。

  判据的分界（这就是「对就对错就错」的那条线）：
    * 非跳转序列不同        -> 真缺陷（源码结构被生成错了）
    * 跳转终点不同          -> 真缺陷（控制流真的走错了）
    * 只有方向/桩不同       -> 编译器版本差异，不算缺陷

用法：
  python _r10_strict_check.py <pyc> [<pyc> ...]
  python _r10_strict_check.py --manifest <清单文件>
  python _r10_strict_check.py --manifest <清单文件> --only-bad   只打印有缺陷的文件
"""
import bisect
import dis
import marshal
import py_compile
import sys
import types
from pathlib import Path

NOISE = {'NOP', 'CACHE', 'PRECALL', 'EXTENDED_ARG'}
UNCOND_JUMPS = {'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'}


def _is_jump(op):
    if op in UNCOND_JUMPS:
        return True
    return op in ('FOR_ITER', 'SEND', 'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP',
                  'SETUP_FINALLY', 'SETUP_WITH', 'SETUP_CLEANUP') or 'JUMP' in op


def _norm_jump_op(op):
    """方向归一：POP_JUMP_FORWARD_IF_FALSE -> POP_JUMP_IF_FALSE，极性保留。"""
    return op.replace('_FORWARD', '').replace('_BACKWARD', '').replace('_ABSOLUTE', '')


def _norm_arg(i):
    op = i.opname
    if _is_jump(op):
        return None                       # 落点单独比
    av = i.argval
    if isinstance(av, types.CodeType):
        return ('CODE', av.co_name)
    try:
        return repr(av)
    except Exception:
        return str(type(av))


def filtered(code):
    return [i for i in dis.get_instructions(code) if i.opname not in NOISE]


def _load_map(path):
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


def _compile_map(py_path):
    cfile = py_compile.compile(py_path, doraise=True, quiet=2)
    return _load_map(cfile)


def strict_compare(orig, decomp):
    """返回 (kind, msg, is_defect)。kind=None 表示判定为一致。"""
    o, d = filtered(orig), filtered(decomp)

    def tok(i):
        if _is_jump(i.opname):
            return ('<JUMP>', _norm_jump_op(i.opname))
        return (_norm_arg(i), i.opname)

    so, sd = [tok(i) for i in o], [tok(i) for i in d]
    if len(so) != len(sd):
        return 'seq_len', 'orig=%d decomp=%d' % (len(so), len(sd)), True
    for n, (a, b) in enumerate(zip(so, sd)):
        if a != b:
            return 'seq_diff', '#%d orig=%s decomp=%s' % (n, a, b), True

    # 非跳转部分完全一致。跳转：追踪无条件跳转桩，比较终点指令签名。
    # 落点映射必须走「过滤后」的指令表 —— 跳到 NOP/CACHE 上等价于跳到它之后
    # 第一条真正有语义的指令（编译器版本差异会在这里留下 NOP 填充）。
    def land_map(code, filt):
        f_offs = [i.offset for i in filt]
        m = {}
        for i in dis.get_instructions(code):
            n = bisect.bisect_left(f_offs, i.offset)
            m[i.offset] = filt[n] if n < len(filt) else None
        return m

    o_map = land_map(orig, o)
    d_map = land_map(decomp, d)

    def land(m, instr):
        seen = set()
        cur = m.get(getattr(instr, 'argval', None))
        while cur is not None and cur.opname in UNCOND_JUMPS:
            if cur.offset in seen:
                break
            seen.add(cur.offset)
            cur = m.get(getattr(cur, 'argval', None))
        return cur

    def sig(t):
        return None if t is None else (_norm_arg(t), t.opname)

    for n, (oi, di) in enumerate(zip(o, d)):
        if not _is_jump(oi.opname):
            continue
        a, b = sig(land(o_map, oi)), sig(land(d_map, di))
        if a != b:
            return 'target_diff', '#%d %s 终点 orig=%s decomp=%s' % (
                n, _norm_jump_op(oi.opname), a, b), True
    return None, 'ok', None


def check_pyc(pyc_path):
    pyc = Path(pyc_path)
    ok_py = Path(str(pyc)[:-4] + 'OK.py')
    if not ok_py.exists():
        return None
    origs = _load_map(str(pyc))
    try:
        decs = _compile_map(str(ok_py))
    except Exception as e:
        return {'error': 'compile failed: %s' % e}
    res = {'file': str(pyc), 'functions': 0, 'ok': 0, 'bad': []}
    for name in sorted(set(origs) & set(decs)):
        res['functions'] += 1
        kind, msg, _ = strict_compare(origs[name], decs[name])
        if kind is None:
            res['ok'] += 1
        else:
            res['bad'].append((name, kind, msg))
    return res


def main():
    args = sys.argv[1:]
    only_bad = '--only-bad' in args
    args = [a for a in args if a != '--only-bad']
    if args and args[0] == '--manifest':
        paths = [l.strip() for l in Path(args[1]).read_text(encoding='utf-8').splitlines() if l.strip()]
    else:
        paths = args
    tot_f = tot_ok = tot_files = full_files = 0
    defect_files = []
    for p in paths:
        r = check_pyc(p)
        if r is None:
            continue
        if 'error' in r:
            print('  [ERR ] %s: %s' % (p, r['error']))
            continue
        tot_files += 1
        tot_f += r['functions']
        tot_ok += r['ok']
        short = p.split('site-packages/')[-1]
        if r['ok'] == r['functions']:
            full_files += 1
            if not only_bad:
                print('  OK    %3d/%d  %s' % (r['ok'], r['functions'], short))
        else:
            defect_files.append((short, r))
            print('  DEFECT %2d/%d  %s' % (r['ok'], r['functions'], short))
            for nm, kind, msg in r['bad'][:12]:
                print('           - %s: [%s] %s' % (nm, kind, msg))
    print()
    print('文件级：全部一致 %d / %d，有真缺陷 %d' % (full_files, tot_files, len(defect_files)))
    print('函数级：严格一致 %d / %d' % (tot_ok, tot_f))


if __name__ == '__main__':
    main()
