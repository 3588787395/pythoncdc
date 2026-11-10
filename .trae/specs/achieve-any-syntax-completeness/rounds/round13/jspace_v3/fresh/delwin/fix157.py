# fix157.py: rr-v5r157 [v157-DELWIN] IfRegion 条件块前置语句段——DELETE_SUBSCR/
# DELETE_ATTR 操作数窗口形 del 语句还原（只增不破，单文件一处）。
#
# F1: `del _tmp[:]` + `if _opener:`（urllib.request.urlcleanup 实形）v156 渲染
#     丢 `del _tmp[:]`（判官 Different bytecode：LOAD _tmp; LOAD_CONST None;
#     LOAD_CONST None; BUILD_SLICE; DELETE_SUBSCR 五指令整句蒸发）。
# 根因: _if_extract_cond_instructions 的 [v133-DELSTMT] 分支（v156:~23116）
#     要求 `not pre_instrs` 才发射 del——DELETE_SUBSCR/DELETE_ATTR 的操作数
#     装载窗口（LOAD obj / 键装载 / BUILD_SLICE）先落入默认累积，DELETE 到达
#     时 pre_instrs 非空 → 分支不命中 → 窗口+DELETE 整段留在 pre_instrs，循环
#     尾部无 flush 直接丢弃（返回 (pre_stmts, cond_instrs)，pre_instrs 弃置）
#     = 整句蒸发。v133 修的简单名形（DELETE_GLOBAL，无操作数窗口）窗口恒空
#     命中；操作数窗口形恒不命中=死代码分支。
# 修复: DELETE_ATTR/DELETE_SUBSCR 分支加操作数窗口精确形（[v157-DELWIN]）：
#     pre_instrs 非空时经 expr_reconstructor 模拟装载窗口，栈恰为
#     DELETE_ATTR→1 项 / DELETE_SUBSCR→2 项（=DELETE 消费数，多余残留 ⇒ 非
#     精确窗口维持旧行为）时调 _build_delete_stmt(instr, 窗口+[DELETE]) 归约
#     单条 Delete 发射 pre_stmts 并清空 pre_instrs。空 pre_instrs 既有 v133
#     路径逐位保留；非精确窗口形维持默认累积（C3）。语言级依据：条件块内
#     DELETE_* 恒为完整语句终结（del 不可作子表达式），其前缀窗口在最后一次
#     语句终结（STORE_*/POP_TOP flush）之后累积——窗口外不可能有未终结残留，
#     「栈恰 N 项」判据把误配封死。
import io

PATH = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
MARKER = 'v157-DELWIN'

s = io.open(PATH, encoding='utf-8-sig').read()
orig = s

old = """            if (instr.opname in ('DELETE_ATTR', 'DELETE_SUBSCR')
                    and not pre_instrs):
                _del_stmts = self._build_delete_stmt(instr, [instr])
                if _del_stmts:
                    pre_stmts.extend(_del_stmts)
                    continue
                pre_instrs.append(instr)
                continue"""
assert s.count(old) == 1, 'anchor count %d' % s.count(old)

new = """            if instr.opname in ('DELETE_ATTR', 'DELETE_SUBSCR'):
                # [v157-DELWIN] 操作数窗口形 del 还原（只增不破）：窗口
                # （LOAD obj / 键装载 / BUILD_SLICE）先落入默认累积，DELETE
                # 到达时 pre_instrs 非空——v133 既有 `not pre_instrs` 门恒不
                # 命中（操作数窗口形死代码），窗口+DELETE 留 pre_instrs 循环
                # 尾弃置=整句蒸发（urlcleanup `del _tmp[:]` 实形，判官
                # Different bytecode 五指令）。精确窗口判据：expr_reconstructor
                # 模拟窗口装载，栈恰为 DELETE 消费数（DELETE_ATTR→1、
                # DELETE_SUBSCR→2；多余残留⇒非精确窗口维持旧行为 C3）时调
                # _build_delete_stmt(instr, 窗口+[DELETE]) 归约单条 Delete 发
                # 射 pre_stmts 并清空 pre_instrs。语言级依据：条件块内
                # DELETE_* 恒为完整语句终结（del 不可作子表达式），前缀窗口
                # 自最后一次语句终结（STORE_*/POP_TOP flush）后累积，窗口外
                # 无未终结残留。
                _v157_handled = False
                if pre_instrs:
                    _v157_pre = [i for i in pre_instrs
                                 if i.opname not in ('RESUME', 'NOP', 'CACHE',
                                                     'PUSH_NULL', 'EXTENDED_ARG')]
                    if _v157_pre:
                        self.expr_reconstructor.reset()
                        for _v157_i in _v157_pre:
                            self.expr_reconstructor._process_instruction(_v157_i)
                        _v157_stack = [v for v in self.expr_reconstructor.stack
                                       if not (isinstance(v, dict)
                                               and v.get('type') == 'PUSH_NULL')]
                        _v157_need = 1 if instr.opname == 'DELETE_ATTR' else 2
                        if len(_v157_stack) == _v157_need:
                            _v157_del = self._build_delete_stmt(
                                instr, _v157_pre + [instr])
                            if _v157_del:
                                pre_stmts.extend(_v157_del)
                                pre_instrs = []
                                _v157_handled = True
                if _v157_handled:
                    continue
                # 既有 v133-DELSTMT 空窗口路径逐位保留（只增不破）
                if not pre_instrs:
                    _del_stmts = self._build_delete_stmt(instr, [instr])
                    if _del_stmts:
                        pre_stmts.extend(_del_stmts)
                        continue
                    pre_instrs.append(instr)
                    continue
                # 非精确窗口形维持旧行为（默认累积）
                pre_instrs.append(instr)
                continue"""
s = s.replace(old, new, 1)

assert s != orig
assert s.count(MARKER) == 1
io.open(PATH, 'w', encoding='utf-8-sig', newline='').write(s)
print('fix157 applied: %d marker' % s.count(MARKER))

import py_compile
py_compile.compile(PATH, doraise=True)
print('syntax OK')
