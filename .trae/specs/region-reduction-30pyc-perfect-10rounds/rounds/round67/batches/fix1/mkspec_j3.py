# -*- coding: utf-8 -*-
"""R67 fix1: narrowed standalone structured-region entry guard (J3 family).

  python -X utf8 mkspec_j3.py

Writes (anchor uniqueness on the CURRENT landed bytes asserted before writing):
  specs/cand_r67_j3.json   arm j3   = J1's three + block-is-entry + region has no own merge/exit
  specs/cand_r67_j3b.json  arm j3b  = same, WITHOUT the self._current_loop conjunct

Measured basis (this dir, logs/j1dbg_*.err): the single-block narrowing diag1 banked is FALSE
on the real frames — every hit carries a 2-element `blocks` list.
"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
LANDED = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
ANCHOR = (
    "            _region = self.region_analyzer.get_entry_region_for_block(block)\n"
    "            if isinstance(_region, RegionASTGenerator._STRUCTURAL_REGION_TYPES):\n"
    "                _rid = id(_region)\n"
    "                if (_rid not in self._generated_regions\n"
    "                        and _rid not in self._generating_regions):\n"
)
TAIL = "                    self._generating_regions.add(_rid)\n"

HDR = (
    "                    # [R67-fix1 J3 无自身汇合点的顶层兄弟区域不得在循环发射中被认领]\n"
    "                    # 识别条件：五条全部只读**本帧自身参数 + _region 自身字段 +\n"
    "                    #   self._current_loop 自身字段**；不扫描任何其它区域的 blocks 集合\n"
    "                    #   （无 `x in r.blocks` 式跨区/跨层包含判据），无函数名/文件名/字面\n"
    "                    #   偏移/计数阈值，无新增 self 状态：\n"
    "                    #   (1) `region is None` —— 本帧是 _if_generate_branch_stmts 的 standalone\n"
    "                    #       调用（L23602），没有 owning 区域（文档串 L21922-21927 声明的正用途\n"
    "                    #       是 loop else body 续接）；\n"
    "                    #   (2) `self._current_loop is not None` —— 发射栈当前正在归约某个\n"
    "                    #       LoopRegion，本帧返回的 stmts 会被并到 for/while 语句**内部**；\n"
    "                    #   (3) `getattr(_region, 'parent', None) is None` —— 待认领入口区域是本函数\n"
    "                    #       区域森林的顶层区域，归 generate() 顶层区域循环（L1754）所有并排放；\n"
    "                    #   (4) `block is _region.entry` —— 本块恰是该区域的**自身 entry**（而非\n"
    "                    #       is_block_entry 也接受的 condition_block / header_block），区域作为\n"
    "                    #       完整单元整体推迟才安全；\n"
    "                    #   (5) `getattr(_region, 'merge_block', None) is None` ∧\n"
    "                    #       `getattr(_region, 'exit', None) is None` —— 该顶层区域**自身没有\n"
    "                    #       汇合点/出口**，即它是函数语句序列的尾段区域，推迟认领不会让任何\n"
    "                    #       「if 之后的续接块」在本帧丢失归属。\n"
    "                    #   实测命中面（arm=j1dbg 逐帧读数，logs/j1dbg_{synth,targets,canary}.err）：\n"
    "                    #     正例 v3   blocks=[68,98]   R=IfRegion e=98  cb=98  mb=None x=None\n"
    "                    #               nb=5 then=[102]        else=[106,148,176] par=None\n"
    "                    #     正例 v4   blocks=[66,80]   R=IfRegion e=80  cb=80  mb=None x=None\n"
    "                    #     正例 get_all_orders blocks=[332,362] R=IfRegion e=362 cb=362\n"
    "                    #               mb=None x=None nb=5 then=[366] else=[370,422,450] par=None\n"
    "                    #     反例 quotation::get_trend blocks=[158,206] R=IfRegion e=206 cb=206\n"
    "                    #               mb=220 x=220 nb=2 then=[210] else=[] —— 第 (5) 条把它挡住。\n"
    "                    # 为何更宽的 J1 被否决（两条硬性门槛读数，本判据即据此收窄）：\n"
    "                    #   J1 = (1)(2)(3) 三条，缺 (4)(5)。实测（arm=j1，specs/cand_r67_j1.json 原样）：\n"
    "                    #   (a) canary **quotation.pyc 仍 143/143 但产物 sha 从 4d41187e356544e0 移开**\n"
    "                    #       （本 dir 复测 3eb76e512df9ab1e）⇒ canary 要求逐字节相同，**门槛失败**；\n"
    "                    #   (b) 具名目标本 dir 复测为 **108/119（get_all_orders 已清）**，未复现\n"
    "                    #       diag1 记下的 ERR（RuntimeError('Failed to decompile ...')）；两条读数\n"
    "                    #       都记在这里，无论哪条成立 J1 都不可落地。\n"
    "                    #   移开 canary 的正是第 (5) 条挡住的反例形状：被认领的顶层 IfRegion 自带\n"
    "                    #   merge_block/exit=220，standalone 尾扫必须穿过它继续发射，跳过认领会改写\n"
    "                    #   该处产物字节。\n"
    "                    #   另：diag1 记账的「standalone blocks 是单块」收窄实测**不成立**——四个命中\n"
    "                    #   帧的 blocks 参数都是 2 个块（[循环尾块, 外层 if 汇合块]），加 `len(blocks)\n"
    "                    #   == 1` 判据后补丁完全失效（arm=j2 复现仍 6/7），故本判据改用 (4)(5) 两条\n"
    "                    #   _region 自身字段收窄。\n"
    "                    # 归约方式：命中时**不在本层认领**——既不 _generate_region(_region)，也不把\n"
    "                    #   _region.blocks 写进 generated_blocks / _generated_regions，直接 continue\n"
    "                    #   让本次 standalone 调用返回空语句；该区域回到它真正的所有者（顶层区域循环）\n"
    "                    #   按既有次序发射**恰好一次**。不删除、不抑制任何语句，只把发射层级从\n"
    "                    #   「循环体内部」归还给「函数体顶层语句序列」。\n"
    "                    # AST 映射：IfRegion(parent=None ∧ merge=None ∧ exit=None) → 与外层 ast.If\n"
    "                    #   **平级**的兄弟 ast.If，位于函数体语句序列；现状把它塞进 ast.For 之后 ⇒\n"
    "                    #   then 臂多吞一整段，且 elif 分支内 listcomp 的 ast.Return 被重复发射一次\n"
    "                    #   （get_all_orders 指纹 orig=79 decomp=78 jumpdiff=2 truediff=24）。\n"
)

COND_TAIL = (
    "                            and getattr(_region, 'parent', None) is None\n"
    "                            and block is _region.entry\n"
    "                            and getattr(_region, 'merge_block', None) is None\n"
    "                            and getattr(_region, 'exit', None) is None):\n"
    "                        continue\n"
)
GUARD_J3 = ("                    if (region is None and self._current_loop is not None\n"
            + COND_TAIL)
GUARD_J3B = ("                    if (region is None\n" + COND_TAIL)

u = io.open(LANDED, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
assert u.count(ANCHOR) == 1, 'anchor count=%d' % u.count(ANCHOR)
for name, guard in (('cand_r67_j3', GUARD_J3), ('cand_r67_j3b', GUARD_J3B)):
    repl = ANCHOR + HDR + guard + TAIL
    io.open('specs/%s.json' % name, 'w', encoding='utf-8').write(json.dumps(
        {'name': name, 'file': 'core/cfg/region_ast_generator.py',
         'edits': [{'anchor': ANCHOR, 'repl': repl}],
         'note': 'R67 fix1 J3: defer parentless tail top-level region claimed by standalone'
                 ' loop-tail scan (narrowed by own merge_block/exit)'},
        ensure_ascii=False, indent=1))
    print('%s written, inserted lines = %d' % (name, repl.count('\n') - ANCHOR.count('\n')))
