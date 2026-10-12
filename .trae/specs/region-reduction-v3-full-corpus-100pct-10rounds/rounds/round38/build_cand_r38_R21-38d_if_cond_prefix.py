"""R38 candidate (R21-38d): emit an IfRegion condition block's leading statement segment.

Measured basis (all on the gate-37 landed bytes, mirror-only diagnostics):
  realtime_event_source.clock_worker  delta -113 -> -6 with [R21-24-M1]+P1+P2, panel 20 files ->
  19 byte-identical, 0 regressions, 0 flips. The -6 residual is two named losses:
    (A) system_log.debug('获取重登信号量')  orig @7270..@7308 (6 instr) absent from the product;
    (B) self.before_trading_date = now_date orig @6778..@6782 emitted at the loop tail (@9170).
  (A) is a region-shape gap: the census (census_clock_r63.py on the landed analyzer) declares
  `IfRegion condition_block=@7270..@7370(17) then=[7372,7488] else=[7492] merge=@7582..@7602` -
  i.e. CPython fused the debug CALL statement and the following test into one maximal straight-line
  block, and that block is an IfRegion CONDITION block. `_generate_if` never cuts a statement
  prefix out of its condition block: `_split_block_condition_prefix` has exactly three consumers
  today (AssertRegion :643, LoopRegion R23-B :7654, ternary :43118/:43533/:43599), so the block is
  marked generated whole while its 6 leading instructions are emitted by nobody. The landed
  `guard_clause_prefix_end` path is a BoolOp-chain special case (region_analyzer writes it only for
  a BoolOpRegion owner), and this test is `acquire(...) is False` - a plain Compare, no BoolOp.

Fix shape = the same cut, the same ledger, a fourth consumer (no new predicate):
  helper `_r38_if_cond_prefix_stmts` calls the existing stack-depth cutter, drops the part already
  registered in `prefix_emitted_upto` (offset granularity, monotone, per _register_prefix_emitted's
  own contract), builds statements with the existing builder, registers, returns them; the two
  `_generate_if` dispatchers prepend them to the region's result (list or dict).
Conservatism: cutter returns [] when the block does not end in a conditional jump, when stack
simulation underflows, or when the prefix is pure noise -> byte-identical product for every region
that is not a dual-role block.

usage: python -X utf8 build_cand_r38_R21-38d_if_cond_prefix.py <generator-file>
"""
import hashlib
import py_compile
import sys

HELPER = [
    "    def _r38_if_cond_prefix_stmts(self, region) -> List[Dict[str, Any]]:",
    "        \"\"\"[R21-38-r63c] IfRegion 条件块的「前导语句段」发射 —— 与 R23-B 的 LoopRegion 同一条划界。",
    "",
    "        1. 算法依据：基本块是极大直线块；若块末是条件跳转，该块在语义上承载「已完结语句段",
    "           + 尾部条件表达式段」两层。切点只由块内栈深前向模拟给出（最后一次回到深度 0 之后），",
    "           与语法形式无关 —— 复用 _split_block_condition_prefix，本方法不新增判据。",
    "        2. 归约顺序（原则 1）：前导段是块内更低层的结构，先于条件表达式归约并发射；调用方",
    "           （两个 _generate_if 派发点）把它接在本区域结果之前，父序列得到 [stmts..., If]。",
    "        3. 唯一归属（原则 2）：块的条件语义归本 IfRegion，块的前导语句归父序列，分界记在",
    "           prefix_emitted_upto（指令偏移，只增不减）。此前整块被登记为已生成而前导无人发射",
    "           （实测 clock_worker 条件块 @7270..@7370 的 6 条 debug 调用指令即丢于此）。",
    "        4. 嵌套即抽象节点（原则 3）：If 仍是单个抽象节点，前导不是第二个节点。",
    "        保守性：切点不存在/栈下溢/纯噪声段/已被他人发射 → 返回空，与修改前逐字节相同。",
    "        \"\"\"",
    "        cb = getattr(region, 'condition_block', None)",
    "        if cb is None:",
    "            cb = getattr(region, 'entry', None)",
    "        if cb is None or not getattr(cb, 'instructions', None):",
    "            return []",
    "        _r38_prefix = self._split_block_condition_prefix(cb)",
    "        if not _r38_prefix:",
    "            return []",
    "        _r38_upto = self.prefix_emitted_upto.get(cb, -1)",
    "        _r38_prefix = [i for i in _r38_prefix if i.offset > _r38_upto]",
    "        if not _r38_prefix:",
    "            return []",
    "        _r38_stmts = self._build_statements_from_instructions(_r38_prefix, cb)",
    "        if not _r38_stmts:",
    "            return []",
    "        self._register_prefix_emitted(cb, _r38_prefix)",
    "        return _r38_stmts",
    "",
]

HOOK_A_OLD = [
    "            if self._consume_top_level_async_protocol_if(region):",
    "                return None",
    "            return self._generate_if(region)",
]
HOOK_A_NEW = [
    "            if self._consume_top_level_async_protocol_if(region):",
    "                return None",
    "            _r38_pre = self._r38_if_cond_prefix_stmts(region)",
    "            _r38_res = self._generate_if(region)",
    "            if _r38_pre:",
    "                _r38_tail = _r38_res if isinstance(_r38_res, list) else ([] if _r38_res is None else [_r38_res])",
    "                return list(_r38_pre) + _r38_tail",
    "            return _r38_res",
]

HOOK_B_OLD = [
    "    def _if_generate_branch_stmts(self, blocks=None, _depth=0, region=None):",
    "        if region is not None:",
    "            return self._generate_if(region)",
]
HOOK_B_NEW = [
    "    def _if_generate_branch_stmts(self, blocks=None, _depth=0, region=None):",
    "        if region is not None:",
    "            _r38_pre_b = self._r38_if_cond_prefix_stmts(region)",
    "            _r38_res_b = self._generate_if(region)",
    "            if _r38_pre_b:",
    "                _r38_tail_b = _r38_res_b if isinstance(_r38_res_b, list) else ([] if _r38_res_b is None else [_r38_res_b])",
    "                return list(_r38_pre_b) + _r38_tail_b",
    "            return _r38_res_b",
]


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def splice(lines, old, new, tag, must_contain=None):
    ob = [x.encode('utf-8') for x in old]
    hits = [n for n in range(len(lines) - len(ob) + 1) if lines[n:n + len(ob)] == ob]
    assert len(hits) == 1, '%s: anchor hits %d (must be unique)' % (tag, len(hits))
    n = hits[0]
    if must_contain:
        ctx = b'\r\n'.join(lines[max(0, n - 900):n + len(ob) + 900])
        assert must_contain.encode('utf-8') in ctx, '%s: anchor in the wrong neighbourhood' % tag
    return n, lines[:n] + [x.encode('utf-8') for x in new] + lines[n + len(old):]


def main():
    target = sys.argv[1]
    which = (sys.argv[2] if len(sys.argv) > 2 else 'both').upper()
    raw = open(target, 'rb').read()
    pre = sha16(raw)
    assert raw.startswith(b'\xef\xbb\xbf'), 'expected BOM'
    assert raw.count(b'\n') == raw.count(b'\r\n'), 'mixed newlines - refuse'
    lines = raw.split(b'\r\n')

    # right-to-left so earlier offsets stay valid
    nC = None
    if which in ('B', 'BOTH'):
        nC, lines = splice(lines, HOOK_B_OLD, HOOK_B_NEW, 'hook B (_if_generate_branch_stmts)')
    nA = None
    if which in ('A', 'BOTH'):
        nA, lines = splice(lines, HOOK_A_OLD, HOOK_A_NEW, 'hook A (_generate_region If dispatch)',
                           must_contain='def _generate_region')
    nH = lines.index(b'    def _generate_if(self, region: IfRegion) -> Union[Dict[str, Any], List[Dict[str, Any]]]:')
    lines = lines[:nH] + [x.encode('utf-8') for x in HELPER] + lines[nH:]
    patched = b'\r\n'.join(lines)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('which=%s hookA @%s hookB @%s helper @%d (+%d lines) size=%d sha16=%s (was %s) py_compile=OK'
          % (which, nA + 1 if nA is not None else '-', nC + 1 if nC is not None else '-',
             nH + 1, len(HELPER), len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
