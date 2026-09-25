# -*- coding: utf-8 -*-
"""R67 fix1: build the narrowed standalone-entry guard specs (J2 / J2b).

  python -X utf8 mkspec_j2.py

Reads the CURRENT landed bytes, asserts the anchor occurs exactly once, and writes
specs/cand_r67_j2.json (with the self._current_loop conjunct) and
specs/cand_r67_j2b.json (without it).  Nothing is patched here; h62.py build applies them.
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

# 注释三件套（识别条件 / 归约方式 / AST 映射）+ 更宽 J1 的两条失败读数。
COMMENT = (
    "                    # [R67-fix1 J2 单块 standalone 不得认领顶层兄弟区域]\n"
    "                    # 识别条件：五条全部只读**本帧自身参数 + _region 自身字段 +\n"
    "                    #   self._current_loop 自身字段**，不扫描任何其它区域的 blocks 集合\n"
    "                    #   （无 `x in r.blocks` 跨区/跨层包含判据），无函数名/文件名/字面偏移/\n"
    "                    #   计数阈值，无新增 self 状态：\n"
    "                    #   (1) `region is None` —— 本帧是 _if_generate_branch_stmts 的\n"
    "                    #       standalone 调用（L23602），没有 owning 区域；\n"
    "                    #   (2) `len(blocks) == 1` —— 本次 standalone 调用**只带来一个块**；\n"
    "                    #       文档串 L21922-21927 声明的正用途是 loop else body 续接，那种\n"
    "                    #       调用带来的是 else 体块序列；单块调用才是「循环尾块跳到外层\n"
    "                    #       if 区域汇合点」这一形状；\n"
    "                    #   (3) `block is _region.entry` —— 待认领区域**以其自身 entry 字段\n"
    "                    #       等于该单块**而匹配（IfRegion.is_block_entry 也接受 condition_block，\n"
    "                    #       LoopRegion 还接受 header/condition：此条把匹配收敛到真正的区域入口）；\n"
    "                    #   (4) `getattr(_region, 'parent', None) is None` —— 该入口区域是本函数\n"
    "                    #       区域森林的**顶层**区域（parent 是其自身字段），归 generate() 顶层\n"
    "                    #       区域循环（L1754 `region_ast = self._generate_region(region)`）所有；\n"
    "                    #   (5) `self._current_loop is not None` —— 当前发射栈正处在某个\n"
    "                    #       LoopRegion 内部，本帧产出的 stmts 会被并进 for/while 语句体，\n"
    "                    #       于是顶层兄弟被降级成循环体语句。\n"
    "                    #   实测复现形状（diag1 捕获，v3 与 trade_live_broker::get_all_orders 同型）：\n"
    "                    #   standalone blocks=[98] ∧ _region=IfRegion@98(entry=98, parent=None) ∧\n"
    "                    #   98 是外层 IfRegion 的 merge_block/exit ⇒ 五条同时成立。\n"
    "                    # 为何更宽的 J1 被否决（两条实测读数，本判据即按捕获形状把它收窄）：\n"
    "                    #   J1 = (1)∧(5)∧(4) 三条，缺 (2)(3)。repro 6/7→7/7、battery 31 项不动，但\n"
    "                    #   (a) 具名目标 trade_live_broker.pyc 在 harness 下变成**不可解码**\n"
    "                    #       （targets 107/119 -> ERR RuntimeError('Failed to decompile ...')），\n"
    "                    #   (b) canary quotation.pyc 仍 143/143 但**产物 sha 离开 4d41187e356544e0**。\n"
    "                    #   即 J1 在多块 standalone else-body 续接与非 entry（condition/header）匹配\n"
    "                    #   上也认领失败，那些形状是既有正确发射路径；(2)(3) 两条正是把判据限制回\n"
    "                    #   捕获形状、把那些形状交还原路径。\n"
    "                    # 归约方式：命中时**不在本层认领**——既不 _generate_region(_region)，也不把\n"
    "                    #   _region.blocks 写进 generated_blocks / _generated_regions，直接 continue\n"
    "                    #   让本次单块 standalone 调用返回空语句；该区域回到它真正的所有者（顶层区域\n"
    "                    #   循环）按既有次序发射**恰好一次**。不删除、不抑制任何语句，只把发射层级\n"
    "                    #   从「循环体内部」归还给「函数体顶层语句序列」。\n"
    "                    # AST 映射：IfRegion(parent=None) → 与外层 ast.If **平级**的兄弟 ast.If 节点，\n"
    "                    #   位于函数体语句序列中；现状则把它塞进 ast.For.body 之后 ⇒ then 臂多吞一整段，\n"
    "                    #   且 elif 分支内 listcomp 的 ast.Return 被重复发射一次（orig=79 decomp=78，\n"
    "                    #   jumpdiff=2 truediff=24 指纹）。\n"
)

GUARD_J2 = (
    "                    if (region is None and len(blocks) == 1\n"
    "                            and block is _region.entry\n"
    "                            and getattr(_region, 'parent', None) is None\n"
    "                            and self._current_loop is not None):\n"
    "                        continue\n"
)
GUARD_J2B = (
    "                    if (region is None and len(blocks) == 1\n"
    "                            and block is _region.entry\n"
    "                            and getattr(_region, 'parent', None) is None):\n"
    "                        continue\n"
)

u = io.open(LANDED, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
for name, guard in (('cand_r67_j2', GUARD_J2), ('cand_r67_j2b', GUARD_J2B)):
    repl = ANCHOR + COMMENT + guard + "                    self._generating_regions.add(_rid)\n"
    assert u.count(ANCHOR) == 1, 'anchor count=%d' % u.count(ANCHOR)
    spec = {
        'name': name,
        'file': 'core/cfg/region_ast_generator.py',
        'edits': [{'anchor': ANCHOR, 'repl': repl}],
        'note': 'R67 fix1 narrowed standalone structured-region entry guard',
    }
    io.open('specs/%s.json' % name, 'w', encoding='utf-8').write(
        json.dumps(spec, ensure_ascii=False, indent=1))
    print('%s written, inserted lines = %d' % (name, repl.count('\n') - ANCHOR.count('\n')))
