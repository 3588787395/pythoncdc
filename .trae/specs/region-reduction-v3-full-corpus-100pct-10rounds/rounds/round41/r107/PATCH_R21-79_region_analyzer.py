"""PATCH_R21-79_region_analyzer.py — idempotent, absolute-path, anchored patcher.

Turns the pinned base analyzer  core/cfg/region_analyzer.py  sha256[:16]=996a1b1acf143458
(the banked [R21-77-F5] product, repo copy .../rounds/round41/CANDIDATE_r2177f5_996a1b1acf143458.py)
into the [R21-79] candidate: a POSITIVE tail claim in the nested-elif expander of
_build_elif_region that removes "sequential code after the whole if/elif statement"
from the chain's final_else arm.

usage:
    python -X utf8 PATCH_R21-79_region_analyzer.py                # build candidate only
    python -X utf8 PATCH_R21-79_region_analyzer.py --install      # build + install into mirror core/

Re-running is a no-op (marker detected -> same bytes re-emitted, exit 0).
Never touches the repo; writes only under D:/Temp/r107.
"""
import hashlib
import os
import py_compile
import sys

BASE_SHA16 = '996a1b1acf143458'
SRC = r'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round41/CANDIDATE_r2177f5_996a1b1acf143458.py'
MIRROR_CORE = r'D:/Temp/r107/core/cfg/region_analyzer.py'
DELIVER_DIR = r'D:/Temp/r107/DELIVER'
NL = chr(10)
CR = chr(13)

ANCHOR = """        elif_info = _check_elif_chain(block, else_blocks, merge)
        if elif_info is None:
            return None
"""

INSERT = ANCHOR + """        # ── [R21-79 链尾正向认领 positive tail claim] ──────────────────────────────
        # ①算法依据：No More Gotos §3「If 区域归约」＋原则 1（块 = 前导语句 + 恰好
        #   一个终结子）＋原则 2（每块唯一归属）。一条 if/elif/…/else 链的 else 臂只含
        #   【末条件假边所进入】的那段语句；链声明的汇合块 merge 之后的语句是整条 if
        #   语句的兄弟（父层序列的续行），不属于任何臂。内层 _collect_branch_blocks 沿
        #   假边/落穿收集过深时，整段「链后顺序代码」被塞进 final_else，由链的最终 else
        #   臂吞掉（absorption），这些语句便在其正确位置消失：实测
        #   realtime_event_source.clock_worker 的 IfRegion@7186（merge=@7216）把
        #   @7582…@9144 共 41 块（其中被丢的一段即 @7972..@8586 的 112 条指令）认成
        #   elif_final_else，产物 unit 体 241 行 vs ORACLE 254、DELTAS instrs=-114。
        #   本判据是正向认领（何为尾），不是又一层拒绝折叠（R21-48 族实测惰性/破坏）。
        # ②归约顺序：自底向上、单向数据流。位置在 _check_elif_chain 返回之后、建区之前
        #   一次性剔出：其后的 else_blocks 结构过滤、all_blocks、IfRegion(elif_final_else=…)、
        #   merge 回补与 trailing_return_none 标注读到同一份 final_else —— 识别阶段定形，
        #   无发射后回溯修正。
        # ③唯一归属判定（只读边数据 + 本链区域数据；无函数名/文件名/绝对偏移匹配键、
        #   无计数器、无阈值、无 len() 量级比较作触发）：
        #     墙 W = 本链自身结构成员集 {链头 block, 主条件块 condition_block,
        #            all_condition_blocks, then 臂, elif 条件 conditions, 各 elif 臂体 bodies}
        #     尾 T = 从链声明的汇合块 merge 出发沿 successors 的传递闭包，遇 W 中的块
        #            既不进入也不穿越。
        #   final_else 中的块 f 判为链后续行，当且仅当
        #     (a) f ∈ T —— f 由链出口之后（落穿或跳转）进入 ⇒ 它在整条 if 语句之后；
        #     (b) f 没有任何前驱 ∈ W —— else 臂入口在字节上必由末条件的假边进入，即必有
        #         一个链内成员前驱；无前驱成员 ⇒ 它不是臂的入口，只是父层的下一条语句。
        #   与被排除前提的调和：「凡属其它区域 entry 的块都从 elif_final_else 剔出」是错的
        #   —— 合法的 `else: if a: …` 其嵌套 IfRegion 的 entry 正落在 else 体内；判据 (b)
        #   保护它（它由末条件假边进入 = 成员前驱），而 @7582 由 merge 直接进入且无成员
        #   前驱，(a)(b) 同时成立才剔出。判别取自边数据，不取自区域 entry 身份。
        # ④嵌套处理（原则 3/4）：闭包不穿越任何成员块，臂内任意深度的嵌套区域仍只由
        #   bodies/conditions 以入口引用；剔出的块回归父层序列，由其自身已声明区域
        #   （IfRegion@7972 / LoopRegion@7706 / TryExceptRegion@8186 …）发射。merge 自身
        #   落在 final_else 里属另一族缺陷（TICKET_R21-78），本判据不介入。
        # ⑤入口引用语义：链的 elif_final_else 只保留真正的 else 臂入口（实测 @7492）；
        #   不新增区域类型、不新增 AST 节点类型、不改链头与各臂的边数据。
        # ⑥反编译流程：region_analyzer._build_elif_region → IfRegion.elif_final_else →
        #   region_ast_generator._if_generate_full_elif_chain → code_generator 发射 →
        #   pyc_verify 逐指令比对（尺子 oracle_diff_r104：hunks_vs_ORACLE / DELTAS instrs）。
        if merge is not None and elif_info.get("final_else"):
            _r2179_final_else = elif_info["final_else"]
            if merge not in _r2179_final_else:
                _r2179_walls = set()
                for _r2179_m in (block, condition_block):
                    if _r2179_m is not None:
                        _r2179_walls.add(_r2179_m)
                _r2179_walls.update(all_condition_blocks or set())
                _r2179_walls.update(then_blocks or [])
                _r2179_walls.update(elif_info.get("conditions") or [])
                for _r2179_body in (elif_info.get("bodies") or []):
                    _r2179_walls.update(_r2179_body)
                _r2179_tail = set()
                _r2179_seen = {merge}
                _r2179_stack = [merge]
                while _r2179_stack:
                    _r2179_b = _r2179_stack.pop()
                    for _r2179_s in (getattr(_r2179_b, 'successors', None) or []):
                        if _r2179_s in _r2179_walls or _r2179_s in _r2179_seen:
                            continue
                        _r2179_seen.add(_r2179_s)
                        _r2179_tail.add(_r2179_s)
                        _r2179_stack.append(_r2179_s)
                _r2179_kept = []
                for _r2179_f in _r2179_final_else:
                    _r2179_arm_entry = False
                    for _r2179_p in (getattr(_r2179_f, 'predecessors', None) or []):
                        if _r2179_p in _r2179_walls:
                            _r2179_arm_entry = True
                            break
                    if _r2179_f in _r2179_tail and not _r2179_arm_entry:
                        continue
                    _r2179_kept.append(_r2179_f)
                if _r2179_kept != _r2179_final_else:
                    elif_info["final_else"] = _r2179_kept
"""

MARKER = '_r2179_walls'


def emit(text):
    return b'\xef\xbb\xbf' + (CR + NL).join(text.split(NL)).encode('utf-8')


def main():
    install = '--install' in sys.argv
    src = SRC if os.path.isfile(SRC) else MIRROR_CORE
    blob = open(src, 'rb').read()
    pre16 = hashlib.sha256(blob).hexdigest()[:16]
    text = blob.decode('utf-8-sig').replace(CR + NL, NL).replace(CR, NL)
    print('[patch] SRC=%s sha16=%s size=%d' % (src, pre16, len(blob)))
    if MARKER in text:
        print('[patch] already patched (marker %r present) -- idempotent rebuild from base' % MARKER)
        # rebuild from the pristine base so the emitted bytes are always the same
        if src != SRC:
            blob = open(SRC, 'rb').read()
            pre16 = hashlib.sha256(blob).hexdigest()[:16]
            text = blob.decode('utf-8-sig').replace(CR + NL, NL).replace(CR, NL)
            print('[patch] re-read pristine base SRC=%s sha16=%s' % (SRC, pre16))
    if pre16 != BASE_SHA16:
        print('[patch] REFUSED: base sha16 %s != pinned %s' % (pre16, BASE_SHA16))
        return 2
    n = text.count(ANCHOR)
    if n != 1:
        print('[patch] REFUSED: anchor occurs %d times (expected 1)' % n)
        return 3
    text = text.replace(ANCHOR, INSERT)
    assert MARKER in text, 'marker missing after patch'
    out = emit(text)
    assert out.count(b'\r\r\n') == 0, 'CR CR LF present'
    assert out.count(b'\n') == out.count(b'\r\n'), 'bare LF present'
    lines = len(text.split(NL))
    assert out.count(b'\r\n') == lines - 1, 'line count mismatch'
    os.makedirs(DELIVER_DIR, exist_ok=True)
    sha16 = hashlib.sha256(out).hexdigest()[:16]
    dst = os.path.join(DELIVER_DIR, 'CANDIDATE_r2179_%s.py' % sha16)
    with open(dst, 'wb') as f:
        f.write(out)
    print('[patch] wrote DST=%s sha16=%s size=%d lines=%d' % (dst, sha16, len(out), lines))
    try:
        py_compile.compile(dst, cfile=dst + '.check.pyc', doraise=True)
        print('[patch] py_compile OK')
    except Exception as e:
        print('[patch] PY_COMPILE FAILED: %s' % e)
        return 5
    finally:
        if os.path.exists(dst + '.check.pyc'):
            os.remove(dst + '.check.pyc')
    if install:
        with open(MIRROR_CORE, 'wb') as f:
            f.write(out)
        print('[patch] installed into %s sha16=%s' % (MIRROR_CORE, sha16))
    return 0


sys.exit(main())
