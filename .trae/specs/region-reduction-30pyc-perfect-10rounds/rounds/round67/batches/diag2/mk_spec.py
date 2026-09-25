# -*- coding: utf-8 -*-
import io, json
ANCHOR = (
"        _noise_ops = {'RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP'}\n"
"        for _tb in (region.then_blocks or []):\n"
"            for _ti in _tb.instructions:\n"
"                if _ti.opname in _noise_ops:\n"
"                    continue\n"
"                if _ti.opname.startswith(('JUMP', 'POP_JUMP')):\n"
"                    continue\n"
"                return False\n"
)
NEW = (
"        # [R66-diag1 E1 单测试空臂不得吞并 if/else 之后的汇合块]\n"
"        # 识别条件：三条都只读**本区域自身的字段**，且第 (2) 条复用上面刚用过的那条\n"
"        #   同层过滤器（`_noise_ops` ∪ `JUMP*`/`POP_JUMP*` ⇒ 该臂不含语句），不新建谓词：\n"
"        #   (1) 能走到此处 ⇒ then 臂已被判为无语句；\n"
"        #   (2) 把同一条过滤器原样作用到本区域自己的 `region.else_blocks`，结论是 else 臂\n"
"        #       **含**有效语句 ⇒ 本区域是源码级真 if/else（而非 else 缺失的单臂形状，\n"
"        #       也而非假出口落在纯清理块的人造双臂）；\n"
"        #   (3) `region.chained_compare_blocks` 为空 ⇒ 条件是单一测试，本区域不存在\n"
"        #       「比较链假出口跨过真身」的旋转布局，即 W15-C 立论的那条布局不成立。\n"
"        #   (2)∧(3) 合取时唯一可能的源码形状是 `if cond: pass` `else: <含语句的臂>`：\n"
"        #     CPython 3.11 把非空 then 体物理排在「条件测试」与「else 体」之间，故单一\n"
"        #     POP_JUMP 测试 + 空 then 臂 + 非空 else 臂只可能来自源码写了 pass。实测\n"
"        #     3.11.7：`pass` 发射 0 条指令，空臂只剩一条打上 pass 行号的\n"
"        #     JUMP_FORWARD→汇合点。此时 merge_block 是 if/else **之后**的顺序续接点，\n"
"        #     归父区域语句序列所有，不是空臂的真身（真身被吞 ⇒ 后继语句重复发射一次）。\n"
"        #   反例（必须保留 W15-C，实测读数见 FACTS 全 402 表）：chained_compare_blocks\n"
"        #   非空的比较链旋转臂——slippage::create_new_price cc=[96]、check_strategy\n"
"        #   cc=[820]/[1180]、strategy::tick_worker_thread cc=[552]/[1022]（else 臂含语句\n"
"        #   但 cc 非空，第 (3) 条把它挡在门外）、scheduler cc=[1366]；else 臂为空的单臂\n"
"        #   if（handlers::perform_rollover else=[]）由第 (2) 条挡住；\n"
"        #   repro_r63b2_tail_cmp_return::case_elif_try_tail_return cc=[1266] 亦保留。\n"
"        # 归约方式：返回 False ⇒ 调用方（同文件 _if_generate_normal 的 W15-C 拼接，\n"
"        #   L17916）不再执行 `_merge_then_stmts` 并入，也不再对 merge_block 做\n"
"        #   discard/add 的二次认领；then 体保留 _if_generate_then_branch 已产出的合成\n"
"        #   `{'type': 'Pass'}`，merge_block 回到父序列按既有次序发射一次。只收紧一条\n"
"        #   既有判据的成立条件：不改发射次序、不新增区域/帧内状态、不抑制任何语句发射。\n"
"        # AST 映射：IfRegion(then_blocks 全为跳转/连接件 ∧ else_blocks 含有效语句 ∧\n"
"        #   chained_compare_blocks 为空 ∧ merge_block ∉ then_blocks∪else_blocks) ⇒\n"
"        #   ast.If(body=[ast.Pass], orelse=[else 臂语句])；merge_block 的语句节点是与该\n"
"        #   ast.If **同层**的后继兄弟节点，而不是 ast.If.body 的子节点。\n"
"        _r66e1_else_has_stmt = False\n"
"        for _r66e1_eb in (region.else_blocks or []):\n"
"            for _r66e1_ei in _r66e1_eb.instructions:\n"
"                if _r66e1_ei.opname in _noise_ops:\n"
"                    continue\n"
"                if _r66e1_ei.opname.startswith(('JUMP', 'POP_JUMP')):\n"
"                    continue\n"
"                _r66e1_else_has_stmt = True\n"
"                break\n"
"            if _r66e1_else_has_stmt:\n"
"                break\n"
"        if _r66e1_else_has_stmt and not (getattr(region, 'chained_compare_blocks', None) or []):\n"
"            return False\n"
)
spec = {
  "name": "cand_r66_e1_empty_then_arm_no_join_absorb",
  "file": "core/cfg/region_ast_generator.py",
  "anchor": ANCHOR,
  "repl": ANCHOR + NEW,
  "note": "R66 diag1 E1"
}
u = io.open(r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py', encoding='utf-8-sig', newline='').read().replace('\r\n','\n')
print('anchor count =', u.count(ANCHOR))
print('repl adds lines =', (spec['repl'].count('\n') - ANCHOR.count('\n')))
io.open('specs/cand_r66_e1.json','w',encoding='utf-8').write(json.dumps(spec, ensure_ascii=False, indent=1))
