"""build_cand_r86a_r2156.py — byte-exact rebuild of the [R21-56] GENERATOR half from the gate-38
landed bytes (region_ast_generator.py sha16 11324f276cce6d5b).

It contains
  (1) the [R21-55c] arm exception-successor relaxation, reproduced verbatim from
      build_cand_r85c_r2155.py (self-check: the file built with (1) alone is byte-identical to the
      banked candidate 45796ca24b371a8c — asserted below), plus
  (2) the [R21-56] consumption conjunct: a span that only exists because of (1) may take over the
      statement only when the leftover instructions of its closing block are complete statements
      (opcode-class / stack-shape test, no names, no offsets, no counters, no thresholds).

Co-requisite of the unchanged [R21-55] analyzer half (round39/r85/CANDIDATE_r85a..., 842e2748bcdfeb66).

BOM + all-CRLF preserved; every anchor asserted unique; refuses on `\\r\\r\\n`; py_compile.
usage: python -X utf8 build_cand_r86a_r2156.py [SRC] [DST]
"""
import hashlib
import os
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/core/cfg/region_ast_generator.py"
DST = sys.argv[2] if len(sys.argv) > 2 else "DELIVER/CANDIDATE_r86a_r2156_generator_relax_tail_boundary.py"
C_BANKED_SHA16 = "45796ca24b371a8c"

raw = open(SRC, "rb").read()
print("SRC sha16 =", hashlib.sha256(raw).hexdigest()[:16], "bytes =", len(raw))
if hashlib.sha256(raw).hexdigest()[:16] != "11324f276cce6d5b":
    raise SystemExit("SRC is not the gate-38 landed generator, refusing")
if raw[:3] != b"\xef\xbb\xbf":
    raise SystemExit("base is not BOM-prefixed, refusing")
if b"\r\r\n" in raw:
    raise SystemExit("base already has \\r\\r\\n, refusing")
if raw.count(b"\n") != raw.count(b"\r\n"):
    raise SystemExit("base is not all-CRLF, refusing")
lines = raw.split(b"\r\n")


def find_unique(exact):
    hits = [i for i, l in enumerate(lines) if l == exact]
    if len(hits) != 1:
        raise SystemExit("anchor not unique (%d): %r" % (len(hits), exact[:70]))
    return hits[0]


# ---------------- (1) [R21-55c] exception-successor relaxation (verbatim from r85c) -------------
A_1 = b"            for sb in (getattr(arm, 'successors', None) or set()):"
A_2 = b"                if sb is not merge:"
A_3 = b"                    return False"
hits = [i for i in range(len(lines) - 2)
        if lines[i] == A_1 and lines[i + 1] == A_2 and lines[i + 2] == A_3]
if len(hits) != 1:
    raise SystemExit("r85c anchor triple not unique (%d)" % len(hits))
i = hits[0]

C_NEW = [
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
lines[i:i + 3] = [l.encode("utf-8") for l in C_NEW]

out_c = b"\r\n".join(lines)
assert out_c[:3] == b"\xef\xbb\xbf" and b"\r\r\n" not in out_c
sha_c = hashlib.sha256(out_c).hexdigest()[:16]
print("(1) only, sha16 =", sha_c, "bytes =", len(out_c),
      "== banked r85c" if sha_c == C_BANKED_SHA16 else "!! DIFFERS FROM BANKED r85c")
if sha_c != C_BANKED_SHA16:
    raise SystemExit("reproduction of the banked r85c half failed")

# ---------------- (2) [R21-56] consumption conjunct -------------
# 2a flag container, right before `visited = {cond_block}`
vi = find_unique(b"        visited = {cond_block}")
lines[vi:vi] = [l.encode("utf-8") for l in [
    "        # [R21-56] 记录本跨度是否**依赖** [R21-55c] 的异常边放宽才认领到臂：新增许可必须",
    "        # 自带消费证明（见 _r2156_tail_is_bounded_statements），未使用该放宽的跨度不受影响。",
    "        _r2156_relaxed_used = []",
]]

# 2b mark the relaxation the moment an exception-entry successor is what let the arm through
ri = find_unique(b"                if _r2155_sb_first.opname not in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START'):")
lines[ri + 2:ri + 2] = [l.encode("utf-8") for l in [
    "                # [R21-56] 本臂正是靠异常边放宽才被认领 —— 记下，跨度收尾时必须过消费判据。",
    "                _r2156_relaxed_used.append(1)",
]]

# 2c the conjunct at the span's exit, before the final return
gi = find_unique(b"        return span_instrs, all_blocks, prefix_instrs, tail_instrs")
lines[gi:gi] = [l.encode("utf-8") for l in [
    "        # [R21-56 消费判据] 只有「闭合块里跨度之后剩余的那段指令」本身是若干条完整语句时，",
    "        # 本跨度才允许接管该语句：否则剩余段里被压栈的值没有人消费（或被下一个区域的测试消费），",
    "        # 通用剩余语句构造器会把该值发成一条**裸表达式语句**，并把它的消费指令（return）留在",
    "        # 已被登记为已生成的块里永远消失。实测 IQCommon/util/replace_utils.pyc 的两处即此形态：",
    "        #   尾段 = [LOAD_FAST decrypted_url, POP_JUMP_FORWARD_IF_FALSE]  ⇒ 多发一条 `decrypted_url`",
    "        #   尾段 = [..., POP_TOP, LOAD_FAST url]（RETURN_VALUE 在下一块）⇒ `return url` 变成 `url`",
    "        # 判据成立与否只读 opcode 族/栈形状，不读名字、常量、绝对偏移、计数器、阈值；不成立即",
    "        # return None，此时尚未登记任何块或偏移，行为逐字节退回既有（gate-38）版本。",
    "        # 实测六处真实触发（_process_order 的宿主 .format/f-string 语句）全部满足该判据：",
    "        #   尾段末条分别为 JUMP_FORWARD @2428 与 POP_TOP @2910，臂均为纯常量值块。",
    "        if _r2156_relaxed_used and tail_instrs:",
    "            if not self._r2156_tail_is_bounded_statements(tail_instrs):",
    "                return None",
    "",
]]

# 2d the helper method, immediately before _ternary_host_call_prefix_span
mi = find_unique(b"    def _ternary_host_call_prefix_span(self, region):")
lines[mi:mi] = [l.encode("utf-8") for l in [
    "    def _r2156_tail_is_bounded_statements(self, tail_instrs):",
    "        \"\"\"[R21-56] 消费判据（栈形状 / opcode 类）：跨度闭合块里剩余的那段指令必须是若干条",
    "        完整语句——即它的最后一个栈上值在尾段内部就被取走，尾段也不得以「某个区域的条件测试",
    "        \"结尾」的形式替下一条语句代持操作数。",
    "",
    "        结构事实（只读 opcode 族，不读名字/常量/绝对偏移/块数阈值/跨层信息）：",
    "          ① 尾段任何位置不得出现条件跳转（`POP_JUMP_*` / `JUMP_IF_*`）：条件跳转的两侧分支块",
    "             不在尾段里，说明尾段是**下一个区域**（if/while/布尔链）的测试前半段，不是完整语句；",
    "          ② 尾段末条必须是语句边界：`POP_TOP`（丢弃结果的表达式语句）/ `RETURN_VALUE`、",
    "             `RETURN_CONST`（返回）/ `RAISE_VARARGS`（抛出）/ `STORE_*`（赋值收尾）/",
    "             `JUMP_*`（无条件跳转，控制流收尾）——这些 opcode 把栈上的值取走或转移控制，",
    "             尾段在其处恰好结束，每条语句都自足；",
    "          ③ 其它末条（`LOAD_*`、`BUILD_*`、`CALL`、`BINARY_OP`…）意味着尾段最后压栈（或未取）的",
    "             值要在**其后另外的块**里才被消费；本跨度已把这些块整体登记为已生成，于是那个值以",
    "             裸表达式语句发射，而真正的语句（如 return）消失——正是 [R21-55c] 放宽在",
    "             `replace_utils` 造成的两处产物差异。",
    "",
    "        与 `_is_statement_close_op`（跨度自身闭合指令判据，[r20a] 特意排除 STORE_*）不冲突：",
    "        那条判据问的是「本三元是不是嵌在一条尚未闭合的语句里」，STORE_* 作为闭合说明赋值语句",
    "        整体已被吞入 ⇒ 保守放弃；本判据问的是「剩余尾段是否自足」，`x = y` 以 STORE_FAST 收尾",
    "        正是一条完整语句 ⇒ 放行。两者面向跨度的两端，不可互相替代。",
    "        \"\"\"",
    "        _r2156_cond_jump = self._ternary_chain_cond_jump_ops()",
    "        for _r2156_i in tail_instrs:",
    "            _r2156_op = _r2156_i.opname",
    "            if _r2156_op in _r2156_cond_jump or _r2156_op.startswith('JUMP_IF'):",
    "                return False",
    "        _r2156_last = tail_instrs[-1].opname",
    "        if _r2156_last.startswith('STORE_') or _r2156_last.startswith('JUMP_'):",
    "            return True",
    "        return _r2156_last in ('POP_TOP', 'RETURN_VALUE', 'RETURN_CONST',",
    "                               'RAISE_VARARGS')",
    "",
]]

out = b"\r\n".join(lines)
if b"\r\r\n" in out:
    raise SystemExit("produced \\r\\r\\n, refusing")
assert out[:3] == b"\xef\xbb\xbf"
assert out.count(b"\n") == out.count(b"\r\n")
os.makedirs(os.path.dirname(DST) or ".", exist_ok=True)
open(DST, "wb").write(out)
print("DST =", DST)
print("DST sha16 =", hashlib.sha256(out).hexdigest()[:16], "bytes =", len(out))
compile(out.decode("utf-8-sig"), DST, "exec")
print("compile: OK")
import py_compile
py_compile.compile(DST, doraise=True)
print("py_compile: OK")
