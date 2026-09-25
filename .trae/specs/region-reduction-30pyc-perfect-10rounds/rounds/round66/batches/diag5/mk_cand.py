# -*- coding: utf-8 -*-
import io, json, sys
REPO = r'F:/Downloads/pythoncdc-main'
REL = 'core/cfg/region_ast_generator.py'
sys.stdout.reconfigure(encoding='utf-8')

src = io.open(REPO + '/' + REL, encoding='utf-8-sig', newline='').read()
nl = '\r\n' if src.count('\r') else '\n'
u = src.replace(nl, '\n')

ANCHOR = """                    self._generated_regions.add(id(_r65_r))
                    break

            if _post_try_stmts_r19n2:
"""

INSERT = """

            # [R66-diag5-B try-tail-unprotected-else]
            # 识别条件（同层次结构身份：只用本 region 自身的异常表字段与该块
            #   自身的指令，无函数名/文件名/偏移阈值特判，无跨区域跨层次认领）：
            #   (1) region 为 TryExceptRegion 且 try_offset_end <
            #       min(handler_entry_blocks) —— 本 try 的保护跨度在体尾提前
            #       收尾，handler 仍在它之后；本 try 无 finalbody、无已登记
            #       orelse、try_offset_end 处不是 analyzer 已认领的 else_blocks；
            #   (2) CFG 中起点恰为 try_offset_end 的块 B 通过 analyzer 既有判据
            #       _w11_unprotected_else_candidate：B 不被本 try 保护、以
            #       JUMP_FORWARD 终结、不含异常框架指令，且本 try 至少一个
            #       handler 块以同一 JUMP_FORWARD 目标正常退出（异常路径与
            #       正常路径在同一 merge 汇合）——该目标在 try ∪ handlers 之后；
            #   (3) B 尚未生成，也不在本 region 的 post-try 队列里。
            # 机制（CPython 3.11 实测发射形状，dis._parse_exception_table 可验）：
            #   try/except/else 的 else 体发射在保护跨度终点与首个 handler 入口
            #   之间，末尾一个 JUMP_FORWARD 跳过整个 handler 区间。当该 try 又
            #   嵌在外层 try 的保护跨度内时，else 块被外层区域唯一归属，
            #   _find_try_else_blocks 只遍历本区域 blocks 因而看不到它，外层
            #   顺序发射器把它当成 try 语句之后的兄弟语句排在 handler 之后
            #   （IQEngine/utils/scheduler.get_checked_time：106/106、
            #   jumpdiff=0、truediff=43 的纯换位）。
            # 归约方式：把 B 的语句作为本抽象节点的 else 子结构并入其 ast.Try
            #   的 orelse，并按原则 2（每块唯一归属）登记 B 已生成，令外层兄弟
            #   序列随后自然不再发射它；区域边界与父子关系不变。
            # AST 映射：B → ast.Try(body, handlers, orelse=stmts(B)) 的 else 分支
            #   （与既有 else_blocks→Try.orelse 映射同一目标节点，只是识别域从
            #   「本区域块」补全为「保护跨度终点处的那一个块」）。
            _r66_tail_off = getattr(region, 'try_offset_end', None)
            _r66_hdl_offs = [b.start_offset for b in
                             (getattr(region, 'handler_entry_blocks', None) or [])
                             if b is not None]
            _r66_else_offs = [b.start_offset for b in
                              (getattr(region, 'else_blocks', None) or [])
                              if b is not None]
            if (isinstance(try_ast, dict) and try_ast.get('type') == 'Try'
                    and try_ast.get('handlers')
                    and not try_ast.get('orelse') and not try_ast.get('finalbody')
                    and _r66_tail_off is not None and _r66_hdl_offs
                    and _r66_tail_off < min(_r66_hdl_offs)
                    and _r66_tail_off not in _r66_else_offs):
                _r66_b = self.cfg.get_block_by_offset(_r66_tail_off)
                if (_r66_b is not None and _r66_b.start_offset == _r66_tail_off
                        and _r66_b not in self.generated_blocks
                        and _r66_b not in _post_try_blocks_r19n2
                        and self.region_analyzer._w11_unprotected_else_candidate(
                            region, _r66_b)):
                    _r66_estmts = self._generate_block_statements(_r66_b)
                    if _r66_estmts:
                        try_ast['orelse'] = _r66_estmts
                        self.generated_blocks.add(_r66_b)
                        self.generated_offsets.add(_r66_b.start_offset)
"""

assert u.count(ANCHOR) == 1, u.count(ANCHOR)
repl = ANCHOR[:ANCHOR.index('\n\n            if _post_try_stmts')] + INSERT + "\n            if _post_try_stmts_r19n2:\n"
assert u.count(repl) == 0
spec = {'file': REL, 'anchor': ANCHOR, 'repl': repl}
assert repl.startswith(ANCHOR.split('\n\n')[0])
io.open('specs/cand_r66_trytail_else.json', 'w', encoding='utf-8', newline='\n').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('anchor occ=%d  repl lines=%d  inserted lines=%d' % (u.count(ANCHOR), repl.count('\n'), repl.count('\n') - ANCHOR.count('\n')))
print(repr(repl[:120]))
