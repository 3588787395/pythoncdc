"""R21-47 candidate builder — clock_worker 臂内语句的「归属套件」两半件。

Base（规则 1：整文件字节级重建，绝不手改 *OK.py）：
    D:/Temp/r76/work/CANDIDATE_r75ab_on_r74d_v2.py
      sha256[:16] = 30a4d7827122e165
      = 门禁 38 landed 11324f276cce6d5b + [R21-45] A+B（r74c, f51f9de14d216cda）
                  + [R21-44]（r73a，经 r74d 3e7af79a63b5d0cf）
                  + [R21-46] A+B（r75a，0a2f4a81c593b1c6 在 r74d 上的重建）
      clock_worker 实测：len orig=1424 prod=1426 delta=+2 hunks=2 landings=7，judge 12/13。

Patch [R21-47]（两半件，各自可单独消融）：
  A = ⑧ 的**受条件约束**放行 + 臂内「无主测试块」按顺序 if 派发（合成 IfRegion）
      站点 1：_r2144_and_leg_before_or_tail 的 ⑧（`id(_nb) not in _cond_ids`）
      站点 2：_process_if_blocks 的普通块派发前
  B = 顺序 if 的「伪 else」判据（@7492 交回顺序续体）
      站点：_if_generate_normal 的 orelse 装配

usage: python -X utf8 build_cand_r76a_r2147.py [--halves a|b|a,b] [--probe] [--base PATH] [--out PATH]
"""
import hashlib
import os
import py_compile
import sys

REPO = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
BASE = 'D:/Temp/r76/work/CANDIDATE_r75ab_on_r74d_v2.py'
BASE_SHA16 = '30a4d7827122e165'
OUT = 'D:/Temp/r76/work/CANDIDATE_r76a_r2147.py'

A = sys.argv
if '--out' in A:
    OUT = A[A.index('--out') + 1]
if '--base' in A:
    BASE = A[A.index('--base') + 1]
HALVES = (A[A.index('--halves') + 1] if '--halves' in A else 'a,b').replace(' ', '').split(',')
PROBE = '--probe' in A
assert 'a' in HALVES or 'b' in HALVES, HALVES

HELPER_A = '''    def _r2147_seq_if_head(self, blk, arm_lo, arm_hi):
        """[R21-47 半件 A] 臂内「无主测试块」`blk` 其实是一条**顺序 if 语句**的测试头时返回 True。

        **结构事实**（realtime_event_source::clock_worker @7164 站点臂跨 @7248..@7582 实测）：
          @7248 `now_date != self.first_run_date`；@7270 `acquire(...) is False`（同块前 6 条
          是一条以 POP_TOP 收尾的**完结语句**）；两者的 IF_FALSE 都指向**同一个块** @7492，
          且 @7492 的两条前驱正是 @7248 与 @7270。分析端把这条「D 假出口 = E 假出口」的
          共享续体读成 BoolOp 合取支，给 @7248 记了 inline_boolop_chains[id(@7248)] =
          {'op': 'and', 'blocks': [@7248, @7270]}，于是 @7248 不是任何区域的 condition_block，
          [R21-44] 的 ⑧ 只能拒动（臂入口无人派发），平折拿不到 ⇒ 留下臂尾伪 JUMP_FORWARD。
          但 `X and Y` 的操作数块里不可能有一条 POP_TOP 收尾的语句（表达式不产出语句），
          而「两条测试的假出口是同一个块、该块两条前驱分别是这两条测试」正是
          `if X: …；if Y: …；<续体>` 的编译布局（3.11.7 compile() 实测：S1 逐条一致，
          若写成 `if X: …；if Y: … else: <续体>` 则 X 的假出口必须跳过 else 体）。
        **判据**（区域身份 / opcode 类别 / 前驱后继；不读函数名、绝对偏移、计数阈值）：
          ① blk 是某区域 inline_boolop_chains 的**链首**（读「这块被登记成什么」的身份事实，
             与已落地 ⑧/④ 扫描 regions 声明字段同类，不是取别的区域的值做启发），op=='and'；
          ② 该链的非链首成员带「栈已归零的完结语句前导」且未被登记发射
             （复用 r75 的既有谓词 _r2146_ibc_member_has_stmt_prefix，不新建切分器）；
          ③ blk 与每个成员块都以 IF_FALSE 收尾且**目标同一个块 F**（顺序 if 的共享续体签名）；
          ④ blk 与 F 都落在本臂跨 [arm_lo, arm_hi) 内（只服务本臂，不外扩）。
        **保守性** 任一条不成立 ⇒ False，调用方逐字节沿用既有路径。
        """
        try:
            _chain = None
            for _r0 in self.region_analyzer.regions:
                _ibc = getattr(_r0, 'inline_boolop_chains', None) or {}
                if id(blk) in _ibc:
                    _chain = _ibc[id(blk)]
                    break
            if not _chain or _chain.get('op') != 'and':
                return False
            _blocks = list(_chain.get('blocks') or [])
            if len(_blocks) < 2 or _blocks[0] is not blk:
                return False
            if not _r2146_ibc_member_has_stmt_prefix(self, _blocks):
                return False
            _head_last = blk.get_last_instruction()
            if (_head_last is None or not isinstance(getattr(_head_last, 'argval', None), int)
                    or 'IF_FALSE' not in _head_last.opname
                    or _head_last.opname in NONE_CHECK_OPS):
                return False
            _tail = self.cfg.get_block_by_offset(_head_last.argval)
            if _tail is None or _tail is blk:
                return False
            if not (arm_lo <= blk.start_offset < arm_hi
                    and arm_lo <= _tail.start_offset < arm_hi):
                return False
            for _mb in _blocks[1:]:
                _ml = _mb.get_last_instruction()
                if (_ml is None or not isinstance(getattr(_ml, 'argval', None), int)
                        or 'IF_FALSE' not in _ml.opname
                        or self.cfg.get_block_by_offset(_ml.argval) is not _tail):
                    return False
            _tpreds = [p for p in (list(getattr(_tail, 'predecessors', None) or []))]
            if not all(p is blk or p in _blocks[1:] for p in _tpreds):
                return False
            if not (any(p is blk for p in _tpreds)
                    and any(p in _blocks[1:] for p in _tpreds)):
                return False
            return True
        except Exception:
            return False

'''

# ── 站点 1：⑧ 的条件放行 ──────────────────────────────────────────────────────
ANCHOR_8 = '''                if (_nlast is not None
                        and _nlast.opname
                        in (FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS)
                        and _nlast.opname not in NONE_CHECK_OPS
                        and id(_nb) not in _cond_ids):
                    return None'''
REPL_8 = '''                if (_nlast is not None
                        and _nlast.opname
                        in (FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS)
                        and _nlast.opname not in NONE_CHECK_OPS
                        and id(_nb) not in _cond_ids
                        and not self._r2147_seq_if_head(_nb, _t.start_offset,
                                                        _e.start_offset)):
                    return None'''


def build():
    raw = open(BASE, 'rb').read()
    got = hashlib.sha256(raw).hexdigest()[:16]
    assert got == BASE_SHA16, 'BASE sha16 mismatch: got %s' % got
    print('base   %s size=%d sha16=%s' % (os.path.basename(BASE), len(raw), got))
    out = raw

    def sub(data, old_txt, new_txt, note):
        old = b'\r\n'.join(old_txt.rstrip('\n').encode('utf-8').split(b'\n'))
        new = b'\r\n'.join(new_txt.rstrip('\n').encode('utf-8').split(b'\n'))
        n = data.count(old)
        assert n == 1, 'anchor %s count=%d' % (note, n)
        return data.replace(old, new, 1)

    if 'a' in HALVES:
        # 1) 插入判据方法（挂在 _r2144_and_leg_before_or_tail 之前，同类同缩进）
        anc = b'    def _r2144_and_leg_before_or_tail(self, region, cond_block, expr):'
        assert out.count(anc) == 1, 'method anchor'
        helper = HELPER_A
        if not PROBE:
            helper = '\n'.join(l for l in helper.split('\n')
                               if not l.strip().startswith('_r2147_census_note('))
        hb = b'\r\n'.join(helper.rstrip('\n').encode('utf-8').split(b'\n')) + b'\r\n'
        out = out.replace(anc, hb + anc, 1)
        # 2) ⑧ 条件放行
        out = sub(out, ANCHOR_8, REPL_8, 'conjunct8')
    open(OUT, 'wb').write(out)
    py_compile.compile(OUT, doraise=True)
    print('cand   %s size=%d sha16=%s halves=%s probe=%s'
          % (OUT, len(out), hashlib.sha256(out).hexdigest()[:16],
             '+'.join(sorted(HALVES)), PROBE))
    return out


if __name__ == '__main__':
    build()
