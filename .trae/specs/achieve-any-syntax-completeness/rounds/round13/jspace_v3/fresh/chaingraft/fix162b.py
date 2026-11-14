# fix162b.py: rr-v5r162 [v162-CHAINGRAFT] 短路口合并点甄别
#
# 缺陷（cg7/cg8 最小复现，与 urllib.request.urlretrieve 实形同构）：
#   with 作用域内
#       if url_type == 'file' and not filename:   # 守卫 and 链（未统一成 BoolOp）
#           return ...
#       if filename: ... else: ...                # 后续 if/else
#   当前产物把后续 if 误挂成守卫 if 的 elif，且守卫的第二成员被塞成嵌套 if：
#       if url_type == 'file':
#           if not filename: return ...
#       elif filename: ...
#       else: ...
#   （判官 Different control flow）
#
# 根因（探针 probe_cg7.py 实证，BUILD_ELIF 序列）：守卫 if（@68）的 else_blocks
#   含 @154——而 @154 是 then 分支（@122 嵌套 if）的死目标/后继，即 @154 是整条
#   守卫链的短路口合并点，不是本 if 的 else 分支。elif 构建器只看「else 目标是不是
#   条件块」就判 elif，未排除「该目标同时可从 then 到达」的情形。
#
# 修复（单点，只增不破）：在 _build_elif_region 调用前加甄别——当 else 目标块本身
#   是条件跳转块（elif 候选）且可从 then_blocks 任一块直接到达时，它是短路口合并
#   点：清空 else_blocks、merge=该目标 → 落回基础 if（无 else）形态，后续 if 由
#   自己成为独立 IfRegion。门控不命中时逐字节维持现状（C3）。
#   I.4 白名单：只读块后继集合 + 末指令 opcode。
import io
import py_compile

PATH = r'F:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'

s = io.open(PATH, encoding='utf-8-sig').read()
orig = s

ANCHOR = ("            region = self._build_elif_region(block, then_blocks, else_blocks, merge, "
          "all_condition_blocks, condition_block, boundary_stop=boundary_stop, "
          "ternary_regions=ternary_regions, main_inline_boolop_chain=_main_inline_boolop_chain)")

GUARD = '''            # [v162-CHAINGRAFT] 短路口合并点甄别（只增不破）：守卫条件（如
            # `if A and B:`）与紧随其后的 `if C: ... else: ...` 在 with/try 作用域
            # 内未统一为 BoolOp 时，守卫 if 的假目标 = 后续 if 的条件块，elif 构建
            # 器会把后续 if 误挂成 elif。判据（结构性）：else 目标块自身是条件跳转
            # 块（elif 候选）**且**可从 then_blocks 任一块直接到达——即它是整条短
            # 路链的合并点，不是本 if 的 else 分支。命中则清空 else_blocks 并把
            # merge 指向该块（渲染为无 else 的 if，后续 if 自成一区）；不命中逐字
            # 节维持现状（C3）。I.4 白名单：块后继集合 + 末指令 opcode。
            if (else_blocks and else_succ is not None and block is not None
                    and else_succ is not then_succ):
                _v162_es_li = else_succ.get_last_instruction()
                _v162_es_is_cond = (_v162_es_li is not None
                                    and _v162_es_li.opname in FORWARD_CONDITIONAL_JUMP_OPS)
                if _v162_es_is_cond:
                    _v162_join_from_then = False
                    for _v162_tb in then_blocks:
                        if _v162_tb is block:
                            continue
                        try:
                            if else_succ in _v162_tb.successors:
                                _v162_join_from_then = True
                                break
                        except TypeError:
                            continue
                    if _v162_join_from_then:
                        else_blocks = []
                        merge = else_succ
'''

assert s.count(ANCHOR) == 1, 'anchor count %d' % s.count(ANCHOR)
s = s.replace(ANCHOR, GUARD + ANCHOR, 1)

assert s != orig
assert s.count('v162-CHAINGRAFT') == 2, 'marker %d' % s.count('v162-CHAINGRAFT')
io.open(PATH, 'w', encoding='utf-8-sig', newline='').write(s)
print('fix162b applied: markers=%d' % s.count('v162-CHAINGRAFT'))

py_compile.compile(PATH, doraise=True)
print('syntax OK')
