# -*- coding: utf-8 -*-
"""Build specs/cand_r67_ccprefix.json (generator-only same-level prefix split)."""
import io, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
REL = 'core/cfg/region_ast_generator.py'
u = io.open(os.path.join(REPO, REL), encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')

A_DEF = ("    def _generate_ternary(self, region: TernaryRegion, skip_store_targets: Set[str] = None)"
         " -> Optional[List[Dict[str, Any]]]:\n")
A1 = ("                _r63b3_stmts = self._r63b3_reduce_value_ctx_chain_store(\n"
      "                    region, cond_expr, pre_stmts, skip_store_targets)\n"
      "                if _r63b3_stmts is not None:\n"
      "                    return _r63b3_stmts\n")
A2 = ("                    _r63b3_stmts = self._r63b3_reduce_value_ctx_chain_store(\n"
      "                        region, cond_expr, pre_stmts, skip_store_targets)\n"
      "                    if _r63b3_stmts is not None:\n"
      "                        return _r63b3_stmts\n")
for nm, a in (('A_DEF', A_DEF), ('A1', A1), ('A2', A2)):
    print(nm, 'count =', u.count(a))

NEW_METHOD = '''    def _r67_split_cc_ternary_stmt_prefix(self, region: 'TernaryRegion',
                                          pre_stmts: List[Dict[str, Any]]) -> None:
        # [R67-diag5 值语境链式比较三元：头块前导已完结语句的同层拆分]
        # 识别条件（三条，全部只读**本区域自身的字段**与该块自身的栈深，不查任何
        #   其他区域/层次的归属，无函数名/文件名/偏移/阈值）：
        #   (1) 本区域的三元条件是 chained compare：`chained_compare_ops` 长度 >= 2
        #       且 `chained_compare_blocks` 非空 —— 与调用点（Phase-7-D 分支 /
        #       R106 补判分支）所依据的是同一条结构性判据；
        #   (2) `condition_block` 末指令消费栈顶条件值，故
        #       _split_block_condition_prefix 的纯栈深划界成立且切出的前导段非空
        #       —— 前导段的定义即「执行完毕后值栈回到块入口深度 0 的**已完结**语句」
        #       （与 AssertRegion.condition_block、旋转 while 的 LoopRegion.
        #       condition_block、_r63b3_reduce_value_ctx_chain_store 用的是同一条
        #       划界，不新建谓词）；
        #   (3) 前导段之后的剩余指令里仍留有链的比较指令
        #       （COMPARE_OP / IS_OP / CONTAINS_OP）——拆分点绝不落在链内部。
        # 归约方式（原则 1「每块 = 前导语句 + 恰一个终止符」+ 原则 3「嵌套即抽象
        #   节点」）：块整体**仍**归本三元区域（不改 block_to_region、不改
        #   generated_blocks 的既有登记），仅把块内栈深已归零的前导段经
        #   _build_statements_from_instructions 归约为语句后 extend 进 pre_stmts，
        #   由 _generate_ternary 既有的 `results = list(pre_stmts)` 通道随本三元一同
        #   返回父序列 —— 与 _r63b3_reduce_value_ctx_chain_store 在同一分支上的既有
        #   做法一字不动地同构，只是那条路径的 (3) 要求「两臂都是链自身的短路结构」，
        #   真三元的值臂不满足，于是前导段此前无人发射（语句整段丢失）。
        #   任一步不成立即原样返回（保守退化到落地行为），不新增区域、不新增帧内/
        #   self 状态、不抑制任何发射。
        # AST 映射：前导段 -> 若干条 ast.Assign / ast.Expr，位置与该三元的
        #   ast.Assign(targets=[Name(value_target)], value=ast.IfExp(test=ast.Compare,
        #   body=<true>, orelse=<false>)) **同层**且在前（源码顺序），而不是 IfExp 的
        #   子节点，也不是任何嵌套语句的臂内节点。
        _ops = getattr(region, 'chained_compare_ops', None) or []
        if len(_ops) < 2 or not (getattr(region, 'chained_compare_blocks', None) or []):
            return
        _cond = getattr(region, 'condition_block', None)
        if _cond is None or not _cond.instructions:
            return
        _prefix = self._split_block_condition_prefix(
            _cond,
            FORWARD_CONDITIONAL_JUMP_OPS | NONE_CHECK_OPS | SHORT_CIRCUIT_JUMP_OPS)
        if not _prefix:
            return
        _all = list(_cond.instructions)
        _rest = _all[len(_prefix):]
        if not _rest or not any(
                i.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP') for i in _rest):
            return
        _pstmts = self._build_statements_from_instructions(_prefix, _cond)
        if not _pstmts:
            return
        pre_stmts.extend(_pstmts)

'''

CALL1 = A1 + ("                self._r67_split_cc_ternary_stmt_prefix(region, pre_stmts)\n")
CALL2 = A2 + ("                    self._r67_split_cc_ternary_stmt_prefix(region, pre_stmts)\n")

edits_both = [{'anchor': A_DEF, 'repl': NEW_METHOD + A_DEF},
              {'anchor': A1, 'repl': CALL1},
              {'anchor': A2, 'repl': CALL2}]
edits_site1 = [{'anchor': A_DEF, 'repl': NEW_METHOD + A_DEF},
               {'anchor': A1, 'repl': CALL1}]
for nm, e in (('cand_r67_ccprefix', edits_both), ('cand_r67_ccprefix_s1', edits_site1)):
    os.makedirs('specs', exist_ok=True)
    io.open('specs/%s.json' % nm, 'w', encoding='utf-8').write(
        json.dumps({'name': nm, 'file': REL, 'edits': e}, ensure_ascii=False, indent=1))
    print('wrote specs/%s.json' % nm)
