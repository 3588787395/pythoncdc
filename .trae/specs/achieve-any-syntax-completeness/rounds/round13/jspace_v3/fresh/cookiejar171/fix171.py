#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r171 修 cookiejar 两族：CJ4 CONTINUE（3 单元）+ CJ1 DOCESC（模块级 1 单元）。

CJ4 [v171-ITER-EXIT]（core/cfg/region_analyzer.py）
--------------------------------------------------
族机制（RECON170 §2 CJ4）：for 体内 `if <判据>: continue`（as_lwp_str、
MozillaCookieJar.save）与 `if <判据>: break`（_normalized_cookie_tuples）
的判据跳转落点被写成循环头/循环出口，`if` 之后的同层语句被吸进臂内，
并在每条臂尾补一条冗余 `continue`。
分析端事实（实测）：
  · as_lwp_str  IfRegion@56  merge=48  = 循环 header（then=[70] 回跳循环头）
  · save         IfRegion@348 merge=326 = 循环 header（then=[362] 回跳循环头）
  · _normalized_cookie_tuples IfRegion@190 merge=564 = 内层循环 for_iter 出口
    （then=[194] JUMP_FORWARD -> 564 = break）
三者的 NCPD 都塌陷到「循环边界」（header / 出口），这正是同层兄弟语句被
臂吞掉的唯一成因。既有 continue-sink 守卫（_identify_conditional_regions，
then 臂回跳循环头 => merge=else_succ）对后两者被 elif 守卫挡住（else_succ
是纯条件块 = elif/后继 if 的条件测试），而 _build_elif_region 在该形态下
会弃权（else 臂在嵌套 if 之后仍有尾随语句，规则③判为非 elif 链），回退
_build_basic_if_region 用的仍是循环边界 merge => 嵌套 + 冗余 continue。
修复谓词（纯结构事实，只在 elif 链构造器弃权后调用一次）：
  merge 是循环边界（continue 臂：merge is 本 if 所在最内层循环的
  header_block；break 臂：merge 不在该循环块集内）且 then 臂无条件离开
  本轮迭代/本循环（块末 JUMP_BACKWARD 落点 = header / JUMP_FORWARD 的
  全部后继在循环块集之外）=> merge = else_succ（if 之后的同层顺序语句
  入口），else 臂清空、块集归 then 臂 + 条件块。else_succ 是退出本循环的
  纯 break 桥时取桥落点（镜像既有 [B133-V3R3]）。
  未命中逐字返回 None（C3）：merge 已是 else_succ、或 merge 落在循环体内
  （真实 else 臂的常规 if/else）、或臂尾为 return/raise/条件跳转时不介入。

CJ1 [v171-DOCESC]（core/cfg/code_generator.py）
-----------------------------------------------
族机制（RECON170 §2 CJ1）：模块级 docstring 原为 raw 三引号（内含 7 处
「反斜杠 + 换行」），产物按普通三引号原样发 => 重编译把该对字符当行连接
吃掉（常量 938->924 字节）。CPython 3.11 把模块 docstring 编成
`LOAD_CONST 0; STORE_NAME __doc__`，常量值参与字节码 => 判官可见
（<module> 355/355 指令、唯一差异是 idx0 的 argval）。
修复：模块体（indent_level == 0）的 docstring 先对既有候选做**语义回读
核验**（ast.literal_eval 结果必须逐字等于原常量）；核验通过逐字返回
（未命中零变化，C3）；失败才按 raw 前缀三引号 -> 反斜杠双写 -> repr 顺序
重建并再次核验。函数/类 docstring 无指令引用，保持既有发射路径不动
（四语料产物逐字节 SAME）。

用法
----
  python -I -X utf8 fix171.py          # 打补丁（幂等）
  python -I -X utf8 fix171.py --check  # 只检查锚点
"""
import os
import py_compile
import sys
import tempfile

REPO = r'F:\Downloads\pythoncdc-main'
RA = os.path.join(REPO, 'core', 'cfg', 'region_analyzer.py')
RG = os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py')
CG = os.path.join(REPO, 'core', 'cfg', 'code_generator.py')

MARKERS = {'region_analyzer.py': ('v171-ITER-EXIT',),
           'region_ast_generator.py': ('v171-ITER-EXIT-b', 'v171-NESTED-ARM'),
           'code_generator.py': ('v171-DOCESC',)}

# ---------------------------------------------------------------- region_analyzer
A1 = '    def _build_basic_if_region(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None, boolop_regions=None, ternary_regions=None, main_inline_boolop_chain=None):'

R1 = '''    def _v171_iter_exit_merge(self, then_succ, else_succ, merge):
        """[v171-ITER-EXIT] 迭代出口臂的 merge 归位（elif 链构造器弃权后的补正）。

        ①算法依据：No More Gotos §3「If 区域归约」（merge = 两臂的同层唯一
        汇合点）+ rules §1.2 原则 2（每块唯一归属）/ 原则 3（嵌套即抽象节点）
        / 原则 4（入口引用语义）。一臂若**无条件离开本轮迭代/本循环**，它
        就不参与本作用域的向前汇合，汇合点只能是对侧臂的入口（if 之后的
        同层顺序语句）。既有 continue-sink 守卫（_identify_conditional_regions：
        then 臂回跳循环头 => merge=else_succ）是同一判据的一半；本方法补上
        它被 elif 守卫挡住、且 _build_elif_region 随后弃权（else 臂在嵌套 if
        之后仍有尾随语句 => 规则③判「非 elif 链」）的形态：回退
        _build_basic_if_region 用的是 NCPD 塌陷到循环边界的 merge，于是 if
        之后的全部同层兄弟语句被吸进臂内、并在臂尾补冗余 continue（实测
        cookiejar 三单元：LWPCookieJar.as_lwp_str@56、MozillaCookieJar.
        save@348、CookieJar._normalized_cookie_tuples@190）。
        ②归约顺序：只在 _build_elif_region 返回 None（确非 elif 链）之后调用
        一次；不回溯修正已归约区域（§1.3 单向数据流）。
        ③唯一归属判定（merge 身份 + 臂末指令，两项都命中才认领）：
          (a) merge 落在循环边界——continue 臂要求 merge 就是本 if 所在
              **最内层循环**的 header_block；break 臂要求 merge 不在该循环
              的块集内（= 循环出口）。merge 落在循环体内（真实 else 臂的
              常规 if/else、`if a: continue / else: X` 之类）一律不认领。
          (b) then 臂无条件离开本轮迭代/本循环——块末 JUMP_BACKWARD
              (_NO_INTERRUPT) 且落点 == header（continue 语义），或块末
              JUMP_FORWARD/JUMP_ABSOLUTE 且**全部后继都在本循环块集之外**
              （break 语义）。return/raise 终态、条件跳转、普通 fall-through
              都不认领（分别交既有 _then_sink / BREAK 角色 / elif 判据）。
        ④嵌套处理：_find_enclosing_loop 取最内层循环（嵌套循环逐层同判，
        归纳得任意深度）；判据只读块末 opcode/argval 与循环 header /
        body_blocks 的块身份，零名字、零绝对偏移阈值、零语句条数。
        ⑤入口引用语义：命中后 merge = else_succ（if 之后的同层顺序语句
        入口），else 臂清空，块集 = 条件块 ∪ then 臂（原则 2）。
        例外（镜像既有 [B133-V3R3]）：else_succ 是退出本循环的纯 break 桥
        （块内除结尾无条件前向跳转外无实质语句，且落点在本循环块集之外）
        时取桥落点——`if a: continue / else: break` 形态。
        ⑥反编译流程：region_analyzer merge 选择 -> IfRegion.merge_block ->
        _collect_branch_blocks 有界收集（臂在 merge 处停止）-> region_ast_
        generator then/else 语句列表 -> code_generator 发射。
        C 条款：[C1] 只读两臂块末指令与本循环 header/body 块身份；[C2] 命中
        才改 merge 与 else 归属；(C3) 未命中逐字返回 None，调用方行为不变。
        """
        if then_succ is None or else_succ is None or merge is None:
            return None
        if merge is else_succ:
            return None
        _loop = self._find_enclosing_loop(then_succ)
        if _loop is None:
            return None
        _hdr = getattr(_loop, 'header_block', None)
        _last = then_succ.get_last_instruction()
        if _last is None or _hdr is None:
            return None
        _is_continue = (_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                        and _last.argval == getattr(_hdr, 'start_offset', None)
                        and merge is _hdr)
        _is_break = False
        if _last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
            _succs = list(getattr(then_succ, 'successors', None) or [])
            _is_break = (bool(_succs)
                         and all(s not in _loop.blocks for s in _succs)
                         and merge not in _loop.blocks)
            if _is_break:
                # 裸 break 臂门：then 臂块内不得有语句性指令（STORE_*/CALL/
                # DELETE_* 等）。带语句的 break 臂（如 tarfile TarFile.next 的
                # `if tarinfo is not None:` 后接 append/else）重算 merge 会把
                # else 极性守卫折叠成无条件语句（`self._loaded = True` 失去
                # `is None` 条件），源形更远；纯 `if c: break` 形态（tarfile
                # _Stream._read 的 `if not buf: break`）不受影响。
                _v171_arm_stmt = frozenset({
                    'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                    'STORE_ATTR', 'STORE_SUBSCR', 'DELETE_NAME', 'DELETE_FAST',
                    'DELETE_GLOBAL', 'DELETE_ATTR', 'DELETE_SUBSCR', 'CALL',
                    'LIST_APPEND', 'SET_ADD', 'MAP_ADD', 'YIELD_VALUE',
                    'RAISE_VARARGS', 'RETURN_VALUE', 'RETURN_CONST'})
                if any(_i.opname in _v171_arm_stmt
                       for _i in then_succ.instructions):
                    _is_break = False
            if _is_break:
                # elif 候选（else_succ 是纯条件块：前向条件跳转 + 2 条件后继）时
                # 不重算 merge——该形态的源码是 `if c: break / elif d: ...`，交
                # 既有 elif 链构造器发射（改成兄弟 `if d:` 与之字节码等价，但文本
                # 更远离源码；实测 r110 pc1/pc2 源为 elif、pc4 源为 if，两者字节码
                # 同形，故只在本形（break 臂 + elif 候选）让位）。
                _es_l = else_succ.get_last_instruction()
                if (len(getattr(else_succ, 'conditional_successors', ())) == 2
                        and _es_l is not None
                        and _es_l.opname in (FORWARD_CONDITIONAL_JUMP_OPS
                                             | SHORT_CIRCUIT_JUMP_OPS)):
                    _is_break = False
        if not (_is_continue or _is_break):
            return None
        _es_last = else_succ.get_last_instruction()
        if (_es_last is not None
                and _es_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE')
                and isinstance(_es_last.argval, int)
                and all(_ei.offset == _es_last.offset
                        or _ei.opname in NOISE_OPS
                        or _ei.opname in ('POP_TOP', 'EXTENDED_ARG')
                        for _ei in else_succ.instructions)):
            _es_tgt = self.cfg.get_block_by_offset(_es_last.argval)
            if _es_tgt is not None and _es_tgt not in _loop.blocks:
                return _es_tgt
        return else_succ

    def _build_basic_if_region(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None, boolop_regions=None, ternary_regions=None, main_inline_boolop_chain=None):'''

A2 = '''            region = self._build_elif_region(block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, boundary_stop=boundary_stop, ternary_regions=ternary_regions, main_inline_boolop_chain=_main_inline_boolop_chain)
            if region is None:
                region = self._build_basic_if_region(block, then_blocks, else_blocks, merge,'''

R2 = '''            region = self._build_elif_region(block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, boundary_stop=boundary_stop, ternary_regions=ternary_regions, main_inline_boolop_chain=_main_inline_boolop_chain)
            if region is None:
                # [v171-ITER-EXIT] elif 链构造器弃权（确非 elif 链）后，若 merge
                # 塌陷到循环边界（循环头/循环出口）且 then 臂无条件离开本轮
                # 迭代/本循环（continue/break），同层兄弟语句已被吸进臂内：
                # 归位 merge=else_succ、清空 else 臂，由循环体顺序流发射 if 之后
                # 的语句（判据与方法 docstring 同源；未命中返回 None = C3）。
                _v171_merge = self._v171_iter_exit_merge(then_succ, else_succ, merge)
                if _v171_merge is not None:
                    merge = _v171_merge
                    else_blocks = []
                region = self._build_basic_if_region(block, then_blocks, else_blocks, merge,'''

# ---------------------------------------------------------------- code_generator
A3 = '    def _generate_expr_stmt(self, node: ASTExpr) -> None:'

R3 = '''    def _v171_doc_literal(self, docstring, expr_code):
        """[v171-DOCESC] 模块级 docstring 字面量的取值保真重建。

        ①算法依据：CPython 3.11 把模块级 docstring 编成 `LOAD_CONST 0;
        STORE_NAME __doc__`——常量值参与字节码（判官逐指令比较的点），必须
        逐字保真；函数/类 docstring 只占 co_consts[0]、没有任何指令引用，
        保持既有发射路径（C3 零触碰）。词法事实：普通三引号字面量只在原文
        不含反斜杠转义时保真；原文含「反斜杠 + 换行」（raw docstring 的续行）
        时，非 raw 字面量把该对字符当行连接吃掉（cookiejar <module> 实测
        938->924 字节、7 处）。
        ②归约方式：先对调用方既有的三元引号候选 expr_code 做**语义回读核验**
        （ast.literal_eval 的结果必须逐字等于原常量）；通过即逐字返回
        expr_code（未命中零变化，C3）。失败才按下列顺序重建并再次核验：
          (a) raw 前缀三引号（r 后接三引号，双引号版 / 单引号版）；
          (b) 反斜杠双写的三引号；
          (c) repr()（永远保真，兜底）。
        ③唯一归属：只改**本语句**的字面量文本（前缀/转义），不改常量表、不
        改其它常量渲染路径（_format_constant / ASTConstant.to_code 原样）。
        ④嵌套处理：调用方以 `self.indent_level == 0` 圈定模块体（函数/类体
        >=1），故只有模块级 docstring 走本路径；嵌套代码对象各自递归生成。
        ⑤入口引用语义：返回文本仍是一条字符串表达式语句，重编译后重新占据
        const[0]，oparg 不变。
        ⑥反编译流程：_generate_expr_stmt -> 本方法 -> _write_line。
        C 条款：[C1] 只读本节点常量与调用方候选文本；[C2] 命中只换前缀/
        转义；[C3] 候选已保真时逐字返回。
        """
        import ast as _ast
        import warnings as _warnings

        def _roundtrip(_lit):
            with _warnings.catch_warnings():
                _warnings.simplefilter('ignore')
                try:
                    return _ast.literal_eval(_lit) == docstring
                except Exception:
                    return False

        if _roundtrip(expr_code):
            return expr_code
        _dq3 = '"' * 3
        _sq3 = "'" * 3
        _cands = []
        if _dq3 not in docstring:
            _cands.append('r' + _dq3 + docstring + _dq3)
        if _sq3 not in docstring:
            _cands.append('r' + _sq3 + docstring + _sq3)
        _esc = docstring.replace('\\\\', '\\\\\\\\')
        if _dq3 not in _esc:
            _cands.append(_dq3 + _esc + _dq3)
        if _sq3 not in _esc:
            _cands.append(_sq3 + _esc + _sq3)
        _cands.append(repr(docstring))
        for _cand in _cands:
            if _roundtrip(_cand):
                return _cand
        return expr_code

    def _generate_expr_stmt(self, node: ASTExpr) -> None:'''

A4 = '''            if '"' in docstring and "'" in docstring:
                # 同时包含单双引号，使用三引号并转义双引号
                escaped = docstring.replace('\"\"\"', '\\"\\"\\"')
                expr_code = f'\"\"\"{escaped}\"\"\"'
            elif '\"\"\"' in docstring:
                # 包含三引号，使用单引号
                expr_code = f"'{docstring}'"
            else:
                # 普通情况，使用三引号
                expr_code = f'\"\"\"{docstring}\"\"\"'
            self._write_line(expr_code)'''

R4 = '''            if '"' in docstring and "'" in docstring:
                # 同时包含单双引号，使用三引号并转义双引号
                escaped = docstring.replace('\"\"\"', '\\"\\"\\"')
                expr_code = f'\"\"\"{escaped}\"\"\"'
            elif '\"\"\"' in docstring:
                # 包含三引号，使用单引号
                expr_code = f"'{docstring}'"
            else:
                # 普通情况，使用三引号
                expr_code = f'\"\"\"{docstring}\"\"\"'
            # [v171-DOCESC] 模块体（indent_level == 0）的 docstring 取值保真：
            # CPython 3.11 的模块 docstring 是 `LOAD_CONST 0; STORE_NAME
            # __doc__`，常量值参与字节码；raw docstring 里的「反斜杠+换行」被
            # 普通三引号当行连接吃掉（cookiejar <module> 实测 938->924 字节）。
            # 按原值重建前缀/转义（判据与方法 docstring 同源）；函数/类
            # docstring 无指令引用，保持既有发射不动（C3：四语料产物逐字节
            # SAME）。
            if self.indent_level == 0:
                expr_code = self._v171_doc_literal(docstring, expr_code)
            self._write_line(expr_code)'''

# ---------------------------------------------------------------- region_ast_generator
# G1: R40-A2「假臂认领」守卫（merge 即循环体尾语句块 + then 臂是裸 continue）
G1A = """                        if (not _ft3_shared_merge
                                and (not _mb_meaningful or _mb_then_escapes)
                                and not self._if_false_path_is_loop_iteration(region)):"""

G1R = """                        # [v171-ITER-EXIT-b] merge 认领守卫：本 if 的 then 臂若是
                        # 「裸 continue」（then 块内除编译噪声与结尾回边外无实质
                        # 语句），且 merge 块本身以「JUMP_BACKWARD -> 当前循环头」
                        # 收尾，则 merge 是循环体里 if 之后的顺序语句块（其回边由
                        # for/while 结构重编译自然再生），不是假臂本体。旧判据
                        # `_mb_then_escapes` 只看「then 臂尾全部跳出到循环头」，
                        # 对这种 guard 形态把 merge 认成 else 臂，于是 merge 的语句
                        # 被缩进进 if 体、并多补一条显式 continue（as_lwp_str
                        # `if cookie.is_expired(now): continue` + r.append 实测
                        # +1 JUMP_BACKWARD）。判据全部为结构事实：then 臂块指令集
                        # 白名单 + merge 块末指令 argval == 循环头偏移；未命中
                        # （then 臂带语句，如 `standard[k] = v; continue`）时逐字
                        # 保持旧判据（C3）。
                        _v171_mb_iter_end = False
                        if (_mb_meaningful and _mb_then_escapes
                                and self._current_loop is not None):
                            _v171_hdr = getattr(self._current_loop, 'header_block', None)
                            _v171_mb_l = region.merge_block.get_last_instruction()
                            _v171_then = list(region.then_blocks or [])
                            _v171_bare = bool(_v171_then) and all(
                                all(_v171_i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                                       'EXTENDED_ARG', 'JUMP_BACKWARD',
                                                       'JUMP_BACKWARD_NO_INTERRUPT',
                                                       'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                                    for _v171_i in _v171_b.instructions)
                                for _v171_b in _v171_then)
                            if (_v171_hdr is not None and _v171_mb_l is not None
                                    and _v171_bare
                                    and _v171_mb_l.opname in ('JUMP_BACKWARD',
                                                              'JUMP_BACKWARD_NO_INTERRUPT')
                                    and _v171_mb_l.argval == _v171_hdr.start_offset):
                                _v171_mb_iter_end = True
                        if (not _ft3_shared_merge
                                and (not _mb_meaningful
                                     or (_mb_then_escapes and not _v171_mb_iter_end))
                                and not self._if_false_path_is_loop_iteration(region)):"""

# G2: 发射侧「嵌套区域臂块唯一归属」过滤
G2A = """        stmts: List[Dict[str, Any]] = []
        child_region_blocks = set()
        child_entries = set()
        child_expr_regions = {}
        if region and hasattr(region, 'children'):"""

G2R = """        # [v171-NESTED-ARM] 区域归约算法原则 2（每块唯一归属）：父 IfRegion 的
        # 臂块列表里可能同时包含**嵌套 IfRegion 的臂块**（`_collect_branch_blocks`
        # 从臂入口沿后继收集时，子 if 的 continue/break 臂尾块无前向后继，会被
        # 父臂当作叶子块一并收下）。这些块已由子区域发射过一次，父臂再按顺序
        # 发射一次就会多补一条显式 Continue / 重复语句（as_lwp_str 的
        # `if cookie.discard: continue` 之后多一条 continue 实测）。判据只用同层
        # 结构事实：候选块是「入口 ∈ 本臂块集、且 merge_block 与本区域同一个」
        # 的嵌套 IfRegion 的 then/else 成员。宿主门：仅在循环体（
        # self._current_loop is not None）内生效——重复认领的成因是循环臂尾
        # 的 continue/break 块无前向后继被父臂收下；循环外的 if 链（如 r161c
        # nottail3 的嵌套 if/else）由既有归约逐位处理，未命中时 blocks 逐字
        # 不变（C3）。
        _v171_owned_arm = set()
        _v171_bset = set(blocks) if self._current_loop is not None else set()
        for _v171_r in self.region_analyzer.regions:
            if not isinstance(_v171_r, IfRegion) or _v171_r is region:
                continue
            if _v171_r.entry is None or _v171_r.entry not in _v171_bset:
                continue
            _v171_mb = getattr(_v171_r, 'merge_block', None)
            _v171_pmb = getattr(region, 'merge_block', None)
            if _v171_mb is not _v171_pmb:
                if not (_v171_mb is not None and _v171_pmb is not None
                        and _v171_mb.start_offset == _v171_pmb.start_offset):
                    continue
            _v171_owned_arm.update(_v171_r.then_blocks or ())
            _v171_owned_arm.update(_v171_r.else_blocks or ())
        if _v171_owned_arm:
            blocks = [b for b in blocks if b not in _v171_owned_arm]
        stmts: List[Dict[str, Any]] = []
        child_region_blocks = set()
        child_entries = set()
        child_expr_regions = {}
        if region and hasattr(region, 'children'):"""

FILES = (
    (RA, ((A1, R1), (A2, R2))),
    (RG, ((G1A, G1R), (G2A, G2R))),
    (CG, ((A3, R3), (A4, R4))),
)


def patch_one(path, anchors, only_check):
    raw = open(path, 'rb').read()
    has_bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig' if has_bom else 'utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    norm = text.replace('\r\n', '\n')
    name = os.path.basename(path)
    marks = MARKERS[name]

    if all(m in norm for m in marks):
        print('[fix171] %-20s already applied (markers present)' % name)
        return 0
    if any(m in norm for m in marks):
        print('[fix171] %-20s FAILED: partial application' % name)
        return 6
    for a, _r in anchors:
        n = norm.count(a)
        if n != 1:
            print('[fix171] %-20s FAILED: anchor count=%d (expected 1): %r'
                  % (name, n, a.strip().splitlines()[0][:70]))
            return 2
    if only_check:
        print('[fix171] %-20s check ok (%d anchors, count=1)' % (name, len(anchors)))
        return 0

    new_norm = norm
    for a, r in anchors:
        new_norm = new_norm.replace(a, r)
    out = new_norm.replace('\n', nl).encode('utf-8')
    if has_bom:
        out = b'\xef\xbb\xbf' + out
    expect = raw
    for a, r in anchors:
        expect = expect.replace(a.replace('\n', nl).encode('utf-8'),
                                r.replace('\n', nl).encode('utf-8'))
    if out != expect:
        print('[fix171] %-20s FAILED: byte-level round-trip mismatch' % name)
        return 3
    inserted = sum(r.count('\n') - a.count('\n') for a, r in anchors)
    if out.count(nl.encode()) != raw.count(nl.encode()) + inserted:
        print('[fix171] %-20s FAILED: line-count accounting mismatch' % name)
        return 4

    tmpdir = tempfile.mkdtemp(prefix='fix171_')
    tmp_py = os.path.join(tmpdir, 'patched.py')
    with open(tmp_py, 'wb') as f:
        f.write(out)
    try:
        py_compile.compile(tmp_py, cfile=tmp_py + 'c', doraise=True, optimize=0)
    except py_compile.PyCompileError as exc:
        print('[fix171] %-20s FAILED: patched source does not compile: %s' % (name, exc))
        return 5

    with open(path, 'wb') as f:
        f.write(out)
    print('[fix171] %-20s applied: %d anchors, +%d lines, %+d bytes'
          % (name, len(anchors), inserted, len(out) - len(raw)))
    return 0


def main():
    only_check = '--check' in sys.argv
    for path, anchors in FILES:
        part = patch_one(path, anchors, only_check)
        if part:
            return part
    return 0


if __name__ == '__main__':
    sys.exit(main())
