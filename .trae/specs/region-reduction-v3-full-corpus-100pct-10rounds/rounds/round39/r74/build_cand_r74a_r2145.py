"""R21-45 candidate builder (clock_worker loss (B): the declared merge block of a positive
single-arm IfRegion is emitted at the function tail instead of at its join).

Base (rule: whole-file byte-exact rebuild, never a hand-edited *OK.py):
    D:/Temp/r74/work/base_anchored_cf5868e68208adf6.py
      = gate-38 landed bytes 11324f276cce6d5b  +  banked P1+P2 (c4a934d595200c84 re-anchored by
        r73 as cf5868e68208adf6)   ->  clock_worker delta=-6 hunks=5, judge 12/13

Patch: half A = ONE pure insertion inside `_if_generate_normal`, in the post-if merge-emission
decision, immediately before the first `if _should_emit:`.  Criterion text is r67a's reclaimed WIP
(rounds/round38/CANDIDATE_r67a_mergeblock_BANKED_reclaimed_WIP.py, 17b73582864fbba0) re-badged
[R21-45] and instrumented with an inert census probe; identifiers renamed _r38b_* -> _r2145_*.
half B = [R21-45b], a pure insertion in `_generate_try`'s orelse loop (the phantom `else: break`).

usage: python -X utf8 build_cand_r74a_r2145.py [--halves a|b|a,b] [--no-probe] [--out PATH] [--base PATH]
"""
import hashlib
import py_compile
import sys

BASE = 'D:/Temp/r74/work/base_anchored_cf5868e68208adf6.py'
OUT = 'D:/Temp/r74/work/CANDIDATE_r74a_r2145.py'
A = sys.argv
if '--out' in A:
    OUT = A[A.index('--out') + 1]
if '--base' in A:
    BASE = A[A.index('--base') + 1]
HALVES = (A[A.index('--halves') + 1] if '--halves' in A else 'a').replace(' ', '')
NO_PROBE = '--no-probe' in A

PROBE = '''def _r2145_census_note(stage, detail=''):
    """[R21-45 普查探针] 仅当环境变量 R2145_CENSUS 指向路径时追加一行；否则立即返回。

    探针不参与任何判定：判据主体不使用它的返回值，FIRE 行写在全部合取成立之后、真正改
    `_should_emit` 之前。开/关探针必须产物逐字节一致，否则普查读数作废（规则 2）。
    """
    import os as _os_r2145
    _p = _os_r2145.environ.get('R2145_CENSUS')
    if not _p:
        return
    try:
        with open(_p, 'a', encoding='utf-8') as _f_r2145:
            _f_r2145.write('%s %s\\n' % (stage, detail))
    except Exception:
        pass


'''

BLOCK = '''            # [R21-45] JOIN-CLAIM：正极性单臂 if 的「已声明汇合块」必须在本 if 之后、
            # 同一 suite 内补发 —— 它现在被外层循环的残余清扫挪到了函数尾（realtime_event_source
            # ::clock_worker 的 `self.before_trading_date = now_date`）。
            # 文本承 r67a 未完成任务（rounds/round38/CANDIDATE_r67a_mergeblock_BANKED_reclaimed_WIP.py,
            # 17b73582864fbba0，在 c4a934d595200c84 基上 0 命中），r74 重新锚定到门禁 38 字节后实测。
            # 四条判据全是形状事实（区域数据 / opcode 类别 / 前驱后继结构），无函数名、无绝对偏移、
            # 无计数阈值、无跨层启发：
            #   ① merge 块不在本区域的 then/else 臂内（臂内 merge 走既有臂发射通道）；
            #   ② merge 块的每一个前驱都属于 `region.blocks`，且前驱不止一条 ——
            #      条件块的假出口落点与某条臂的尾块共同汇流到此块，它是本 if 的真汇合点
            #      （汇流 arity>=2），不是别人路过的入口，也不是只有假臂的悬空尾；
            #   ③ merge 块剥掉噪声指令（RESUME/NOP/CACHE/PUSH_NULL/EXTENDED_ARG）后的末条
            #      必须是一条「语句终止符」（STORE_* / POP_TOP / 声明收尾），且既不是
            #      JUMP*/POP_JUMP*/RETURN*/RAISE* —— 前者保证该块真的「装完了一条语句」，
            #      后者保证控制流经此继续后面的顺序代码（「顺序后继」而非「出口」的签名）。
            #      反例（实测过发射）：merge 块尾为 SWAP（栈变形，语句未完成，它属于
            #      外层表达式取值的流程），若放行会凭空发出一条 `return None`。
            #   ④ 唯一归属（原则 2）：没有别的区域把它宣为 condition_block/header_block/
            #      entry，也没有别的区域把它列为自己的 then/else 臂成员（那样由该臂发射，
            #      本处再发就是重复）；且没有「嵌套在本 if 之内」的 Try/With/Match 区域
            #      含住它 —— 祖先结构区域不算嵌套，判据用包含（本 if 的 entry 落在其
            #      blocks 内）而非 region.parent 指针，故 parent 链断裂时仍然成立。
            # 命中 ⇒ 依原则 4（父引用子入口）由本区域在 If 节点之后、同一 suite 内补发。
            # 放在 `_mb_in_nested_structural` 之外：该守卫只沿 region.parent 认祖先，
            # parent 链断时整块被跳过，merge 遂被外层循环的残余清扫 `_loop_postprocess`
            # 挪到循环体之后（实测：clock_worker 的该赋值被发射到函数级 while 的尾部）。
            # 保守性：四条同时成立才动；否则 `_should_emit` 保持原值，产物逐字节不变。
            # 可证性而非偏好：②的前驱集合 = {条件块假出口, 臂尾} 正是 `if X: arm` 之后紧跟一条
            # 语句的 CFG 签名；③排除出口/栈变形块；④排除双发射者 —— 三者合起来唯一确定
            # 「本 if 的顺序后继就是这条语句」。
            if (not _should_emit
                    and region.merge_block not in (region.then_blocks or [])
                    and region.merge_block not in (region.else_blocks or [])):
                _r2145_mb = region.merge_block
                _r2145_preds = [p for p in (getattr(_r2145_mb, 'predecessors', None) or [])
                               if getattr(p, 'instructions', None)]
                _r2145_own = set(b for b in (getattr(region, 'blocks', None) or [])
                                 if getattr(b, 'instructions', None))
                _r2145_tail = None
                _r2145_meaningful = []
                for _r2145_i in (_r2145_mb.instructions or ()):
                    if _r2145_i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                          'EXTENDED_ARG'):
                        continue
                    _r2145_meaningful.append(_r2145_i)
                if _r2145_meaningful:
                    _r2145_tail = _r2145_meaningful[-1]
                _r2145_term = _r2145_tail is not None and (
                    _r2145_tail.opname.startswith('STORE_')
                    or _r2145_tail.opname in ('POP_TOP', 'FOR_ITER', 'SEND', 'YIELD_VALUE',
                                              'DELETE_FAST', 'DELETE_DEREF', 'DELETE_ATTR',
                                              'DELETE_SUBSCR', 'IMPORT_STAR'))
                _r2145_rej = None
                if not (len(_r2145_preds) >= 2
                        and all(p in _r2145_own for p in _r2145_preds)
                        and _r2145_meaningful and _r2145_term
                        and not _r2145_tail.opname.startswith(
                            ('JUMP', 'POP_JUMP', 'RETURN', 'RAISE'))):
                    _r2145_rej = 'shape'
                else:
                    for _r2145_o in self.region_analyzer.regions:
                        if _r2145_o is region:
                            continue
                        for _r2145_f in ('condition_block', 'header_block', 'entry'):
                            if getattr(_r2145_o, _r2145_f, None) is _r2145_mb:
                                _r2145_rej = 'declared-head'
                                break
                        if _r2145_rej:
                            break
                        # ④b 该块若是别的区域的臂成员（then/else），由该臂的发射者负责，
                        #     本处再发即整臂重复（实测双发 13 条：@6406..@6486 同时是
                        #     IfRegion@6374 的 then 成员、@9144 同时是 IfRegion@8948 的
                        #     else 成员）。
                        if any(_r2145_mb in (getattr(_r2145_o, _r2145_g, None) or ())
                               for _r2145_g in ('then_blocks', 'else_blocks')):
                            _r2145_rej = 'other-arm-member'
                            break
                        if not isinstance(_r2145_o, (TryExceptRegion, WithRegion, MatchRegion)):
                            continue
                        _r2145_ob = getattr(_r2145_o, 'blocks', None) or ()
                        if _r2145_mb not in _r2145_ob:
                            continue
                        _r2145_ent = getattr(region, 'entry', None)
                        if _r2145_ent is not None and _r2145_ent in _r2145_ob:
                            continue      # 祖先结构区域（包含本 if）：不压制
                        _r2145_rej = 'nested-structural'
                        break
                _r2145_census_note('R2145EVAL', 'mb=@%s np=%s term=%s rej=%s' % (_r2145_mb.start_offset, len(_r2145_preds), (_r2145_tail.opname if _r2145_tail else '-'), _r2145_rej))
                if _r2145_rej is None:
                    _r2145_census_note('R2145FIRE', 'mb=@%s region=@%s' % (_r2145_mb.start_offset, getattr(getattr(region, 'entry', None), 'start_offset', '?')))
                    _should_emit = True
'''

BLOCK_B = '''                    # [R21-45b] try-else 假臂：被宣为 else 的块若只是「与所有 handler 出口同落点」
                    # 的一条前向跳转，那它是 try 体的正常完成边，不是 else 语句 —— 不发 Break。
                    # 结构事实（CPython 3.11 的 try/except 布局，实测）：没有 else 时，try 体尾发一条
                    #   JUMP_FORWARD T（跳过 handler），每个 handler 的正常收尾也发 JUMP_FORWARD T
                    #   （跳过 else 段、落到整条语句之后）—— 两条边落在同一块 T；有 else 时 try 体的边
                    #   落在 else 首块，handler 的边落在 else 之后，两个目标必不相同。
                    #   realtime_event_source::clock_worker 的 @6652 与 handler 尾 @6678 都指向 @6690，
                    #   区域端仍把 @6652 宣进 else_blocks，发射端按 PURE_BREAK 角色发了 `else: break`，
                    #   于是 try 成功后直接跳出外层 while（编译成函数中的 RETURN），控制流与原码不符。
                    # 判据（只用本区域的 else_blocks / except_handlers 与 CFG 跳转目标同一性；
                    #   无函数名、无绝对偏移、无计数阈值、无跨层启发）：
                    #   ① eb 剥掉噪声（RESUME/NOP/CACHE/PUSH_NULL/EXTENDED_ARG）后恰剩一条无条件
                    #     前向跳转（JUMP_FORWARD/JUMP_ABSOLUTE），目标 T 是真实块；
                    #   ② 本区域至少有一个非空 handler 臂，且每个臂的末块（按 start_offset 取尾）
                    #     剥噪后的收尾指令也跳向同一个 T；
                    #   ③ 任一不成立即原样落回既有角色分派路径，产物逐字节不变。
                    # 归约：命中 ⇒ 该 else 块视作空臂：与既有 BREAK 分支同样登记 generated_blocks
                    #   （原则 2 唯一归属，禁止第二个发射者再走它），但不产出任何语句。
                    # 可证性而非偏好：①+② 合起来正是「try 体正常完成边与 handler 出口共目标」这一
                    #   唯一签名，真 else 臂不可能同时满足，故这是布局事实的判读而非取值偏好。
                    _r2145b_noise = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG')
                    _r2145b_eb_i = [i for i in (eb.instructions or ()) if i.opname not in _r2145b_noise]
                    _r2145b_handlers = [h for h in (getattr(region, 'except_handlers', None) or [])
                                        if isinstance(h, tuple) and len(h) == 3 and h[2]]
                    _r2145b_bare = (len(_r2145b_eb_i) == 1
                                    and _r2145b_eb_i[0].opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE')
                                    and isinstance(_r2145b_eb_i[0].argval, int))
                    _r2145b_target = (self.cfg.get_block_by_offset(_r2145b_eb_i[0].argval)
                                      if _r2145b_bare else None)
                    _r2145b_rej = None
                    if not _r2145b_bare:
                        _r2145b_rej = 'not-bare-jump'
                    elif _r2145b_target is None:
                        _r2145b_rej = 'no-target-block'
                    elif not _r2145b_handlers:
                        _r2145b_rej = 'no-handler'
                    else:
                        for _r2145b_h in _r2145b_handlers:
                            _r2145b_lastb = sorted(_r2145b_h[2], key=lambda b: b.start_offset)[-1]
                            _r2145b_tail = [i for i in (_r2145b_lastb.instructions or ())
                                            if i.opname not in _r2145b_noise]
                            if not (_r2145b_tail
                                    and _r2145b_tail[-1].opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE')
                                    and isinstance(_r2145b_tail[-1].argval, int)
                                    and self.cfg.get_block_by_offset(_r2145b_tail[-1].argval) is _r2145b_target):
                                _r2145b_rej = 'handler-exit-not-shared'
                                break
                    _r2145_census_note('R2145bEVAL', 'eb=@%s nh=%d bare=%s rej=%s' % (eb.start_offset, len(_r2145b_handlers), _r2145b_bare, _r2145b_rej))
                    if _r2145b_rej is None:
                        _r2145_census_note('R2145bFIRE', 'eb=@%s T=@%s try=@%s' % (eb.start_offset, _r2145b_target.start_offset, region.entry.start_offset))
                        self.generated_blocks.add(eb)
                        continue
'''

raw = open(BASE, 'rb').read()
crlf = lambda s: s.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')


def strip_probe(text):
    return '\n'.join(ln for ln in text.split('\n')
                     if not ln.strip().startswith('_r2145_census_note('))


def splice(data, anchor_text, block_text, where='after'):
    """Insert a whole-line block adjacent to a UNIQUE anchor given as consecutive lines.

    'after'  -> block goes immediately after the anchor's LAST line
    'before' -> block goes immediately before the anchor's FIRST line
    'mid'    -> anchor must be exactly two lines; block goes between them
    Anchors are matched on CRLF bytes and asserted unique; the caller py_compiles the result.
    """
    anc = crlf(anchor_text)
    n = data.count(anc)
    assert n == 1, 'anchor count %d for %r' % (n, anchor_text.split('\n')[0][:60])
    blk = crlf(block_text)
    if where == 'after':
        return data.replace(anc, anc + blk, 1)
    if where == 'before':
        return data.replace(anc, blk + anc, 1)
    first, last = anchor_text.split('\n')
    return data.replace(anc, crlf(first) + b'\r\n' + blk + crlf(last), 1)


out = raw
if not NO_PROBE:
    # module-level probe helper, inserted just before the top-level `class ` that owns
    # `_if_generate_normal` (column 0, so it cannot split the class body).
    mi = out.find(b'    def _if_generate_normal(')
    assert mi != -1 and out.count(b'    def _if_generate_normal(') == 1, 'method anchor'
    pos = out.rfind(b'\nclass ', 0, mi) + 1
    assert pos > 0, 'no top-level class before the method'
    out = out[:pos] + crlf(PROBE) + out[pos:]

if 'a' in HALVES:
    out = splice(out,
                 '                            break\n            if _should_emit:',
                 (BLOCK if not NO_PROBE else strip_probe(BLOCK)) + '\n', where='mid')
if 'b' in HALVES:
    out = splice(out,
                 '                    eb_role = self.region_analyzer.get_block_role(eb)',
                 (BLOCK_B if not NO_PROBE else strip_probe(BLOCK_B)) + '\n', where='before')

open(OUT, 'wb').write(out)
py_compile.compile(OUT, doraise=True)
print('built %s size=%d sha16=%s probe=%s halves=%s' % (OUT, len(out),
                                              hashlib.sha256(out).hexdigest()[:16], not NO_PROBE, HALVES))
