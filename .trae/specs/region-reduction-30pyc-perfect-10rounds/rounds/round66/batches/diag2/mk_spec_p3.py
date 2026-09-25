# -*- coding: utf-8 -*-
"""diag2 R66: build specs/cand_r66_p3_prefixparts.json (single anchor edit).

Anchor: the `fstring_parts = _stack` line that closes the cond_block prefix scan
inside the merge_ctx == 'fstring' branch of _generate_ternary.  The patch keeps
that scan untouched as the fallback and additionally reduces every *complete*
interpolation group (right-bounded by its own FORMAT_VALUE) with the existing
same-level helper _fstring_parts_from_segment.
"""
import io
import json

GEN = 'core/cfg/region_ast_generator.py'
P = 'F:/Downloads/pythoncdc-main/' + GEN
src = io.open(P, encoding='utf-8-sig', newline='').read()
nl = '\r\n' if src.count('\r') else '\n'
u = src.replace(nl, '\n')

ANCHOR = "                    fstring_parts = _stack\n"
assert u.count(ANCHOR) == 1, u.count(ANCHOR)

REPL = ANCHOR + """                    # [R66-d2 P3] 前缀以 FORMAT_VALUE 为右界逐段归约（C1b 同族判据）。
                    # 识别条件: cond_block 前缀里以 FORMAT_VALUE 收尾的一段是一个
                    #   完整插值组——段顶操作数被该 FORMAT_VALUE 消费、段底其余项
                    #   全为字面量 Constant（判据即既有 _fstring_parts_from_segment
                    #   的单趟栈模拟，与 [R65-d3 C1b] 在 merge 尾段所用者同层次同族）；
                    #   不引入函数名/文件名/偏移/阈值条件，也不跨区域跨层次包含。
                    # 归约方式: 完整段整体归约为 字面量 Constant + 单个 FormattedValue
                    #   （段内 LOAD_FAST/LOAD_CONST/BUILD_SLICE/BINARY_SUBSCR/
                    #   PRECALL+CALL 等自包含求值序列由表达式重建器折叠成一个操作数
                    #   节点）；结尾不完整段仍走上方改前的逐条 LOAD_* 扫描；任一段
                    #   解释不了（返回 None）即整条前缀退回改前结果，无新增逃逸口。
                    # AST 映射: JoinedStr.values = [Constant | FormattedValue(<完整
                    #   表达式>)]，插值表达式的多条 LOAD_* 不再被拆成多个假字面量。
                    if cond_val_start is not None and cond_val_start > 0:
                        _p3_parts = []
                        _p3_seg = []
                        _p3_ok = True
                        for _p3_pi in cond_block_instrs[
                                _r65_callee_skip:cond_val_start]:
                            if _p3_pi.opname != 'FORMAT_VALUE':
                                _p3_seg.append(_p3_pi)
                                continue
                            _p3_parsed = self._fstring_parts_from_segment(
                                _p3_seg, _p3_pi)
                            if _p3_parsed is None:
                                _p3_ok = False
                                break
                            _p3_parts.extend(_p3_parsed)
                            _p3_seg = []
                        if _p3_ok and _p3_parts:
                            _p3_tail = []
                            for _p3_ti in _p3_seg:
                                if _p3_ti.opname.startswith('LOAD_'):
                                    _p3_te = self.expr_reconstructor.reconstruct(
                                        [_p3_ti])
                                    if _p3_te:
                                        _p3_tail.append(_p3_te)
                            fstring_parts = _p3_parts + _p3_tail
"""

spec = {'file': GEN, 'anchor': ANCHOR, 'repl': REPL}
io.open('specs/cand_r66_p3_prefixparts.json', 'w', encoding='utf-8').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('ok, added lines =', REPL.count('\n') - ANCHOR.count('\n'))
