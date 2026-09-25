# -*- coding: utf-8 -*-
"""diag5 spec builder: slices anchors straight out of the LANDED generator bytes (read-only)
so whitespace cannot drift, and writes candidate specs into specs/.

usage: python -X utf8 mkspecs.py
"""
import io
import json
import os

REPO = r'F:/Downloads/pythoncdc-main'
ROOT = r'D:/Temp/opencode/r65gate/diag5'
REL = 'core/cfg/region_ast_generator.py'

t = io.open(os.path.join(REPO, REL), encoding='utf-8-sig', newline='').read()
U = t.replace('\r\n', '\n')
LS = U.split('\n')


def lines(a, b):
    """1-based inclusive line slice from the LF-normalised landed text."""
    return '\n'.join(LS[a - 1:b])


# ---------- edit A : _generate_if  L11581-11584  (return [] bail) ----------
A_ANCHOR = lines(11581, 11584)
A_REPL = lines(11581, 11583) + """
                        # [R65-D5-A] 双生 common_func::get_kline_time_by_section 的
                        # `if datetime_list_section[-1] in datetime_list:` 整条语句被吞
                        # （两支 .pyc 元组逐字相同 orig=210 decomp=190 jumpdiff=0 true=84）。
                        # 机制：IfRegion@530 的 merge_block 恰是其**后继兄弟** IfRegion@618
                        # 的 entry；@530 发射时把汇合块登记进 generated_blocks，@618 便在
                        # 「entry 已生成」判据（L11528）上被误判成「本区域已发射」，落到
                        # L11584 return []，整条 if 连同 then 块 638 一起消失。
                        # 识别条件（三条同层次结构事实，只看本区域与前驱区域的
                        # entry / merge_block / then_blocks / block_to_region 身份）：
                        #   (a) block_to_region[region.entry] is region —— 原则 2「每块
                        #       唯一归属」：entry 块的归属区域就是本区域本身，没有任何
                        #       BoolOp/Ternary 子区域认领它（IfRegion@530 的 entry 归
                        #       BoolOpRegion@530，所以它重入时不会误触发）；
                        #   (b) 本区域仍有未发射的臂块：then_blocks/else_blocks 里存在不在
                        #       generated_blocks 的块（@618 的 then 块 638 未发射）—— 若整条
                        #       if 真已被某处发射，其臂块必然已被同时认领；
                        #   (c) 这个 generated 标记只可能是**前驱区域的汇合点记账**：存在
                        #       另一区域 pr 使 pr.merge_block is region.entry 且
                        #       pr.entry is not region.entry。汇合块只记录「控制流跳到此」，
                        #       pr 并不负责发射此块的指令（原则 4：父/兄弟只引用子入口）。
                        # 归约方式：三条同时成立 ⇒ 撤销「entry 已生成 ⇒ 本区域已发射」这一
                        #   推断，不 return []，继续走 _detect_if_region_as_while_loop 与
                        #   _if_generate_normal，由本区域自行认领 entry 并重建条件。
                        # AST 映射：ast.If(test=由 entry 块尾 POP_JUMP_IF_FALSE 重建的
                        #   Compare(..., In, ...)，body=then_blocks 语句，orelse 空)，即复原
                        #   `if x[-1] in lst: lst.append(x[-1])`。
                        # 成对要求：本编辑只找回被吞的 if 语句；同一函数里另一条丢失语句
                        #   （and 链首块 entry 的前缀赋值）由同文件 [R65-D5-B] 找回，
                        #   缺一支该函数都过不了字节码门禁。
                        _r65d5a_merge_entry_sibling = (
                            self.region_analyzer.block_to_region.get(region.entry) is region
                            and any(_b not in self.generated_blocks
                                    for _b in (list(region.then_blocks or [])
                                               + list(region.else_blocks or [])))
                            and any(_pr is not region and _pr.entry is not region.entry
                                    and getattr(_pr, 'merge_block', None) is region.entry
                                    for _pr in self.regions))
                        if not _r65d5a_merge_entry_sibling:
                            return []"""

# ---------- edit B : _if_generate_normal L17346-17348 (entry prefix peel) ----------
B_ANCHOR = lines(17346, 17348)
B_REPL = lines(17346, 17347) + """
            if not _should_extract_entry:
                # [R65-D5-B] 双生 common_func::get_kline_time_by_section 的
                # `datetime_list = datetime_list[offset:]` 丢失（两支 .pyc 元组逐字相同：
                # orig=210 decomp=190 jumpdiff=0 true=84；单加本编辑→197/true=63）。
                # 机制：`if datetime_list and int(frequency[:-1]) >= 5:` 的分析端形态是
                #   IfRegion@530(condition_block=558, inline_boolop_chains=[[530,558],'and'],
                #   block_to_region[530] is 本 IfRegion) + 直接子 BoolOpRegion@530
                #   (blocks=[530,558], value_target=None, op_chain=[530,558])。
                #   generate() 的 L745「and 链首块 == entry」passthrough 分支据此**故意**
                #   不在入口处理里发射 entry 前缀语句、也不登记 _entry_prefix_emitted_blocks，
                #   把发射权显式让给本方法的 entry != cond_block 分支；但 BoolOpRegion 是
                #   条件上下文模式（_generate_boolop_impl 只写 condition_expr、不产出语句、
                #   return None），却把链成员块 530 登记进了 generated_blocks。于是
                #   L17347 判 entry 已 generated ⇒ 跳过前缀提取 ⇒ 落在块 530 里的那条完整
                #   赋值语句既不属于 BoolOp 操作数、也没人发射，整条消失。
                # 识别条件（四条同层次父子结构事实，均为区域归约算法内部身份，不含
                #   函数名/文件名/偏移阈值/字面量计数）：
                #   (a) region.entry is not cond_block —— 链首块不是主条件块（外层 if 已给）；
                #   (b) block_to_region[region.entry] is region —— 原则 2「每块唯一归属」：
                #       entry 块的分析端归属就是本 IfRegion（scheduler::run_weekly 的块 0
                #       归属是普通 Region@0，故该处不触发，不会重复发射）；
                #   (c) region 有**直接子** BoolOpRegion c 使 c.entry is region.entry、
                #       not c.value_target（条件上下文模式，c 不产出任何语句）、且
                #       region.entry 出现在 c.op_chain 成员里 —— 精确刻画「generated 标记
                #       只来自 c 的操作数认领」这一 provenance；
                #   (d) region.entry not in self._entry_prefix_emitted_blocks —— 前缀语句
                #       **尚未**被 generate() 的任何入口通道发射过（该集合就是本文件既有的
                #       provenance 记账，L766/996/1102，并被 L6010/29383 以同样用途引用）。
                # 归约方式：四条同时成立 ⇒ 撤销该 generated 标记对前缀提取的封锁，照常调用
                #   _if_extract_cond_instructions(region.entry, region)。该方法已有的
                #   「cond_block 是 TernaryRegion.merge_block 时跳过首个 STORE_*」规则负责
                #   排除块首属于三元汇合的 STORE_FAST offset，故不会重复发射 `offset = ...`；
                #   条件操作数本身仍由下方 _if_extract_condition_from_instructions /
                #   _discover_predicate_and_chain 负责，前缀提取不触碰。
                # AST 映射：pre_stmts = [ast.Assign(targets=[Name datetime_list],
                #   value=Subscript(Name datetime_list, Slice(None, None, Name offset)))]，
                #   置于 If(test=BoolOp(and,[Name datetime_list, Compare(...)])) 之前。
                # 成对要求：本编辑只找回链首块的前缀赋值；同函数另一条丢失语句（汇合块
                #   即兄弟入口的整条 if）由同文件 [R65-D5-A] 找回，缺一支过不了门禁。
                _r65d5b_deferred_head = (
                    self.region_analyzer.block_to_region.get(region.entry) is region
                    and region.entry not in self._entry_prefix_emitted_blocks
                    and any(isinstance(_r65d5b_c, BoolOpRegion)
                            and _r65d5b_c.entry is region.entry
                            and not getattr(_r65d5b_c, 'value_target', None)
                            and any(_r65d5b_b is region.entry
                                    for _r65d5b_b, _r65d5b_op in (_r65d5b_c.op_chain or []))
                            for _r65d5b_c in (getattr(region, 'children', None) or [])))
                if _r65d5b_deferred_head:
                    _should_extract_entry = True
            if _should_extract_entry:"""

# ---- fix indentation of A_REPL body (anchor had 20 spaces at 'if self._boolop...') ----
os.makedirs(os.path.join(ROOT, 'specs'), exist_ok=True)


def spec(path, edits):
    io.open(path, 'w', encoding='utf-8', newline='').write(
        json.dumps({'file': REL, 'edits': edits}, ensure_ascii=False, indent=1) + '\n')
    for e in edits:
        assert U.count(e['anchor']) == 1, ('anchor not unique', e['anchor'][:60])
    print('wrote', os.path.basename(path), 'edits=%d' % len(edits))


io.open(os.path.join(ROOT, 'specs', '_anchors.json'), 'w', encoding='utf-8', newline='').write(
    json.dumps({'A_ANCHOR': A_ANCHOR, 'B_ANCHOR': B_ANCHOR,
                'A_REPL': A_REPL, 'B_REPL': B_REPL}, ensure_ascii=False, indent=1) + '\n')

spec(os.path.join(ROOT, 'specs', 'r65d5_a.json'), [{'anchor': A_ANCHOR, 'repl': A_REPL}])
spec(os.path.join(ROOT, 'specs', 'r65d5_b.json'), [{'anchor': B_ANCHOR, 'repl': B_REPL}])
spec(os.path.join(ROOT, 'specs', 'r65d5_ab.json'),
     [{'anchor': A_ANCHOR, 'repl': A_REPL}, {'anchor': B_ANCHOR, 'repl': B_REPL}])
print('OK')
