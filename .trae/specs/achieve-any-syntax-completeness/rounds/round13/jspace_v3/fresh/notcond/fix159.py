# fix159.py: rr-v5r159 [v159-NOTCOND] not 复合条件 if 的 FALSE 模式准入窗扩展
# （只增不破，单文件一处）。
#
# F1: `m = req.get_method(); if not (code in (301,...,308) and m in ('GET','HEAD')
#     or code in (301,302,303) and m == 'POST'): raise ...`（urllib.request.
#     HTTPRedirectHandler.redirect_request 实形，源 line 664-666）v158 渲染
#     `if code in (301,...,308): if not (m in ... or ...): raise`——not(A∧B∨C∧D)
#     被重组为嵌套 factored 形=真实 R1（语义反转：¬A 时源码 raise、渲染不
#     raise——如 305 redirect 会漏检；判官 Different bytecode：ORIG A 假边
#     →60 下一 or 成员，REC A 假边→128 跳过 raise）。
#
# 根因: _detect_boolop_conditional_chain 的入口块 body 语句判据 _sb_has_body
#     扫描「条件起始之后」的指令（_cond_start_offset 门控，34405-34412）。
#     POP_JUMP_IF_FALSE（and 短路模式）分支的栈深回溯准入窗只放行「简单变量
#     真值测试」（LOAD_*/LOAD_ATTR/LOAD_METHOD 结尾，34374-34376）与 R54-A 混
#     合链结构判据——`x in T` 成员测试形（CONTAINS_OP + POP_JUMP_IF_FALSE）
#     不在窗内 → 前置赋值（m = req.get_method() 的 STORE）被 _sb_has_body 当
#     body 语句 → BoolOp 链在首操作数块拒绝启动 → or 链碎片化（A 独立
#     IfRegion=factored 外层、仅 C∧D 成 BoolOpRegion——区域树探针实证 d 案
#     BoolOpRegion blocks=[58,66] vs e 案 blocks=[0,10,18,26]）→ 渲染语义反转。
#     对照组：无前置赋值形（e_docstring）回溯不触发（无 STORE 可豁免）链照常
#     识别=faithful（矩阵 E 案证明链走查本身对 or-run 结构完备）。TRUE 模式
#     （R38）准入窗早已含 IS_OP/CONTAINS_OP/COMPARE_OP（`value is DEFAULT or
#     callable(value)` 实形）——本修复把同一理据镜像到 FALSE 模式的 CONTAINS_OP。
#
# 修复: POP_JUMP_IF_FALSE 分支准入窗追加 'CONTAINS_OP'（与 R38 的 TRUE 窗同
#     一成员测试理据；命中即放行既有的栈深回溯体——回溯后 _cond_start_offset
#     = 条件首操作数入栈点，前置语句不再被 _sb_has_body 当 body）。IS_OP/
#     COMPARE_OP 仍排除（COMPARE_OP 链式比较/boolop 结果比较回归风险，注释
#     既有；IS_OP 无语料证据，登记后续）。不命中逐字节落回现状（C3）。
import io

PATH = r'F:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'
MARKER = 'v159-NOTCOND'

s = io.open(PATH, encoding='utf-8-sig').read()
orig = s

old = """                if _r54_mixed or (_prev_instrs and _prev_instrs[-1].opname in ('LOAD_FAST', 'LOAD_NAME',
                                                                  'LOAD_GLOBAL', 'LOAD_DEREF',
                                                                  'LOAD_ATTR', 'LOAD_METHOD')):"""
assert s.count(old) == 1, 'anchor count %d' % s.count(old)

new = """                # [v159-NOTCOND] 成员测试形（CONTAINS_OP + POP_JUMP_IF_FALSE）
                # 入窗——镜像 R38 的 TRUE 窗同一理据（`value is DEFAULT or ...`
                # → `x in T and ...`）：`x = f(); if x in T and y:` 与
                # `m = req.get_method(); if not (x in T and y or z and w): raise`
                # （redirect_request 实形）的首操作数块含前置赋值 STORE，此前被
                # _sb_has_body 误判为 if 体、BoolOp 链拒绝启动 → or 链碎片化 →
                # not(A∧B∨C∧D) 被重组为嵌套 factored 形（语义反转：¬A 时源码
                # raise、渲染不 raise）。命中即放行既有栈深回溯体（回溯后
                # _cond_start_offset=条件首操作数入栈点，前置语句不再当 body）。
                # IS_OP/COMPARE_OP 仍排除（COMPARE_OP 链式比较/boolop 结果比较
                # 回归风险——既有注释；IS_OP 无语料证据，登记后续）。不命中逐字
                # 节落回现状。
                if _r54_mixed or (_prev_instrs and _prev_instrs[-1].opname in ('LOAD_FAST', 'LOAD_NAME',
                                                                  'LOAD_GLOBAL', 'LOAD_DEREF',
                                                                  'LOAD_ATTR', 'LOAD_METHOD',
                                                                  'CONTAINS_OP')):"""
s = s.replace(old, new, 1)

assert s != orig
assert s.count(MARKER) == 1
io.open(PATH, 'w', encoding='utf-8-sig', newline='').write(s)
print('fix159 applied: %d marker' % s.count(MARKER))

import py_compile
py_compile.compile(PATH, doraise=True)
print('syntax OK')
