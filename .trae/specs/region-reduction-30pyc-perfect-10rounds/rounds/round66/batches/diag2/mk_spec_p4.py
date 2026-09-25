# -*- coding: utf-8 -*-
"""diag2 R66: build specs/cand_r66_p4_chainhead_owner.json (single anchor edit).

Anchor: the owner-selection loop of _generate_chain_head_prefix_assign
(lands on the unique BoolOp-without-value_target skip inside that loop).
Patch adds one same-level unique-ownership guard: an expression region whose
OWN blocks are all already registered in self.generated_blocks has already
been emitted by an earlier statement walk, so it must not be re-claimed as a
chain-head prefix-assign owner (that re-claim is what emitted the
`self.log.quote.debug(f'调用函数load_bars_from_hundsun，参数为：stocks=...')`
statement group twice in quote.load_bars_from_hundsun).
"""
import io
import json

GEN = 'core/cfg/region_ast_generator.py'
P = 'F:/Downloads/pythoncdc-main/' + GEN
src = io.open(P, encoding='utf-8-sig', newline='').read()
nl = '\r\n' if src.count('\r') else '\n'
u = src.replace(nl, '\n')

ANCHOR = ("            if isinstance(_r, BoolOpRegion) and not _r.value_target:\n"
          "                continue\n")
assert u.count(ANCHOR) == 1, u.count(ANCHOR)

REPL = ANCHOR + """            # [R66-d2 P4] 链首前缀赋值的同层唯一归属守卫（重复发射消除）。
            # 识别条件: 候选表达式区域自身的 blocks 已全部登记在
            #   self.generated_blocks，即该区域的指令流在本次调用之前已由语句
            #   walk 认领并发射完毕（实测 quote.load_bars_from_hundsun 的
            #   merge_ctx=='fstring' 三元区：序言处 _generate_region 已生成它
            #   并标记其 4 个块，本方法被调用时的快照为 mask=GGGG、
            #   id(region) 尚未进入 _generated_regions）。
            # 归约方式: 与同一循环里既有的 `id(_r) in self._generated_regions
            #   / self._generating_regions`「已生成或生成中即不再认领」守卫同
            #   级同性质，只读区域自身状态；不引入名字/偏移/阈值判据，不做跨
            #   区域跨层次包含，也不抑制任何区域的正常发射（首次发射路径不经
            #   本方法）。
            # AST 映射: 不新增映射。合法链首前缀赋值（`first = lo <= x <= hi;`）
            #   的链首块此刻尚未被所属 IfRegion 认领（其 generated_blocks.add
            #   发生在 pre_stmts 生成之后的 _disc_ok 收尾里），故其
            #   all-blocks-generated 恒为 False，守卫只在重复认领时生效。
            if _r.blocks and all(_gb in self.generated_blocks
                                 for _gb in _r.blocks):
                continue
"""

spec = {'file': GEN, 'anchor': ANCHOR, 'repl': REPL}
io.open('specs/cand_r66_p4_chainhead_owner.json', 'w', encoding='utf-8').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('ok, added lines =', REPL.count('\n') - ANCHOR.count('\n'))
