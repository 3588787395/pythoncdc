"""build_cand_r85a_r2155.py — byte-exact rebuild of the [R21-55] ANALYZER candidate from the
gate-38 landed bytes (region_analyzer.py sha16 f7d849e974904492).

Installs
  (1) method `_r2155_diamond_join_from_value_blocks` (before `def _identify_ternary_regions`)
  (2) its mounting point in `_detect_ternary_pattern`'s merge-cascade, right before the
      `value_target = None` / `merge_context = None` scan so the recovered join is seen by
      every downstream consumer.

BOM + all-CRLF preserved; each anchor asserted unique; refuses on `\\r\\r\\n`.
Prints sha16 before/after.

usage: python -X utf8 build_cand_r85a_r2155.py [SRC] [DST]
"""
import hashlib
import os
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "core/cfg/region_analyzer.py"
DST = sys.argv[2] if len(sys.argv) > 2 else "DELIVER/CANDIDATE_r85a_r2155_diamond_join_region_analyzer.py"

raw = open(SRC, "rb").read()
print("SRC sha16 =", hashlib.sha256(raw).hexdigest()[:16], "bytes =", len(raw))
if raw[:3] != b"\xef\xbb\xbf":
    raise SystemExit("base is not BOM-prefixed, refusing")
if b"\r\r\n" in raw:
    raise SystemExit("base already has \\r\\r\\n, refusing")
if raw.count(b"\n") != raw.count(b"\r\n"):
    raise SystemExit("base is not all-CRLF, refusing")
lines = raw.split(b"\r\n")


def find_unique(exact=None, sw=None):
    hits = [i for i, l in enumerate(lines)
            if (exact is not None and l.strip() == exact)
            or (sw is not None and l.strip().startswith(sw))]
    if len(hits) != 1:
        raise SystemExit("anchor not unique (%d): %r" % (len(hits), exact or sw))
    return hits[0]


METHOD_LINES = [
    "    def _r2155_diamond_join_from_value_blocks(self, true_block, false_block):",
    '        """[R21-55] 结构判据：值钻石（三元表达式的两条臂）的汇合块由「显式无条件跳转 +',
    "        前驱唯一」确定，而不是由后支配树确定。",
    "",
    "        结构事实（只读本块/邻块的 opcode 类与前驱后继，不读函数名、绝对偏移、计数器、",
    "        跨区域/跨层次信息）：",
    "          ① true_block 末指令是无条件前跳（JUMP_FORWARD / JUMP_ABSOLUTE），目标块 J；",
    "          ② J 同时是 false_block 的后继（false 臂顺序落合到 J）；",
    "          ③ false_block 末指令不是条件/短路跳转，即 false 臂是值块而非另一条语句级分支；",
    "          ④ J 不是异常入口块（首指令非 PUSH_EXC_INFO / WITH_EXCEPT_START）；",
    "          ⑤ J 的前驱集合恰为 {true_block, false_block}，即 J 不被任何其他正常控制流进入。",
    "",
    "        为什么是「可证」而非「偏好」：调用方在进入本判据前已用 _is_ternary_block 校验两臂",
    "        均为单值块，①②⑤ 说明 J 只可能在这两条臂之后出现，且每条臂各带恰好一个栈上值进入",
    "        J——因此 J 就是该三元值的唯一消费点。异常边（try 范围内每个块都挂一条指向 handler",
    "        的边）为两臂各自引入一条绕过 J 的路径，使 find_nearest_common_post_dominator 返回",
    "        None；异常边不是正常完成路径，不改变「正常完成必到 J」这一结构事实。",
    "",
    "        保守性：任一条不成立即返回 None ⇒ 调用方保持 [R47 消费点守卫] 的原判决（拒绝创建",
    "        该 TernaryRegion），产物逐字节不变。①③ 各自独立排除语句级 if/else（臂以条件跳转",
    "        结尾）——实测同文件 market_fund_transfer:@126 即被 ①③ 双重复否。",
    "        本方法无副作用，可被探针包裹做点名数派并证惯性。",
    "        \"\"\"",
    "        _JUMP_FWD = ('JUMP_FORWARD', 'JUMP_ABSOLUTE')",
    "        _COND_TAIL = FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS",
    "        _EXC_ENTRY = ('PUSH_EXC_INFO', 'WITH_EXCEPT_START')",
    "        _t_last = true_block.get_last_instruction()",
    "        if _t_last is None or not isinstance(_t_last.argval, int):",
    "            return None",
    "        if _t_last.opname not in _JUMP_FWD:",
    "            return None",
    "        _join = self.cfg.get_block_by_offset(_t_last.argval)",
    "        if _join is None or _join is true_block or _join is false_block:",
    "            return None",
    "        if _join not in list(false_block.successors or []):",
    "            return None",
    "        _f_last = false_block.get_last_instruction()",
    "        if _f_last is not None and _f_last.opname in _COND_TAIL:",
    "            return None",
    "        _j_first = _join.get_first_instruction()",
    "        if _j_first is not None and _j_first.opname in _EXC_ENTRY:",
    "            return None",
    "        _preds = [p for p in (_join.predecessors or []) if p is not None]",
    "        if len(_preds) != 2:",
    "            return None",
    "        if set(id(p) for p in _preds) != {id(true_block), id(false_block)}:",
    "            return None",
    "        return _join",
    "",
    "",
]

MOUNT_LINES = [
    "            # [R21-55] 汇合块由值钻石的显式跳转与前驱唯一性恢复，取代「只有后支配树",
    "            # 才能给出 merge」这一前提：try 范围内的异常边使 find_nearest_common_post_",
    "            # dominator 返回 None，[R47 消费点守卫] 随即整体拒绝该三元候选，区域交给",
    "            # IfRegion 按语句级归约——IfRegion 只能表示语句级 if，于是把宿主语句（一条",
    "            # f-string/format 调用）连同两个常量臂一起丢成空臂（实测 _process_order 的",
    "            # 14 个窗口 / -68 条指令全部由此产生）。判据与可证性见",
    "            # _r2155_diamond_join_from_value_blocks；任一条不成立即保持 [R47] 原判决。",
    "            # 挂载点必须在 value_target / merge_context 扫描之前：区域一旦补齐，其后",
    "            # merge_context 判定与 all_blocks.add(merge_block) 都要看到同一个汇合块",
    "            # （依「每块唯一归属」，汇合块归属本三元区域）。",
    "            if merge_block is None:",
    "                _r2155_join = self._r2155_diamond_join_from_value_blocks(",
    "                    true_block, false_block)",
    "                if _r2155_join is not None:",
    "                    merge_block = _r2155_join",
    "",
]

# (1) mount inside _detect_ternary_pattern's merge cascade, just before the value scan.
# anchor = the two-line sequence `value_target = None` / `merge_context = None  # 新增…`
# (the single line occurs 8x in the file, the pair exactly once).
vi = [i for i in range(len(lines) - 1)
      if lines[i].strip() == b"value_target = None"
      and lines[i + 1].strip().startswith(b"merge_context = None")]
if len(vi) != 1:
    raise SystemExit("mount anchor pair not unique (%d)" % len(vi))
vi = vi[0]
lines[vi:vi] = [l.encode("utf-8") for l in MOUNT_LINES]

# (2) the method, before _identify_ternary_regions
mi = find_unique(sw=b"def _identify_ternary_regions")
lines[mi:mi] = [l.encode("utf-8") for l in METHOD_LINES]

out = b"\r\n".join(lines)
if b"\r\r\n" in out:
    raise SystemExit("produced \\r\\r\\n, refusing")
assert out[:3] == b"\xef\xbb\xbf"
os.makedirs(os.path.dirname(DST) or ".", exist_ok=True)
open(DST, "wb").write(out)
print("DST =", DST)
print("DST sha16 =", hashlib.sha256(out).hexdigest()[:16], "bytes =", len(out))
compile(out.decode("utf-8-sig"), DST, "exec")
print("compile: OK")
import py_compile
py_compile.compile(DST, doraise=True)
print("py_compile: OK")
