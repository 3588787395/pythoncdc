# -*- coding: utf-8 -*-
"""build the R67-diag3 candidate spec: bare-RETURN_VALUE successor block is the
ternary merge block's return sink (recovers `return <expr>` lost to demotion)."""
import io
import json

ANCHOR = (
    "                    if _has_return_sink:\n"
    "                        results.append({'type': 'Return', 'value': _merge_consumer_expr})\n"
    "                    else:\n"
    "                        results.append({'type': 'Expr', 'value': _merge_consumer_expr})\n"
)

NEW = (
    "                    # [R67-diag3 C1 bare-RETURN_VALUE successor = return sink]\n"
    "                    # 识别条件（三条全部只读本区域/其后继块自身的指令与边，同层次、\n"
    "                    #   不引函数名/文件名/偏移/阈值，不做跨区域跨层次包含判断）：\n"
    "                    #   (1) 能走到此处 ⇒ 本 TernaryRegion 已是 merge_context is None ∧\n"
    "                    #       value_target 为空 ∧ merge_block 非空 的「无 STORE 汇点」形态，\n"
    "                    #       且上面既有的三条判据（merge 块尾 / merge_extra_blocks 块尾 /\n"
    "                    #       await 轮询链）都没能认出 return 汇点（not _has_return_sink）；\n"
    "                    #   (2) merge_block 的**有效**尾指令（滤去 RESUME/NOP/CACHE/PUSH_NULL）\n"
    "                    #       是一条产 valued 指令 —— 不是 POP_TOP（值已弃 = 语句）、\n"
    "                    #       不是 STORE_*（值已入名字空间 = 赋值）、不是 RETURN_*（已被\n"
    "                    #       判据 (1) 排除）、不是 JUMP*（控制流已离开本块）⇒ 本块出口栈顶\n"
    "                    #       仍留着 _merge_consumer_expr 这一个值；\n"
    "                    #   (3) merge_block 恰有一个后继块 S，且 S 的**有效**指令序列恰为一条\n"
    "                    #       RETURN_VALUE 并落在 S 的入口偏移上，且 S 恰有一个前驱即\n"
    "                    #       merge_block。第 (3) 条是 CPython 发射纪律的身份判据：3.11 的\n"
    "                    #       `return` / 隐式落尾 return 必发 `LOAD_CONST None; RETURN_VALUE`\n"
    "                    #       两条，RETURN_VALUE 与它配对的 LOAD_CONST 同块，故『块首就是\n"
    "                    #       RETURN_VALUE』只可能是 return **继承自前驱栈顶的值**；又因 S\n"
    "                    #       唯一前驱 = merge_block，该值唯一来源就是本三元归约式。\n"
    "                    #   实测反例方向：`(a, b)` 作独立表达式语句 + 裸 `return` 时，orig 必\n"
    "                    #   含 POP_TOP，被 (2) 挡住；S 有多个前驱（真汇合点）时被 (3) 的入度\n"
    "                    #   判据挡住，此时 S 归父序列所有，不认领。\n"
    "                    # 归约方式：仅把本路径**已经算好的同一棵** _merge_consumer_expr 的语句\n"
    "                    #   外壳从 Expr 改判为 Return（复用下面既有的 _has_return_sink 分支，\n"
    "                    #   不新增发射、不抑制任何语句、不改次序），并按「每块唯一归属」把 S\n"
    "                    #   记入 generated_blocks/generated_offsets，避免 S 再被父序列二次生成\n"
    "                    #   成 `return None`。不引入任何新的 self 帧内状态。\n"
    "                    # AST 映射：TernaryRegion(merge_context=None ∧ value_target 空 ∧\n"
    "                    #   merge_block 尾为值构建) + 后继单指令 RETURN_VALUE 块 ⇒\n"
    "                    #   ast.Expr(IfExp/builtin.TypeVar) 降格为 ast.Return(value=同一节点)，\n"
    "                    #   即源码 `return <a if c else b>` / `return (<x>, (a if c else b))`，\n"
    "                    #   而非 `<expr>; return None` 两条语句。\n"
    "                    if not _has_return_sink and region.merge_block is not None:\n"
    "                        _r67_succs = [s for s in region.merge_block.successors\n"
    "                                      if s not in getattr(region.merge_block,\n"
    "                                                          'exception_successors', set())]\n"
    "                        if len(_r67_succs) == 1:\n"
    "                            _r67_succ = _r67_succs[0]\n"
    "                            _r67_sc = [i for i in _r67_succ.instructions\n"
    "                                       if i.opname not in ('RESUME', 'NOP', 'CACHE',\n"
    "                                                           'PUSH_NULL')]\n"
    "                            _r67_mc = [i for i in region.merge_block.instructions\n"
    "                                       if i.opname not in ('RESUME', 'NOP', 'CACHE',\n"
    "                                                           'PUSH_NULL')]\n"
    "                            if (len(_r67_sc) == 1\n"
    "                                    and _r67_sc[0].opname == 'RETURN_VALUE'\n"
    "                                    and _r67_sc[0].offset == _r67_succ.start_offset\n"
    "                                    and len(_r67_succ.predecessors) == 1\n"
    "                                    and next(iter(_r67_succ.predecessors)) is region.merge_block\n"
    "                                    and _r67_mc\n"
    "                                    and _r67_mc[-1].opname not in (\n"
    "                                        'POP_TOP', 'RETURN_VALUE', 'RETURN_CONST')\n"
    "                                    and not _r67_mc[-1].opname.startswith('JUMP')\n"
    "                                    and not _r67_mc[-1].opname.startswith('POP_JUMP')\n"
    "                                    and not _r67_mc[-1].opname.startswith('STORE')):\n"
    "                                _has_return_sink = True\n"
    "                                self.generated_blocks.add(_r67_succ)\n"
    "                                self.generated_offsets.add(_r67_succ.start_offset)\n"
)

spec = {
    "name": "cand_r67_bare_return_value_successor_sink",
    "file": "core/cfg/region_ast_generator.py",
    "edits": [{"anchor": ANCHOR, "repl": NEW + ANCHOR}],
    "note": "R67 diag3 C1",
}
P = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
u = io.open(P, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
print('anchor count =', u.count(ANCHOR))
print('added lines =', NEW.count('\n'))
io.open('specs/cand_r67_bare_return_sink.json', 'w', encoding='utf-8').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('wrote specs/cand_r67_bare_return_sink.json')
