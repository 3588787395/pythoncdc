"""build_cand_r71a_r2144.py — reconstruct CANDIDATE_r71a_region_analyzer.py byte-exactly
from the LANDED bytes (region_analyzer.py sha16 f7d849e974904492) by inserting the R21-44
analyzer-side compound-while detector (or-head run + bracketed and-tail group, the
structural mirror of the landed [R7-B45]) + its single call site.

Landed source: repo core/cfg/region_analyzer.py (READ-ONLY).
Output: D:/Temp/r71/CANDIDATE_r71a_region_analyzer.py  (BOM + all-CRLF preserved).

Asserts: sha16(f7d849e974904492) base; each anchor occurs exactly once; py_compile passes.
NOTE (campaign Rule 3): this candidate is BANKED, NOT installed — see FIX doc: it fires
uniquely on _sync_worker but produces ZERO unit flips (the BoolOpRegion is reclaimed by the
block_to_region priority rebuild at :1871/:4119, and even forced retention leaves a
`while False: pass` back-edge residue, worsening delta -3 -> +19).
"""
import hashlib, os, py_compile, sys

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
LANDED = os.path.join(REPO, "core/cfg/region_analyzer.py")
OUT = r"D:/Temp/r71/CANDIDATE_r71a_region_analyzer.py"
BASE_SHA16 = "f7d849e974904492"

def sha16(b): return hashlib.sha256(b).hexdigest()[:16]

raw = open(LANDED, "rb").read()
assert raw[:3] == b"\xef\xbb\xbf", "landed file must start with UTF-8 BOM"
assert sha16(raw) == BASE_SHA16, "landed bytes hash mismatch: got %s want %s" % (sha16(raw), BASE_SHA16)
assert raw.count(b"\n") == raw.count(b"\r\n"), "landed file must be all-CRLF"
lines = raw.split(b"\r\n")   # BOM stays on line 0 bytes after split? BOM is before first line text
# NOTE: split keeps BOM in lines[0]; we re-join, so untouched.

METHOD_LINES = [
    "    def _r2144_detect_while_condition_nested_or_and(self, cond_block: BasicBlock,",
    "                                                   loop: LoopRegion) -> Optional[List[Tuple[BasicBlock, str]]]:",
    '        """[R21-44] 检测 while 复合条件「or 头前缀 run + 括号化 and 尾组」嵌套链（[R7-B45] 结构镜像）。',
    "",
    "        结构事实（识别只读区域数据 / opcode 类别 / 前驱后继，[C1]，无名字/偏移/计数/阈值）：",
    "          ① cond_block 末指令是前向条件跳转 POP_JUMP_FORWARD_IF_TRUE，其真边落点 = 循环体",
    "             入口 true_exit（属循环体语义集合），fall-through 续接下一个 or 操作数；",
    "          ② 沿 fall-through 前向走 or run：每成员末指令 IF_TRUE→true_exit、假边（另一后继）",
    "             续接下一成员，or run 成员数 ≥ 2；",
    "          ③ or run 末成员的假边续接一个以 POP_JUMP_FORWARD_IF_*→false_exit(≠true_exit) 收尾",
    "             的块，即括号化 and 尾组的头；and 尾组成员 ≥ 2，逐成员末指令跳转目标均为同一",
    "             false_exit，组末成员 fall-through（含沿纯 JUMP_FORWARD 连接块的有效落点）=",
    "             true_exit。true_exit ≠ false_exit ⇒ 扁平 all_same_target 判据结构性不满足，",
    "             这正是「or 头 + and 尾组」而非均匀 or 链的判别核心。",
    "        保守性：任一结构事实不成立即返回 None，调用方回退既有 walk，产物逐字节不变；连接",
    "          块跟随仅沿「唯一一条 JUMP_FORWARD/JUMP_BACKWARD 指令」的块推进（≤4 步），不读函数",
    "          名/绝对偏移/计数阈值；无副作用、单出口。[C2][C3]",
    "        \"\"\"",
    "        _r2144_noise = ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG', 'PUSH_NULL')",
    "        def _r2144_resolve(_self, _b):",
    "            _seen = 0",
    "            while _b is not None and _seen < 4:",
    "                _eff = [i for i in _b.instructions if i.opname not in _r2144_noise]",
    "                if (len(_eff) == 1 and _eff[0].opname in ('JUMP_FORWARD', 'JUMP_BACKWARD')",
    "                        and _eff[0].argval is not None):",
    "                    _b = _self.cfg.get_block_by_offset(_eff[0].argval); _seen += 1",
    "                else:",
    "                    return _b",
    "            return _b",
    "        if cond_block is None or loop is None or loop.header_block is None:",
    "            return None",
    "        _sem = set(loop.body_blocks or [])",
    "        _sem.add(loop.header_block)",
    "        if loop.entry is not None: _sem.add(loop.entry)",
    "        if loop.condition_block is not None: _sem.add(loop.condition_block)",
    "        _last = cond_block.get_last_instruction()",
    "        if (_last is None or _last.argval is None",
    "                or _last.opname not in FORWARD_CONDITIONAL_JUMP_OPS",
    "                or 'TRUE' not in _last.opname):",
    "            return None",
    "        _true_exit = _r2144_resolve(self, self.cfg.get_block_by_offset(_last.argval))",
    "        if _true_exit is None or _true_exit not in _sem:",
    "            return None",
    "        _or_members = []",
    "        _cur = cond_block",
    "        _false_exit = None",
    "        while True:",
    "            _cl = _cur.get_last_instruction()",
    "            if (_cl is None or _cl.argval is None",
    "                    or _cl.opname not in FORWARD_CONDITIONAL_JUMP_OPS):",
    "                return None",
    "            _succs = list(_cur.conditional_successors)",
    "            if len(_succs) != 2:",
    "                return None",
    "            _ft = next((s for s in _succs if s.start_offset != _cl.argval), None)",
    "            if _ft is None:",
    "                return None",
    "            _tgt = _r2144_resolve(self, self.cfg.get_block_by_offset(_cl.argval))",
    "            if 'TRUE' in _cl.opname and _tgt is _true_exit:",
    "                _or_members.append((_cur, 'or'))",
    "                if _ft in _sem:",
    "                    return None",
    "                _cur = _ft",
    "                continue",
    "            if 'FALSE' in _cl.opname and _tgt is not _true_exit:",
    "                _false_exit = _tgt",
    "                break",
    "            return None",
    "        if len(_or_members) < 2 or _false_exit is None:",
    "            return None",
    "        _and_members = []",
    "        while True:",
    "            _cl = _cur.get_last_instruction()",
    "            if (_cl is None or _cl.argval is None",
    "                    or _cl.opname not in FORWARD_CONDITIONAL_JUMP_OPS):",
    "                return None",
    "            _succs = list(_cur.conditional_successors)",
    "            if len(_succs) != 2:",
    "                return None",
    "            _ft = next((s for s in _succs if s.start_offset != _cl.argval), None)",
    "            _tgt = _r2144_resolve(self, self.cfg.get_block_by_offset(_cl.argval))",
    "            if _ft is None or _tgt is not _false_exit:",
    "                return None",
    "            _and_members.append((_cur, 'and'))",
    "            if _r2144_resolve(self, _ft) is _true_exit:",
    "                break",
    "            if _ft in _sem:",
    "                return None",
    "            _cur = _ft",
    "        if len(_and_members) < 2:",
    "            return None",
    "        return _or_members + _and_members",
    "",
]

CALL_LINES = [
    "        # [R21-44] or 头前缀 run + 括号化 and 尾组嵌套链检测（[R7-B45] 的结构镜像）：",
    "        # 扁平 all_same_target 判据对 `while A or B or (C and D)` 结构性不满足（C 的跳转",
    "        # 目标是循环假出口、A/B 的真边才是体入口），前向/后向 walk 各拿半条链，缺 and 尾",
    "        # 组时其块被 IfRegion 认领为独立条件、or run 被拆成嵌套 while（本次实测形态）。",
    "        _r2144_chain = self._r2144_detect_while_condition_nested_or_and(cond_block, loop)",
    "        if _r2144_chain and len(_r2144_chain) >= 2:",
    "            return _r2144_chain",
]

# --- anchor 1: insert METHOD right before `def _detect_while_boolop_forward_chain`
m1 = b"    def _detect_while_boolop_forward_chain(self, cond_block: BasicBlock, loop: LoopRegion, BOOLOP_CHAIN_JUMPS) -> Optional[List[Tuple[BasicBlock, str]]]:",
# split on crlf: find line index
def find_lines(lines, needle_b):
    return [i for i, L in enumerate(lines) if L == needle_b]

anchor_method = m1[0].decode()
idxs = [i for i, L in enumerate(lines) if L.decode('utf-8', 'replace') == anchor_method]
assert len(idxs) == 1, "method anchor count=%d" % len(idxs)
im = idxs[0]

# --- anchor 2: insert CALL right after the `return _nested_chain` line (unique)
anchor_call_ret = "            return _nested_chain"
jc = [i for i, L in enumerate(lines) if L.decode('utf-8', 'replace') == anchor_call_ret]
assert len(jc) == 1, "call anchor count=%d" % len(jc)
jc = jc[0]

# patch order: insert the later one first (method before forward-chain, which is AFTER the call site)
method_enc = [l.encode('utf-8') for l in METHOD_LINES]
call_enc = [l.encode('utf-8') for l in CALL_LINES]
# im > jc (28066 > 27224) confirmed
assert im > jc
lines[im:im] = method_enc
lines[jc + 1:jc + 1] = call_enc

out = b"\r\n".join(lines)
open(OUT, "wb").write(out)
print("landed sha16 :", BASE_SHA16)
print("candidate size:", len(out), "lines:", out.count(b"\r\n") + 1)
# py_compile
tmp = OUT + ".compilecheck"
import shutil; shutil.copyfile(OUT, tmp)
try:
    py_compile.compile(tmp, doraise=True)
    print("py_compile   : OK")
finally:
    os.remove(tmp)
print("candidate sha16:", sha16(out))
