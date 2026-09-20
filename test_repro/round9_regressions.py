"""Round 9 回归用例：三处真实反编译缺陷的最小复现与自检。

每个用例的做法是「源码 -> 反编译 -> 重编译 -> 字节码比对」。

比对用两把尺子：
  1. 官方口径 testqouter.round1.base.compare_bytecode（没有 true_diffs 即
     matched，跳转目标偏移差异只记入 jump_diffs、不参与判定）。
  2. 严格口径 strict_compare（本文件内）：非跳转指令逐位相同，且每条跳转
     的**落点指令内容**与原始一致。它能把「指令序列逐位相同、只是跳到别的
     块」这类语义反转识别出来——这正是官方口径漏判（假 ok）的一类。

  例：`if p is None or p.strip() == ''` 被反演成 `if p is not None and
  p.strip() == ''` 时，两版指令序列逐位相同，只有 4 号指令的跳转目标从
  `LOAD_CONST False` 块变成 `LOAD_CONST True` 块。官方口径判 matched，
  严格口径判不一致。

用例：
  A  or 短路首段为 None 检查（Round 9 已修）
     旧产物首个操作数被取反、or 变 and，None 入参返回值由 False 变 True。
     根因：region_analyzer._normalize_none_check_op_types 在「无其他链成员
     共享 then_body 目标」时把 op 回退成 'and'。

  B  列表推导式值被丢弃 + 分支内裸 return（Round 9 已修）
     `if ev in h: [g(x) for x in h[ev]]; return`
     旧产物：`return [g(x) for x in h[ev]]` + 伪造 `else: return None`
     + 结构外重复一条推导式（else 分支走到时对不存在的键下标 -> KeyError）。
     根因：comprehension_generator.try_generate_comprehension_assign 只看
     块末是否为 RETURN_VALUE 就认定推导式是返回值，无视了其后的 POP_TOP。

  C  语句级 if 被外层条件链吞并（Round 9 定位，未修）
     `if a is not None and b is not None:` 体内第一条语句是
     `if isinstance(a, str): a = a.encode()`，且该 if 之后还有语句
     （第二个 isinstance 检查 + 赋值 + 尾随语句）时，内层 if 被吸进外层
     BoolOp 链，其失败目标（指向体内后续语句）被当成链的 exit，于是
     `isinstance(a, str)` 为假时直接跳到 else —— 真实受害者
     IQCommon/util/crypto_utils.aes_encrypt：传入 bytes 形式的密钥时会
     静默改用模块默认密钥加密。此用例当前标记为已知失败（严格口径可检出，
     官方口径判 matched）。
"""
import bisect
import dis
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cfg import build_cfg                                    # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator      # noqa: E402
from core.cfg.ast_converter import CFGASTConverter                # noqa: E402
from core.cfg.code_generator import CFGCodeGenerator              # noqa: E402
from testqouter.round1.base import compare_bytecode               # noqa: E402

_NOISE = {'NOP', 'CACHE', 'PRECALL', 'EXTENDED_ARG'}


def decompile(src):
    code = compile(src, '<t>', 'exec')
    cfg = build_cfg(code)
    gen = RegionASTGenerator(cfg, top_level_code=code)
    return CFGCodeGenerator().generate(CFGASTConverter().convert(gen.generate()))


def _is_jump(op):
    return ('JUMP' in op or op in ('FOR_ITER', 'SEND', 'SETUP_FINALLY',
                                   'SETUP_WITH', 'SETUP_CLEANUP'))


def _sig(instr):
    if instr is None:
        return None
    av = instr.argval
    if isinstance(av, types.CodeType):
        return ('CODE', av.co_name)
    return (instr.opname, repr(av))


def _filtered(code):
    return [i for i in dis.get_instructions(code) if i.opname not in _NOISE]


def _offset_to_instr(code, filt):
    f_offs = [i.offset for i in filt]
    out = {}
    for i in dis.get_instructions(code):
        n = bisect.bisect_left(f_offs, i.offset)
        out[i.offset] = filt[n] if n < len(filt) else None
    return out


def strict_compare(orig, dec):
    """逐层比对 code 对象（含嵌套函数/推导式），返回 None 表示一致。"""
    o_map, d_map = {}, {}

    def walk(code, prefix, store):
        store.setdefault(prefix + code.co_name, code)
        for k in code.co_consts:
            if hasattr(k, 'co_consts'):
                walk(k, prefix + code.co_name + '.', store)

    walk(orig, '', o_map)
    walk(dec, '', d_map)
    for name in sorted(set(o_map) | set(d_map)):
        a, b = o_map.get(name), d_map.get(name)
        if a is None or b is None:
            return '%s: 一侧缺失（orig=%s decomp=%s）' % (name, a is not None, b is not None)
        diff = _compare_one(a, b)
        if diff is not None:
            return '%s: %s' % (name, diff)
    return None


def _compare_one(orig, dec):
    o, d = _filtered(orig), _filtered(dec)
    if len(o) != len(d):
        return 'seq_len orig=%d decomp=%d' % (len(o), len(d))
    for n, (a, b) in enumerate(zip(o, d)):
        if _is_jump(a.opname) or _is_jump(b.opname):
            if a.opname != b.opname:
                return '#%d orig=%s decomp=%s' % (n, a.opname, b.opname)
            continue
        if _sig(a) != _sig(b):
            return '#%d orig=%s decomp=%s' % (n, _sig(a), _sig(b))
    o_map = _offset_to_instr(orig, o)
    d_map = _offset_to_instr(dec, d)
    for n, (a, b) in enumerate(zip(o, d)):
        if not _is_jump(a.opname):
            continue
        ta = o_map.get(getattr(a, 'argval', None))
        tb = d_map.get(getattr(b, 'argval', None))
        if _sig(ta) != _sig(tb):
            return '#%d %s 落点 orig=%s decomp=%s' % (n, a.opname, _sig(ta), _sig(tb))
    return None


CASES = [
    ('A or 短路首段为 None 检查', False, '''
def f(p):
    if p is None or p.strip() == '':
        return False
    return True
'''),
    ('B 推导式值丢弃 + 分支内裸 return', False, '''
def f(ev, h, g):
    if ev in h:
        [g(x) for x in h[ev]]
        return
    return
'''),
    ('C 语句级 if 被外层条件链吞并', True, '''
def f(a, b):
    if a is not None and b is not None:
        if isinstance(a, str):
            a = a.encode()
        if isinstance(b, str):
            b = b.encode()
        c = make(a, b)
    else:
        c = make(DEF_A, DEF_B)
    return c
'''),
]


def main():
    bad = 0
    for name, known_fail, src in CASES:
        out = decompile(src)
        orig_code = compile(src, '<orig>', 'exec')
        dec_code = compile(out, '<dec>', 'exec')
        official = bool(compare_bytecode(orig_code, dec_code).get('match'))
        strict = strict_compare(orig_code, dec_code)
        if known_fail:
            tag = 'FIXED' if strict is None else 'KNOWN-FAIL'
        else:
            tag = 'PASS' if strict is None else 'FAIL'
            if strict is not None:
                bad += 1
        print('[%s] %s' % (tag, name))
        print('       官方口径=%-8s 严格口径=%s'
              % ('matched' if official else 'mismatch',
                 '一致' if strict is None else '不一致'))
        if strict is not None and not known_fail:
            print('--- 产物 ---')
            print(out)
            print('--- 严格差异 ---')
            print('   ', strict)
    print('\n失败用例数（不含已知未修）: %d' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
