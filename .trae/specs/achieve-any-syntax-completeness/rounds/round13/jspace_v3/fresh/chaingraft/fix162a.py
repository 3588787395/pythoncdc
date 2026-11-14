# -*- coding: utf-8 -*-
"""fix162a.py — rr-v5r162「语句级 if 链尾」子缺陷：add_handler 的 `else: continue` 降级。

目标文件：core/cfg/region_analyzer.py（唯一改动文件）
注入点：_build_elif_region 内嵌 _check_elif_chain 的 inner_merge 修正段
        （外层链汇合点回填之后、`if inner_merge is None:` 之前）
纪律：anchor 断言 count==1；不命中不改；utf-8-sig 读写（保留 BOM）；py_compile 校验。
"""
import io
import os
import py_compile
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
TARGET = os.path.join(ROOT, 'core', 'cfg', 'region_analyzer.py')

ANCHOR = (
    "            if inner_merge is None and merge_ is not None and inner_else_succ == merge_:\n"
    "                inner_merge = merge_\n"
    "            if inner_merge is None:\n"
)

GATE = '''            # [v162-CHAINGRAFT] 语句级 if 链尾：尾 elif 的 false 边直落循环控制块
            #（continue）时保留 elif 形态，不把该 elif 降级进 else、也不把 continue 并入 else。
            # 缺陷形态（add_handler）：`if A: ... elif B: ... elif C: ... else: continue`
            # 中最后一个 elif 条件块的两条边是 then→链汇合点(merge_)、false→纯
            # JUMP_BACKWARD 回循环头（continue）。NCPD(then, false) 沿回边所求的
            # inner_merge 落在【循环头】——「≠ merge_ 且非终态」恰好命中下方 _d2 判据
            #（else 内嵌套 if + 尾随语句：inner_merge 非终态即 return None），整级弃权 ⇒ 该 elif 被降级进
            # else：`else: if B: ...; continue`，continue 落进 else 分支并被无条件执行
            #（语义破坏：B 为真时也 continue，跳过链汇合点后的尾随语句）。
            # 判据（只读 CFG/块后继/末指令 opcode，I.4 白名单）：
            #   ① 当前 elif 条件块在某个循环内，NCPD 的 inner_merge 正是该循环的循环头
            #      （回边造成的伪汇合点）；
            #   ② false 边入口 inner_else_succ 是【纯】回边块：末指令为 JUMP_BACKWARD*、
            #      目标即 inner_merge，除该跳转外无可语句化指令 ⇒ 它就是 continue，
            #      不可能承载「嵌套 if 之后的尾随语句」；
            #   ③ then 边入口以 JUMP_FORWARD/JUMP_ABSOLUTE 直接跳到外层链汇合点 merge_
            #      ⇒ then 臂【越过】continue 块，这正是 elif 形态（若源码为
            #      `else: if B: ...; continue`，then 臂应跳向 continue 块而非 merge_）。
            # 归约方式：inner_merge 由「循环头」改写为外层链汇合点 merge_（then 臂与
            # false 边都止于 merge_），末尾 final_else 恰为 [inner_else_succ]（`else:
            # continue`）；不新建区域/AST 节点。判据任一不成立 ⇒ 逐字节保持原行为。
            if (inner_merge is not None
                    and merge_ is not None
                    and inner_else_succ is not None
                    and inner_then_succ is not None
                    and inner_merge is not merge_
                    and merge_ is not inner_else_succ
                    and merge_ is not first_else
                    and inner_merge in getattr(self.loop_analyzer, 'loop_headers', ())):
                _cg_loop = self._find_enclosing_loop(first_else)
                _cg_false_last = inner_else_succ.get_last_instruction()
                _cg_then_last = inner_then_succ.get_last_instruction()
                if (_cg_loop is not None
                        and inner_merge in _cg_loop.blocks
                        and _cg_false_last is not None
                        and _cg_false_last.opname in ('JUMP_BACKWARD',
                                                      'JUMP_BACKWARD_NO_INTERRUPT')
                        and _cg_false_last.argval == inner_merge.start_offset
                        and _cg_then_last is not None
                        and _cg_then_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE')
                        and _cg_then_last.argval == merge_.start_offset):
                    _cg_false_stmts = [i for i in inner_else_succ.instructions
                                       if i.opname not in NOISE_OPS
                                       and i.opname not in ('JUMP_BACKWARD',
                                                            'JUMP_BACKWARD_NO_INTERRUPT')]
                    if not _cg_false_stmts:
                        inner_merge = merge_
'''


def main():
    with io.open(TARGET, 'r', encoding='utf-8-sig', newline='') as f:
        src = f.read()
    n = src.count(ANCHOR)
    if n != 1:
        print('ANCHOR count=%d (expect 1) -> abort' % n)
        return 2
    if '[v162-CHAINGRAFT]' in src:
        print('already patched -> abort')
        return 3
    out = src.replace(ANCHOR, ANCHOR.replace(
        "            if inner_merge is None:\n",
        GATE + "            if inner_merge is None:\n"), 1)
    assert out != src
    with io.open(TARGET, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(out)
    py_compile.compile(TARGET, doraise=True)
    print('PATCHED ok; anchor count=1; py_compile ok')
    return 0


if __name__ == '__main__':
    sys.exit(main())
