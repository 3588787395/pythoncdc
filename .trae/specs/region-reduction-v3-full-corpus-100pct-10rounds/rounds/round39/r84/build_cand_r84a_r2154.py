"""build_cand_r84a_r2154.py — byte-exact rebuild of the [R21-54] generator candidate
from base `30a4d7827122e165` (rounds/round39/r75/CANDIDATE_r75a_r2146_AB_on_r74d).

Installs a GENERATOR-side criterion `_r2154_chain_elif_is_nested_body` plus its orelse
action (same mounting point + same nested-else idiom as landed [R21-43], but WITHOUT a
Continue, since this chain's arm tail is not a pure continue block).

Prints sha16 of the file before and after the patch. BOM + all-CRLF preserved; asserts
each anchor is unique; refuses if the result contains `\\r\\r\\n`.

usage: python -X utf8 build_cand_r84a_r2154.py [SRC] [DST]
"""
import hashlib
import os
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "core/cfg/region_ast_generator.py"
DST = sys.argv[2] if len(sys.argv) > 2 else "DELIVER/CANDIDATE_r84a_r2154_nested_else_if.py"

raw = open(SRC, "rb").read()
print("SRC sha16 =", hashlib.sha256(raw).hexdigest()[:16], "bytes =", len(raw))
if b"\r\r\n" in raw:
    raise SystemExit("base already has \\r\\r\\n, refusing")
lines = raw.split(b"\r\n")


def find_unique(sub_startswith=None, exact=None):
    hits = [i for i, l in enumerate(lines)
            if (exact is not None and l == exact)
            or (sub_startswith is not None and l.strip().startswith(sub_startswith))]
    if len(hits) != 1:
        raise SystemExit("anchor not unique (%d): %r" % (len(hits), sub_startswith or exact))
    return hits[0]


METHOD_LINES = [
    "    def _r2154_chain_elif_is_nested_body(self, region: IfRegion):",
    '        """[R21-54] 结构判据：本 IF_ELIF_CHAIN 的唯一 elif 条件其实是外层 then 体里嵌套的 if，',
    "        不是真正的 elif ⇒ 该臂必须以 `else: If(…)` 发射（与已落地 [R21-43] 同一动作挂点，",
    "        但谓词不同：[R21-43] 证明「两臂收敛于纯 continue 块」，本判据证明「elif 条件的真边",
    "        不落入其自称的臂体」。",
    "",
    "        结构事实（只读区域声明与 opcode 类 / 前驱后继，不读函数名、绝对偏移、块数阈值）：",
    "          ① 链恰有一个 elif 条件与一组 elif 臂块（被折叠的节点正好是「这一个 elif 臂 + 链尾 else 臂」两级）；",
    "          ② 该 elif 条件的条件跳转**假出口**落在本链 `elif_final_else` 之内、且不在 `elif_bodies` 内、",
    "             且不等于 `merge_block`——真 elif 的假出口应指向下一臂测试或链尾汇合，而非臂体内；",
    "          ③ `merge_block` 自身是条件测试块（末指令为 POP_JUMP_*），即「链的汇合点」其实是下一个测试，",
    "             flat 链没有真正的公共汇出块（与 [R21-53] 观测的「链尾出口即循环回测」同源）；",
    "          ④ 该 elif 条件的**真出口**（fall-through 后继：起始偏移更大、非假出口目标、非异常入口块）",
    "             不在 `elif_bodies[0]` 内——真 elif 的条件真边必然直落其臂体首块，真边另有所在 ⇒",
    "             该条件不是 elif，而是外层 then 体里一条独立的嵌套 if。",
    "",
    "        为什么是「必须嵌套」的证明而非偏好：④ 可证伪 flat 折叠——若 @cond 真是 elif，其真边即",
    "        臂体入口；实测真边另有所在，说明折叠破坏了 then 体的语句归属。",
    "        保守性：任一条不成立即返回 False ⇒ 调用方保持现有 flat elif 渲染，产物逐字节不变。",
    "        本方法无副作用，可被探针包裹做点名数派并证惯性。",
    "        \"\"\"",
    "        conds = list(getattr(region, 'elif_conditions', None) or [])",
    "        bodies = list(getattr(region, 'elif_bodies', None) or [])",
    "        if len(conds) != 1 or len(bodies) != 1:",
    "            return False",
    "        fin = list(getattr(region, 'elif_final_else', None) or [])",
    "        if not fin:",
    "            return False",
    "        _c = conds[0]",
    "        if not getattr(_c, 'instructions', None):",
    "            return False",
    "        _li = _c.get_last_instruction()",
    "        if _li is None or not isinstance(getattr(_li, 'argval', None), int):",
    "            return False",
    "        _POPJUMP = ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE',",
    "                    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE',",
    "                    'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE')",
    "        if _li.opname not in _POPJUMP:",
    "            return False",
    "        _fx = self.cfg.get_block_by_offset(_li.argval)",
    "        _fin = set(fin)",
    "        _body = set(bodies[0] or [])",
    "        _merge = getattr(region, 'merge_block', None)",
    "        if _fx is None or _fx not in _fin or _fx in _body or _fx is _merge:",
    "            return False",
    "        if _merge is None or not getattr(_merge, 'instructions', None):",
    "            return False",
    "        _ml = _merge.get_last_instruction()",
    "        if _ml is None or _ml.opname not in _POPJUMP:",
    "            return False",
    "        _te = None",
    "        for _s in sorted((getattr(_c, 'successors', None) or []), key=lambda b: b.start_offset):",
    "            if _s is _fx or _s.start_offset <= _c.start_offset:",
    "                continue",
    "            _fi = _s.get_first_instruction() if getattr(_s, 'instructions', None) else None",
    "            if _fi is not None and _fi.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START'):",
    "                continue",
    "            _te = _s",
    "            break",
    "        if _te is None or _te in _body:",
    "            return False",
    "        return True",
    "",
    "",
]

ACTION_LINES = [
    "        # [R21-54] 外层链的单 elif 其实是 then 体里嵌套的 if ⇒ 解除 elif 折叠，改发 else 子句。",
    "        # 与 [R21-43] 同一动作挂点、同一惯用写法（摘 _is_elif、标 _is_nested_if，发射器走",
    "        # code_generator._generate_elif_or_else 的「嵌套 if ≠ elif」分支，把 orelse 整列表作为 else",
    "        # 子句依次发射），区别是不补 Continue（本链臂尾不是纯 continue 块，判据 ③/④ 已述）。",
    "        # 不改动任何跳转目标；判据不成立时零副作用 ⇒ 产物逐字节不变。",
    "        if (isinstance(_ft3_orelse, list) and len(_ft3_orelse) == 1",
    "                and self._r2154_chain_elif_is_nested_body(region)):",
    "            _r2154_root = _ft3_orelse[0]",
    "            if (isinstance(_r2154_root, dict) and _r2154_root.get('type') == 'If'",
    "                    and _r2154_root.get('_is_elif')):",
    "                _r2154_new_root = dict(_r2154_root)",
    "                _r2154_new_root.pop('_is_elif', None)",
    "                _r2154_new_root['_is_nested_if'] = True",
    "                _ft3_orelse = [_r2154_new_root]",
]

# insert method before `def _if_generate_full_elif_chain`
mi = find_unique(sub_startswith=b"def _if_generate_full_elif_chain")
lines[mi:mi] = [l.encode("utf-8") for l in METHOD_LINES]

# insert action before the result assembly line in _if_generate_full_elif_chain
result_anchor = b"        result = {'type': 'If', 'test': condition, 'body': then_stmts if then_stmts else [{'type': 'Pass'}], 'orelse': _ft3_orelse}"
ri = find_unique(exact=result_anchor)
lines[ri:ri] = [l.encode("utf-8") for l in ACTION_LINES] + [b""]

out = b"\r\n".join(lines)
if b"\r\r\n" in out:
    raise SystemExit("produced \\r\\r\\n, refusing")
os.makedirs(os.path.dirname(DST) or ".", exist_ok=True)
open(DST, "wb").write(out)
print("DST =", DST)
print("DST sha16 =", hashlib.sha256(out).hexdigest()[:16], "bytes =", len(out))
# compile check
compile(out.decode("utf-8-sig"), DST, "exec")
print("py_compile: OK")
