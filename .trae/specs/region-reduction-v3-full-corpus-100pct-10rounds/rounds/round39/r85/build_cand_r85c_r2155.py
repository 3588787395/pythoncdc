"""build_cand_r85c_r2155.py — byte-exact rebuild of the [R21-55c] GENERATOR half from the gate-38
landed bytes (region_ast_generator.py sha16 11324f276cce6d5b).

Half alone: in `_ternary_host_call_prefix_span`'s arm adopter `_adopt_arm`, an arm successor that is
an exception-handler entry (first instruction PUSH_EXC_INFO / WITH_EXCEPT_START) is not a
normal-completion path, so it must not disqualify the arm. Co-requisite of the [R21-55] analyzer
half (build_cand_r85a_r2155.py), which makes the sibling-ternary regions exist at all.

Prints sha16 before/after. BOM + all-CRLF preserved, anchor asserted unique, refuses `\\r\\r\\n`.
usage: python -X utf8 build_cand_r85c_r2155.py [SRC] [DST]
"""
import hashlib
import os
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "core/cfg/region_ast_generator.py"
DST = sys.argv[2] if len(sys.argv) > 2 else "DELIVER/CANDIDATE_r85c_r2155_generator_arm_exc_successor.py"

raw = open(SRC, "rb").read()
print("SRC sha16 =", hashlib.sha256(raw).hexdigest()[:16], "bytes =", len(raw))
if raw[:3] != b"\xef\xbb\xbf":
    raise SystemExit("base is not BOM-prefixed, refusing")
if b"\r\r\n" in raw:
    raise SystemExit("base already has \\r\\r\\n, refusing")
if raw.count(b"\n") != raw.count(b"\r\n"):
    raise SystemExit("base is not all-CRLF, refusing")
lines = raw.split(b"\r\n")

A_1 = b"            for sb in (getattr(arm, 'successors', None) or set()):"
A_2 = b"                if sb is not merge:"
A_3 = b"                    return False"
hits = [i for i in range(len(lines) - 2)
        if lines[i] == A_1 and lines[i + 1] == A_2 and lines[i + 2] == A_3]
if len(hits) != 1:
    raise SystemExit("anchor triple not unique (%d)" % len(hits))
i = hits[0]

NEW = [
    "            for sb in (getattr(arm, 'successors', None) or set()):",
    "                if sb is merge:",
    "                    continue",
    "                # [R21-55c] 臂的「非 merge 后继」若是异常入口块（首指令 PUSH_EXC_INFO /",
    "                # WITH_EXCEPT_START），它不是正常完成路径：CFG 给 try 范围内的**每个**块都",
    "                # 挂一条指向 handler 的边，于是纯值臂的后继集合里混进了 handler（本单元实测",
    "                # 臂 @1754/@1758 的后继 = {汇合块, handler @3026}）。既有判据「臂只落到 merge」",
    "                # 因此永远不成立，宿主调用跨度 (_ternary_host_call_prefix_span) 整体退回 None，",
    "                # 兄弟三元被降级成裸表达式语句、宿主语句消失。放行条件只读该后继的首指令",
    "                # opcode 类（结构事实，不读名字/偏移/计数器/跨层信息）；其余后继一律 return False，",
    "                # 保持既有「臂只落到 merge」判据 ⇒ 判据不成立时产物逐字节不变。",
    "                _r2155_sb_first = (sb.get_first_instruction()",
    "                                   if getattr(sb, 'instructions', None) else None)",
    "                if _r2155_sb_first is None:",
    "                    return False",
    "                if _r2155_sb_first.opname not in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START'):",
    "                    return False",
]
lines[i:i + 3] = [l.encode("utf-8") for l in NEW]

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
