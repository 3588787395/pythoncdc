"""R21-46 candidate builder — clock_worker 损失 (A)：臂内 ibc 折叠吞掉成员块的前导语句。

Base (规则：整文件字节级重建，绝不手改 *OK.py)：
    D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round39/r74/CANDIDATE_r74c_r2145_AB_f51f9de14d216cda.py
      sha256[:16] = f51f9de14d216cda   （= 门禁 38 landed 11324f276cce6d5b + [R21-45] A+B，
                                         分析端 f7d849e974904492 不动）
      clock_worker 实测：len orig=1424 prod=1420 delta=-4，未过滤 hunk=3（简报给的「1 窗」是
      unit_diff 默认小窗过滤的读数，见 FIX_R21-46 §0）。

Patch（本工单的唯一机制 [R21-46]，插在 `_if_generate_elif_chain` 首个 elif 折叠站点）：
  共享触发判据 `_r2146_ibc_member_has_stmt_prefix`（模块级新函数，插在 class 之前）：
    inline_boolop_chains 的**非链首成员块**带一段「栈已归零的完结语句前导」且该前导未被任何
    消费者登记发射 ⇒ 折叠会丢语句。只读既有切分器 `_split_block_condition_prefix`（纯 CPython
    栈纪律）与既有单调台账 `prefix_emitted_upto`，不新建谓词、不读偏移/名字/计数。
  half A = `_inline_chain_info = None`      —— 否决抬升（= r66a 的纯拒绝守卫重新锚定到本基）
  half B = `_r2113_legs_back = blocks[1:]`  —— 成员块交还臂体（复用已落地的 [R21-13] 通道：
    消费点在 `_if_generate_elif_chain` 的 elif 臂装配处，块表按 start_offset 排序后交给
    `_process_if_blocks`，语句因此落在 elif 臂内而非链尾）
  A+B 才既是「不丢」又是「位置对」（规则 4：A 独走 = 丢位置、B 独走 = 双归属诊断）。

usage: python -X utf8 build_cand_r75a_r2146.py [--halves a|b|a,b] [--probe] [--site2] [--base PATH] [--out PATH]
"""
import hashlib
import os
import py_compile
import sys

REPO = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
BASE = (REPO + '/.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/'
        'round39/r74/CANDIDATE_r74c_r2145_AB_f51f9de14d216cda.py')
BASE_SHA16 = 'f51f9de14d216cda'
OUT = 'D:/Temp/r75/work/CANDIDATE_r75a_r2146.py'

A = sys.argv
if '--out' in A:
    OUT = A[A.index('--out') + 1]
if '--base' in A:
    BASE = A[A.index('--base') + 1]
HALVES = (A[A.index('--halves') + 1] if '--halves' in A else 'a,b').replace(' ', '').split(',')
if '--expect-sha16' in A:
    BASE_SHA16 = A[A.index('--expect-sha16') + 1]
PROBE = '--probe' in A
SITE2 = '--site2' in A

assert 'a' in HALVES or 'b' in HALVES, HALVES

# ── 普查探针（不参与任何判定；开/关必须产物逐字节相同）────────────────────────
PROBE_FN = '''def _r2146_census_note(stage, detail=''):
    """[R21-46 普查探针] 仅当环境变量 R2146_CENSUS 指向路径时追加一行；否则立即返回。

    探针不参与任何判定：判据主体不使用它的返回值，FIRE 行写在全部合取成立之后、真正改
    `_inline_chain_info` / `_r2113_legs_back` 之前。开/关探针必须产物逐字节一致，否则普查
    读数作废（规则 2）。
    """
    import os as _os_r2146
    _p = _os_r2146.environ.get('R2146_CENSUS')
    if not _p:
        return
    try:
        with open(_p, 'a', encoding='utf-8') as _f_r2146:
            _f_r2146.write('%s %s\\n' % (stage, detail))
    except Exception:
        pass


'''

# ── 判据主体 ─────────────────────────────────────────────────────────────────
HELPER = '''def _r2146_ibc_member_has_stmt_prefix(gen, chain_blocks):
    """[R21-46] inline_boolop_chains 的「非链首成员块」里藏着一条**没人发射的前导语句**时
    返回 True —— realtime_event_source::clock_worker 的臂内折叠正是这样丢掉了 6 条指令。

    结构事实（本单元实测，`work/probe_ibc.py` 只读探针）：
      IfRegion@7186 带 `inline_boolop_chains[id(@7248)] = {'op': 'and', 'blocks': [@7248, @7270]}`；
      @7248 = `now_date != self.first_run_date` 测试（5 条），
      @7270 = `system_log.debug('获取重登信号量')`(LOAD_GLOBAL/LOAD_ATTR/LOAD_CONST/PRECALL/
              CALL/POP_TOP 共 6 条) ++ `login_semaphore.acquire(...) is False` 测试(11 条)，
              它同时是已声明区域 IfRegion@7270 的 condition_block（then=[7372,7488] else=[7492]）。
      CPython 3.11 不在「语句结束」与「紧随其后的条件求值」之间分裂基本块（块边界只在控制流转移
      处产生），所以 `if D:` 为真时执行的下一条语句与 `E` 的求值物理同块。折叠把每个成员块**只**
      当作一个合取支重建表达式（`_cb_instrs` 过滤 + `expr_reconstructor.reconstruct`），随后
      `for _cb in _chain_blocks[1:]: self.generated_blocks.add(_cb)` 把成员块整体记为已生成 ——
      前导语句既进不了表达式，也没有第二个语句发射者，实测产物恰好缺这 6 条
      （`delete orig[1051..1057 @@7270..@@7308] del=6 ins=0`）。

    判据只用既有设施，不新建谓词：
      ① 切分器 `_split_block_condition_prefix`（纯 CPython 栈纪律：块末为条件跳转时，前向栈深
         模拟中最后一次回到入口深度 0 的位置之前 = 完结语句段）。AssertRegion 前导、R23-B 旋转
         while 的循环体首语句、三元前导三个既有消费者已在用它；对**纯测试块**返回 [] —— 因此
         今日语料里所有无前缀的折叠一律不命中，本判据对它们是惰性的（规则 2 的字节普查已证）。
      ② 台账 `prefix_emitted_upto`（指令粒度、单调、由真正产出语句的漏斗登记）：前缀偏移若已
         被别的消费者发射过，则**不**否决折叠 —— 那是「已发射」而非「会丢」，否决会制造重复发射。
      ③ 只看链首之外的成员块（链首的条件段由本臂测试自己消费）。
    保守性：成员列表空、任何异常、前缀全为噪声（切分器自身已排除）⇒ False，调用方逐字节沿用
    既有折叠路径。可证性而非偏好：「块内栈归零 ⇒ 该段是一条完结语句」与「成员块整体标
    generated ⇒ 该段再无语句发射者」两条合起来是「折叠必丢语句」的充分签名，不涉及函数名、
    绝对偏移、计数阈值或跨层取值启发。
    """
    _hit = False
    for _cb in list(chain_blocks or [])[1:]:
        try:
            _pfx = gen._split_block_condition_prefix(_cb)
        except Exception:
            break
        if not _pfx:
            continue
        _upto = gen.prefix_emitted_upto.get(_cb, -1)
        if any(getattr(_i, 'offset', None) is None or _i.offset > _upto for _i in _pfx):
            _hit = True
            break
    _r2146_census_note('R2146EVAL', 'chain=%s hit=%s' % ([getattr(_m, 'start_offset', '?') for _m in list(chain_blocks or [])], _hit))
    return _hit


'''

SITE1_BLOCK = '''            # [R21-46] 折叠会丢语句的臂内 ibc 链：既不抬进 elif 测试，成员块另交还臂体。
            # 承 r66a（rounds/round38/CANDIDATE_r66a_ibc_prefix_guard_BANKED_not_landed.py，
            # 07ff9a163b07140a，基为门禁 37 的 c4a934d595200c84）：它的纯拒绝守卫让 6 条指令
            # **出现**（delta -6→0）但落在链尾（hunks 5→6，位置窗）；本工单补上「交还臂体」的
            # 另一半，落点由已落地的 [R21-13] 通道决定（消费点见下方 `_r2113_legs_back`：腿块并入
            # region.elif_bodies[0] 并按 start_offset 排序后交给 _process_if_blocks）。
            # 判据全文见 _r2146_ibc_member_has_stmt_prefix（结构事实 / 保守性 / 可证性在其 docstring）。
            if (_inline_chain_info
                    and _r2146_ibc_member_has_stmt_prefix(
                        self, _inline_chain_info.get('blocks') or [])):
                PROBE_EVAL_PLACEHOLDER
                HALF_B_PLACEHOLDER
                HALF_A_PLACEHOLDER
'''

SITE2_BLOCK = '''                    # [R21-46] 末臂同一折叠站点：同一判据、同一否决（臂体装配在此站点由
                    # `_process_if_blocks(region.elif_final_else, ...)` 承担，交还通道不同，
                    # 故此处只否决；命中与否由普查决定，见 FIX_R21-46 §数派）。
                    if (_inline_chain_info
                            and _r2146_ibc_member_has_stmt_prefix(
                                self, _inline_chain_info.get('blocks') or [])):
                        PROBE_EVAL_PLACEHOLDER
                        _inline_chain_info = None
'''

HALF_A = '_inline_chain_info = None'
HALF_B = ('_r2113_legs_back = list(_inline_chain_info.get(\'blocks\') or [])[1:]')


PROBE_S1 = ("_r2146_census_note('R2146FIRE', 'cond=@%s chain=%s halves=%s' % ("
            "getattr(elif_cond_block, 'start_offset', '?'), "
            "[getattr(_m, 'start_offset', '?') for _m in (_inline_chain_info.get('blocks') or [])], "
            "'@HALVES@'))")
PROBE_S2 = "_r2146_census_note('R2146S2FIRE', 'cond=@%s' % getattr(_last_elif_cond_block, 'start_offset', '?'))"


def _render(block, probe_line, halves_note):
    """Expand PLACEHOLDER lines of an insertion block; returns plain '\\n' text."""
    out = []
    for ln in block.split('\n'):
        st = ln.strip()
        ind = ln[:len(ln) - len(ln.lstrip())]
        if st == 'PROBE_EVAL_PLACEHOLDER':
            if probe_line:
                out.append(ind + probe_line)
            continue
        if st == 'HALF_A_PLACEHOLDER':
            if 'a' in HALVES:
                out.append(ind + HALF_A)
            continue
        if st == 'HALF_B_PLACEHOLDER':
            if 'b' in HALVES:
                out.append(ind + HALF_B)
            continue
        out.append(ln)
    return '\n'.join(out).rstrip('\n') + '\n'


def build_text(probe):
    """Return (helper_text, site1_text, site2_text_or_None) with probes/halves resolved."""
    p1 = PROBE_S1.replace('@HALVES@', '+'.join(sorted(HALVES))) if probe else None
    s1 = _render(SITE1_BLOCK, p1, None)
    s2 = _render(SITE2_BLOCK, PROBE_S2 if probe else None, None) if SITE2 else None
    return HELPER, s1, s2


def strip_probe(text):
    """Remove probe-note lines (used for the delivered no-probe build)."""
    return '\n'.join(ln for ln in text.split('\n')
                     if not ln.strip().startswith('_r2146_census_note('))


def crlf(text):
    return text.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')


def splice(data, anchor_lines, block_bytes, where='before'):
    """Insert a whole-line block adjacent to a UNIQUE anchor given as consecutive CRLF lines.

    'before' -> block goes immediately before the anchor's first line (so my insertion sits
                 *outside* the `if _inline_chain_info:` body it guards, never inside it)
    Anchors are matched on CRLF bytes and asserted unique; the caller py_compiles the result.
    """
    anc = b'\r\n'.join(anchor_lines)
    n = data.count(anc)
    assert n == 1, 'anchor count %d for %r' % (n, anchor_lines[0][:70])
    blk = block_bytes
    if not blk.endswith(b'\r\n'):
        blk = blk + b'\r\n'
    assert where == 'before', where
    return data.replace(anc, blk + anc, 1)


raw = open(BASE, 'rb').read()
assert hashlib.sha256(raw).hexdigest()[:16] == BASE_SHA16, \
    'BASE sha16 mismatch: got %s' % hashlib.sha256(raw).hexdigest()[:16]
print('base   %s size=%d sha16=%s' % (os.path.basename(BASE), len(raw),
                                      hashlib.sha256(raw).hexdigest()[:16]))

helper, site1, site2 = build_text(PROBE)
if not PROBE:
    helper = strip_probe(helper)
out = raw
# 模块级插入点：class RegionASTGenerator 之前（列 0，绝不切开类体）
cls_anchor = b'class RegionASTGenerator:'
assert out.count(cls_anchor) == 1, 'class anchor'
pos = out.find(cls_anchor)
ins = crlf(PROBE_FN + helper) if PROBE else crlf(helper)
out = out[:pos] + ins + out[pos:]

# 站点 1：首个 elif 的 ibc 折叠（`if _inline_chain_info:` + 其后 `_chain_blocks = ...`）
SITE1_ANCHOR = (b"            if _inline_chain_info:",
                b"                _chain_blocks = _inline_chain_info['blocks']")
out = splice(out, SITE1_ANCHOR, crlf(site1))

if site2 is not None:
    SITE2_ANCHOR = (b"                    if _inline_chain_info:",
                    b"                        _chain_blocks = _inline_chain_info['blocks']")
    out = splice(out, SITE2_ANCHOR, crlf(site2))

open(OUT, 'wb').write(out)
py_compile.compile(OUT, doraise=True)
print('cand   %s size=%d sha16=%s probe=%s halves=%s site2=%s'
      % (OUT, len(out), hashlib.sha256(out).hexdigest()[:16], PROBE,
         '+'.join(sorted(HALVES)), SITE2))
