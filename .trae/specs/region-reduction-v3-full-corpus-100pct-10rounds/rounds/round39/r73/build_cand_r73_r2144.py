import re
"""Build the [R21-44] candidate: lift `X; POP_JUMP_IF_FALSE -> B` + chained-compare and-leg A +
or-tail B into ONE BoolOp test `X and A or B`, instead of the nested `if X: if A or B: arm`
the region decomposition currently renders (which the elif collector then folds, leaving a
spurious arm-tail JUMP_FORWARD).

Base = the re-anchored P1+P2 file (work/ANCHORED_r38_P1P2_on_g38.py, sha16 cf5868e68208adf6):
loss (B) is only visible under that residual (RECLAIM_R21-38B_r67a.md 1).

Byte-level patch on split(b'\\r\\n') with unique-anchor asserts + py_compile (rule 7).
Halves, separately ablatable:
  H1 = census probe `_r2144_census_note`      (--no-probe drops it; must be byte-inert)
  H2 = criterion `_r2144_and_leg_before_or_tail` + its call site
  --merge-none flips the merge convention (region.merge_block = None instead of = E)

usage: python -X utf8 work/build_cand_r73_r2144.py [--no-probe] [--merge-none] [--out PATH]
"""
import hashlib
import py_compile
import sys

BASE = 'D:/Temp/r73/work/ANCHORED_r38_P1P2_on_g38.py'
OUT = 'D:/Temp/r73/work/CANDIDATE_r73_r2144.py'
ARGS = sys.argv[1:]
if '--out' in ARGS:
    OUT = ARGS[ARGS.index('--out') + 1]
NO_PROBE = '--no-probe' in ARGS
MERGE_NONE = '--merge-none' in ARGS
if '--base' in ARGS:
    BASE = ARGS[ARGS.index('--base') + 1]

PROBE = '''def _r2144_census_note(stage, detail=''):
    """[R21-44 普查探针] 仅当环境变量 R2144_CENSUS 指向路径时追加一行计数，否则立即返回。

    探针不参与任何判定：判据主体不用它的返回值改变控制流（FIRE 行写在全部合取成立之后、
    真正改区域之前）。开/关探针必须产物逐字节一致，否则普查读数作废（规则 2）。
    """
    import os as _os_r2144
    _p = _os_r2144.environ.get('R2144_CENSUS')
    if not _p:
        return
    try:
        with open(_p, 'a', encoding='utf-8') as _f_r2144:
            _f_r2144.write('%s %s\\n' % (stage, detail))
    except Exception:
        pass


'''

METHOD = '''    def _r2144_and_leg_before_or_tail(self, region, cond_block, expr):
        """[R21-44] 正极性单腿 if 的"汇合块"实为短路 or 尾腿 ⇒ 并成一条 `X and A or B` 测试。

        **结构事实** CPython 3.11 把 `(X and A) or B` 编译成唯一布局（3.11.7 实测两形对照：
        flat 与原始字节码逐条一致；nested 的两条腿假出口被移到臂后、且臂尾多一条
        JUMP_FORWARD）：
            X;  POP_JUMP_IF_FALSE -> B      # and 的假出口线程到 or 的下一操作数
            A(链式比较); 真 -> arm / 假 -> 清理块 -> B
            B;  POP_JUMP_IF_FALSE -> after / 真 -> fallthrough arm
            arm 末尾**没有 JUMP_FORWARD**，直接 fallthrough 进 after。
        区域归约把 B 误记为本区域的 merge_block、把 A 的链式比较块算进本区域 then_blocks，
        于是发射 `if X: if A or B: arm`，随后 elif 采集器把它并成 if/elif —— 本单元
        realtime_event_source::clock_worker 有四处同形站点（条件块 @6322/@6496/@7164/@7582），
        实测留下 2 条伪 JUMP_FORWARD 与 12 处 landing 差。

        **判据（全部为区域数据 + 前驱后继结构；不含函数名/文件名字面量、绝对偏移、计数阈值）**
          ① 本区域 else_blocks 为空，merge_block M 存在；
          ② M 的末跳是前向条件跳转（非 NONE_CHECK 同族）—— 真正的汇合点不会再测东西；
          ③ M 的两个条件后继里恰有一个是本区域 then 块 T：M **流向臂体**，而 merge 只可能被
             臂体流向，方向不可能反，故 M 不是 merge 而是 or 尾腿；
          ④ 条件块 X 末跳为 IF_FALSE 且目标恰为 M 起点；X 的另一条件后继 A 也在 then_blocks，
             且 A 是某子 IfRegion 的 condition_block，该子区域带 chained_compare_ops+blocks
             （A 是一条可整体重建的链式比较 and 腿）；
          ⑤ 腿内部自洽：I = [A 起点, T 起点) 内的本区域块，其每个条件后继仍落在 I ∪ {T, M, E}；
          ⑥ 臂体确实落回 E（M 的假出口）—— 原源码里紧跟其后的那条语句；
          ⑦ X / 腿块 / M 的指令中没有任何 STORE_*：三条腿都是纯表达式，杜绝把语句吞进测试。
        **保守性** 七条同时成立才动；任一不成立立即返回 None，调用方走既有路径，产物逐字节不变。
        **可证性而非偏好** ②+③+④ 合起来唯一确定 `(X and A) or B` 的编译布局（and 假出口线程
        给 or 尾腿、尾腿真出口 fallthrough 进臂），与 3.11.7 compile() 实测骨架一致。
        **归约** 测试 = BoolOp(or, [BoolOp(and, [X, A]), B])；臂重声明为 then=[T]、
        merge=E、else 空 ⇒ 既有 elif 采集器再也找不到可折的 merge，臂尾伪跳转随之消失；
        I 内所有块与 M 登记 generated，避免第二个发射者重发腿块。
        """
        def _rej(_why):
            _r2144_census_note('R2144REJ', '%s cond=@%s' % (
                _why, getattr(cond_block, 'start_offset', '?')))
            return None
        try:
            _m = getattr(region, 'merge_block', None)
            if _m is None or getattr(region, 'else_blocks', None):
                return _rej('M0')
            if not (getattr(region, 'condition_block', None) is cond_block):
                return _rej('M1')
            _then_offs = {b.start_offset for b in (getattr(region, 'then_blocks', None) or [])
                          if b is not None and b.instructions}
            _x_last = cond_block.get_last_instruction()
            if (_x_last is None or getattr(_x_last, 'argval', None) is None
                    or 'IF_FALSE' not in _x_last.opname
                    or _x_last.opname in NONE_CHECK_OPS):
                return _rej('M2')
            if _x_last.argval != _m.start_offset:
                return _rej('M3')
            _x_cs = [s for s in (cond_block.conditional_successors
                                 or cond_block.successors or [])
                     if s is not None and s.instructions]
            if len(_x_cs) != 2:
                return _rej('X0')
            _a = _x_cs[0] if _x_cs[1] is _m else (_x_cs[1] if _x_cs[0] is _m else None)
            if _a is None or _a.start_offset not in _then_offs:
                return _rej('X1')
            _m_last = _m.get_last_instruction()
            if (_m_last is None or getattr(_m_last, 'argval', None) is None
                    or _m_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS
                    or _m_last.opname in NONE_CHECK_OPS):
                return _rej('X2')
            _e_off = _m_last.argval
            _e = self.cfg.get_block_by_offset(_e_off)
            if _e is None or _e is _m:
                return _rej('T0')
            _m_cs = [s for s in (_m.conditional_successors or _m.successors or [])
                     if s is not None and s.instructions and s is not _e]
            if len(_m_cs) != 1:
                return _rej('XA')
            _t = _m_cs[0]
            if _t is _m or _t.start_offset not in _then_offs:
                return _rej('ML')
            _fr = None
            for _r in self.region_analyzer.regions:
                if isinstance(_r, IfRegion) and getattr(_r, 'condition_block', None) is _a:
                    _fr = _r
                    break
            if _fr is None:
                return _rej('E0')
            _cc = list(getattr(_fr, 'chained_compare_blocks', None) or [])
            if not _cc or not (getattr(_fr, 'chained_compare_ops', None) or []):
                return _rej('E1')
            _inner = [b for b in sorted(_then_offs) if _a.start_offset <= b < _t.start_offset]
            if _a.start_offset not in _inner:
                return _rej('FR')
            _inner_set = set(_inner) | {b.start_offset for b in _cc if b.instructions}
            _all_leg_blocks = [b for b in (getattr(region, 'blocks', None) or [])
                                if b is not None and b.instructions
                                and b.start_offset in _inner_set]
            _forbidden = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_ATTR',
                          'STORE_SUBSCR', 'STORE_DEREF')
            for _b in _all_leg_blocks + [_m, cond_block]:
                for _i in _b.instructions:
                    if _i.opname in _forbidden:
                        return _rej('CC')
                for _s in (_b.conditional_successors or _b.successors or []):
                    if _s is None or not _s.instructions:
                        continue
                    if (_s.start_offset not in _inner_set and _s is not _t
                            and _s is not _m and _s is not _e):
                        return _rej('IN')
            _a_expr = self._build_chained_compare_from_region_data(_fr)
            if _a_expr is None:
                return _rej('LB')
            _m_pure = [i for i in _m.instructions
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
                       and i is not _m_last]
            _b_expr = self.expr_reconstructor.reconstruct(_m_pure) if _m_pure else None
            if _b_expr is None:
                return _rej('BE')
            # ⑥ 臂体确实落回 E：在 [T 起点, E 起点) 区间内做后继闭包，能到 E 即证明
            # 「臂之后紧跟的就是 E」这条语句顺序事实；到不了就不动（保守）。
            _seen = set()
            _front = [_t]
            _arm_hits_e = False
            while _front and not _arm_hits_e:
                _fb = _front.pop()
                if id(_fb) in _seen:
                    continue
                _seen.add(id(_fb))
                for _fs in (_fb.conditional_successors or _fb.successors or []):
                    if _fs is None or not _fs.instructions:
                        continue
                    if _fs is _e:
                        _arm_hits_e = True
                        break
                    if _t.start_offset <= _fs.start_offset < _e.start_offset and _fs is not _m:
                        _front.append(_fs)
            if not _arm_hits_e:
                return _rej('AE')
            # 臂体块表取自「被误判成 merge 的那条尾腿自己的 then」：M 实为本测试的尾腿，
            # 它的 then 就是 and/or 全部成立后要执行的臂体（区域数据，非偏移猜测）；只保留
            # 落在 [T, E) 臂跨内的块，且必须含 T，否则不动（保守）。
            # ⑧ 臂体正常流里不得有「无主测试块」：沿后继闭包走一遍臂，凡以条件跳转收尾
            # 的块都必须是某 IfRegion 的 condition_block，否则没人派发它。异常处理器入口
            # （首指令 PUSH_EXC_INFO）由 try 机制而非区域归属派发，按 opcode 类别排除。
            # realtime_event_source::clock_worker @7164 站点实测臂跨里的 @7248 只是
            # inline_boolop_chains 成员、无任何区域认领 ⇒ 该站点不动（保守）。
            _cond_ids = {id(getattr(_r0, 'condition_block', None))
                         for _r0 in self.region_analyzer.regions
                         if getattr(_r0, 'condition_block', None) is not None}
            _nseen = set()
            _nfront = [_t]
            while _nfront:
                _nb = _nfront.pop()
                if _nb is None or id(_nb) in _nseen or not _nb.instructions:
                    continue
                _nseen.add(id(_nb))
                _nfirst = _nb.instructions[0]
                if _nfirst.opname == 'PUSH_EXC_INFO':
                    continue
                _nlast = _nb.get_last_instruction()
                if (_nlast is not None
                        and _nlast.opname
                        in (FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS)
                        and _nlast.opname not in NONE_CHECK_OPS
                        and id(_nb) not in _cond_ids):
                    return _rej('ORPHAN')
                _nsucc = list(_nb.conditional_successors or [])
                if not _nsucc:
                    _nsucc = list(_nb.successors or [])
                for _ns in _nsucc:
                    if _ns is None or _ns is _e or _ns is _m:
                        continue
                    if _t.start_offset <= _ns.start_offset < _e.start_offset:
                        _nfront.append(_ns)
            _fr_m = None
            for _r in self.region_analyzer.regions:
                if isinstance(_r, IfRegion) and getattr(_r, 'condition_block', None) is _m:
                    _fr_m = _r
                    break
            _arm = [b for b in (getattr(_fr_m, 'then_blocks', None) or [])
                    if b is not None and b.instructions
                    and _t.start_offset <= b.start_offset < _e.start_offset]
            if _t not in _arm:
                _arm = [_t]
            _r2144_census_note('R2144FIRE', 'cond=@%s M=@%s T=@%s E=@%s arm=%s' % (
                cond_block.start_offset, _m.start_offset, _t.start_offset, _e.start_offset,
                [b.start_offset for b in _arm]))
            for _b in _all_leg_blocks + [_m]:
                self.generated_blocks.add(_b)
                self.generated_offsets.add(_b.start_offset)
            region.then_blocks = _arm
            region.merge_block = __MERGE__
            region.else_blocks = []
            return {'type': 'BoolOp', 'op': 'or',
                    'values': [{'type': 'BoolOp', 'op': 'and',
                                'values': [expr, _a_expr]}, _b_expr]}
        except Exception as _exc_r2144:
            return _rej('EXC:%s' % type(_exc_r2144).__name__)

'''

METHOD = METHOD.replace('__MERGE__', 'None' if MERGE_NONE else '_e')

if NO_PROBE:
    # 交付版：剥掉普查探针与其全部调用点（判据本体一字不动）。
    METHOD = METHOD.replace("""        def _rej(_why):
            _r2144_census_note('R2144REJ', '%s cond=@%s' % (
                _why, getattr(cond_block, 'start_offset', '?')))
            return None
""", '')
    METHOD = METHOD.replace("""            _r2144_census_note('R2144FIRE', 'cond=@%s M=@%s T=@%s E=@%s arm=%s' % (
                cond_block.start_offset, _m.start_offset, _t.start_offset, _e.start_offset,
                [b.start_offset for b in _arm]))
""", '')
    METHOD = METHOD.replace("""        except Exception as _exc_r2144:
            return _rej('EXC:%s' % type(_exc_r2144).__name__)""",
                            """        except Exception:
            return None""")
    METHOD = re.sub(r"return _rej\('[A-Za-z0-9]+'\)", "return None", METHOD)
    METHOD = re.sub(r"return _rej\('[A-Za-z0-9]+'\)", "return None", METHOD)

_EVAL_NOTE = """                    _r2144_census_note('R2144EVAL', 'cond=%r then=%d' % (
                        getattr(region.condition_block, 'start_offset', None)
                        if getattr(region, 'condition_block', None) is not None else None,
                        len(getattr(region, 'then_blocks', None) or [])))
"""

CALL = '''                # [R21-44] 正极性单腿 + "汇合块"是 or 尾腿 ⇒ 并成一条 `X and A or B` 测试
                # （判据与结构事实见 _r2144_and_leg_before_or_tail）。成功时本区域臂已
                # 重声明为 then=[尾腿真出口的臂体]、merge=[尾腿假出口]；不成立时返回
                # None，走既有路径，产物逐字节不变。
                if not negate and not region.else_blocks:
                    _r2144_census_note('R2144EVAL', 'cond=%r then=%d' % (
                        getattr(region.condition_block, 'start_offset', None)
                        if getattr(region, 'condition_block', None) is not None else None,
                        len(getattr(region, 'then_blocks', None) or [])))
                    _r2144_lift = self._r2144_and_leg_before_or_tail(
                        region, cond_block, expr)
                    if _r2144_lift is not None:
                        return _r2144_lift
'''

if NO_PROBE:
    CALL = CALL.replace(_EVAL_NOTE, '')

ANCHOR_PROBE = [b'def _negate_expr(expr: Dict[str, Any]) -> Dict[str, Any]:']
ANCHOR_METHOD = [b'    def _r4701_and_lift_or_tail(self, region, cond_block, expr):']
ANCHOR_CALL = [b'                if negate and not region.else_blocks:',
               b'                    _r4701_lift = self._r4701_and_lift_or_tail(',
               b'                        region, cond_block, expr)',
               b'                    if _r4701_lift is not None:',
               b'                        return _r4701_lift']


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


raw = open(BASE, 'rb').read()
assert raw.startswith(b'\xef\xbb\xbf'), 'base lacks the UTF-8 BOM'
assert raw.count(b'\n') == raw.count(b'\r\n'), 'base has mixed newlines'
lines = raw.split(b'\r\n')


def find(needle):
    return [n for n in range(len(lines) - len(needle) + 1) if lines[n:n + len(needle)] == needle]


def as_bytes(text):
    return [l.encode('utf-8') for l in text.split('\n')]


def insert_before(anchor, new_lines, label):
    hits = find(anchor)
    assert len(hits) == 1, '%s: anchor hits=%d (must be exactly 1)' % (label, len(hits))
    lines[hits[0]:hits[0]] = new_lines
    return hits[0]


def insert_after(anchor, new_lines, label):
    hits = find(anchor)
    assert len(hits) == 1, '%s: anchor hits=%d (must be exactly 1)' % (label, len(hits))
    at = hits[0] + len(anchor)
    lines[at:at] = new_lines
    return at


if not NO_PROBE:
    at = insert_before(ANCHOR_PROBE, as_bytes(PROBE), 'probe anchor')
    print('   probe def inserted at :%d' % (at + 1))
at = insert_before(ANCHOR_METHOD, as_bytes(METHOD.rstrip('\n')) + [b''], 'method anchor')
print('   criterion method inserted at :%d (%d lines)' % (at + 1, len(METHOD.rstrip('\n').split('\n'))))
at = insert_after(ANCHOR_CALL, as_bytes(CALL.rstrip('\n')), 'call anchor')
print('   call site inserted at :%d' % (at + 1))

merged = b'\r\n'.join(lines)
open(OUT, 'wb').write(merged)
py_compile.compile(OUT, doraise=True)

back = merged.split(b'\r\n')
for probe in (b'_r2144_census_note', b'_r2144_and_leg_before_or_tail'):
    print('   occurrences of %s = %d' % (probe.decode(), merged.count(probe)))
print('OUT=%s size=%d sha16=%s (base was %s) py_compile=OK BOM=%s allCRLF=%s'
      % (OUT, len(merged), sha16(merged), sha16(raw),
         merged.startswith(b'\xef\xbb\xbf'), merged.count(b'\n') == merged.count(b'\r\n')))
