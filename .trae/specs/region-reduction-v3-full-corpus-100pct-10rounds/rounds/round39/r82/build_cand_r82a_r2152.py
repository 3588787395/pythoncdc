"""R21-52 candidate builder — 成员块资格：被 POP_TOP 抢先消费的推送值不是布尔操作数。

基（整文件字节级重建，绝不手改 *OK.py）：
    REPO/.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round39/r75/
      CANDIDATE_r75a_r2146_AB_on_r74d_30a4d7827122e165.py    sha256[:16] = 30a4d7827122e165
    analyzer 保持 landed f7d849e974904492（本 builder 默认不改分析端）。

补丁（本工单唯一机制 [R21-52]，两处，均在 core/cfg/region_ast_generator.py）：
  1) 新方法 `_r2152_ibc_member_is_operand`，插在既有否证器 `_inline_and_chain_exits_agree`
     之后（同一层次、同一保守性：证据不足一律返回 True=维持既有折叠）。
  2) 消费点：`_if_generate_elif_chain` 的 elif 条件 ibc 查找处，插在 [R21-13]/[R21-46]
     **之前**，作用于分析端原始记录：从第一个不合格成员起截断链成员资格，被截下的成员块
     经既有 [R21-13] 通道 `_r2113_legs_back` 交还臂体。整条链的 elif_conditions /
     elif_final_else 一字不动 —— 这是它与已否证的 [R21-49]（分析端 break / return None，
     -269）唯一的区别。

usage: python -X utf8 build_cand_r82a_r2152.py [--out PATH] [--probe] [--expect-sha16 HEX]
"""
import hashlib
import os
import py_compile
import sys

REPO = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
BASE = (REPO + '/.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/'
        'round39/r75/CANDIDATE_r75a_r2146_AB_on_r74d_30a4d7827122e165.py')
BASE_SHA16 = '30a4d7827122e165'
OUT = 'D:/Temp/r82/work/CANDIDATE_r82a_r2152_generator.py'

A = sys.argv
if '--out' in A:
    OUT = A[A.index('--out') + 1]
if '--expect-sha16' in A:
    BASE_SHA16 = A[A.index('--expect-sha16') + 1]
PROBE = '--probe' in A


def sha16(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


raw = open(BASE, 'rb').read()
assert sha16(raw) == BASE_SHA16, (sha16(raw), BASE_SHA16)
lines = raw.split(b'\r\n')
assert b'\r\r\n' not in raw, 'base already has CR CR LF'
n_before = len(lines)

# ── 探针（--probe）：只在环境变量 R2152_CENSUS 指向路径时追加一行；不参与任何判定 ──
PROBE_FN = '''def _r2152_census_note(stage, detail=''):
    """[R21-52 普查探针] 仅当环境变量 R2152_CENSUS 指向路径时追加一行；否则立即返回。

    探针不参与任何判定：判据主体不使用它的返回值，FIRE 行写在全部合取成立之后、真正改
    `_inline_chain_info` / `_r2113_legs_back` 之前。开/关探针必须产物逐字节一致，否则
    普查读数作废（规则 2）。
    """
    import os as _os_r2152
    _p = _os_r2152.environ.get('R2152_CENSUS')
    if not _p:
        return
    try:
        with open(_p, 'a', encoding='utf-8') as _f_r2152:
            _f_r2152.write('%s %s\\r\\n' % (stage, detail))
    except Exception:
        pass
'''.replace('\n', '\r\n')

METHOD = '''    def _r2152_ibc_member_is_operand(self, blk) -> bool:
        """[R21-52] inline_boolop_chains 的**成员块资格**核验：该块推送的值是否真的由
        本链自己的终结条件跳转消费（即它是布尔操作数），还是被一条 POP_TOP 抢先消费
        （即它是臂内的一条完结语句，其后才跟着下一个测试）。

        **算法依据** CPython 3.11 的 `A and B` / `A or B` 短路链把每个操作数编成「求值该
        操作数 → 由块末条件跳转消费其唯一栈值」的直线块：块内值栈从入口深度 0 单调抬升到
        1，**中途绝不归零**。归零只有一种成因——一条语句执行完毕后把它的返回值丢弃，而
        语句级丢弃的 opcode 恰是 `POP_TOP`（`f()`、`x.method()`、链式比较的临时量清理都
        在此列）。于是「块末条件跳转之前出现把栈带回入口深度 0 的 POP_TOP」证明该块承载
        「先执行一条语句、再求值下一个测试」两段内容，它是**语句序列**而非本链的操作数；
        把它吸收进条件既表达不了那条语句，也没有第二个发射者（成员块整体被记为已生成），
        实测后果就是 realtime_event_source::clock_worker 的 `system_log.debug(...)`。
        与已落地的 `[R21-13]` 否证器 `_inline_and_chain_exits_agree` 同域同层：那个读
        **跳转目标**（各腿出口是否同一块），本方法读**块内栈形**（成员自己的值归谁消费）。

        **输入契约** blk: 链成员 BasicBlock（链首由调用方保留，不送本方法）。

        **归约方式** 返回 bool。True = 维持吸收（含证据不足）；False = 该成员不得吸收，
        调用方从该成员起截断链成员资格并把截下的成员交还臂体。

        **唯一归属判定** 只读块内指令与 CPython 自己声明的 stack effect
        （`_instruction_stack_effect`，既有切分器 `_split_block_condition_prefix` 同源），
        不标记 generated_blocks、不改块归属、不读函数名/绝对偏移/计数器/阈值。

        **保守性** 空块、块末非条件跳转、任一指令取不到栈效应、模拟中出现栈下溢 —— 一律
        返回 True，产物逐字节沿用既有折叠路径，绝不因证据不足而否决（与
        `_inline_and_chain_exits_agree` 的「只在测得矛盾时否决」同规）。
        """
        try:
            _instrs = list(blk.instructions or [])
        except Exception:
            return True
        if not _instrs:
            return True
        _term = _instrs[-1]
        if _term.opname not in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS
                                | NONE_CHECK_OPS):
            return True
        _depth = 0
        for _ins in _instrs[:-1]:
            if _ins.opname in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG'):
                continue
            _eff = self._instruction_stack_effect(_ins)
            if _eff is None or _depth + _eff < 0:
                return True
            _depth += _eff
            if _ins.opname == 'POP_TOP' and _depth == 0:
                return False
        return True
'''.replace('\n', '\r\n')

SITE = '''            # [R21-52] 成员块资格核验（在 [R21-13]/[R21-46] 之前，直接作用于分析端原始
            # 记录）：只有「推送值由本链自己的终结条件跳转消费」的块才是布尔操作数。成员块
            # 内若有 POP_TOP 先把值栈带回入口深度 0（= 一条完结语句闭合），该块是臂内顺序
            # 内容（`语句; 下一个测试`）。处置 = **从第一个不合格成员起截断链成员资格**，
            # 截下的成员块经既有 [R21-13] 通道 `_r2113_legs_back` 交还臂体；整条链的
            # elif_conditions / elif_final_else 一字不动（与已否证的 [R21-49] 分析端
            # break/return None 的唯一区别，那条把 44 块的函数尾归属一起摘走 → -269）。
            if _inline_chain_info and (_inline_chain_info.get('blocks') or []):
                _r2152_blocks = list(_inline_chain_info.get('blocks') or [])
                _r2152_keep = _r2152_blocks[:1]
                for _r2152_m in _r2152_blocks[1:]:
                    if not self._r2152_ibc_member_is_operand(_r2152_m):
                        break
                    _r2152_keep.append(_r2152_m)
                if len(_r2152_keep) < len(_r2152_blocks):
                    if PROBE_MARKER:
                        _r2152_census_note(
                            'FIRE', 'head=%s op=%s blocks=%s kept=%s dropped=%s' % (
                                getattr(_r2152_blocks[0], 'start_offset', None),
                                _inline_chain_info.get('op'),
                                [getattr(_b, 'start_offset', None) for _b in _r2152_blocks],
                                [getattr(_b, 'start_offset', None) for _b in _r2152_keep],
                                [getattr(_b, 'start_offset', None)
                                 for _b in _r2152_blocks[len(_r2152_keep):]]))
                    if PROBE_MARKER:
                        _r2152_census_note('EVAL_TOTAL')
                    _r2152_dropped = _r2152_blocks[len(_r2152_keep):]
                    if len(_r2152_keep) >= 2:
                        _inline_chain_info = dict(_inline_chain_info)
                        _inline_chain_info['blocks'] = _r2152_keep
                    else:
                        _inline_chain_info = None
                    _r2113_legs_back = _r2152_dropped + list(_r2113_legs_back)
                elif PROBE_MARKER:
                    _r2152_census_note('EVAL_TOTAL')
'''.replace('\n', '\r\n')


def find_unique(needle):
    hits = [i for i, l in enumerate(lines) if needle in l]
    assert len(hits) == 1, (needle.decode('utf-8', 'replace')[:90], len(hits))
    return hits[0]


# 1) 方法插在 `_inline_and_chain_exits_agree` 之后（其唯一收尾行 = all(...) 那行）
idx = find_unique(b"        return all(_x is _exits[0] for _x in _exits[1:])")
method_lines = [l.encode('utf-8') for l in METHOD.split('\r\n')[:-1]]
lines[idx + 1:idx + 1] = [b''] + method_lines

# 2) 消费点插在 [R21-13] 判据块之前（[R21-46] 块的头部注释唯一，用它定位其所在 if）
anchor = find_unique(b"            # [R21-13 \xe5\x88\xa4\xe6\x8d\xae]")
site_lines = [l.encode('utf-8') for l in SITE.split('\r\n')[:-1]]
lines[anchor:anchor] = site_lines

out = b'\r\n'.join(lines)
if PROBE:
    _ol = out.split(b'\r\n')
    _cls = next(i for i, _l in enumerate(_ol) if _l.startswith(b'class RegionASTGenerator:'))
    _ol[_cls:_cls] = [l.encode('utf-8') for l in PROBE_FN.split('\r\n')[:-1]]
    out = b'\r\n'.join(_ol).replace(b'PROBE_MARKER', b'True')
else:
    out = out.replace(b'PROBE_MARKER', b'False')

assert b'\r\r\n' not in out, 'CR CR LF introduced'
open(OUT, 'wb').write(out)
py_compile.compile(OUT, doraise=True)
print('base      sha16 = %s   bytes=%d lines=%d' % (sha16(raw), len(raw), n_before))
print('candidate sha16 = %s   bytes=%d lines=%d  probe=%s' % (sha16(out), len(out),
                                                              len(out.split(b'\r\n')), PROBE))
print('added lines = %d' % (len(out.split(b'\r\n')) - n_before))
print('out = %s' % OUT)
