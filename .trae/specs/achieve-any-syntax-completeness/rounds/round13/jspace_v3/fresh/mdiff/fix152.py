# fix152.py: rr-v5r152 two add-only fixes
#   A) [v152-HANDLERRET] generator: except-handler body block membership exemption
#      for the return-None->Break conversion (role coarsened to LOOP_BODY misses
#      the EXCEPT_* role guard; difflib._line_pair_iterator `except StopIteration:
#      return` renders as break = real R1, generator terminates instead of returning)
#   B) [v152-ORCLAIM] analyzer: forward or-chain walk claimant exemption — when the
#      fall-through successor of an or-head chain is claimed by an ancestor
#      LoopRegion (B11 structural clause: claimant blocks contain this loop's
#      header) and the block carries the or-member signature (false-side jump
#      target outside this loop's body-semantic set + fall-through == this loop's
#      header), continue the walk; v143 closure criteria ①-④ still validate the
#      whole chain (difflib._line_pair_iterator `while (len(fromlines)==0 or
#      len(tolines)==0):` loses the second member = real R1)
import io

# ---------- Fix A ----------
p1 = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
s1 = io.open(p1, encoding='utf-8-sig').read()

anchor_a = """                    _hb_role = self.region_analyzer.get_block_role(block)
                    _is_except_block = _hb_role in (
                        getattr(BlockRole, 'EXCEPT_STORE', None),
                        getattr(BlockRole, 'EXCEPT_HANDLER', None),
                    ) if _hb_role is not None else False
                    if _is_except_block:
                        pass  # Fall through to normal Return handling below"""
assert anchor_a in s1, 'fixA anchor missing'
repl_a = """                    _hb_role = self.region_analyzer.get_block_role(block)
                    _is_except_block = _hb_role in (
                        getattr(BlockRole, 'EXCEPT_STORE', None),
                        getattr(BlockRole, 'EXCEPT_HANDLER', None),
                    ) if _hb_role is not None else False
                    # [v152-HANDLERRET] 角色粗化豁免（只增不破）：循环体内的
                    # handler 臂块（POP_EXCEPT + LOAD_CONST None + RETURN_VALUE，
                    # `except StopIteration: return`，difflib._line_pair_iterator
                    # 实形）的 block_role 被循环体标注粗化为 LOOP_BODY，既有
                    # EXCEPT_STORE/EXCEPT_HANDLER 角色守卫够不着它——裸
                    # `return None` 在 try+loop 上下文被误转成 Break（真实 R1：
                    # 生成器遇 StopIteration 应终止返回，却继续下一轮迭代）。
                    # 结构事实补充：块归属 TryExceptRegion（block_to_region
                    # 成员，handler 臂块的唯一归属）即豁免 Break/Continue
                    # 转换，落回下方正常 Return 重建（与 R3-B115 设计意图
                    # 一致：handler 臂 return 显式重建，不转循环出口）。
                    if not _is_except_block:
                        _v152_owner = self.region_analyzer.block_to_region.get(block)
                        _is_except_block = isinstance(_v152_owner, TryExceptRegion)
                    if _is_except_block:
                        pass  # Fall through to normal Return handling below"""
s1 = s1.replace(anchor_a, repl_a, 1)
io.open(p1, 'w', encoding='utf-8-sig').write(s1)
print('fix A inserted')

# ---------- Fix B ----------
p2 = r'F:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'
s2 = io.open(p2, encoding='utf-8-sig').read()

anchor_b = """            region_for_ft = self.block_to_region.get(ft_succ)
            if region_for_ft is not None and region_for_ft.interrupts_boolop_forward_chain(ft_succ):
                break
            visited.add(ft_succ.start_offset)"""
assert anchor_b in s2, 'fixB anchor missing'
repl_b = """            region_for_ft = self.block_to_region.get(ft_succ)
            if region_for_ft is not None and region_for_ft.interrupts_boolop_forward_chain(ft_succ):
                # [v152-ORCLAIM] 祖先循环认领豁免（只增不破）：or 首链的
                # fall-through 后继被祖先 while-True 循环体收集收走时
                # （B11 结构判据：认领者 blocks 含纳本循环 header），该块
                # 语义上是本循环 or 条件的次操作数（真边落空进体入口、
                # 假边前向跳循环出口——difflib._line_pair_iterator 实形
                # `while (len(fromlines)==0 or len(tolines)==0):` 的第二
                # 成员 len(tolines)==0 块被外层循环收走，前向走查在此截断
                # 成单成员链→闭合判据整体失败→条件第二成员丢失=真实 R1）。
                # 豁免继续走查；折叠合法性仍由 v143 闭合判据①-④整体承担
                # （链首真边=header、末成员假边=出口+落空=header、非首成员
                # 无 STORE），判据不满足时整链 None 逐位落回既有行为（C3）。
                _v152_orclaim_ok = False
                if (chain and chain[0][1] == 'or'
                        and isinstance(region_for_ft, LoopRegion)
                        and loop.header_block is not None
                        and loop.header_block in getattr(region_for_ft, 'blocks', ())):
                    _v152_last_ft = ft_succ.get_last_instruction()
                    _v152_jt = (self.cfg.get_block_by_offset(_v152_last_ft.argval)
                                if _v152_last_ft is not None and _v152_last_ft.argval is not None
                                else None)
                    _v152_body_sem = set(loop.body_blocks or [])
                    if loop.header_block is not None:
                        _v152_body_sem.add(loop.header_block)
                    if loop.condition_block is not None:
                        _v152_body_sem.add(loop.condition_block)
                    _v152_ft_succ = next((s for s in ft_succ.conditional_successors
                                          if s.start_offset != _v152_last_ft.argval), None) if _v152_last_ft else None
                    if (_v152_jt is not None and _v152_jt not in _v152_body_sem
                            and _v152_ft_succ is not None
                            and _v152_ft_succ is loop.header_block):
                        _v152_orclaim_ok = True
                if not _v152_orclaim_ok:
                    break
            visited.add(ft_succ.start_offset)"""
s2 = s2.replace(anchor_b, repl_b, 1)
io.open(p2, 'w', encoding='utf-8-sig').write(s2)
print('fix B inserted')

import py_compile
py_compile.compile(p1, doraise=True)
py_compile.compile(p2, doraise=True)
print('syntax OK')
