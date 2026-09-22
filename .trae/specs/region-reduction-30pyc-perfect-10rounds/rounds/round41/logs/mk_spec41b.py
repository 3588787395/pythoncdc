import io
import json

anchor = """                if _meaningful_instrs:
                    bs = self._generate_block_statements(block)
                    if bs:
                        stmts.extend(bs)
                    self.generated_blocks.add(block)
                    self.generated_offsets.add(block.start_offset)
                    continue"""

repl = """                if _meaningful_instrs:
                    bs = self._generate_block_statements(block)
                    if bs:
                        stmts.extend(bs)
                    # [R41-B] 带有效语句的 CONTINUE 角色块：它的回边并不总能由
                    # For 节点重编译自然再生。自然再生只覆盖「本 if 是循环体末条
                    # 语句」的形态，即所属 IfRegion.merge_block 就是当前循环
                    # header（R4-H 注释所称 t4/t6 形态）；merge 另有所指时，循环体
                    # 在 if 之后仍有代码，本块语句之后的落点是**别的块**，隐式回边
                    # 归属于那个落点块，本块必须补发显式 Continue，否则原码这条
                    # JUMP_BACKWARD 整条丢失（one_prod_to_dataframe 形态）。
                    # 判据（全部同层结构事实，不读名称/常量/偏移/指令计数）：
                    #   ①本块末指令为无条件 JUMP_BACKWARD(_NO_INTERRUPT)，且其目标块
                    #     就是 self._current_loop.header_block —— 逃逸到最内层循环头，
                    #     故 ast.Continue 是忠实映射；
                    #   ②所属 region 是 IfRegion 且其 merge_block 存在且不是该 header
                    #     —— if 之后循环体内还有代码，隐式回边不落在本块位置。
                    _r41b_hdr = (getattr(self._current_loop, 'header_block', None)
                                 if self._current_loop else None)
                    _r41b_last = block.get_last_instruction()
                    if (_r41b_hdr is not None
                            and _r41b_last is not None
                            and _r41b_last.opname in ('JUMP_BACKWARD',
                                                      'JUMP_BACKWARD_NO_INTERRUPT')
                            and _r41b_last.argval is not None
                            and self.cfg.get_block_by_offset(_r41b_last.argval) is _r41b_hdr
                            and isinstance(region, IfRegion)
                            and getattr(region, 'merge_block', None) is not None
                            and region.merge_block is not _r41b_hdr):
                        stmts.append({'type': 'Continue'})
                    self.generated_blocks.add(block)
                    self.generated_offsets.add(block.start_offset)
                    continue"""

spec = {'file': 'core/cfg/region_ast_generator.py', 'anchor': anchor, 'repl': repl, 'count': 1}
io.open(r'D:/Temp/r41gate/spec41b.json', 'w', encoding='utf-8').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('spec written; anchor lines', anchor.count('\n'), 'inserted', repl.count('\n') - anchor.count('\n'))
