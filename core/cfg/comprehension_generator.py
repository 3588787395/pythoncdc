from typing import List, Dict, Any, Optional, Tuple, Union

from .basic_block import Instruction
from .region_analyzer import (
    CONDITIONAL_JUMP_OPS,
)

# [Round6-B30] async 挂起轮询协议操作码全集（CPython 3.11）：
# GET_ANEXT/GET_AWAITABLE 取得挂起协程后以 LOAD_CONST None + SEND 启动，
# YIELD_VALUE 交出控制权、RESUME 恢复、JUMP_BACKWARD_NO_INTERRUPT 回环
# 轮询；CLEANUP_THROW/END_ASYNC_FOR 为协议尾（3.12+ 替代形态 / 迭代耗尽
# 清理），CACHE/EXTENDED_ARG/NOP 为填充噪声。本集合是推导式子句头识别
# （_find_async_clause_heads 协议尾）与语句级 async for/await 轮询块识别
# （region_ast_generator 挂起协议块消费）的唯一事实源。
ASYNC_POLL_PROTOCOL_OPS = frozenset({
    'SEND', 'YIELD_VALUE', 'RESUME', 'JUMP_BACKWARD_NO_INTERRUPT',
    'CLEANUP_THROW', 'END_ASYNC_FOR', 'CACHE', 'EXTENDED_ARG', 'NOP',
})


def is_async_poll_protocol_block(instrs: List[Instruction]) -> bool:
    """[Round6-B30] 判定指令序列是否构成 async 挂起轮询协议块。

    [识别条件] 序列非空，去噪后全部操作码 ∈ ASYNC_POLL_PROTOCOL_OPS，
    且含 SEND（挂起启动）与 JUMP_BACKWARD_NO_INTERRUPT（轮询回环，其
    argval 落在本序列指令偏移内 = 自循环）。用户 await 的恢复点块
    （STORE/CALL 等用户指令）不满足全成员判定，天然排除。
    [归约方式] 纯操作码形态判定：只读指令操作码与跳转 argval 同块性，
    不读常量值/用户名，无偏移魔数；协议块整体消费、不重组内部。
    [AST 映射] 无独立映射；消费方将该块标记已生成且不产出任何语句
    （挂起协议不是用户源码）。
    [C1] 仅读本序列操作码/偏移（同层结构事实）；[C2] 判定失败即返回
    False，调用方维持原路径；[C3] 无状态、无副作用。
    """
    if not instrs:
        return False
    if not all(i.opname in ASYNC_POLL_PROTOCOL_OPS for i in instrs):
        return False
    if not any(i.opname == 'SEND' for i in instrs):
        return False
    _offsets = {i.offset for i in instrs}
    return any(i.opname == 'JUMP_BACKWARD_NO_INTERRUPT' and i.argval in _offsets
               for i in instrs)


def _and_operand_raw_text(cond: Dict[str, Any]) -> Optional[str]:
    """把 and 链断行处的操作数渲染成「带续行换行」的原始文本。

    [识别条件] 推导式过滤条件里，某操作数的条件跳转是 POP_JUMP_FORWARD_IF_FALSE
      （目标是循环体末尾那条 JUMP_BACKWARD 的偏移，而不是循环头），而其后的
      操作数仍是 POP_JUMP_BACKWARD_IF_FALSE（目标是循环头）：CPython 3.11 按
      BoolOp 各操作数所处的源码物理行选择跳转方向——操作数 i 与其后所有操作数
      同处一行时回跳循环头，一旦之后存在行界则前跳循环体末尾。因此「前向」
      就是原源码在该操作数之后换过行的指令侧证据。
    [归约方式] 用与发射侧完全相同的两个对象（CFGASTConverter._convert_expression
      把 dict 转 ASTNode、CodeGenerator._generate_expression 以 and 的父优先级
      渲染）拿到该操作数的原文，尾部追加换行与续行缩进；转换或渲染抛错一律
      返回 None，由调用方保持单行原状，不做降级、不猜文本。
    [AST 映射] 返回值只作为 Name.id 的内容使用：发射侧对 Name 原样输出 id，
      换行因此精确落在 and 两侧操作数之间；外层仍是 BoolOp(and, values)，
      重编译回同一 BoolOp，语义与单行版逐字节等价，只有行界不同。
    """
    try:
        from .code_generator import CodeGenerator
        from .ast_converter import CFGASTConverter
        node = CFGASTConverter(verbose=False)._convert_expression(cond)
        if node is None:
            return None
        gen = CodeGenerator()
        text = gen._generate_expression(node, gen._precedence['and'])
    except Exception:
        return None
    if not text:
        return None
    # 续行缩进 15 空格 + 发射侧操作符前的那个分隔空格 = 成行后 16 列。
    return text + '\n' + ' ' * 15


def parse_comprehension_code_object(code_obj: Any,
                                    iter_expr: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """[Round2-B96] 把推导式 code object（<listcomp>/<dictcomp>/<setcomp>/
    <genexpr>）解析为推导式表达式 dict（ListComp/SetComp/DictComp/
    GeneratorExp），供 dict→AST 转换层（ast_converter）在收到
    ``Call(func=ComprehensionObject(code), args=[iter])`` 泄漏形态时
    恢复推导式节点使用。

    [识别条件] code object 的编译器合成名 ∈ {<listcomp>, <dictcomp>,
    <setcomp>, <genexpr>}（与 generate_comprehension_function、
    region_analyzer 侧 _const_code_is_async_comprehension 同一编译器
    合成事实，非用户标识符白名单）；is_async 由内层 code object 的
    GET_AITER/GET_ANEXT/END_ASYNC_FOR 协议指令元数据判定
    （_parse_comprehension_inner_impl 既有判据）。
    [归约方式] 自底向上：对 code object 独立建 CFG（CFGBuilder.build），
    归约顺序 = 内层 clause 先归约（多 for/async 混合 clause 走
    _parse_multi_for_comprehension，单 clause 走单 for 路径），目标/
    元素/filter 全部从内层指令流结构化提取；迭代对象 = 调用方传入的
    iter_expr（推导式调用指令的实参，即外层 iterable 构造表达式）。
    [AST 映射] 返回值是 dict 形式的推导式表达式（'type': 'ListComp'/
    'SetComp'/'DictComp'/'GeneratorExp' + generators[].is_async），
    由调用方经 ast_converter._convert_expression 落到对应 ASTNode。
    [反编译流程] 位于表达式重建管线末端：区域装配层产出
    ComprehensionObject 泄漏 dict → 本函数解析内层 code object →
    ast_converter 生成 AST → code_generator 发射。
    [C1] 只读 code object 自身指令流（内层 CFG）与调用方 iter_expr，
    不读宿主块/区域信息；[C2] 内层推导式整体黑箱解析，宿主只见
    返回的表达式 dict；[C3] 解析失败返回 None，调用方保持原路径
    （不静默降级为占位表达式）。
    """
    from .ast_generator_v2 import ExpressionReconstructor
    er = ExpressionReconstructor(None)
    cg = ComprehensionGenerator(er)
    return cg.parse_comprehension_inner(code_obj, iter_expr)


class ComprehensionGenerator:
    def __init__(self, expr_reconstructor):
        self.expr_reconstructor = expr_reconstructor

    # [B96] async 推导式 code object co_flags 位（inspect.CO_COROUTINE=0x80 /
    # CO_ASYNC_GENERATOR=0x200，Python 3.11 实测：await 内嵌或 async for 的
    # <listcomp>/<setcomp>/<dictcomp> 恒置 0x80；含 await 的 <genexpr> 恒置
    # 0x200）。code object 元数据 = I.4 白名单判据（任务 B96 判据方向）。
    _B96_ASYNC_COMP_FLAG_MASK = 0x80 | 0x200

    def convert_comprehension_objects(self, expr: Dict[str, Any],
                                      cond_block) -> Dict[str, Any]:
        if not expr or not isinstance(expr, dict):
            return expr

        if expr.get('type') == 'ComprehensionObject':
            comp_code = expr.get('code')
            if comp_code:
                iter_expr = self.extract_comp_iter_expr(cond_block)
                comp_ast = self.parse_comprehension_inner(comp_code, iter_expr)
                if comp_ast:
                    # [B96] async 标注由 _build_comp_result 单点完成
                    #（co_flags 元数据判据，见该方法注释）。
                    return comp_ast

        for key in ('value', 'func', 'left', 'right', 'comparators', 'args', 'elt'):
            val = expr.get(key)
            if val is None:
                continue
            if isinstance(val, dict):
                converted = self.convert_comprehension_objects(val, cond_block)
                if converted is not None and converted is not val:
                    expr[key] = converted
            elif isinstance(val, list):
                new_list = []
                changed = False
                for item in val:
                    if isinstance(item, dict):
                        converted_item = self.convert_comprehension_objects(item, cond_block)
                        new_list.append(converted_item if converted_item else item)
                        if converted_item is not None and converted_item is not item:
                            changed = True
                    else:
                        new_list.append(item)
                if changed:
                    expr[key] = new_list

        return expr

    def extract_comp_iter_expr(self, cond_block) -> Dict[str, Any]:
        instrs = cond_block.instructions
        for idx, instr in enumerate(instrs):
            if instr.opname == 'GET_ITER':
                if idx > 0:
                    prev_instr = instrs[idx - 1]
                    if prev_instr.opname in ('LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_NAME',
                                             'LOAD_DEREF', 'LOAD_ATTR'):
                        var_name = getattr(prev_instr, 'argval', None)
                        if var_name:
                            return {'type': 'Name', 'id': var_name, 'ctx': 'Load'}
        return {'type': 'Name', 'id': '<iterator>', 'ctx': 'Load'}

    def try_generate_comprehension_assign(self, block, region_ast_gen=None) -> Optional[List[Dict[str, Any]]]:
        SKIP_OPS = frozenset({'RESUME', 'NOP', 'CACHE', 'PUSH_NULL'})
        instrs = [i for i in block.instructions if i.opname not in SKIP_OPS]

        comp_indices = []
        for idx, instr in enumerate(instrs):
            if instr.opname == 'MAKE_FUNCTION':
                if idx > 0 and instrs[idx - 1].opname == 'LOAD_CONST':
                    code_val = instrs[idx - 1].argval
                    if hasattr(code_val, 'co_name') and code_val.co_name in (
                            '<listcomp>', '<dictcomp>', '<setcomp>', '<genexpr>'):
                        comp_indices.append((idx, code_val, instr.arg))

        if not comp_indices:
            return None

        # async comprehension 的 await 模板 (GET_AWAITABLE + SEND +
        # YIELD_VALUE + RESUME + JUMP_BACKWARD_NO_INTERRUPT + STORE_*) 跨多个
        # 基本块。先把后续 fallthrough 块的指令合并进来，并把它们标记为已生成，
        # 避免被外层 _generate_block_statements 当作独立语句重复处理。
        _has_async_comp = False
        for _ci, _cc, _ in comp_indices:
            for _idx in range(_ci + 1, len(instrs)):
                if instrs[_idx].opname == 'GET_AITER':
                    _has_async_comp = True
                    break
        _extra_async_blocks = []
        if _has_async_comp and region_ast_gen is not None:
            _cur = block
            _seen = {block.start_offset}
            # 最多延伸 4 个 fallthrough 块（足够覆盖 SEND/YIELD/RESUME/JUMP_BACK
            # + STORE_* + trailing return）
            for _ in range(4):
                _succs = [s for s in _cur.successors
                          if s.start_offset not in _seen
                          and s.start_offset > _cur.start_offset]
                if len(_succs) != 1:
                    break
                _nb = _succs[0]
                _seen.add(_nb.start_offset)
                _extra_async_blocks.append(_nb)
                _cur = _nb
        if _extra_async_blocks:
            for _eb in _extra_async_blocks:
                for _i in _eb.instructions:
                    if _i.opname not in SKIP_OPS:
                        instrs.append(_i)

        _chained_pairs = []
        if len(comp_indices) >= 2:
            for _cci in range(len(comp_indices) - 1):
                _ci1, _cc1, _cf1 = comp_indices[_cci]
                _ci2, _cc2, _cf2 = comp_indices[_cci + 1]
                # 识别条件（一个 region 只归约成一种 AST 节点，判据必须是结构性的）：
                # 相邻两个 MAKE_FUNCTION 对究竟该不该焊接，取决于「第二个 code 对象是不
                # 是前一个推导式的 iterable 的一部分」，而这一点在字节码上是可判定的——
                # 推导式的**可调用对象**先装载，其**可迭代对象**随后装载，两者之间不出
                # 现该推导式自己的调用闭合。于是扫描 _ci1 之后的第一个 GET_ITER
                # （= 该推导式 iterable 构造链的起点，记为 _first_get_iter）：
                #   真嵌套  内层 code 的 MAKE_FUNCTION 索引 _ci2 < _first_get_iter，
                #           即内层是在外层 iterable 构造**期间**装载的
                #           （LOAD_CONST 外; MAKE_FUNCTION 外; LOAD_CONST 内;
                #            MAKE_FUNCTION 内; LOAD_FAST it; GET_ITER; CALL; ...）；
                #   兄弟    第二个 code 的装载出现在第一个推导式调用链开始之后
                #           （_ci2 > _first_get_iter，实测更在其 CALL 之后），它属于另一
                #           个表达式，绝不能塞进前一个推导式的 iter 槽。
                # 旧实现只从 _ci1+1 找 _first_call_end，再对 instrs[_first_call_end:_ci2]
                # 施加「是否只有闭包装载」弱检验，该检验双向失效：真嵌套时切片为空
                # （all([]) 恒真），兄弟时切片恰含兄弟自己的 LOAD_CONST <code>，被
                # LOAD_CONST+co_name 那个 disjunct 放过。故改为上面的装载次序判据。
                _first_call_end = None
                _first_get_iter = None
                for _fci in range(_ci1 + 1, len(instrs)):
                    if instrs[_fci].opname == 'GET_ITER':
                        _first_get_iter = _fci
                        for _fci2 in range(_fci + 1, min(_fci + 4, len(instrs))):
                            if instrs[_fci2].opname == 'CALL':
                                _first_call_end = _fci2 + 1
                                break
                        break
                if _first_call_end is None or _first_get_iter is None:
                    continue
                if _ci2 >= _first_get_iter:
                    continue
                # 通过装载次序判据后，原「闭包装载」检验恒真（_first_call_end 必然大于
                # _first_get_iter，切片必为空），故删除，不改变可焊接集合的宽度。
                _found_getiter = False
                for _ai in instrs[_first_call_end:]:
                    if _ai.opname == 'GET_ITER':
                        _found_getiter = True
                        break
                    if _ai.opname in ('STORE_FAST', 'STORE_NAME', 'POP_TOP'):
                        break
                if _found_getiter:
                    _has_closure_flag2 = bool(_cf2 & 0x08)
                    _no_closure_flag1 = not bool(_cf1 & 0x08)
                    if _no_closure_flag1 and _has_closure_flag2:
                        continue
                    _chained_pairs.append(_cci)

        all_stmts = []
        prev_end = 0
        _skip_next = False

        for _comp_loop_idx, (comp_idx, comp_code, _) in enumerate(comp_indices):
            if _skip_next:
                _skip_next = False
                continue
            if _comp_loop_idx in _chained_pairs:
                _ci1, _cc1, _ = comp_indices[_comp_loop_idx]
                _ci2, _cc2, _ = comp_indices[_comp_loop_idx + 1]
                _inner_get_iter = None
                for _igi in range(_ci1 + 1, len(instrs)):
                    if instrs[_igi].opname == 'GET_ITER':
                        _inner_get_iter = _igi
                        break
                _inner_iter_instrs_raw = instrs[_ci1 + 1:_inner_get_iter] if _inner_get_iter else []
                _cso = frozenset({'MAKE_CELL', 'LOAD_CLOSURE', 'COPY_FREE_VARS'})
                _real_iter_instrs = []
                _in_cl = False
                for _iii in _inner_iter_instrs_raw:
                    if _iii.opname in _cso:
                        _in_cl = True
                        continue
                    if _iii.opname == 'BUILD_TUPLE' and _in_cl:
                        _in_cl = False
                        continue
                    _in_cl = False
                    if _iii.opname == 'LOAD_CONST' and hasattr(_iii.argval, 'co_name'):
                        continue
                    _real_iter_instrs.append(_iii)
                _inner_iter_expr = self.expr_reconstructor.reconstruct(_real_iter_instrs) if _real_iter_instrs else {'type': 'Name', 'id': '<iterator>'}
                _inner_comp_ast = self.parse_comprehension_inner(_cc1, _inner_iter_expr)
                _outer_get_iter = None
                for _ogi in range(_ci2 + 1, len(instrs)):
                    if instrs[_ogi].opname == 'GET_ITER':
                        _outer_get_iter = _ogi
                        break
                if _inner_comp_ast is not None and _outer_get_iter is not None:
                    _outer_comp_ast = self.parse_comprehension_inner(_cc2, _inner_comp_ast)
                    if _outer_comp_ast is not None:
                        _outer_call_end = _outer_get_iter + 1
                        for _oci in range(_outer_get_iter + 1, len(instrs)):
                            if instrs[_oci].opname in ('PRECALL', 'CALL'):
                                _outer_call_end = _oci + 1
                                if instrs[_oci].opname == 'CALL':
                                    break
                        _ow_post = instrs[_outer_call_end:]
                        _ow_meaningful = [i for i in _ow_post if i.opname not in SKIP_OPS]
                        _ow_closure = frozenset({'LOAD_CLOSURE', 'COPY_FREE_VARS', 'MAKE_CELL'})
                        _ow_clean = [i for i in _ow_meaningful if i.opname not in _ow_closure and not (i.opname == 'BUILD_TUPLE' and any(j.opname in _ow_closure for j in _ow_meaningful[:_ow_meaningful.index(i)]))]
                        # 归约方式 / 不变式：焊接只允许认领「推导式自身」的指令。_ow_clean
                        # 里只要还剩任何**消费者** op——容器构建（BUILD_TUPLE/LIST/SET/MAP、
                        # dict 字面量的 BUILD_CONST_KEY_MAP）、推导式累加（MAP_ADD/
                        # LIST_APPEND/SET_ADD）、容器合并（LIST_EXTEND/SET_UPDATE/DICT_UPDATE/
                        # DICT_MERGE）、调用（CALL/CALL_FUNCTION/CALL_METHOD/
                        # CALL_FUNCTION_KW/CALL_FUNCTION_EX）、运算与下标（BINARY_OP/
                        # BINARY_SUBSCR）——本块最外层表达式的**节点类型**就是那个消费者的
                        # 类型（Dict/Call/…），而不是其中一个子推导式的 ListComp 类型；
                        # 此时不得声明自己没翻译的指令（prev_end = len(instrs) 是「全吃了」
                        # 的记账），必须 return None 放弃焊接、把整块交回通用
                        # ExpressionReconstructor：它在 core/cfg/ast_generator_v2.py 的
                        # BUILD_CONST_KEY_MAP 分支（弹键元组 + 弹 count 个值）与 CALL 分支
                        # （推导式 Iter/ComprehensionObject 合并）里本来就能正确合成父节点。
                        # 白名单成员即该不变式的机器可读形式，缺一个成员就漏一类宿主表达式。
                        _expr_build = frozenset({'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_SET', 'BUILD_MAP', 'BUILD_CONST_KEY_MAP', 'BINARY_OP', 'BINARY_SUBSCR', 'MAP_ADD', 'LIST_APPEND', 'SET_ADD', 'LIST_EXTEND', 'SET_UPDATE', 'DICT_UPDATE', 'DICT_MERGE', 'CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX'})
                        if any(i.opname in _expr_build for i in _ow_clean):
                            return None
                        _store_instr = None
                        for _si in _ow_post:
                            if _si.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF', 'STORE_SUBSCR', 'STORE_ATTR'):
                                _store_instr = _si
                                break
                        if _store_instr:
                            if _store_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                                all_stmts.append({'type': 'Assign', 'targets': [{'type': 'Name', 'id': _store_instr.argval, 'ctx': 'Store'}], 'value': _outer_comp_ast})
                            prev_end = instrs.index(_store_instr) + 1
                        else:
                            _last_i = instrs[-1]
                            if _last_i.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                all_stmts.append({'type': 'Return', 'value': _outer_comp_ast})
                            else:
                                all_stmts.append({'type': 'Expr', 'value': _outer_comp_ast})
                            prev_end = len(instrs)
                    else:
                        prev_end = len(instrs)
                else:
                    prev_end = len(instrs)
                _skip_next = True
                continue
            pre_comp_instrs = instrs[prev_end:comp_idx - 1]
            _closure_setup_ops = frozenset({'MAKE_CELL', 'LOAD_CLOSURE', 'COPY_FREE_VARS'})
            # [Round5-B23] 闭包装载序列的识别改为「局部状态机」：closure 系 op
            # （LOAD_CLOSURE/MAKE_CELL/COPY_FREE_VARS）开启序列，紧随其后的
            # BUILD_TUPLE 闭合该序列（= MAKE_FUNCTION 的闭包元组）。旧实现要求
            # 「BUILD_TUPLE 之前全部指令都是 closure 系」才认领，本块只要混入
            # 任何先导指令（async/生成器函数前导 RETURN_GENERATOR 的伴声
            # POP_TOP、先前语句的残留）即失配，闭包元组的 BUILD_TUPLE 被当作
            # 值生产指令留在 pre_comp 段，随后 L306 终止符守卫（末条非
            # STORE/POP_TOP/IMPORT）把整块判 return None —— 推导式识别被整体
            # 跳过，函数体落入通用重建坍缩为 `await <iterable>()`（r5_10
            # a_async_multi/a_await_body 的 MAKE_FUNCTION 8 闭包形态）。
            # 识别条件：closure 系 op 与 BUILD_TUPLE 的紧邻相邻性（同层结构
            # 事实）；用户数据的 BUILD_TUPLE 前驱是 LOAD_*/CALL 等，不会被误认。
            # [C1] 只读本块指令流；[C3] 终止符守卫保持原判据宽度，仅消除
            # 闭包元组的误报。
            _filtered = []
            _in_closure_seq = False
            for _pi in pre_comp_instrs:
                if _pi.opname in _closure_setup_ops:
                    _in_closure_seq = True
                    continue
                if _pi.opname == 'BUILD_TUPLE' and _in_closure_seq:
                    _in_closure_seq = False
                    continue
                _in_closure_seq = False
                _filtered.append(_pi)
            pre_comp_instrs = _filtered
            # 区域归约算法原则 3（嵌套即抽象节点）：当 comprehension 是
            # 更大表达式的子节点时（如 `return (sum(items), len(items), [listcomp])`），
            # pre_comp_instrs 会包含未被 STORE/POP_TOP/IMPORT 消费的值生产指令
            # （LOAD_GLOBAL/CALL/BUILD_* 等），这些值留在栈上与 comprehension 一起
            # 被后续 BUILD_TUPLE 消费。此时不应将 comprehension 作为独立语句提取，
            # 应返回 None 让标准 expr_reconstructor.reconstruct 路径处理整个块
            # （正确重建 Return(Tuple([...]))）。判据：pre_comp_instrs 末尾指令不是
            # 语句终止符（STORE/POP_TOP/IMPORT）时，说明栈上仍有未消费值。
            if pre_comp_instrs:
                _pre_last = pre_comp_instrs[-1]
                if _pre_last.opname not in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                                             'STORE_DEREF', 'POP_TOP', 'IMPORT_NAME',
                                             'IMPORT_FROM'):
                    return None
            if pre_comp_instrs:
                pre_stmts = self._generate_pre_comp_stmts(pre_comp_instrs, instrs, prev_end, region_ast_gen=region_ast_gen)
                all_stmts.extend(pre_stmts)

            # async comprehension 外层使用 GET_AITER 而非 GET_ITER。
            # 字节码: MAKE_FUNCTION, LOAD_* iter, GET_AITER, PRECALL, CALL,
            # GET_AWAITABLE, LOAD_CONST None, SEND, YIELD_VALUE, RESUME,
            # JUMP_BACKWARD_NO_INTERRUPT, STORE_* result
            get_iter_idx = None
            _async_iter = False
            for idx in range(comp_idx + 1, len(instrs)):
                if instrs[idx].opname in ('GET_ITER', 'GET_AITER'):
                    get_iter_idx = idx
                    _async_iter = (instrs[idx].opname == 'GET_AITER')
                    break

            if get_iter_idx is None:
                continue

            iter_instrs = instrs[comp_idx + 1:get_iter_idx]
            iter_expr = self.expr_reconstructor.reconstruct(iter_instrs)
            if iter_expr is None:
                iter_expr = {'type': 'Name', 'id': '<iterator>'}

            # [R35] Fix: is_method_form causes false Call wrapping in comprehensions.
            # When LOAD_ATTR is followed by GET_ITER (not CALL), the attribute is
            # being iterated, not called. The is_method_form flag is a compiler
            # optimization hint (arg & 1), not a definitive indicator of a method
            # call. Strip it from the iter expression to prevent downstream code
            # (ast_generator_v2.py lines ~24022) from wrapping Attribute in Call.
            if isinstance(iter_expr, dict) and iter_expr.get('type') == 'Attribute':
                iter_expr.pop('is_method_form', None)

            comp_ast = self.parse_comprehension_inner(comp_code, iter_expr)
            if comp_ast is None:
                continue

            gen_call_end = get_iter_idx + 1
            for idx in range(get_iter_idx + 1, len(instrs)):
                if instrs[idx].opname in ('PRECALL', 'CALL'):
                    gen_call_end = idx + 1
                    if instrs[idx].opname == 'CALL':
                        break

            # async comprehension 在 CALL 后有一段 await 循环
            # (GET_AWAITABLE + LOAD_CONST None + SEND + YIELD_VALUE + RESUME +
            # JUMP_BACKWARD_NO_INTERRUPT)。这段是 CPython 自动生成的 await
            # 模板，重建时归约到 await 表达式语句的语义内（listcomp 已含 is_async），
            # 不产生独立语句，但要跳过这些指令避免误归约。
            if _async_iter:
                _async_end = gen_call_end
                _send_idx = None
                for idx in range(gen_call_end, min(gen_call_end + 8, len(instrs))):
                    if instrs[idx].opname == 'SEND':
                        _send_idx = idx
                        break
                if _send_idx is not None:
                    # SEND 后是 YIELD_VALUE, RESUME, JUMP_BACKWARD_NO_INTERRUPT
                    for idx in range(_send_idx + 1, min(_send_idx + 5, len(instrs))):
                        if instrs[idx].opname == 'JUMP_BACKWARD_NO_INTERRUPT':
                            _async_end = idx + 1
                            break
                        if instrs[idx].opname in ('STORE_FAST', 'STORE_NAME',
                                                   'STORE_GLOBAL', 'STORE_DEREF'):
                            _async_end = idx
                            break
                    gen_call_end = _async_end

            wrapper_call = None
            wrapper_end = gen_call_end
            if gen_call_end < len(instrs):
                post_instrs = instrs[gen_call_end:]
                is_wrapper = False
                if len(post_instrs) >= 2:
                    maybe_precall = post_instrs[0]
                    maybe_call = post_instrs[1]
                    if (maybe_precall.opname == 'PRECALL' and
                        maybe_call.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD')):
                        is_wrapper = True
                if not is_wrapper and len(post_instrs) >= 1:
                    if post_instrs[0].opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD'):
                        is_wrapper = True
                if is_wrapper:
                    func_name = None
                    is_method_call = False
                    for back in range(comp_idx - 1, -1, -1):
                        if instrs[back].opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                            func_name = instrs[back].argval
                            break
                        if instrs[back].opname == 'LOAD_METHOD':
                            func_name = instrs[back].argval
                            is_method_call = True
                            break
                    if func_name is not None:
                        if is_method_call:
                            obj_name = None
                            for back2 in range(back - 1, -1, -1):
                                if instrs[back2].opname in ('LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_NAME', 'LOAD_DEREF'):
                                    obj_name = instrs[back2].argval
                                    break
                            if obj_name:
                                wrapper_call = {
                                    'type': 'Call',
                                    'func': {
                                        'type': 'Attribute',
                                        'value': {'type': 'Name', 'id': obj_name, 'ctx': 'Load'},
                                        'attr': func_name,
                                        'ctx': 'Load',
                                    },
                                    'args': [comp_ast],
                                    'kwargs': [],
                                }
                            else:
                                wrapper_call = {
                                    'type': 'Call',
                                    'func': {'type': 'Name', 'id': func_name, 'ctx': 'Load'},
                                    'args': [comp_ast],
                                    'kwargs': [],
                                }
                        else:
                            wrapper_call = {
                                'type': 'Call',
                                'func': {'type': 'Name', 'id': func_name, 'ctx': 'Load'},
                                'args': [comp_ast],
                                'kwargs': [],
                            }
                        for wi in range(gen_call_end, min(gen_call_end + 3, len(instrs))):
                            if instrs[wi].opname in ('PRECALL', 'CALL'):
                                wrapper_end = wi + 1
                                if instrs[wi].opname == 'CALL':
                                    break

            comp_value = wrapper_call if wrapper_call is not None else comp_ast

            # 区域归约算法原则 3（嵌套即抽象节点）：post-wrapper
            # 指令含表达式构建指令（BUILD_TUPLE/BINARY_OP 等）时，comprehension
            # 是更大表达式的子节点（如 `return ([listcomp], max(items))` 中
            # listcomp 被后续 BUILD_TUPLE 2 消费）。返回 None 让标准
            # expr_reconstructor.reconstruct 路径处理整个块。
            if wrapper_end < len(instrs):
                _post_wrapper = instrs[wrapper_end:]
                _closure_setup = frozenset({'MAKE_CELL', 'LOAD_CLOSURE', 'COPY_FREE_VARS'})
                _pw_filtered = []
                _in_closure_seq = False
                for _pw in _post_wrapper:
                    if _pw.opname in _closure_setup:
                        _in_closure_seq = True
                        continue
                    if (_pw.opname == 'BUILD_TUPLE' and _in_closure_seq
                            and _pw.arg is not None and _pw.arg <= 2):
                        _in_closure_seq = False
                        continue
                    _in_closure_seq = False
                    _pw_filtered.append(_pw)
                _expr_building_ops = frozenset({
                    'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_SET', 'BUILD_MAP',
                    'BUILD_CONST_KEY_MAP', 'BINARY_OP', 'BINARY_SUBSCR',
                    'BUILD_SLICE', 'FORMAT_VALUE', 'BUILD_STRING',
                })
                if any(i.opname in _expr_building_ops for i in _pw_filtered):
                    return None

            store_instr = None
            for instr in instrs[wrapper_end:]:
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                    'STORE_SUBSCR', 'STORE_ATTR'):
                    store_instr = instr
                    break

            if store_instr:
                store_idx = instrs.index(store_instr)
                if store_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    all_stmts.append({
                        'type': 'Assign',
                        'targets': [{'type': 'Name', 'id': store_instr.argval, 'ctx': 'Store'}],
                        'value': comp_value,
                    })
                elif store_instr.opname == 'STORE_SUBSCR':
                    # [R34 fix] 推导式赋值目标是下标（`d[k] = [listcomp]` 编译为
                    # <listcomp> + LOAD cont + LOAD key + STORE_SUBSCR）。旧实现只
                    # 认 STORE_FAST 系列，下标目标被跳过 → 退化为裸 Expr(listcomp)
                    # 且 STORE_SUBSCR 丢失（graph._process_task_queue 的 else 子句
                    # node_dict[node] = [...listcomp...]）。重建 Subscript 目标：
                    # 目标窗口 = wrapper_end..store_idx 的 [容器, 键] LOAD 指令。
                    _tgt_instrs = instrs[wrapper_end:store_idx]
                    _tgt_cont = None
                    _tgt_key = None
                    if len(_tgt_instrs) >= 2:
                        _tgt_cont = self.expr_reconstructor.reconstruct([_tgt_instrs[-2]])
                        _tgt_key = self.expr_reconstructor.reconstruct([_tgt_instrs[-1]])
                    if _tgt_cont is not None and _tgt_key is not None:
                        all_stmts.append({
                            'type': 'Assign',
                            'targets': [{
                                'type': 'Subscript',
                                'value': _tgt_cont,
                                'slice': _tgt_key,
                                'ctx': 'Store',
                            }],
                            'value': comp_value,
                        })
                elif store_instr.opname == 'STORE_ATTR':
                    # [R34 fix] 推导式赋值目标是属性（`self.items = [listcomp]`
                    # 编译为 <listcomp> + LOAD obj + STORE_ATTR items）。
                    _tgt_instrs = instrs[wrapper_end:store_idx]
                    _tgt_obj = None
                    if _tgt_instrs:
                        _tgt_obj = self.expr_reconstructor.reconstruct([_tgt_instrs[-1]])
                    if _tgt_obj is not None:
                        all_stmts.append({
                            'type': 'Assign',
                            'targets': [{
                                'type': 'Attribute',
                                'value': _tgt_obj,
                                'attr': store_instr.argval,
                                'ctx': 'Store',
                            }],
                            'value': comp_value,
                        })
                prev_end = store_idx + 1
            else:
                # [Round 9 fix] 先判「推导式值被丢弃」：wrapper 之后若出现
                # POP_TOP，说明推导式是语句级表达式（值随即丢弃），块末的
                # LOAD_CONST None + RETURN_VALUE 才是该 return 的真实值（None）。
                # 旧实现只看块末指令是否为 RETURN_VALUE 就认定「推导式就是返回
                # 值」，于是
                #   if ev in self.h:
                #       [handler(ev) for handler in self.h[ev]]
                #       return
                # 形状的块被反演成 `return [handler(ev) for ...]`（返回列表而非
                # None），并把真正的 return 与后续语句挤出结构之外
                # （event_engine.__process 生成 `return [...]` + 伪造
                # `else: return None` + 死代码重复一条推导式）。
                # 依区域归约算法原则 3（嵌套即抽象节点）：POP_TOP 是语句终结符，
                # 把 wrapper 段（表达式）与其后的语句段切开，两段各自归约。
                # [Round5-B24] 判据收窄（栈顶来源/前驱形态）：只有 POP_TOP
                # **紧邻** wrapper 段末（instrs[wrapper_end] 即 POP_TOP）时，
                # 它弹出的才是推导式值本身 —— 判「推导式值被丢弃」；POP_TOP
                # 位于其后若干语句之间时，弹出的是那些语句自己的值（如
                # try/finally 清理段的 append(...) 返回值），推导式值仍悬挂
                # 栈上，交由后置 RETURN 语义分支与 [Round5-B24] 后继块判据
                # 归约。旧 any(全窗扫描) 会把「清理语句的 POP_TOP」误读成
                # 「推导式值被丢弃」，是 r5_09 t_try_finally 的 return 剥除
                # 共因之一。R9 原形（推导式; POP_TOP; LOAD_CONST None;
                # RETURN_VALUE 单块）中 POP_TOP 恰紧邻 wrapper 段末，收窄后
                # 仍命中（不关闭 R9）。
                _r9_pop_after_wrapper = (
                    wrapper_end < len(instrs)
                    and instrs[wrapper_end].opname == 'POP_TOP')
                last_instr = instrs[-1]
                if _r9_pop_after_wrapper:
                    all_stmts.append({'type': 'Expr', 'value': comp_value})
                    prev_end = wrapper_end
                elif last_instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    # [识别条件] 本块自身的指令结构事实：store_instr 为空（推导式之后
                    #   无 STORE_* 目标）、last_instr 是本块最后一条 RETURN_VALUE/
                    #   RETURN_CONST、且本块 comp_indices 清单里当前项已是**尾项**
                    #   （其后不再有同块的 MAKE_FUNCTION <listcomp>/<genexpr> 项）——
                    #   此时 comp_value 就是本块 return 的完整值表达式，与同 else 族
                    #   L242-246（_chained_pairs 尾项记账）、L565/L568/L571（_ret_succ
                    #   与兜底分支）的记账完全同型。
                    # [归约方式] 尾项才把记账推进到块末 prev_end = len(instrs)，使
                    #   remaining 段为空、不再落入 _generate_remaining_stmts 对同一块
                    #   的第二次重建；旧实现漏推进记账，前缀为空时 all_stmts 变成
                    #   [Return(comp_value)] + 整块重建的第二条 Return，逐字重复发射
                    #   （broker get_orders/get_trades/get_open_orders 的 <listcomp>
                    #   单元被判 Extra/Different bytecode）。非尾项（嵌套外层在后）
                    #   则保持记账不动，交由下一轮 pre_comp 终止符守卫把整块判回通用
                    #   重建路径，避免把嵌套推导式拆成两条 Return。
                    # [AST 映射] 尾项 ⇒ 单发 ast.Return(ListComp/Call(comp_value))；
                    #   非尾项 ⇒ 本块整体 return None，由 expr_reconstructor 发射
                    #   ast.Return(ListComp(iter=ListComp)) 的嵌套形态。
                    all_stmts.append({'type': 'Return', 'value': comp_value})
                    if _comp_loop_idx == len(comp_indices) - 1:
                        prev_end = len(instrs)
                elif (region_ast_gen is not None and block.successors):
                    _ret_succ = None
                    _last_off = last_instr.offset if hasattr(last_instr, 'offset') else 0
                    _fall_through_off = _last_off + 2
                    for _s in block.successors:
                        if _s.start_offset != _fall_through_off:
                            continue
                        _s_skip = [i for i in _s.instructions if i.opname not in SKIP_OPS]
                        if (len(_s_skip) == 1
                                and _s_skip[0].opname in ('RETURN_VALUE', 'RETURN_CONST')):
                            _ret_succ = _s
                            break
                    # [R12 fix] 宽指令 fall-through 落点修正（merger_storage
                    # .get_merger_date_info：`return {dictcomp}` 的 try 体被
                    # 异常表边界切成两块 —— wrapper CALL 在块末，RETURN_VALUE
                    # 在唯一后继块）。旧判据用 _last_off + 2 计算 fall-through
                    # 落点，对带 CACHE 的宽指令（3.11 的 CALL 宽 10 字节，
                    # 下一块起点 = +10）必然失配 → 推导式被降级为裸 Expr +
                    # 伪造 `return None`（orig=32 decomp=34, true_diffs=22）。
                    # 识别条件：块末指令非跳转（值消费型指令如 CALL，控制流
                    # 直落下一块），在前向 后继 中找平凡 return 块（异常表
                    # 产生的 handler 边以 PUSH_EXC_INFO 开头、含多条指令，
                    # 天然不满足平凡判据，故多后继无歧义）；
                    # 归约方式：该后继即 fall-through 块，过滤噪声后仅含一条
                    # RETURN_VALUE/RETURN_CONST 时，推导式值即 return 值；
                    # AST 映射：Return(comp_value)，后继块标记 generated，
                    # 由 try 体归约吞并（原则 3：嵌套即抽象节点，不重复发射）。
                    if (_ret_succ is None
                            and not last_instr.opname.startswith('JUMP')
                            and not last_instr.opname.startswith('POP_JUMP')):
                        for _s in block.successors:
                            if _s.start_offset <= _last_off:
                                continue
                            _s_skip = [i for i in _s.instructions
                                       if i.opname not in SKIP_OPS]
                            if (len(_s_skip) == 1
                                    and _s_skip[0].opname in ('RETURN_VALUE', 'RETURN_CONST')):
                                _ret_succ = _s
                                break
                    if _ret_succ is not None:
                        all_stmts.append({'type': 'Return', 'value': comp_value})
                        region_ast_gen.generated_blocks.add(_ret_succ)
                        region_ast_gen.generated_offsets.add(_ret_succ.start_offset)
                        prev_end = len(instrs)
                    elif (_comp_loop_idx == len(comp_indices) - 1
                          and not last_instr.opname.startswith('JUMP')
                          and not last_instr.opname.startswith('POP_JUMP')
                          and self._find_returns_pending_value_successor(block) is not None):
                        # [Round5-B24] try/finally 包 `return <推导式>`：本块末条
                        # 指令是推导式值消费型 CALL（值悬挂栈上），其前向正常
                        # 后继块是 finally 清理段的正常路径副本 —— return 值压栈
                        # 穿越清理段、由清理段末尾的 RETURN_VALUE 返回（3.11
                        # 异常表把 try 体在保护区间末尾切块的必然布局）。旧实现
                        # 在此分支无条件降级 Expr 语句，return 被剥除、值被
                        # POP_TOP 丢弃、函数改返回 None（r5_09 t_try_finally）。
                        # 识别条件/归约方式/AST 映射见
                        # _find_returns_pending_value_successor 三要素注记。
                        # 不标记后继块为已生成：它仍由 try 区域装配认领为
                        # finalbody 语句源（原则 3 嵌套即抽象节点）。
                        all_stmts.append({'type': 'Return', 'value': comp_value})
                        prev_end = len(instrs)
                    else:
                        all_stmts.append({'type': 'Expr', 'value': comp_value})
                        prev_end = len(instrs)
                else:
                    all_stmts.append({'type': 'Expr', 'value': comp_value})
                    prev_end = len(instrs)

        remaining_instrs = instrs[prev_end:]
        if remaining_instrs:
            remaining_stmts = self._generate_remaining_stmts(remaining_instrs, region_ast_gen=region_ast_gen)
            all_stmts.extend(remaining_stmts)

        # async comprehension 跨块的 fallthrough 已被合并处理，
        # 标记延伸块为已生成，避免外层 _generate_block_statements 重复处理。
        if _extra_async_blocks and region_ast_gen is not None:
            for _eb in _extra_async_blocks:
                region_ast_gen.generated_blocks.add(_eb)
                region_ast_gen.generated_offsets.add(_eb.start_offset)

        return all_stmts if all_stmts else None

    def _find_returns_pending_value_successor(self, block):
        """[Round5-B24] 识别「返回值穿越清理段」的前向正常后继块（try/finally 包
        `return <推导式>` 的字节码布局特征）。

        [识别条件] 本块末条指令为值消费型指令（推导式值悬挂栈上，控制流直落）
        时，检查其前向正常后继块是否满足：
          (a) 非异常帧头——首条有意义指令 ∈ {PUSH_EXC_INFO, CHECK_EXC_MATCH,
              CHECK_EG_MATCH} 的块是 handler/异常路径边，不是正常出口；
          (b) 块体线性——除末条 RETURN_VALUE 外不含任何跳转指令（清理段
              的用户语句可含调用/属性链，但不回跳不分叉）；
          (c) 栈效应判据——从栈深 0 起对块内指令按 dis.stack_effect 线性
              模拟（未知操作码即放弃）：模拟过程中任何时刻不得下溢（下溢=
              提前消费了悬挂值），且模拟至末条 RETURN_VALUE 前栈深恰为 0，
              即 RETURN 弹出的操作数不是本块产生的值，而是进入本块前悬挂的
              调用方值（推导式返回值）。
        反例甄别（同一判据双向排除）：`LOAD_CONST None; RETURN_VALUE`
        （隐式 return None 块，末条前栈深 1）、`LOAD_FAST x; RETURN_VALUE`
        （返回块内产值）、`cleanup; POP_TOP; LOAD y; RETURN_VALUE`（返回
        块内产值）末条前栈深均非 0，不命中。
        [归约方式] 该后继块即 try/finally 正常路径清理副本（3.11 异常表把
        try 体在其保护区间末尾切块，return 值保持压栈穿越清理段，由清理段
        末尾的 RETURN_VALUE 返回）；推导式值即函数返回值，其消费 RETURN
        位于后继块而非本块，故本块的推导式表达式归约为 Return 而非 Expr。
        [AST 映射] Return(comp_value)；重编译后 return 值再次压栈穿越
        finally 清理段，与原字节码同构（try/finally 与 try/except/finally
        双形同法：异常边后继被 (a) 排除，正常边后继即清理副本）。
        [C1] 只读本块与其直接后继的指令流与栈效应，不读区域标签/行表；
        [C2] 后继块作为清理段整体模拟（黑箱），不窥视其语句归约内部；
        [C3] (a)(b)(c) 三重守卫显式排除 handler 边、分叉清理段与返回块内
        产值三类反例，未命中即放弃（交回 Expr 降级原路径）。
        """
        try:
            import dis as _dis
        except Exception:
            return None
        _noise = ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG', 'PUSH_NULL')
        _frame_heads = {'PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'}
        _jump_prefixes = ('JUMP', 'POP_JUMP')
        # [Round5-B24] 异常帧簿记 op：POP_EXCEPT 弹的是异常帧伪状态（不承载
        # 用户值，except handler 内 `return <值>` 经 SWAP 2 + POP_EXCEPT 把
        # 值留在栈上后剥除帧状态），栈模拟中按 0 处理。SWAP/COPY/RERAISE
        # 同属帧簿记（异常表把 handler 的 comp 块与清理段切成多个块时，
        # 中间块可能只含簿记 op）。
        _frame_bookkeeping = {'POP_EXCEPT', 'COPY', 'SWAP', 'RERAISE'}
        _last_off = None
        for _i in reversed(block.instructions):
            if _i.opname in _noise:
                continue
            _last_off = _i.offset if hasattr(_i, 'offset') else None
            break
        for s in block.successors:
            # [Round5-B24] 异常表会把 handler 的「值就位段」与「清理段」切成
            # 多个块，二者之间可能隔着一个纯簿记块（仅 POP_EXCEPT/COPY/SWAP
            # 等，无用户值操作）。沿前向正常边穿越簿记块（有界 4 跳、逐跳
            # 排除异常帧头后继），对首个含用户操作的块做判据检查。
            _chain_blk = s
            _user_instrs = [i for i in _chain_blk.instructions if i.opname not in _noise]
            _hops = 0
            while (_user_instrs
                   and all(i.opname in _frame_bookkeeping for i in _user_instrs)
                   and _hops < 4):
                _fwd = [t for t in _chain_blk.successors
                        if getattr(t, 'start_offset', 0) > getattr(_chain_blk, 'start_offset', 0)
                        and not [j for j in t.instructions[:1] if j.opname in _frame_heads]]
                if len(_fwd) != 1:
                    _user_instrs = None
                    break
                _chain_blk = _fwd[0]
                _user_instrs = [i for i in _chain_blk.instructions if i.opname not in _noise]
                _hops += 1
            if not _user_instrs:
                continue
            s_instrs = _user_instrs
            # (a) 异常帧头排除
            if s_instrs[0].opname in _frame_heads:
                continue
            # 前向边（正常出口只能向前汇入）
            s_off = getattr(_chain_blk, 'start_offset', None)
            if s_off is None or (_last_off is not None and s_off <= _last_off):
                continue
            if s_instrs[-1].opname != 'RETURN_VALUE':
                continue
            # (b) 线性块：末条 RETURN_VALUE 之前不得有任何跳转
            if any(i.opname.startswith(_jump_prefixes) for i in s_instrs[:-1]):
                continue
            # (c) 栈效应模拟：末条前栈深恰为 0 且全程无下溢
            depth = 0
            underflow = False
            supported = True
            for i in s_instrs[:-1]:
                if i.opname in _frame_bookkeeping:
                    continue
                try:
                    try:
                        eff = _dis.stack_effect(_dis.opmap[i.opname], i.arg if i.arg is not None else 0)
                    except ValueError:
                        # 无操作数指令（POP_TOP/RETURN_VALUE 等）不接受 oparg
                        eff = _dis.stack_effect(_dis.opmap[i.opname])
                except (KeyError, ValueError):
                    supported = False
                    break
                depth += eff
                if depth < 0:
                    underflow = True
                    break
            if not supported or underflow or depth != 0:
                continue
            return _chain_blk
        return None

    def _generate_pre_comp_stmts(self, pre_instrs, all_instrs, start_idx, region_ast_gen=None):
        stmts = []
        current_instrs = []
        _import_pending = False
        _import_module = ''
        _import_pairs = []  # [(imported_name, stored_name), ...]
        _import_is_from = False

        def _flush_import():
            """Build and append Import/ImportFrom node from collected _import_pairs."""
            nonlocal _import_pending, _import_module, _import_pairs, _import_is_from
            if not _import_pending:
                return
            if _import_is_from:
                names_list = []
                for _imp_n, _sto_n in _import_pairs:
                    _alias = _sto_n if _sto_n != _imp_n else None
                    names_list.append({'name': _imp_n, 'asname': _alias})
                stmts.append({'type': 'ImportFrom', 'module': _import_module, 'names': names_list})
            else:
                # Plain import: _import_pairs has (module, stored_name)
                for _imp_n, _sto_n in _import_pairs:
                    # `import os.path` stores `os` (top-level module).
                    # `import os.path as path` stores `os.path` as `path`.
                    # When stored_name == first component of module name,
                    # it's a plain `import module.submodule` (no asname).
                    _top_level = _imp_n.split('.')[0]
                    _alias = _sto_n if _sto_n != _top_level else None
                    stmts.append({'type': 'Import', 'names': [{'name': _imp_n, 'asname': _alias}]})
            _import_pending = False
            _import_module = ''
            _import_pairs = []
            _import_is_from = False

        for instr in pre_instrs:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            if instr.opname == 'POP_TOP':
                # [R32-C 同层判据 · 原则 1 块 = 前导语句 + 尾终止] POP_TOP 是「栈上的值被
                # 丢弃」的语句终止符，不是填充指令 —— 调用方把「pre_comp_instrs 末尾是
                # STORE/POP_TOP/IMPORT」当作语句边界，本扫描器却把同一 op 当噪声滤掉，
                # 两侧必须同层一致。它闭合此前累积的栈上表达式并作为 Expr 语句发射；累积
                # 段为空（该行没有值被丢弃）时与既有行为逐字节相同。
                if current_instrs:
                    _r32c_expr = self.expr_reconstructor.reconstruct(current_instrs)
                    if _r32c_expr:
                        stmts.append({'type': 'Expr', 'value': _r32c_expr})
                current_instrs = []
                continue
            if instr.opname == 'IMPORT_NAME':
                # Flush previous import if any
                _flush_import()
                # IMPORT_NAME 前的 LOAD_CONST (level=0) + LOAD_CONST (fromlist 元组)
                # 是 import 的参数，不是独立语句——直接丢弃。
                current_instrs = []
                _import_pending = True
                _import_module = instr.argval if instr.argval else ''
                _import_pairs = []
                _import_is_from = False
                continue
            if instr.opname == 'IMPORT_FROM':
                _import_is_from = True
                _import_pairs.append((instr.argval if instr.argval else '', instr.argval if instr.argval else ''))
                continue
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                if _import_pending:
                    stored_name = instr.argval
                    if _import_is_from and _import_pairs:
                        # Update last pair's stored_name
                        _imp_n, _ = _import_pairs[-1]
                        _import_pairs[-1] = (_imp_n, stored_name)
                    else:
                        # Plain import: (module, stored_name)
                        _import_pairs.append((_import_module, stored_name))
                    continue
                current_instrs.append(instr)
                if region_ast_gen is not None:
                    store_stmt = region_ast_gen._build_store_statement(current_instrs)
                    if store_stmt:
                        stmts.append(store_stmt)
                else:
                    value_instrs = current_instrs[:-1]
                    store_instr = current_instrs[-1]
                    if value_instrs:
                        value_expr = self.expr_reconstructor.reconstruct(value_instrs)
                        if value_expr:
                            stmts.append({
                                'type': 'Assign',
                                'targets': [{'type': 'Name', 'id': store_instr.argval, 'ctx': 'Store'}],
                                'value': value_expr,
                            })
                current_instrs = []
                continue
        # Non-import instruction: flush any pending import
            _flush_import()
            current_instrs.append(instr)
        # Flush any remaining import
        _flush_import()
        return stmts

    def _generate_remaining_stmts(self, remaining_instrs, region_ast_gen=None):
        # [R33] 推导式后的剩余指令可能包含类定义（LOAD_BUILD_CLASS +
        # MAKE_FUNCTION + CALL + STORE_*）或函数定义（MAKE_FUNCTION +
        # CALL + STORE_*）。直接用 expr_reconstructor.reconstruct + Assign
        # 会将 __build_class__ 调用包装为 Assign(value=Call(__build_class__))
        # 而非 ClassDef。当 region_ast_gen 可用时，委托其 _build_store_statement
        # 进行高级语句识别（ClassDef/FunctionDef/装饰器/walrus 等），
        # 与 _generate_pre_comp_stmts 保持一致。
        stmts = []
        current_instrs = []
        _import_pending = False
        _import_module = ''
        _import_pairs = []
        _import_is_from = False

        def _flush_import():
            nonlocal _import_pending, _import_module, _import_pairs, _import_is_from
            if not _import_pending:
                return
            if _import_is_from:
                names_list = []
                for _imp_n, _sto_n in _import_pairs:
                    _alias = _sto_n if _sto_n != _imp_n else None
                    names_list.append({'name': _imp_n, 'asname': _alias})
                stmts.append({'type': 'ImportFrom', 'module': _import_module, 'names': names_list})
            else:
                for _imp_n, _sto_n in _import_pairs:
                    _top_level = _imp_n.split('.')[0]
                    _alias = _sto_n if _sto_n != _top_level else None
                    stmts.append({'type': 'Import', 'names': [{'name': _imp_n, 'asname': _alias}]})
            _import_pending = False
            _import_module = ''
            _import_pairs = []
            _import_is_from = False

        for instr in remaining_instrs:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            # [R34 fix] POP_TOP 是表达式语句终结符（如 `value_list.append(nodes)`
            # 编译为 <expr_instrs> + POP_TOP）。旧实现直接丢弃 POP_TOP，把
            # current_instrs 与后续语句指令混合，导致尾部语句（含 STORE_SUBSCR
            # 赋值）被整体 reconstruct、退化为裸 Name 表达式（graph._process_task_queue
            # 的 try 块内 append + 2 个下标赋值被吞成 `task_id`）。镜像
            # _build_statements_from_instructions 的边界处理：POP_TOP 时把累积
            # 指令重建为 Expr 语句并清空。
            if instr.opname == 'POP_TOP':
                if current_instrs:
                    value_expr = self.expr_reconstructor.reconstruct(current_instrs)
                    if value_expr is not None:
                        stmts.append({'type': 'Expr', 'value': value_expr})
                    current_instrs = []
                continue
            if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                _flush_import()
                if current_instrs:
                    value_expr = self.expr_reconstructor.reconstruct(current_instrs)
                    if value_expr:
                        stmts.append({'type': 'Return', 'value': value_expr})
                    current_instrs = []
                continue
            if instr.opname == 'IMPORT_NAME':
                _flush_import()
                current_instrs = []
                _import_pending = True
                _import_module = instr.argval if instr.argval else ''
                _import_pairs = []
                _import_is_from = False
                continue
            if instr.opname == 'IMPORT_FROM':
                _import_is_from = True
                _import_pairs.append((instr.argval if instr.argval else '', instr.argval if instr.argval else ''))
                continue
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                if _import_pending:
                    stored_name = instr.argval
                    if _import_is_from and _import_pairs:
                        _imp_n, _ = _import_pairs[-1]
                        _import_pairs[-1] = (_imp_n, stored_name)
                    else:
                        _import_pairs.append((_import_module, stored_name))
                    continue
                current_instrs.append(instr)
                if region_ast_gen is not None:
                    store_stmt = region_ast_gen._build_store_statement(current_instrs)
                    if store_stmt:
                        stmts.append(store_stmt)
                else:
                    value_instrs = current_instrs[:-1]
                    store_instr = current_instrs[-1]
                    if value_instrs:
                        value_expr = self.expr_reconstructor.reconstruct(value_instrs)
                        if value_expr:
                            stmts.append({
                                'type': 'Assign',
                                'targets': [{'type': 'Name', 'id': store_instr.argval, 'ctx': 'Store'}],
                                'value': value_expr,
                            })
                current_instrs = []
                continue
            # [R34 fix] 下标/属性赋值（STORE_SUBSCR/STORE_ATTR）不是 STORE_FAST
            # 系列，旧实现把它们堆积进 current_instrs，与后续指令混合后整体
            # reconstruct 退化为裸表达式。镜像 _build_statements_from_instructions
            # 的 L23180/L23186 处理：委托 _build_subscript_assign/_build_attr_assign
            # 重建 Assign 语句。
            if instr.opname == 'STORE_SUBSCR':
                _flush_import()
                if region_ast_gen is not None:
                    _ss_stmt = region_ast_gen._build_subscript_assign(current_instrs + [instr])
                    if _ss_stmt:
                        stmts.append(_ss_stmt)
                else:
                    _ss_val_instrs = current_instrs[:-2]
                    _ss_cont_instrs = current_instrs[-2:-1]
                    _ss_idx_instrs = current_instrs[-1:]
                    _ss_val = self.expr_reconstructor.reconstruct(_ss_val_instrs) if _ss_val_instrs else None
                    _ss_cont = self.expr_reconstructor.reconstruct(_ss_cont_instrs) if _ss_cont_instrs else None
                    _ss_idx = self.expr_reconstructor.reconstruct(_ss_idx_instrs) if _ss_idx_instrs else None
                    if _ss_val is not None and _ss_cont is not None and _ss_idx is not None:
                        stmts.append({
                            'type': 'Assign',
                            'targets': [{
                                'type': 'Subscript',
                                'value': _ss_cont,
                                'slice': _ss_idx,
                                'ctx': 'Store',
                            }],
                            'value': _ss_val,
                        })
                current_instrs = []
                continue
            if instr.opname == 'STORE_ATTR':
                _flush_import()
                if region_ast_gen is not None:
                    _sa_stmt = region_ast_gen._build_attr_assign(current_instrs + [instr])
                    if _sa_stmt:
                        stmts.append(_sa_stmt)
                current_instrs = []
                continue
            _flush_import()
            current_instrs.append(instr)
        _flush_import()
        if current_instrs:
            value_expr = self.expr_reconstructor.reconstruct(current_instrs)
            if value_expr:
                stmts.append({'type': 'Expr', 'value': value_expr})
        return stmts

    def parse_comprehension_inner(self, code_obj: Any,
                                  iter_expr: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            from .cfg_builder import CFGBuilder
            builder = CFGBuilder()
            nested_cfg = builder.build(code_obj)
        except Exception:
            return None

        _orig_cfg = self.expr_reconstructor.cfg
        self.expr_reconstructor.cfg = nested_cfg
        try:
            return self._parse_comprehension_inner_impl(code_obj, iter_expr, nested_cfg)
        finally:
            self.expr_reconstructor.cfg = _orig_cfg

    def _parse_comprehension_inner_impl(self, code_obj, iter_expr, nested_cfg):

        all_instrs = []
        for b in nested_cfg.get_blocks_in_order():
            all_instrs.extend(b.instructions)
        all_instrs.sort(key=lambda i: i.offset)

        # [Round5-03] 多 for 子句检测：统计 FOR_ITER 数量。
        # 多 for 子句（如 `{x+y for x in a for y in b}`）字节码含多个 FOR_ITER，
        # 每个 FOR_ITER 后接 STORE_* target，最后一个 FOR_ITER 的 body 含 element + APPEND。
        # 单 for 路径保留原逻辑；多 for 走新路径分别提取每个 generator。
        # [Round5-B23] async for 子句（GET_ANEXT 协议块）与同步 FOR_ITER 子句
        # 一并计入 clause 头：clause 头总数 > 1 即多 clause 路径（`async for x
        # in ait for y in b` 的内层只有 1 个 FOR_ITER + 1 个 GET_ANEXT，旧判据
        # 漏判走单 for 路径，异步 clause 目标被同步 FOR_ITER 的名袋/前缀解析
        # 错误认领）。
        for_iter_indices = [i for i, instr in enumerate(all_instrs) if instr.opname == 'FOR_ITER']
        _async_head_indices = self._find_async_clause_heads(all_instrs)
        if len(for_iter_indices) + len(_async_head_indices) > 1:
            return self._parse_multi_for_comprehension(code_obj, all_instrs, iter_expr,
                                                       for_iter_indices, _async_head_indices)

        target_name = self._find_comp_target_names(all_instrs, first_only=True)
        if target_name is None:
            return None

        target = self._build_comprehension_target(all_instrs)
        if target is None:
            return None

        # [B106] 元素产出锚点按推导式种类精化（co_name → 产出 opcode，
        # 见 _find_comp_append_op 的 [B106] 注释；普通形态首=末不变；
        # <genexpr> 产出 YIELD——星实参调用形元素的实参构建 LIST_APPEND
        # 同样先于产出，最末 YIELD = 元素产出，async 轮询 YIELD 恒在前，
        # 与 B96 判据结论一致）。
        _b106_kind = {'<listcomp>': 'LIST_APPEND', '<setcomp>': 'SET_ADD',
                      '<dictcomp>': 'MAP_ADD',
                      '<genexpr>': 'YIELD_VALUE'}.get(getattr(code_obj, 'co_name', ''))
        append_op, append_idx = self._find_comp_append_op(
            all_instrs, append_kind=_b106_kind)
        if append_op is None:
            return None

        _, store_idx = self._find_comp_append_op(all_instrs, target_name)
        if store_idx is None:
            return None

        # 优先尝试 Pattern B：三元作 if-filter。
        # 模式: ``[elt for x in iter if (a if c else b)]``
        # 区分依据: BOTH 真假分支以 BACKWARD 条件跳转（filter skip）结束。
        # 依「父引用子入口」：父推导式通过 merge 块的 elt 指令引用三元
        # 子节点作为 if-filter 条件，元素独立重建。
        #
        # [B256-V3R58] 前置「块划分 + compiler_jump_if 递归下降」整窗通道：
        # 三元（含嵌套/极性翻转/位于 and・or 链成员位）与布尔短路链共存时，
        # 既有 `_detect_comp_ternary_as_filter` 只取三元本体、`_extract_comp_ifs`
        # 只按跳转极性给项，会丢链成员或语义错。该通道只在整窗可完整归属时
        # 认领（[C3] 否则 None，逐位沿用既有通道）。
        _ternary_filter_info = None
        if append_op != 'MAP_ADD':
            _ternary_filter_info = self._b256_filter_boolchain(
                all_instrs, store_idx, append_idx)
        if _ternary_filter_info is None:
            _ternary_filter_info = self._detect_comp_ternary_as_filter(
                all_instrs, store_idx, append_idx)
        if _ternary_filter_info is not None:
            _tf_expr, _tf_elt_start = _ternary_filter_info
            _tf_ifs = [_tf_expr]
            if append_op == 'MAP_ADD':
                _tf_key, _tf_val = self._split_dict_comp_kv(
                    all_instrs, _tf_elt_start, append_idx)
                if _tf_key is None:
                    _tf_key = {'type': 'Name', 'id': target_name, 'ctx': 'Load'}
                if _tf_val is None:
                    _tf_val = {'type': 'Constant', 'value': None}
                _tf_elt = (_tf_key, _tf_val)
            else:
                # [B98-V3R2 修复] 元素窗自身含三元（filter 位三元与 elt 位
                # 三元共存形，如 ``[(a if f1 else b) for x in xs if (a if c
                # else b)]`` 及折叠 orelse 过滤器的 ``[x if flag else 0
                # for x in xs if (x % 2 if flag else True)]``）：先以
                # `_tf_elt_start - 1`（元素窗前一条 = 最后一条 filter 回跳）
                # 为窗起点调用 `_detect_comp_ternary` 折叠元素位三元；返回
                # None 时逐字回落 reconstruct 原路径（[C3] 显式守卫）。
                _tf_elt = None
                if _tf_elt_start > 0:
                    _tf_elt = self._detect_comp_ternary(
                        all_instrs, _tf_elt_start - 1, append_idx)
                if _tf_elt is None:
                    _tf_elt_instrs = all_instrs[_tf_elt_start:append_idx]
                    _tf_elt = self.expr_reconstructor.reconstruct(_tf_elt_instrs)
                if _tf_elt is None:
                    _tf_elt = {'type': 'Name', 'id': target_name, 'ctx': 'Load'}
            _tf_is_async = 0
            for _instr in all_instrs:
                if _instr.opname in ('GET_AITER', 'GET_ANEXT', 'END_ASYNC_FOR'):
                    _tf_is_async = 1
                    break
            _tf_generators = [{
                'type': 'comprehension',
                'target': target,
                'iter': iter_expr,
                'ifs': _tf_ifs,
                'is_async': _tf_is_async,
            }]
            return self._build_comp_result(code_obj, _tf_elt, _tf_generators)

        # 检测三元模式：条件跳转的目标在LIST_APPEND之前
        ternary_info = self._detect_comp_ternary(all_instrs, store_idx, append_idx)
        # [B113] 单 for 路径前导扁平子句（仅非三元分支消费；三元+扁平共存
        # 形态未及，见 FIX_C §4 残余登记）
        _b113_flats = []
        if ternary_info is not None:
            if append_op == 'MAP_ADD':
                # [Round7-08] Dict comprehension with ternary: ternary can be either key
                # or value. Distinguish by checking if there are meaningful instructions
                # between the ternary merge point and MAP_ADD:
                # - If yes → ternary is the KEY, those trailing instructions are the value
                # - If no  → ternary is the VALUE, key (if any) was pushed before the cond
                value_expr = self._extract_dict_comp_value_after_ternary(
                    all_instrs, store_idx, append_idx)
                if value_expr is not None:
                    elt_expr = (ternary_info, value_expr)
                else:
                    key_expr = self._extract_dict_comp_key_before_ternary(
                        all_instrs, store_idx, append_idx)
                    if key_expr is not None:
                        elt_expr = (key_expr, ternary_info)
                    else:
                        elt_expr = ternary_info
            else:
                elt_expr = ternary_info
            # ternary + filter 共存时也提取 filter。
            # _extract_comp_ifs 看到 FORWARD ternary 跳转会 break（不 return），
            # 已收集的 BACKWARD filter segments 会被处理为 ifs。
            ifs, _ = self._extract_comp_ifs(all_instrs, store_idx, append_idx)
        else:
            ifs, elt_start_idx = self._extract_comp_ifs(all_instrs, store_idx, append_idx)
            # [B113] 单 for 路径的元素窗前导扁平子句：唯一真子句之后、元素
            # 表达式之前的 ``<expr>; STORE T`` 内联对（e2/e09_comp_host 形——
            # 源码 ``for a in [X] for b in [Y]`` 的第二子句被内联，全式仅剩
            # 一个 FOR_ITER）。贪心消费为追加 generator（源序在真子句之后）；
            # 不命中时元素窗起点不变（C3）。
            _b113_flats, _b113_flat_end = self._b113_extract_flat_clauses(
                all_instrs, elt_start_idx, append_idx)
            if _b113_flat_end != elt_start_idx:
                elt_start_idx = _b113_flat_end
            if append_op == 'MAP_ADD':
                key_expr, value_expr = self._split_dict_comp_kv(all_instrs, elt_start_idx, append_idx)
                if key_expr is None:
                    key_expr = {'type': 'Name', 'id': target_name, 'ctx': 'Load'}
                if value_expr is None:
                    value_expr = {'type': 'Constant', 'value': None}
                elt_expr = (key_expr, value_expr)
            else:
                elt_instrs = all_instrs[elt_start_idx:append_idx]
                # [B237-V3R40] 元素窗的 keep-or-pop 短路归约：`[x or y ...]` /
                # `[x and y ...]` 的元素位 `A and B`/`A or B` 由
                # JUMP_IF_FALSE_OR_POP/JUMP_IF_TRUE_OR_POP 表达（短路时左值即
                # 结果、否则弹出左值取右值）；不开启该开关时通用重建只返回栈
                # 顶右值，左操作数整段消失（语义错）。开关仅作用于本元素窗。
                elt_expr = self.expr_reconstructor.reconstruct(
                    elt_instrs, fold_boolop_keep_or_pop=True)
                if elt_expr is None:
                    elt_expr = {'type': 'Name', 'id': target_name, 'ctx': 'Load'}

        is_async = 0
        for instr in all_instrs:
            # async comprehension 内层用 GET_ANEXT 而非 FOR_ITER，
            # 外层用 GET_AITER 而非 GET_ITER。任一出现即标记 is_async=1。
            if instr.opname in ('GET_AITER', 'GET_ANEXT', 'END_ASYNC_FOR'):
                is_async = 1
                break

        generators = [{
            'type': 'comprehension',
            'target': target,
            'iter': iter_expr,
            'ifs': ifs,
            'is_async': is_async,
        }]
        # [B113] 前导扁平子句按源序追加在真子句之后（单 for 路径）。
        for _b113_tgt, _b113_expr in _b113_flats:
            generators.append({
                'type': 'comprehension',
                'target': _b113_tgt,
                'iter': _b113_expr,
                'ifs': [],
                'is_async': 0,
            })

        return self._build_comp_result(code_obj, elt_expr, generators)

    def _find_async_clause_heads(self, all_instrs: List[Instruction]) -> List[Tuple[int, int]]:
        """[Round5-B23] 识别推导式 code object 内 async for 子句头（GET_ANEXT 取值协议块）。

        [识别条件] 3.11 async-for 取值协议：GET_ANEXT; LOAD_CONST None; SEND;
        （YIELD_VALUE; RESUME; JUMP_BACKWARD_NO_INTERRUPT 回环），其后第一条
        STORE_*/UNPACK_SEQUENCE/UNPACK_EX 即该 clause 目标存储序列起点
        （协议尾可含 END_ASYNC_FOR/CLEANUP_THROW——3.12+ 以 CLEANUP_THROW
        替代部分协议尾，同法计入）。每 async clause 恰有一个 GET_ANEXT 协议
        块，其回跳边（JUMP_BACKWARD/JUMP_BACKWARD_NO_INTERRUPT 目标 =
        GET_ANEXT 偏移）与过滤跳转（POP_JUMP_BACKWARD_IF_FALSE 目标 =
        GET_ANEXT 偏移）共同构成该 clause 的循环头语义，与同步 clause 的
        FOR_ITER 头同构。
        [归约方式] 线性扫描：GET_ANEXT 后跳过 CACHE/EXTENDED_ARG/NOP 取
        LOAD_CONST(None)+SEND 协议头，再跳过协议尾指令集取第一条目标存储
        序列指令；返回 [(头索引, 目标存储序列起点索引), ...] 按偏移序。
        [AST 映射] 无独立映射；供 _parse_multi_for_comprehension 统一 clause
        装配（该 clause 的 is_async=1、target 自目标序列起点结构化解析）。
        [C1] 仅读本推导式指令流（操作码形态/常量值）；[C2] 协议块整体消费，
        不重组其内部；[C3] 头判据失败即不认领（返回空表，走既有单 for 路径）。
        """
        heads: List[Tuple[int, int]] = []
        n = len(all_instrs)
        _skip = ('CACHE', 'EXTENDED_ARG', 'NOP')
        # [Round6-B30] 协议尾集合由 ASYNC_POLL_PROTOCOL_OPS 派生（去掉头部
        # 启动指令 SEND），与语句级挂起轮询块识别共享同一事实源。
        _tail_ops = ASYNC_POLL_PROTOCOL_OPS - {'SEND'}
        for i, instr in enumerate(all_instrs):
            if instr.opname != 'GET_ANEXT':
                continue
            j = i + 1
            while j < n and all_instrs[j].opname in _skip:
                j += 1
            if j + 1 >= n:
                continue
            if all_instrs[j].opname != 'LOAD_CONST' or all_instrs[j].argval is not None:
                continue
            j += 1
            while j < n and all_instrs[j].opname in _skip:
                j += 1
            if j >= n or all_instrs[j].opname != 'SEND':
                continue
            pos = j + 1
            target_pos = None
            while pos < n:
                op = all_instrs[pos].opname
                if op in _tail_ops:
                    pos += 1
                    continue
                if op in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL',
                          'UNPACK_SEQUENCE', 'UNPACK_EX'):
                    target_pos = pos
                break
            if target_pos is not None:
                heads.append((i, target_pos))
        return heads

    def _parse_multi_for_comprehension(self, code_obj, all_instrs, iter_expr, for_iter_indices,
                                       async_clause_heads=None):
        """[Round5-03] 多 for 子句推导式重建。

        字节码结构（以 `{x+y for x in a for y in b}` 为例）:
            BUILD_SET 0
            LOAD_FAST .0           <- 外部传入的迭代器（对应第一个 for 的 iter）
            FOR_ITER (outer)       <- for_iter_indices[0]
            STORE_FAST x           <- 第一个 for 的 target
            LOAD_GLOBAL b
            GET_ITER
            FOR_ITER (inner)       <- for_iter_indices[1]
            STORE_FAST y           <- 第二个 for 的 target
            <element>
            SET_ADD
            JUMP_BACKWARD to inner FOR_ITER
            JUMP_BACKWARD to outer FOR_ITER

        生成多个 generator，按外→内顺序。第一个 generator 的 iter 是 iter_expr
        （外部传入），后续 generator 的 iter 由 LOAD_* + GET_ITER 重建。
        元素表达式从最内层 FOR_ITER 的 STORE_* 之后、APPEND 之前提取。

        [Round5-B20] 每个 clause 的过滤条件按归属 clause 各自提取：
        [识别条件] clause k 的过滤跳转链全部回跳 clause k 自己的 FOR_ITER
        偏移，且位于该 clause 目标存储序列之后、下一 clause FOR_ITER 之前
        （最内层则位于 APPEND 之前）；[归约方式] 非最内层 clause 以
        [seq_end_k, fi_{k+1}) 为窗复用 _extract_comp_ifs 的段机制（BACKWARD
        回跳段=and 成员、前向 IF_TRUE+回向 IF_FALSE=or 过滤，[R10]/[B6-comp]
        判据沿用），最内层保持原窗 [store, APPEND)，互不重叠（[C3] 守卫）；
        [AST 映射] 过滤表达式依序挂到对应 comprehension.ifs，多过滤按既有
        and/or 合并规则合并。 [C1] 窗口边界只由本指令流的 FOR_ITER 偏移与
        存储序列末端决定，不读父/邻区域信息。

        [Round5-B23] async 子句统一装配：clause 头 = 同步 FOR_ITER ∪ async
        GET_ANEXT 协议块（_find_async_clause_heads），按偏移序合并为同一
        clause 序列。async clause 的目标存储序列位于 GET_ANEXT; LOAD_CONST
        None; SEND; (YIELD_VALUE; RESUME; JUMP_BACKWARD_NO_INTERRUPT) 协议块
        之后（CLEANUP_THROW/END_ASYNC_FOR 兼容计入协议尾），其过滤跳转回跳
        该 GET_ANEXT 偏移、iter 表达式窗锚点为 GET_AITER（同步 clause 锚点
        为 GET_ITER）——两种头的窗口语义完全同构，判据仅按头种类选择锚点
        操作码；is_async 标志沿 clause 归位（async 头 → 1，同步头 → 0），
        不再整推导式统一标记。 [C1] 只读本推导式指令流；[C2] GET_ANEXT/
        SEND 协议块作为取值协议整体消费（等价于同步路径的 FOR_ITER 头）；
        [C3] 头种类只改变锚点操作码选择，过滤窗/存储序列窗互不重叠守卫
        与 B20 相同。
        """
        # [B106] 同款种类精化（多 for 路径）。
        _b106_kind_m = {'<listcomp>': 'LIST_APPEND', '<setcomp>': 'SET_ADD',
                        '<dictcomp>': 'MAP_ADD',
                        '<genexpr>': 'YIELD_VALUE'}.get(getattr(code_obj, 'co_name', ''))
        append_op, append_idx = self._find_comp_append_op(
            all_instrs, append_kind=_b106_kind_m)
        if append_op is None:
            return None

        # [Round5-B23] 统一 clause 头：同步 FOR_ITER ∪ async GET_ANEXT 协议块。
        _async_heads = list(async_clause_heads or [])
        _async_target_pos = {h: tp for h, tp in _async_heads}
        _async_head_set = {h for h, _ in _async_heads}
        heads = sorted(list(for_iter_indices) + [h for h, _ in _async_heads])
        if not heads:
            return None

        generators = []
        _seq_ends = []
        # [Round5-B20] 上一 clause 过滤段之后的窗起点（= 本 clause iter 表达式的
        # 指令窗起点）。每个非最内层 clause 的过滤谓词链挂在该 clause 的
        # FOR_ITER 之后、下一 clause FOR_ITER 之前：clause k 的过滤跳转全部
        # 回跳 clause k 自己的 FOR_ITER 偏移，最后一个过滤跳转之后的指令才是
        # 下一 clause 的可迭代对象求值序列。故 clause k 的 ifs 提取窗取
        # [seq_end_k, fi_{k+1})，_extract_comp_ifs 返回的 elt_start 恰为
        # clause k+1 的 iter 窗起点。 [Round5-B23] 下一 clause 头为 async 时，
        # 锚点偏移取其 GET_ANEXT 偏移（async clause 的过滤跳转回跳该偏移，
        # 语义与 FOR_ITER 锚点同构）。
        _next_iter_start = None
        for gen_idx, head_idx in enumerate(heads):
            _is_async_clause = head_idx in _async_head_set
            if _is_async_clause:
                _target_pos = _async_target_pos[head_idx]
            else:
                _target_pos = head_idx + 1
            # [Round5-B21] target 按存储序列结构解析（支持嵌套元组/星号），
            # 不再要求 FOR_ITER 后恰为单条 STORE_*。
            target, seq_end = self._parse_target_store_sequence(all_instrs, _target_pos)
            if target is None:
                return None
            _seq_ends.append(seq_end)

            # 本 clause 的 iter 窗起点 = 上一 clause 过滤段之后的位置
            # （gen_idx==0 时用外部传入 iter_expr，不读该值）。
            _iter_start = _next_iter_start

            # [Round5-B20] 非最内层 clause 的过滤条件：窗口 [seq_end, 下一
            # 头)。_extract_comp_ifs 的段机制按同层结构事实甄别过滤段
            # （BACKWARD 回跳段）与三元/or 过滤（[R10]/[B6-comp] 判据沿用，
            # append 锚点换成下一 clause 头偏移）；其返回的窗起点
            # 即本 clause 过滤段之后的位置 = 下一 clause 的 iter 窗起点。
            # 最内层 clause 的 ifs 由后置既有逻辑提取（窗口到 APPEND 为止），
            # 此处置空占位，避免同一过滤被双重归属（[C3] 显式守卫）。
            ifs = []
            if gen_idx + 1 < len(heads):
                ifs, _next_iter_start = self._extract_comp_ifs(
                    all_instrs, seq_end - 1, heads[gen_idx + 1])

            if gen_idx == 0:
                # 第一个 for 的 iter 来自外部传入
                gen_iter_expr = iter_expr
            else:
                # 后续 for 的 iter 来自「上一 clause 过滤段之后」到本 clause
                # 迭代协议锚点之间的 LOAD_* + 锚点序列。 [Round5-B20] 窗起点
                # 不再回扫 STORE（有过滤时会把过滤跳转误收进 iter 窗），改用
                # 上一 clause 过滤提取返回的窗起点。 [Round5-B23] async clause
                # 的锚点为 GET_AITER（async-for 在 comp 内对非首个 clause 需要
                # 显式建立 async 迭代器；首个 clause 的迭代器由外层 GET_AITER
                # 建立后传入 .0，故 gen_idx==0 不回扫），同步 clause 锚点仍为
                # GET_ITER。
                anchor_op = 'GET_AITER' if _is_async_clause else 'GET_ITER'
                anchor_idx = None
                for j in range(head_idx - 1, -1, -1):
                    if all_instrs[j].opname == anchor_op:
                        anchor_idx = j
                        break
                    if all_instrs[j].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL'):
                        break
                    if _iter_start is not None and j < _iter_start:
                        break
                if anchor_idx is None or _iter_start is None:
                    return None
                # [B113] iter 窗前导扁平子句：``for T in [<单元素>]`` 内联为
                # ``<expr>; STORE T``，位于上一真子句过滤段之后、本子句
                # GET_ITER 之前。先贪心消费扁平子句（各成独立 generator，
                # 插在本真子句之前），剩余窗口才是本子句 iter 表达式。
                # 不命中（窗首即 GET_ITER 协议）时窗口起点不变（C3）。
                _b113_flats, _b113_flat_end = self._b113_extract_flat_clauses(
                    all_instrs, _iter_start, anchor_idx)
                for _b113_tgt, _b113_expr in _b113_flats:
                    generators.append({
                        'type': 'comprehension',
                        'target': _b113_tgt,
                        'iter': _b113_expr,
                        'ifs': [],
                        'is_async': 0,
                    })
                if _b113_flat_end != _iter_start:
                    _iter_start = _b113_flat_end
                # iter 表达式指令范围：从过滤段之后到锚点之前
                iter_instrs = [i for i in all_instrs[_iter_start:anchor_idx]
                               if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                gen_iter_expr = self.expr_reconstructor.reconstruct(iter_instrs) if iter_instrs else None
                if gen_iter_expr is None:
                    gen_iter_expr = {'type': 'Name', 'id': '<iterator>'}

            generators.append({
                'type': 'comprehension',
                'target': target,
                'iter': gen_iter_expr,
                'ifs': list(ifs),
                'is_async': 1 if _is_async_clause else 0,
            })

        # 最内层 clause 的目标存储序列末端（用于元素提取）。
        # [Round5-B23] 最内层头可为 async 头：目标序列起点由
        # _async_target_pos 给出，seq_end 由统一解析记录。
        innermost_store_idx = _seq_ends[-1] - 1
        # 元素提取：从 innermost_store_idx + 1 到 append_idx
        elt_start_idx = innermost_store_idx + 1

        # 优先尝试 Pattern B：三元作 if-filter。
        # 同 _parse_comprehension_inner 中的 Pattern B 逻辑，但作用域是
        # 最内层 for body。依「父引用子入口」原则同上。
        _ternary_filter_info = self._detect_comp_ternary_as_filter(
            all_instrs, innermost_store_idx, append_idx)
        if _ternary_filter_info is not None:
            _tf_expr, _tf_elt_start = _ternary_filter_info
            generators[-1]['ifs'] = [_tf_expr]
            if append_op == 'MAP_ADD':
                _tf_key, _tf_val = self._split_dict_comp_kv(
                    all_instrs, _tf_elt_start, append_idx)
                if _tf_key is None:
                    _tf_key = {'type': 'Name', 'id': all_instrs[innermost_store_idx].argval, 'ctx': 'Load'}
                if _tf_val is None:
                    _tf_val = {'type': 'Constant', 'value': None}
                elt_expr = (_tf_key, _tf_val)
            else:
                # [B98-V3R2 修复] 同单 for 路径：元素窗自身含三元时先走
                # `_detect_comp_ternary`（窗起点 `_tf_elt_start - 1`），
                # None 时逐字回落 reconstruct 原路径（[C3] 显式守卫）。
                _tf_elt = None
                if _tf_elt_start > 0:
                    _tf_elt = self._detect_comp_ternary(
                        all_instrs, _tf_elt_start - 1, append_idx)
                if _tf_elt is None:
                    _tf_elt_instrs = all_instrs[_tf_elt_start:append_idx]
                    _tf_elt = self.expr_reconstructor.reconstruct(_tf_elt_instrs)
                if _tf_elt is None:
                    _tf_elt = {'type': 'Name', 'id': all_instrs[innermost_store_idx].argval, 'ctx': 'Load'}
                elt_expr = _tf_elt
            return self._build_comp_result(code_obj, elt_expr, generators)

        # 检测三元 / ifs（在最内层 for body 内）
        ternary_info = self._detect_comp_ternary(all_instrs, innermost_store_idx, append_idx)
        if ternary_info is not None:
            if append_op == 'MAP_ADD':
                # [Round7-08] Ternary could be key or value - see parse_comprehension_inner.
                value_expr = self._extract_dict_comp_value_after_ternary(
                    all_instrs, innermost_store_idx, append_idx)
                if value_expr is not None:
                    elt_expr = (ternary_info, value_expr)
                else:
                    key_expr = self._extract_dict_comp_key_before_ternary(
                        all_instrs, innermost_store_idx, append_idx)
                    if key_expr is not None:
                        elt_expr = (key_expr, ternary_info)
                    else:
                        elt_expr = ternary_info
            else:
                elt_expr = ternary_info
            # ternary + filter 共存时也提取 filter，
            # 挂到最内层 generator。
            ifs, _ = self._extract_comp_ifs(all_instrs, innermost_store_idx, append_idx)
            if ifs:
                generators[-1]['ifs'] = ifs
        else:
            ifs, elt_start_idx = self._extract_comp_ifs(all_instrs, innermost_store_idx, append_idx)
            # [B113] 最内层元素窗前导扁平子句：末真子句之后、元素表达式之前
            # 的 ``<expr>; STORE T`` 内联对（e2/e09_comp_host 形——扁平子句是
            # 全部子句的最后一个）。贪心消费后元素窗起点前移；不命中时窗口
            # 起点不变（C3）。
            _b113_flats, _b113_flat_end = self._b113_extract_flat_clauses(
                all_instrs, elt_start_idx, append_idx)
            for _b113_tgt, _b113_expr in _b113_flats:
                generators.append({
                    'type': 'comprehension',
                    'target': _b113_tgt,
                    'iter': _b113_expr,
                    'ifs': [],
                    'is_async': 0,
                })
            if _b113_flat_end != elt_start_idx:
                elt_start_idx = _b113_flat_end
            if append_op == 'MAP_ADD':
                key_expr, value_expr = self._split_dict_comp_kv(all_instrs, elt_start_idx, append_idx)
                if key_expr is None:
                    key_expr = {'type': 'Name', 'id': all_instrs[innermost_store_idx].argval, 'ctx': 'Load'}
                if value_expr is None:
                    value_expr = {'type': 'Constant', 'value': None}
                elt_expr = (key_expr, value_expr)
            else:
                elt_instrs = all_instrs[elt_start_idx:append_idx]
                elt_expr = self.expr_reconstructor.reconstruct(elt_instrs)
                if elt_expr is None:
                    elt_expr = {'type': 'Name', 'id': all_instrs[innermost_store_idx].argval, 'ctx': 'Load'}
            # 把 ifs 挂到最内层 generator
            if ifs:
                generators[-1]['ifs'] = ifs

        return self._build_comp_result(code_obj, elt_expr, generators)

    def _split_dict_comp_kv(self, all_instrs: List[Instruction], start_idx: int, end_idx: int) -> Tuple[Optional[Dict], Optional[Dict]]:
        if start_idx >= end_idx:
            return None, None

        instrs_to_split = all_instrs[start_idx:end_idx]
        if not instrs_to_split:
            return None, None

        # [Round10-05] 识别 walrus 副作用块（COPY 1 + STORE_*）。
        # walrus 的 STORE_* 必须保留，让 expr_reconstructor 把 COPY+STORE
        # 序列识别为 NamedExpr（无论 walrus 落在 key 还是 value 位置）。
        # 仅过滤非 walrus 的 STORE_*（如 UNPACK_SEQUENCE 的多目标 store、
        # 迭代变量 store），它们不属于 key/value 表达式。
        _walrus_store_indices = set()
        for _i in range(len(instrs_to_split) - 1):
            _cur = instrs_to_split[_i]
            _nxt = instrs_to_split[_i + 1]
            if (_cur.opname == 'COPY' and _cur.arg == 1
                    and _nxt.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL')
                    and _nxt.argval != '.0'):
                _walrus_store_indices.add(_i + 1)

        filtered_instrs = [
            instr for idx, instr in enumerate(instrs_to_split)
            if not (instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL')
                    and idx not in _walrus_store_indices)
        ]

        if not filtered_instrs:
            return None, None

        map_add_instr = all_instrs[end_idx] if end_idx < len(all_instrs) else None
        if map_add_instr and map_add_instr.opname == 'MAP_ADD':
            num_values = map_add_instr.arg
        else:
            num_values = 1
        append_offset_of_window = (map_add_instr.offset if map_add_instr is not None else None)

        best_key_end = self._value_chain_key_split_point(filtered_instrs, append_offset_of_window)
        if best_key_end is None:
            best_key_end = self._find_dict_kv_split_point(filtered_instrs, num_values)

        if best_key_end is not None and best_key_end > 0:
            key_instrs = filtered_instrs[:best_key_end]
            value_instrs = filtered_instrs[best_key_end:]
        else:
            key_instrs = []
            value_instrs = filtered_instrs

        # [B243-V3R46] 键/值窗先试 keep-or-pop 整组归约：dict 推导式键位或
        # 值位可能是 `k and y or z` 这类短路链，通用重建器只返回栈顶尾项。
        # `_b237_kop_window` 判据不命中时返回 None，逐字回落既有通道（C3）。
        key_expr = self._b237_kop_window(key_instrs) if key_instrs else None
        # [B244-V3R47] 键位的汇合点就是 value 的起始（键链在 value 之前闭合），
        # 因此取键窗之后的首条指令偏移；键窗占满整窗时回落到追加点偏移。
        _key_merge_off = (filtered_instrs[best_key_end].offset
                          if (best_key_end is not None
                              and 0 < best_key_end < len(filtered_instrs))
                          else None)
        if _key_merge_off is None:
            _key_merge_off = (all_instrs[end_idx].offset
                              if end_idx < len(all_instrs) else None)
        if key_expr is None:
            # [B244-V3R47] 键位是「假出口短路链」（`(k or y) and (z or k)`）：
            # 首个跳转是弹跳型 POP_JUMP，纯 keep-or-pop 通道不接管。
            key_expr = self._dict_shortcircuit_chain(key_instrs, _key_merge_off)
        if key_expr is None:
            # [B243-V3R46] 键窗自身的纯 keep-or-pop 链（`k or y and z`）：其全部
            # 跳转的汇合点都落在追加点之前（右操作数是 value 的起始），说明
            # 链只在本窗内闭合。此时开启同族归约，否则重建器把 keep-or-pop
            # 当无操作、只返回栈顶尾项（实测键退化为 `z`）。汇合点等于追加点
            # 的值位链不开（其键窗边界不在本通道语义内）。
            _append_off = (all_instrs[end_idx].offset
                           if end_idx < len(all_instrs) else None)
            _kop_here = [i for i in key_instrs
                         if i.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP')]
            _key_chain = bool(_kop_here) and _append_off is not None and all(
                i.argval is not None and i.argval < _append_off for i in _kop_here)
            key_expr = self.expr_reconstructor.reconstruct(
                key_instrs, fold_boolop_keep_or_pop=_key_chain) if key_instrs else None
        value_expr = self._b237_kop_window(value_instrs) if value_instrs else None
        if value_expr is None:
            # [B244-V3R47] 值位同族形态（`{k: (y or z) and w}`）。
            value_expr = self._dict_shortcircuit_chain(value_instrs, append_offset_of_window)
        if value_expr is None:
            # [B243-V3R46] 值窗自身是「在追加点闭合」的 keep-or-pop 链时开启
            # 同族归约，否则重建器只返回栈顶尾项（`{k: y or z}` 退化为 `z`）。
            _value_chain = self._is_value_kop_chain(value_instrs, append_offset_of_window)
            value_expr = self.expr_reconstructor.reconstruct(
                value_instrs, fold_boolop_keep_or_pop=_value_chain) if value_instrs else None

        # [Round10-05] walrus 的 COPY+STORE 已由 expr_reconstructor 识别为
        # NamedExpr（reconstruct 中 COPY 1 + STORE_* 会生成 NamedExpr 节点），
        # 无需根据 _walrus_var 手动包裹 value_expr。这样 key 位置和 value 位置
        # 的 walrus 都能被正确归约到对应的表达式上。

        return key_expr, value_expr

    def _is_value_kop_chain(self, instrs: List[Instruction],
                            append_offset: Optional[int]) -> bool:
        """[B243-V3R46] 判定窗内是否含「在追加点闭合」的 keep-or-pop 链。

        [识别条件] 窗内至少一条 keep-or-pop 跳转，且全部 keep-or-pop 的跳转
        目标都等于追加点偏移——即链的最外层汇合点正是 MAP_ADD/LIST_APPEND，
        该链是 value（追加点的最后一段求值），而不是键位链（后者的汇合点
        落在追加点之前、右操作数才是 value 的起始）。
        [归约方式] 纯 opcode/跳转目标判定（I.4 白名单），不读名字与偏移魔数。
        [AST 映射] 无独立映射；返回 True 时调用方对 value 窗开启同族归约。
        [C1] 只读本窗指令与追加点偏移（同层结构事实）；[C2] 返回 False 时
        调用方维持原通道；[C3] 无状态、无副作用。
        """
        if append_offset is None or not instrs:
            return False
        _kop = [i for i in instrs
                if i.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP')]
        return bool(_kop) and all(i.argval == append_offset for i in _kop)

    def _value_chain_key_split_point(self, instrs: List[Instruction],
                                     append_offset: Optional[int]) -> Optional[int]:
        """[B243-V3R46] value 位 keep-or-pop 链的键边界定位。

        [识别条件] 见 `_is_value_kop_chain`：链的最外层汇合点为追加点偏移，
        说明键是链之前的独立表达式、value 是整条链。
        [归约方式] 键边界取「净栈效应 +1 且不含任何跳转的最长前缀末尾」：
        自窗首逐条累计 `_get_stack_delta`，遇到首条跳转即停止，取最后一次
        深度回到 1 的位置。前缀内无跳转保证它只覆盖键自身的求值指令
        （跳转只出现在 value 链内部），深度回到 1 保证键恰压出一个栈项。
        [AST 映射] 返回值是键窗长度，供调用方切出 key/value 两段。
        [C1] 只读本窗指令的栈效应与 opcode 族（同层结构事实）；[C2] 判定
        不成立返回 None，调用方回落既有切分通道；[C3] 无状态、无副作用。
        """
        if not self._is_value_kop_chain(instrs, append_offset):
            return None
        _jump_ops = set(CONDITIONAL_JUMP_OPS) | {
            'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP',
            'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
            'JUMP_BACKWARD_NO_INTERRUPT'}
        _depth = 0
        _best = None
        for _i, _ins in enumerate(instrs):
            if _ins.opname in _jump_ops:
                break
            _depth += self._get_stack_delta(_ins)
            if _depth == 1:
                _best = _i + 1
        if _best is None or _best >= len(instrs):
            return None
        return _best

    def _dict_shortcircuit_chain(self, instrs: List[Instruction],
                                 merge_offset: Optional[int]) -> Optional[Dict[str, Any]]:
        """[B244-V3R47] dict 推导式键/值位的「假出口短路链」整组归约。

        [识别条件]（I.4 白名单：同层 opcode / 跳转目标，无名字与偏移魔数）
          (1) 窗内首个条件跳转是前向 `POP_JUMP_FORWARD_IF_TRUE/_IF_FALSE`
              （弹跳型假出口），其目标 `t` 落在窗内且 `j.offset < t <= merge_offset`；
              首个条件跳转若是 keep-or-pop，则属纯短路链，交由 `_b237_kop_window`
              既有通道，本方法返回 None（C3）。
          (2) 首个 keep-or-pop 之前的段内可含**多个**同目标弹跳（`(k or y or z) and w`
              形态），各弹跳目标同为右链起点 `t`；末条 keep-or-pop 的目标必须是
              `merge_offset`，它既给出外层运算符，也给出右链的起点。
          (3) `t` 之后到窗末的右链段非空，可再含弹跳组或纯 keep-or-pop 链（递归）。
        [归约方式] 各弹跳的极性给出内层运算符（IF_TRUE ⇒ `or`，IF_FALSE ⇒
          `and`），跳转之间的指令段各自重建后左结合成左链；末条 keep-or-pop 的
          极性给出外层运算符（IF_FALSE_OR_POP ⇒ `and`，IF_TRUE_OR_POP ⇒ `or`），
          其后的整段作为右链递归还原；左链与右链按外层运算符合成。
          这一形态的成因：结果位置上的 `(X or A) and R` / `(X and A) or R`
          在 X 已能决定内层结果时不需要保留 X（外层只看真值），CPython 因此
          发**弹跳**假出口直落 rest，而不是 keep-or-pop。
        [唯一归属判定] 左链各段、外层运算符与右链整体归属同一个键或值表达式，
          不留下游离指令，也不产生独立语句。
        [嵌套处理] 右链递归（弹跳组可多层，纯 keep-or-pop 链由开启同族归约的
          重建器按布尔优先级折叠）；左链各段为无跳转操作数，整体重建。
        [入口引用语义] 调用方（`_split_dict_comp_kv`）把返回值作为 key/value
          唯一节点引用。
        [反编译流程] CPython 3.11 对 `{(k or y) and (z or k): v ...}` 发射
          `LOAD k; POP_JUMP_FORWARD_IF_TRUE <rest>; LOAD y;
          JUMP_IF_FALSE_OR_POP <merge>; LOAD z; JUMP_IF_TRUE_OR_POP <merge>;
          LOAD k`；不归约时通用重建器把 keep-or-pop 记成 `and`/`or` 扁平链、
          首项 `k` 被丢弃（实测产物 `{y and z or k: v ...}`，语义错）。
        """
        if not instrs or merge_offset is None or len(instrs) < 3:
            return None

        def _single(seq: List[Instruction]) -> Optional[Dict[str, Any]]:
            if not seq:
                return None
            self.expr_reconstructor.reset()
            _saved = self.expr_reconstructor._fold_boolop_keep_or_pop
            self.expr_reconstructor._fold_boolop_keep_or_pop = True
            _targets = {i.argval for i in seq
                        if i.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP')
                        and i.argval is not None}
            try:
                for _ins in seq:
                    if _targets and _ins.offset in _targets:
                        self.expr_reconstructor._b242_flush_boolop_pending()
                    self.expr_reconstructor._process_instruction(_ins)
                self.expr_reconstructor._b242_flush_boolop_pending()
            finally:
                self.expr_reconstructor._fold_boolop_keep_or_pop = _saved
            _out = [s for s in self.expr_reconstructor.stack
                    if not (isinstance(s, dict) and s.get('type') == 'PUSH_NULL')]
            return _out[0] if len(_out) == 1 else None

        def _parse(seq: List[Instruction], merge: int) -> Optional[Dict[str, Any]]:
            """[B244-V3R47] 单窗布尔链递归还原（弹跳段可多层）。

            [识别条件] 首个条件跳转是前向弹跳 `POP_JUMP_FORWARD_IF_TRUE/_IF_FALSE`
              且其目标 `t` 在本窗内（`j.offset < t <= merge`）；首个条件跳转若是
              keep-or-pop 或窗内无跳转，本层交回 `_single`（纯短路链按优先级归约）。
            [归约方式] 目标同为 `t`、且位于首个 keep-or-pop 之前的弹跳组按其极性
              给出内层运算符（IF_TRUE ⇒ `or`，IF_FALSE ⇒ `and`），把跳转之间的
              指令段各自重建后左结合成左链；首个 keep-or-pop 的目标必须是 `merge`
              （极性给出外层运算符：IF_FALSE_OR_POP ⇒ `and`，IF_TRUE_OR_POP ⇒
              `or`），其后的整段作为右链递归还原。
            [唯一归属判定] 左链各段、外层运算符与右链整体归属同一个键或值表达式。
            [嵌套处理] 右链递归（可再含弹跳组或纯 keep-or-pop 链）；左链各段为
              无跳转操作数，按 `_single` 重建。
            [入口引用语义] 返回值由调用方作为 key/value 唯一节点引用。
            [反编译流程] CPython 3.11 对结果位置上 `(k or y or z) and w` 发射
              `LOAD k; POP_JUMP_FORWARD_IF_TRUE <w>; LOAD y;
              POP_JUMP_FORWARD_IF_TRUE <w>; LOAD z; JUMP_IF_FALSE_OR_POP <merge>;
              LOAD w`：除末项外每个 or 操作数的弹跳直落右链起点，末项由外层
              keep-or-pop 保持。只按首跳切一层时左链段内仍留弹跳，重建器栈上多出
              两项 ⇒ 整窗返回 None（实测 r6 退化为 `{z and w: v ...}`）。
            """
            _first_jump = None
            _first_kop = None
            for _k, _ins in enumerate(seq):
                _op = _ins.opname
                if _op in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE'):
                    _first_jump = _k
                    break
                if _op in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                    _first_kop = _k
                    break
                if _op in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                           'JUMP_BACKWARD_NO_INTERRUPT'):
                    return None
            if _first_jump is None:
                if _first_kop is None:
                    return _single(seq)
                # 纯 keep-or-pop 链：首条跳转即顶层运算符，右操作数递归还原
                # （右嵌套是 CPython 发射顺序的规范逆：`a and (b or c)` 与
                # `a and b or c` 的跳转序列不同，左结合优先级折叠会把二者混同）。
                if getattr(seq[_first_kop], 'argval', None) != merge:
                    return None
                _op = 'and' if seq[_first_kop].opname == 'JUMP_IF_FALSE_OR_POP' else 'or'
                _left_s = _single(seq[:_first_kop])
                _right_s = _parse(seq[_first_kop + 1:], merge)
                if _left_s is None or _right_s is None:
                    return None
                if (isinstance(_right_s, dict) and _right_s.get('type') == 'BoolOp'
                        and _right_s.get('op') == _op):
                    return {'type': 'BoolOp', 'op': _op,
                            'values': [_left_s] + list(_right_s['values'])}
                return {'type': 'BoolOp', 'op': _op, 'values': [_left_s, _right_s]}
            if _first_jump == 0:
                return None
            _t = getattr(seq[_first_jump], 'argval', None)
            if _t is None or _t <= seq[_first_jump].offset or _t > merge:
                return None
            _ops: List[str] = []
            _operands: List[List[Instruction]] = []
            _cur: List[Instruction] = list(seq[:_first_jump])
            _kop = None
            for _k in range(_first_jump, len(seq)):
                _op = seq[_k].opname
                if _op in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE'):
                    if getattr(seq[_k], 'argval', None) != _t:
                        return None
                    _operands.append(_cur)
                    _cur = []
                    _ops.append('or' if 'IF_TRUE' in _op else 'and')
                elif _op in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                    _kop = _k
                    break
                elif _op in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                             'JUMP_BACKWARD_NO_INTERRUPT'):
                    return None
                else:
                    _cur.append(seq[_k])
            if _kop is None:
                return None
            _operands.append(_cur)
            if getattr(seq[_kop], 'argval', None) != merge:
                return None
            _outer = 'and' if seq[_kop].opname == 'JUMP_IF_FALSE_OR_POP' else 'or'
            _right = _parse(seq[_kop + 1:], merge)
            if _right is None:
                return None
            _nodes: List[Dict[str, Any]] = []
            for _seg in _operands:
                _e = _single(_seg)
                if _e is None:
                    return None
                _nodes.append(_e)
            _left = _nodes[0]
            for _op_name, _nd in zip(_ops, _nodes[1:]):
                _left = {'type': 'BoolOp', 'op': _op_name, 'values': [_left, _nd]}
            # 同运算符的右链并入同一 BoolOp（`and`/`or` 结合律），避免多出一层
            # 同运算嵌套导致的重编译跳转极性差异。
            if (isinstance(_right, dict) and _right.get('type') == 'BoolOp'
                    and _right.get('op') == _outer):
                _values = [_left] + list(_right['values'])
            else:
                _values = [_left, _right]
            return {'type': 'BoolOp', 'op': _outer, 'values': _values}

        # 顶层只接管「首跳为弹跳」的窗；纯 keep-or-pop 窗交由既有通道（C3）。
        for _k, _ins in enumerate(instrs):
            if _ins.opname in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE'):
                return _parse(instrs, merge_offset)
            if _ins.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                return None
            if _ins.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                               'JUMP_BACKWARD_NO_INTERRUPT'):
                return None
        return None

    def _find_dict_kv_split_point(self, instrs: List[Instruction], num_values: int) -> Optional[int]:
        if len(instrs) < 2:
            return None

        # [R40 fix] Track LOAD_METHOD calling convention to correct CALL
        # stack delta. In Python 3.11, LOAD_METHOD pushes NULL+method
        # (delta +1: pops obj, pushes 2). CALL n then pops n+2 (n args +
        # callable + NULL) and pushes 1, delta = -(n+1). Without
        # LOAD_METHOD (e.g. LOAD_ATTR), CALL n pops n+1 (n args +
        # callable), delta = -n. The original _get_stack_delta returns
        # -(n)+1 for CALL, which is incorrect for both cases and causes
        # dict comp key/value split point detection to fail when the key
        # contains a method call (e.g. {v.strftime('%Y-%m-%d'): k}).
        stack_depth = 0
        depth_history = []
        _has_load_method = False

        for i, instr in enumerate(instrs):
            if instr.opname == 'LOAD_METHOD':
                # [B106-R3] 3.11 方法调用协议：LOAD_METHOD 弹 receiver、压
                # [self|NULL, method] 两槽，净栈 +1（与 [R40 fix] 的 CALL
                # ``-(n+1)`` 口径配套：CALL 弹 n 实参 + method + self|NULL
                # 共 n+2、压 1 个结果）。B106 elif 链重构时本分支只置标记未
                # 定 delta，落入其后 ``stack_depth += delta`` 复用上一迭代
                # 的 stale delta——方法链（``k.m1(...).m2(...)``）的第二个
                # LOAD_METHOD 紧跟 CALL（delta = -(n+1)）之后，深度历史被
                # 负值二次污染 ⇒ final_depth < 1 ⇒ 切分点 None ⇒ dictcomp
                # 键整体蒸发（finance.pyc PositionDict 键链 132→131 回退
                # 根因；单方法键/值侧链因 stale delta 恰为 +1 而侥幸存活）。
                # 判据 = opcode 栈净效应（I.4 白名单）；B106 的
                # PUSH_NULL/CALL_FUNCTION_EX/LIST_EXTEND 族覆盖维持不变
                #（c4_12/r5v5_07/lambda 变体放行面，C3）。
                _has_load_method = True
                delta = 1
            elif instr.opname == 'CALL':
                if _has_load_method:
                    # CALL with LOAD_METHOD: delta = -(n+1)
                    delta = -(instr.arg + 1)
                else:
                    # CALL without LOAD_METHOD: delta = -(n)
                    delta = -instr.arg
                _has_load_method = False
                stack_depth += delta
                depth_history.append((i, stack_depth))
                continue
            elif instr.opname == 'PUSH_NULL':
                # [B106] CALL_FUNCTION_EX 调用协议的 NULL 槽（压栈 +1）
                delta = 1
            elif instr.opname == 'CALL_FUNCTION_EX':
                # [B106] 星实参调用协议：弹 args 元组 + callable + NULL
                #（flag&1 再弹 kwargs dict），压 1 个结果。键/值窗含星实参
                # 调用（``{f(*k, v): ...}``）时旧 sim 未覆盖该协议族
                # （PUSH_NULL/LIST_EXTEND/LIST_APPEND/CALL_FUNCTION_EX 均按
                # delta=0 计），深度历史虚高 ⇒ 键窗切分错位（v8 实测键窗
                # 截到 BUILD_LIST 0 → 键退化为 []）。判据 = 块内 opcode 栈
                # 效应（I.4 白名单），普通形态深度路径不变（C3）。
                delta = -(3 + (1 if (instr.arg or 0) & 1 else 0)) + 1
            elif instr.opname in ('LIST_EXTEND', 'LIST_APPEND',
                                   'DICT_UPDATE', 'DICT_MERGE', 'SET_UPDATE'):
                # [B106] 容器原地更新/追加协议：弹 1（可迭代表/值），容器留栈
                delta = -1
            elif instr.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                # [B243-V3R46] keep-or-pop 短路跳转的双路栈净效应：
                # 短路时保留操作数（0），不短路时弹出操作数（-1）。栈深模拟
                # 只能记一个值，取「弹出」口径——非短路径总是接在弹出后的
                # 落点（假值区入口或汇合点之后）继续求值，于是 value 的首条
                # 压栈指令恰好落在 depth==1 → 2 的边界上，切分点因此停在
                # key 链末尾。记 0 时 `k and y or z` 的键链会多吞掉假值区
                # 首指令 `z`（键退化为 `y`、值退化为 `v` 整体错位）。
                delta = -1
            else:
                delta = self._get_stack_delta(instr)
            stack_depth += delta
            depth_history.append((i, stack_depth))

        final_depth = stack_depth
        if final_depth < 1:
            return None

        # Find the LAST transition from depth==1 to depth>1.
        # For dict comprehension {key: value}, key_expr is evaluated first
        # (depth reaches 1), then value_expr starts (depth goes to 2).
        # The split point is after the last instruction that leaves depth==1
        # before value_expr begins.
        # - Simple key {a: b}: depth [(0,1),(1,2)] → last transition at i=0 → split at 1
        # - Compound key {a+b: c}: depth [(0,1),(1,2),(2,1),(3,2)] → last transition at i=2 → split at 3
        # Region reduction: key_expr and value_expr are sibling sub-nodes of the
        # dict comp element; the split point is the boundary where the parent
        # (MAP_ADD) references child entry points (key entry / value entry).
        last_transition_idx = None
        for i in range(len(depth_history) - 1):
            idx, depth = depth_history[i]
            next_idx, next_depth = depth_history[i + 1]
            if depth == 1 and next_depth > 1:
                last_transition_idx = i

        if last_transition_idx is not None:
            return last_transition_idx + 1

        best_split = None
        for split_pos in range(1, len(instrs)):
            key_part = instrs[:split_pos]
            value_part = instrs[split_pos:]

            key_test = self.expr_reconstructor.reconstruct(key_part)
            value_test = self.expr_reconstructor.reconstruct(value_part)

            if key_test and value_test:
                has_operation = any(
                    inp.opname in ('BINARY_OP', 'COMPARE_OP', 'UNARY_NOT', 'UNARY_NEGATIVE',
                                   'UNARY_POSITIVE', 'BINARY_SUBSCR', 'CALL')
                    for inp in value_part
                )
                if has_operation or len(value_part) >= 2:
                    best_split = split_pos
                    break

        return best_split

    def _get_stack_delta(self, instr: Instruction) -> int:
        if instr.opname.startswith('LOAD_') and not instr.opname.startswith('LOAD_ATTR'):
            return 1
        elif instr.opname in ('BUILD_TUPLE', 'BUILD_LIST', 'BUILD_SET', 'BUILD_STRING'):
            # [B106] BUILD_* n 弹 n 压 1——arg=0（空容器种子，星实参构建
            # BUILD_LIST 0 的标准起点）同样压 1；旧 `if instr.arg else 0`
            # 把 BUILD_LIST 0 记为 0，dict comp 键/值切分点的深度历史
            # 全程偏低一位 ⇒ 星实参键窗切分失败（v8 形）。判据 = opcode
            # 栈效应（I.4 白名单）。
            return 1 - (instr.arg or 0)
        elif instr.opname == 'BUILD_MAP':
            return 1 - 2 * instr.arg if instr.arg else 1
        elif instr.opname in ('BINARY_OP', 'COMPARE_OP'):
            return -1
        elif instr.opname in ('UNARY_NOT', 'UNARY_NEGATIVE', 'UNARY_POSITIVE'):
            return 0
        elif instr.opname == 'BINARY_SUBSCR':
            return -1
        elif instr.opname == 'CALL':
            return -(instr.arg) + 1
        elif instr.opname == 'FORMAT_VALUE':
            return 0
        elif instr.opname == 'COPY':
            # [Round10-05] COPY 总是向栈压入一个已有元素的副本，栈深度 +1。
            # 用于 walrus (x := expr) 的 COPY 1 + STORE_x 模式：COPY 压栈、
            # STORE 弹栈，净效果为 0，但中间状态需正确跟踪以便定位 key/value
            # 边界（边界应落在 STORE 之后，使 walrus 整体归属 key 或 value）。
            return 1
        elif instr.opname.startswith('POP_') or instr.opname == 'POP_TOP':
            return -1
        elif instr.opname.startswith('STORE_'):
            return -1
        else:
            return 0

    def _find_comp_target_names(self, all_instrs: List[Instruction], first_only: bool = False) -> Union[Optional[str], List[str]]:
        """收集推导式 code object 内的迭代目标名（名袋，仅作回退用途）。

        [识别条件] 名袋 = 全部 STORE_FAST/STORE_DEREF/STORE_NAME 的 argval
        （排除 .0），但排除 walrus 副作用块内的 STORE： walrus 在 3.11 编译为
        ``COPY 1; STORE_*``，其 STORE 紧跟 COPY 之后且位于 elt/if 表达式窗内，
        不属于迭代目标存储序列（与 _split_dict_comp_kv 的 [Round10-05] 守卫
        同一结构事实）。迭代目标的 STORE 来自 FOR_ITER/UNPACK 链，其后继前
        指令不是 COPY。
        [归约方式] 线性扫描去重收集；first_only 时返回首个非 .0 的 STORE 名。
        [AST 映射] 无独立映射，仅供 _build_comprehension_target 回退路径与
        target_name 定位使用。

        [C1] 仅读本推导式指令流（L(A)）；[C3] walrus STORE 经显式守卫
        （前驱 COPY arg==1）排除，防止表达式内绑定被吸收为幻影迭代目标。
        """
        names = []
        _walrus_store_indices = set()
        for _i in range(len(all_instrs) - 1):
            _cur = all_instrs[_i]
            _nxt = all_instrs[_i + 1]
            if (_cur.opname == 'COPY' and _cur.arg == 1
                    and _nxt.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL')
                    and _nxt.argval != '.0'):
                _walrus_store_indices.add(_i + 1)
        for idx, instr in enumerate(all_instrs):
            if instr.opname in ('STORE_FAST', 'STORE_DEREF', 'STORE_NAME'):
                if idx in _walrus_store_indices:
                    continue
                if instr.argval != '.0' and instr.argval not in names:
                    if first_only:
                        return instr.argval
                    names.append(instr.argval)
        return names if not first_only else None

    def _parse_target_store_sequence(self, all_instrs: List[Instruction], pos: int) -> Tuple[Optional[Dict], int]:
        """[Round5-B21/B22] 按 UNPACK_SEQUENCE/UNPACK_EX 的栈结构递归解析 for-target 存储序列。

        [识别条件] 目标存储序列 = FOR_ITER 之后由 STORE_* 与
        UNPACK_SEQUENCE/UNPACK_EX 构成的前缀：叶目标是一条 STORE_*；元组目标
        以 UNPACK_SEQUENCE n 开头，其后恰好 n 个子目标按左→右存储序展开；星号
        目标以 UNPACK_EX arg 开头（低 8 位 = 星号前元素数，高 8 位 = 星号后
        元素数），星号位本身是一个子目标。EXTENDED_ARG 为纯 arg 前缀，跳过。
        walrus 的 ``COPY 1; STORE_*`` 副作用块不属于该前缀（其 STORE 位于
        elt/if 表达式窗、且前驱是 COPY 而非 UNPACK/FOR_ITER），结构上不可达，
        故不会被吸收为迭代目标。
        [归约方式] 对前缀做确定性递归下降：遇 STORE_* 产出 Name 叶并前进一步；
        遇 UNPACK_* 按其 arity/星号位递归消费对应个数的子目标后组合成
        Tuple/Starred 节点；解析失败（前缀断裂）返回 None。
        [AST 映射] Name(id, ctx=Store) / Tuple(elts=[...], ctx=Store) /
        Starred(value=目标, ctx=Store)，嵌套深度与星号组合不限。

        [C1] 仅读本推导式指令流的同层结构事实（操作码形态/栈效应）；
        [C2] 子目标作为黑箱递归组合，父层不窥视子层内部。
        """
        n = len(all_instrs)
        while pos < n and all_instrs[pos].opname == 'EXTENDED_ARG':
            pos += 1
        if pos >= n:
            return None, pos
        instr = all_instrs[pos]
        if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL'):
            if instr.argval == '.0':
                return None, pos
            return {'type': 'Name', 'id': instr.argval, 'ctx': 'Store'}, pos + 1
        if instr.opname == 'UNPACK_SEQUENCE':
            arity = instr.arg
            pos += 1
            elts = []
            for _ in range(arity):
                elt, pos = self._parse_target_store_sequence(all_instrs, pos)
                if elt is None:
                    return None, pos
                elts.append(elt)
            return {'type': 'Tuple', 'elts': elts, 'ctx': 'Store'}, pos
        if instr.opname == 'UNPACK_EX':
            before = instr.arg & 0xFF
            after = (instr.arg >> 8) & 0xFF
            pos += 1
            elts = []
            for _ in range(before):
                elt, pos = self._parse_target_store_sequence(all_instrs, pos)
                if elt is None:
                    return None, pos
                elts.append(elt)
            starred, pos = self._parse_target_store_sequence(all_instrs, pos)
            if starred is None:
                return None, pos
            elts.append({'type': 'Starred', 'value': starred, 'ctx': 'Store'})
            for _ in range(after):
                elt, pos = self._parse_target_store_sequence(all_instrs, pos)
                if elt is None:
                    return None, pos
                elts.append(elt)
            return {'type': 'Tuple', 'elts': elts, 'ctx': 'Store'}, pos
        return None, pos

    def _b113_extract_flat_clauses(self, all_instrs: List[Instruction], start_idx: int,
                                   end_idx: int) -> Tuple[List[Tuple[Dict, Dict]], int]:
        """[B113] 单元素 for 子句内联（扁平子句）识别与重构。

        ①算法依据：CPython 3.11 推导式 codegen 不变式 + I.1 原则 4（入口引用
        语义）。``for T in [<单元素>]`` 的单元素列表字面量被编译器内联展开为
        ``<expr 求值>; STORE T``——无 BUILD_LIST/GET_ITER/FOR_ITER 协议，仅剩
        扁平赋值对。等价源 = ``for T in (<expr>,)``（单元素元组同样内联，重
        编译逐字节复现原始指令序；c4_18 直接探针 e4 形已证）。多 for 子句
        （含嵌套最内层窗口）中该扁平对位于真子句迭代协议之间/元素表达式之前，
        不识别则子句整条丢失（comp2 e1/e2、c4_05 e09_comp_host 实测）。
        ②归约顺序：自底向上——由 _parse_multi_for_comprehension 的两处窗口
        （真子句 iter 窗前导、最内层元素窗前导）自左向右贪心消费；消费后窗口
        起点前移，真子句 iter/元素表达式提取不受扰动。
        ③唯一归属判定（识别条件，I.4 白名单 = 块内指令 opcode 序）：候选段 =
        [窗口起点, 首个 STORE_*) 之间的指令，且段内只含表达式构造类 opcode
        （LOAD_*/BUILD_*/BINARY_*/COMPARE_OP/UNARY_*/PRECALL/CALL/
        CALL_FUNCTION*/MAKE_FUNCTION 等可重建表达式）；含 COPY（walrus
        ``COPY 1; STORE`` 副作用对，[Round10-05] 判据）、POP_*、任意跳转、
        FOR_ITER/GET_ITER、LIST_APPEND/SET_ADD/MAP_ADD/YIELD_VALUE、
        STORE、UNPACK_*、RETURN、RAISE 之一即终止扫描（不命中，窗口起点
        不变，既有行为零扰动）。目标存储序列经 _parse_target_store_sequence
        结构化解析（支持元组/星号目标）；表达式经 expr_reconstructor 重建，
        失败即终止。
        ④嵌套处理：连续多个扁平子句按序贪心消费（e1 的双扁平+单真子句形态）；
        扁平子句作为独立 comprehension 生成元插入 generators 序列，保持源序。
        ⑤入口引用语义：返回 ([(target, iter_expr)], 新窗口起点)；iter 表达式
        包装为单元素元组 ``{'type': 'Tuple', 'elts': [expr], 'ctx': 'Load'}``。
        ⑥反编译流程：多 for 推导式重建的子句收集步；终止性由窗口有限长度保证
        （无计数上限）。
        [C1] 只读本推导式指令流的块内 opcode 序；[C2] 扁平子句经独立
        comprehension 节点被父推导式黑箱消费；[C3] 扫描遇任何非表达式构造
        opcode 立即终止，不命中时窗口起点不变（既有 iter/元素提取逐位保持）。
        """
        flats = []
        pos = start_idx
        _b113_stop_ops = ('COPY', 'FOR_ITER', 'GET_ITER', 'LIST_APPEND',
                          'SET_ADD', 'MAP_ADD', 'YIELD_VALUE', 'YIELD_FROM',
                          'RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS',
                          'GET_AWAITABLE', 'GET_AITER', 'SEND',
                          'BEFORE_WITH', 'BEFORE_ASYNC_WITH')
        while pos < end_idx:
            first_instr = all_instrs[pos]
            if first_instr.opname.startswith('POP_'):
                break
            if first_instr.opname in _b113_stop_ops:
                break
            if first_instr.opname.startswith('JUMP'):
                break
            if first_instr.opname.startswith('POP_JUMP'):
                break
            if first_instr.opname.startswith('STORE_'):
                break
            if first_instr.opname.startswith('UNPACK_'):
                break
            # 扫描到首个 STORE_*：候选扁平段 = [pos, store_pos)
            store_pos = None
            for j in range(pos, end_idx):
                _op = all_instrs[j].opname
                if _op in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL'):
                    store_pos = j
                    break
                if _op in _b113_stop_ops or _op.startswith('JUMP') or _op.startswith('POP_'):
                    break
                if _op.startswith('STORE_') or _op.startswith('UNPACK_'):
                    break
                if _op in CONDITIONAL_JUMP_OPS:
                    break
            if store_pos is None or store_pos == pos:
                break
            if all_instrs[store_pos].argval == '.0':
                break
            target, seq_end = self._parse_target_store_sequence(all_instrs, store_pos)
            if target is None or seq_end <= store_pos:
                break
            expr_instrs = [i for i in all_instrs[pos:store_pos]
                           if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            if not expr_instrs:
                break
            expr = self.expr_reconstructor.reconstruct(expr_instrs)
            if expr is None:
                break
            flats.append((target, {'type': 'Tuple', 'elts': [expr], 'ctx': 'Load'}))
            pos = seq_end
        return flats, pos

    def _build_comprehension_target(self, all_instrs: List[Instruction]) -> Optional[Dict]:
        """构造推导式迭代目标 AST（B21/B22：结构化解包解析，名袋仅作回退）。

        [识别条件] 同步推导式的目标存储序列紧跟 FOR_ITER 之后（含嵌套
        UNPACK_SEQUENCE/UNPACK_EX 与星号位）；异步推导式（GET_ANEXT/SEND
        布局，无 FOR_ITER）暂无该前缀锚点。
        [归约方式] 优先以 _parse_target_store_sequence 从 FOR_ITER 之后做
        结构化递归解析；仅当找不到 FOR_ITER 或前缀断裂（异步布局等结构未
        覆盖形态）时回退到 _find_comp_target_names 名袋（已带 walrus COPY
        守卫），与旧行为兼容。
        [AST 映射] 单目标 → Name；解包 → Tuple（嵌套 Tuple/Starred 依
        UNPACK 结构保留）；不再按名袋一律拍平为顶层 Tuple。

        [C1] 结构判据只读本推导式指令流；[C2] 嵌套子目标黑箱递归；
        [C3] 名袋回退路径以 walrus COPY 守卫显式排除表达式内绑定。
        """
        for i, instr in enumerate(all_instrs):
            if instr.opname == 'FOR_ITER':
                target, _seq_end = self._parse_target_store_sequence(all_instrs, i + 1)
                if target is not None:
                    return target
                break

        target_names = self._find_comp_target_names(all_instrs)

        if len(target_names) == 1:
            return {
                'type': 'Name',
                'id': target_names[0],
                'ctx': 'Store'
            }
        elif len(target_names) > 1:
            return {
                'type': 'Tuple',
                'elts': [
                    {'type': 'Name', 'id': name, 'ctx': 'Store'}
                    for name in target_names
                ],
                'ctx': 'Store'
            }
        else:
            return None

    def _find_comp_append_op(self, all_instrs: List[Instruction], target_name: str = None,
                              append_kind: str = None) -> Tuple[Optional[str], Optional[int]]:
        if target_name:
            for idx, instr in enumerate(all_instrs):
                if instr.opname in ('STORE_FAST', 'STORE_DEREF', 'STORE_NAME') and instr.argval == target_name:
                    return 'STORE', idx
        # [B106] 元素产出锚点按推导式种类精化（code object co_name → 产出
        # opcode）：星实参调用形元素（``[f(*xs, v) for v in xs]``）的实参
        # 构建段含内层 BUILD_LIST + LIST_EXTEND + LIST_APPEND + LIST_TO_TUPLE
        # （CALL_FUNCTION_EX 协议）——首个 LIST_APPEND 属内层实参构建，
        # 被误当元素产出锚点 ⇒ 元素窗错位、Call 整体蒸发（st_comp 实测
        # 元素退化为回退 Name(target)）。判据（I.4 白名单：code object
        # co_name 元数据 + 块内 opcode 序）= 该推导式种类的产出 opcode 的
        # **最末**出现（元素产出是循环体最后一条有效指令，其后即回边
        # JUMP_BACKWARD；内层实参构建的 LIST_APPEND 恒在其前）。普通形态
        # 首=末，行为逐位不变（C3）。
        if append_kind is not None:
            _b106_last = None
            for idx, instr in enumerate(all_instrs):
                if instr.opname == append_kind:
                    _b106_last = idx
            if _b106_last is not None:
                return append_kind, _b106_last
            return None, None
        for idx, instr in enumerate(all_instrs):
            if instr.opname in ('LIST_APPEND', 'SET_ADD', 'MAP_ADD', 'DICT_MERGE'):
                return instr.opname, idx
        # [B96] async genexpr 的元素产出 YIELD 识别：含 await 的
        # <genexpr> code object（co_flags 置 CO_ASYNC_GENERATOR）内，
        # 用户级 ``await <expr>`` 的挂起协议（GET_AWAITABLE; LOAD_CONST
        # None; SEND; YIELD_VALUE; RESUME; JUMP_BACKWARD_NO_INTERRUPT 回
        # SEND）先于元素产出执行——其 YIELD_VALUE 以 RESUME +
        # JUMP_BACKWARD_NO_INTERRUPT 收尾（轮询回环），元素产出 YIELD 以
        # RESUME + POP_TOP/JUMP_BACKWARD 收尾（无 NO_INTERRUPT 回环）。
        # 判据（I.4 白名单：块内指令 opcode 序）= 跳过轮询回环 YIELD，
        # 取首个非协议 YIELD 为 append 锚点；否则 a_four 形（``sum(1 for
        # x in xs if await g2(x))``）把 await 轮询 YIELD 误当元素产出，
        # 过滤窗错位 ⇒ 元素 1 丢失、await 表达式错位为元素。无协议
        # YIELD 的同步 genexpr 行为逐位不变（C3）。
        for idx, instr in enumerate(all_instrs):
            if instr.opname == 'YIELD_VALUE':
                if (idx + 2 < len(all_instrs)
                        and all_instrs[idx + 1].opname == 'RESUME'
                        and all_instrs[idx + 2].opname == 'JUMP_BACKWARD_NO_INTERRUPT'):
                    continue
                return 'YIELD_VALUE', idx
        return None, None

    def _extract_comp_ifs(self, all_instrs: List[Instruction], store_idx: int,
                          append_idx: int) -> Tuple[List[Dict], int]:
        ifs = []
        seg_ops = []
        elt_start_idx = store_idx + 1
        # 获取LIST_APPEND指令的偏移量，用于区分过滤条件和三元条件
        append_offset = all_instrs[append_idx].offset if append_idx < len(all_instrs) else float('inf')
        segments = []
        current_start = store_idx + 1
        for idx in range(store_idx + 1, append_idx):
            instr = all_instrs[idx]
            if instr.opname in CONDITIONAL_JUMP_OPS:
                # 区分三元条件和过滤条件：
                # - 过滤条件：跳转目标在LIST_APPEND之后（跳过元素表达式）
                # - 三元条件：跳转目标在LIST_APPEND之前（跳转到false值）
                # 三元条件不应被提取为过滤条件，而应作为元素表达式的一部分
                if hasattr(instr, 'argval') and instr.argval is not None:
                    if instr.argval < append_offset and 'BACKWARD' not in instr.opname:
                        # [R10] OR-filter pattern: if there's a BACKWARD conditional
                        # jump between this FORWARD jump and its target, this FORWARD
                        # jump is part of an OR filter (e.g. `if cond1 or cond2`),
                        # not a ternary. Collect it as a filter segment instead of
                        # breaking for ternary detection.
                        has_backward_after = False
                        for inner_idx in range(idx + 1, append_idx):
                            inner_instr = all_instrs[inner_idx]
                            if inner_instr.offset >= instr.argval:
                                break
                            if inner_instr.opname in CONDITIONAL_JUMP_OPS and 'BACKWARD' in inner_instr.opname:
                                has_backward_after = True
                                break
                        # [B6-comp 混合过滤器甄别扩展] and→or 边界成员的前向假边
                        # 直达 or 尾成员（目标块仍是条件块），or 尾成员的「假边跳
                        # 回 FOR_ITER」回跳位于目标偏移之后且与求值指令同块（前驱
                        # 指令非跳转即同块，[C1] 同层结构事实）。命中即仍按过滤
                        # 器段收集，不 break 出循环（不命中维持 R10 原判据，
                        # [C3] 显式守卫）。
                        if not has_backward_after:
                            for inner_idx in range(idx + 1, append_idx):
                                inner_instr = all_instrs[inner_idx]
                                if inner_instr.offset < instr.argval:
                                    continue
                                if inner_instr.offset >= append_offset:
                                    break
                                if inner_instr.opname in CONDITIONAL_JUMP_OPS and 'BACKWARD' in inner_instr.opname:
                                    if inner_idx > 0:
                                        prev_instr = all_instrs[inner_idx - 1]
                                        if (prev_instr.opname not in CONDITIONAL_JUMP_OPS
                                                and prev_instr.opname not in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                                                              'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                                                              'RETURN_VALUE', 'RETURN_CONST')):
                                            has_backward_after = True
                                            break
                        if not has_backward_after:
                            # FORWARD ternary cond 跳转 — break
                            # 出循环让已收集的 filter segments 被处理，而非 return
                            # 丢弃 filters。elt_start_idx 保持为 current_start
                            # （最后一个 filter 之后，ternary cond 之前），由
                            # parse_comprehension_inner 决定是否使用 ternary_info
                            # 作为 elt（若使用则 elt_start_idx 不被使用）。
                            break
                segments.append((current_start, idx, instr))
                current_start = idx + 1

        if segments:
            # [Round09] Detect chained comparison filter: when segment 0 contains
            # COPY(arg=2)+COMPARE_OP/IS_OP/CONTAINS_OP and subsequent segments
            # also contain COMPARE_OP/IS_OP/CONTAINS_OP, these form a chained
            # comparison like `a <= b <= c`. Merge them into a single Compare node
            # instead of BoolOp(and, a<=b, c).
            _cc_chain_end = -1
            for _cc_si in range(len(segments)):
                _cc_seg_s, _cc_seg_e, _cc_jmp = segments[_cc_si]
                _cc_instrs = all_instrs[_cc_seg_s:_cc_seg_e]
                _cc_has_copy_compare = any(
                    _cc_instrs[ci].opname == 'COPY' and _cc_instrs[ci].arg == 2
                    and _cc_instrs[ci + 1].opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP')
                    for ci in range(len(_cc_instrs) - 1))
                if _cc_has_copy_compare:
                    _cc_chain_end = _cc_si
                    for _cc_next in range(_cc_si + 1, len(segments)):
                        _cc_ns, _cc_ne, _cc_njmp = segments[_cc_next]
                        _cc_ninstrs = all_instrs[_cc_ns:_cc_ne]
                        _cc_has_cmp = any(
                            i.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP')
                            for i in _cc_ninstrs)
                        if _cc_has_cmp:
                            _cc_chain_end = _cc_next
                        else:
                            break
                    break
            if _cc_chain_end > 0:
                _cc_first_seg_s, _cc_first_seg_e, _cc_first_jmp = segments[0]
                _cc_first_instrs = all_instrs[_cc_first_seg_s:_cc_first_seg_e]
                _cc_first_expr = self.expr_reconstructor.reconstruct(_cc_first_instrs)
                if _cc_first_expr and _cc_first_expr.get('type') == 'Compare' and len(_cc_first_expr.get('ops', [])) == 1:
                    _cc_ops = list(_cc_first_expr.get('ops', []))
                    _cc_left = _cc_first_expr.get('left')
                    _cc_comps = list(_cc_first_expr.get('comparators', []))
                    for _cc_next in range(1, _cc_chain_end + 1):
                        _cc_ns, _cc_ne, _cc_njmp = segments[_cc_next]
                        _cc_ninstrs = all_instrs[_cc_ns:_cc_ne]
                        _cc_ninstrs_no_jmp = [i for i in _cc_ninstrs if i.opname not in CONDITIONAL_JUMP_OPS]
                        _cc_has_cmp = any(i.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP') for i in _cc_ninstrs_no_jmp)
                        if _cc_has_cmp:
                            _cc_cmp_instr = None
                            for i in _cc_ninstrs_no_jmp:
                                if i.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP'):
                                    _cc_cmp_instr = i
                                    break
                            _cc_op_str = (_cc_cmp_instr.argval if _cc_cmp_instr.opname == 'COMPARE_OP'
                                          else ('is' if _cc_cmp_instr.arg == 0 else 'is not')
                                          if _cc_cmp_instr.opname == 'IS_OP'
                                          else ('in' if _cc_cmp_instr.arg == 0 else 'not in'))
                            _cc_ops.append(_cc_op_str)
                            _cc_cmp_idx = _cc_ninstrs_no_jmp.index(_cc_cmp_instr)
                            _cc_before_cmp = _cc_ninstrs_no_jmp[:_cc_cmp_idx]
                            _cc_comp_expr = self.expr_reconstructor.reconstruct(_cc_before_cmp) if _cc_before_cmp else None
                            if _cc_comp_expr:
                                _cc_comps.append(_cc_comp_expr)
                    if len(_cc_ops) >= 2 and len(_cc_comps) == len(_cc_ops) and _cc_left:
                        _cc_compare = {'type': 'Compare', 'left': _cc_left,
                                       'ops': _cc_ops, 'comparators': _cc_comps}
                        ifs = [_cc_compare]
                        _cc_after_idx = segments[_cc_chain_end][1] + 1
                        elt_start_idx = _cc_after_idx
                        # [B151-V3R7] 链式比较之后仍有过滤项时的续解析。
                        # 旧行为在此直接 return，把链式比较之后的过滤项
                        # （`if 0 < x < lim and (flag or x % 2)` 的后半段）
                        # 整段丢弃——推导式只剩 `0 < x < lim`，语义与控制流
                        # 双错。归约方式：沿链式比较的真值续接点继续解析
                        # 后续过滤项并以 'and' 串联（详见
                        # _b151_parse_comp_filter_terms /
                        # _b151_compose_comp_filter_terms 的六项 docstring）。
                        # 无后续项或解析失败时逐位沿用旧结果（C3 封闭）。
                        _b151_tail = self._b151_parse_comp_filter_terms(
                            all_instrs, _cc_after_idx,
                            segments[-1][1] + 1 if segments else _cc_after_idx)
                        if _b151_tail is not None:
                            _b151_expr = self._b151_compose_comp_filter_terms(
                                _b151_tail)
                            if _b151_expr is not None:
                                ifs = [{'type': 'BoolOp', 'op': 'and',
                                        'values': [_cc_compare, _b151_expr]}]
                        return ifs, elt_start_idx

            # [B245-V3R49] 过滤器短路链整组归约（见
            # _b245_comp_filter_chain 的六项 docstring）。
            _b245_expr = self._b245_comp_filter_chain(
                all_instrs, segments, current_start, append_idx)
            if _b245_expr is not None:
                return [_b245_expr], current_start

            # [B249-V3R53] 过滤器位的「值位混合短路链」整组归约。CPython 3.11
            # 对 `if <值位布尔链>`（如 `if ((x or y) and z or (w and v) - 1)`、
            # `if bool((x and y) or (z and w) or v)`）把整条链编译在**值位**：
            # 链内既有 keep-or-pop（`JUMP_IF_*_OR_POP`）又有前向假出口弹跳
            # （`POP_JUMP_FORWARD_IF_*`），而唯一的过滤终结跳转是链尾那条
            # `POP_JUMP_*_IF_FALSE`。段收集只在后者处切段 ⇒ 整窗仅一段，且
            # 段内弹跳目标落在窗中另一段的起点（上文的段切分不认这些起点）
            # ⇒ _b245 的落点分类失败、逐段重建只能看到被切碎的前导项。
            # 判据（I.4 白名单：块内 opcode 序 + 跳转目标）：窗内最后一个条件
            # 跳转的落点是跳过本轮（BACKWARD 或落在追加点之后）——这正是该
            # `if` 子句的终结跳转，其前方整段就是值位布尔链；把整窗交给
            # _b237_kop_window（其入口先调 _b247_mixed_boolchain），命中即整组
            # 归约并把元素起点定为终结跳转之后。非本族形态（前三元、链式比较、
            # 无 keep-or-pop 的纯 POP 链）由归约器自身返回 None ⇒ 逐位沿用
            # 既有通道（[C3] 封闭）。
            _b249_term = None
            for _b249_i in range(append_idx - 1, store_idx, -1):
                if all_instrs[_b249_i].opname in CONDITIONAL_JUMP_OPS:
                    _b249_term = _b249_i
                    break
            if _b249_term is not None:
                _b249_jmp = all_instrs[_b249_term]
                _b249_tgt = getattr(_b249_jmp, 'argval', None)
                _b249_skips = ('BACKWARD' in _b249_jmp.opname
                               or (_b249_tgt is not None
                                   and _b249_tgt >= append_offset))
                if _b249_skips:
                    _b249_expr = self._b237_kop_window(
                        all_instrs[store_idx + 1:_b249_term])
                    if _b249_expr is not None:
                        return [_b249_expr], _b249_term + 1
                # [B249-V3R53] 过滤位纯「假出口弹跳」链的 jump_if 文法归约
                # （见 _b249_jumpif_boolchain 的六项 docstring）：窗内全部
                # 跳转都是 POP_JUMP_*_IF_*，没有 keep-or-pop 族 ⇒ 上一条
                # 路由恒不命中（t993/t1203 等）。按 CPython `compiler_jump_if`
                # 的 BoolOp 递归文法自顶向下反向解析「段 + 跳转」序列，命中
                # 即整组归约、元素起点为终结跳转之后。非本族形态由该方法
                # 自身返回 None ⇒ 逐位沿用既有通道（[C3] 封闭）。
                _b249_jif = self._b249_filter_boolchain(
                    all_instrs, segments, store_idx, _b249_term)
                if _b249_jif is not None:
                    return [_b249_jif], _b249_term + 1

            # [R10] Detect OR-filter pattern: FORWARD IF_TRUE segment followed by
            # BACKWARD IF_FALSE segment means `if cond1 or cond2` filter.
            # CPython compiles `if cond1 or cond2` as:
            #   cond1 → POP_JUMP_FORWARD_IF_TRUE body (skip to body if cond1 true)
            #   cond2 → POP_JUMP_BACKWARD_IF_FALSE loop (skip iteration if cond2 false)
            # For OR filters, do NOT invert IF_TRUE conditions, combine with 'or'.
            is_or_pattern = False
            if len(segments) >= 2:
                has_forward_if_true = False
                has_backward_if_false = False
                for _, _, jump_instr in segments:
                    if 'FORWARD' in jump_instr.opname and 'IF_TRUE' in jump_instr.opname:
                        has_forward_if_true = True
                    if 'BACKWARD' in jump_instr.opname and 'IF_FALSE' in jump_instr.opname:
                        has_backward_if_false = True
                if has_forward_if_true and has_backward_if_false:
                    is_or_pattern = True

            for seg_start, seg_end, jump_instr in segments:
                cond_instrs = all_instrs[seg_start:seg_end]
                if cond_instrs:
                    # [B249-V3R53] 过滤器段的 keep-or-pop 短路建模：CPython 3.11
                    # 对过滤器位 `if <布尔链>` 在段内同样发射
                    # `A; JUMP_IF_FALSE_OR_POP <merge>; B; merge:`，且段内
                    # 还可能有前导压栈项（`'%s' % (x and y)` 的 `'%s'`）
                    # 与汇合点后的消费指令。不开该开关时 JUMP_IF_*_OR_POP
                    # 无分支 ⇒ 前导项静默留在栈上、链首操作数被当作后继
                    # 二元运算的操作数（产物 `if x % y`）。开关开启后由
                    # reconstruct 在汇合点 flush 成 BoolOp，前导项按正常
                    # 栈序参与后续消费，语义与字节码逐条一致。
                    cond_expr = self.expr_reconstructor.reconstruct(
                        cond_instrs, fold_boolop_keep_or_pop=True)
                    if cond_expr:
                        # [识别条件] None 恒等条件跳转 POP_JUMP_*_IF_NONE /
                        #   IF_NOT_NONE：CPython 把 `x is None` / `x is not None`
                        #   折叠成单条跳转，指令流里不再有 COMPARE_OP/IS_OP，
                        #   重建出来的 cond_expr 只有裸 x。
                        # [归约方式] 仅在非 OR 过滤（is_or_pattern 为假，即跳转
                        #   落空侧=跳过本轮，极性与 _fallthrough_cond_for_jump
                        #   同向）时按 opname 极性补回恒等比较：IF_NOT_NONE →
                        #   x is None、IF_NONE → x is not None。OR 过滤的前向
                        #   跳转 taken 侧是进循环体，极性相反，保持原样不改。
                        # [AST 映射] Compare(left=x, ops=[Is/IsNot],
                        #   comparators=[Constant(None)])；禁止降级成
                        #   UnaryOp('not', x)——None 之外还有 0/''/[] 等 falsy，
                        #   真值取反语义不等价，字节码也会退化成
                        #   UNARY_NOT + POP_JUMP_*_IF_FALSE。
                        if not is_or_pattern and 'IF_NOT_NONE' in jump_instr.opname:
                            cond_expr = {'type': 'Compare', 'left': cond_expr,
                                         'ops': [{'type': 'Is'}],
                                         'comparators': [{'type': 'Constant', 'value': None}]}
                        elif not is_or_pattern and 'IF_NONE' in jump_instr.opname:
                            cond_expr = {'type': 'Compare', 'left': cond_expr,
                                         'ops': [{'type': 'IsNot'}],
                                         'comparators': [{'type': 'Constant', 'value': None}]}
                        elif 'IF_TRUE' in jump_instr.opname:
                            if is_or_pattern and 'FORWARD' in jump_instr.opname:
                                pass
                            else:
                                cond_expr = {'type': 'UnaryOp', 'op': 'not', 'operand': cond_expr}
                        ifs.append(cond_expr)
                        # [B6-comp 混合 op 标注] 逐段按跳转方向标注组别 op：
                        # 前向 IF_TRUE=or 成员（真→进循环体）；回向 IF_TRUE=
                        # 取反 and 成员（not X：真→跳过本轮）；其余（前向/回向
                        # IF_FALSE、NONE 检查）=and 成员。与 BoolOpRegion
                        # op_chain 的方向标注同源（[C1] 同层块末 opcode 事实）。
                        seg_ops.append('or' if ('FORWARD' in jump_instr.opname
                                                and 'IF_TRUE' in jump_instr.opname) else 'and')
            elt_start_idx = current_start

        # Multiple if conditions in comprehension are connected by 'and' (short-circuit).
        # In Python bytecode, `if a and b` and `if a if b` produce identical bytecode,
        # so we combine multiple conditions into a single BoolOp to match the more common
        # source form and produce correct BoolOp AST nodes.
        # [R10] OR-filter pattern uses 'or' instead.
        if len(ifs) > 1:
            is_or_pattern = False
            if segments:
                has_forward_if_true = False
                has_backward_if_false = False
                for _, _, jump_instr in segments:
                    if 'FORWARD' in jump_instr.opname and 'IF_TRUE' in jump_instr.opname:
                        has_forward_if_true = True
                    if 'BACKWARD' in jump_instr.opname and 'IF_FALSE' in jump_instr.opname:
                        has_backward_if_false = True
                if has_forward_if_true and has_backward_if_false:
                    is_or_pattern = True
            op = 'or' if is_or_pattern else 'and'
            # [B6-comp 混合 op 分组] 识别条件：段跳转方向标注（seg_ops）与
            # ifs 一一对应且存在 and→or / or→and 组别边界（混合 and/or 过滤
            # 链，r1_21 实测 `if a and b or c`）。归约方式：or_groups 分组
            # ——and 绑定比 or 紧，连续同 op 段合并为 BoolOp、组间以 'or'
            # 连接，与 _build_boolop_expression_inner 的 segment 算法同一
            # 语义（[C2] 单 BoolOp 黑箱组合）。AST 映射：
            # ``A and B or C`` → BoolOp(or, [BoolOp(and,[A,B]), C])。
            # 全部段同 op 时走既有单 op 路径（逐位不变）。
            _b6_seg_ops = seg_ops if len(seg_ops) == len(ifs) else []
            _b6_mixed = bool(_b6_seg_ops) and any(o != _b6_seg_ops[0] for o in _b6_seg_ops)
            if not _b6_mixed:
                # [识别条件] 仅 and 链：segments 与 ifs 一一对应时，数出前缀里连续的
                #   「POP_JUMP_FORWARD_IF_FALSE」段数 p。该形态只在原源码把 and 链拆到
                #   两行时出现（同一行上 CPython 两条都回跳循环头），而单行产物必然
                #   两条都回跳，故 p>0 恒为当前失配单元，p==0 的单元（含全部金丝雀）
                #   一个字节都不改。
                # [归约方式] 把第 p-1 个操作数渲染成「原文 + 换行 + 续行缩进」的原始
                #   文本（_and_operand_raw_text，渲染失败返回 None 则保持单行），
                #   换行正好落在第 p-1 与第 p 个操作数之间，使重编译时这两行分界
                #   复现原 pyc 的前向/回跳方向。
                # [AST 映射] 外层仍是 BoolOp(op, values)，仅 values[p-1] 换成
                #   Name(原始文本)——发射侧对 Name 原样输出 id，重编译回
                #   BoolOp(and, [...])，与单行版同一 AST 形状。
                if op == 'and' and segments and len(segments) == len(ifs):
                    split_at = 0
                    for _, _, lead_jump in segments[:-1]:
                        if 'FORWARD' in lead_jump.opname and 'IF_FALSE' in lead_jump.opname:
                            split_at += 1
                        else:
                            break
                    if split_at:
                        raw_text = _and_operand_raw_text(ifs[split_at - 1])
                        if raw_text is not None:
                            ifs = list(ifs)
                            ifs[split_at - 1] = {'type': 'Name', 'id': raw_text}
                ifs = [{'type': 'BoolOp', 'op': op, 'values': ifs}]
            else:
                # [B98-V3R2 or-prefix 过滤器组] 识别条件（I.4 白名单：段起始
                # 偏移 + 段末跳转 opcode/目标）：is_or_pattern 成立，且存在
                # 边界 t（2 <= t < len(segments)）——前 t-1 段的条件跳转均为
                # FORWARD IF_TRUE 且目标同为第 t 段起始偏移（真值边落到后续
                # 条件检查而非元素产出），第 t 段起全部段标注为 'and'（尾部
                # 纯 and 链）。CPython 对显式括号的 ``(A or B) and C`` 生成该
                # 形态：A 真→跳到 C 检查、B 假→跳过本轮、C 假→跳过本轮；
                # 而无括号 ``A or B and C`` 的 A 真边直达元素产出（目标不是
                # 段起始，也不满足 < 段数边界），不会命中（[C3] 显式封闭）。
                # 归约方式：前 t 段合成 or 组 BoolOp(or, [...])，与后续 and
                # 段整体由 'and' 连接（单 BoolOp，[C2]）。
                # AST 映射：And[Or[A,B], C, ...]，重编译回同一字节码形态。
                _b6_opr_t = None
                if is_or_pattern and segments and len(segments) == len(ifs) and len(segments) >= 3:
                    for _b6_opr_cand in range(2, len(segments)):
                        _b6_opr_cand_off = all_instrs[segments[_b6_opr_cand][0]].offset
                        _b6_opr_ok = True
                        for _b6_opr_k in range(_b6_opr_cand - 1):
                            _b6_opr_j = segments[_b6_opr_k][2]
                            if not ('FORWARD' in _b6_opr_j.opname
                                    and 'IF_TRUE' in _b6_opr_j.opname
                                    and _b6_opr_j.argval == _b6_opr_cand_off):
                                _b6_opr_ok = False
                                break
                        if not _b6_opr_ok:
                            continue
                        if any(_b6_seg_ops[_b6_opr_k2] != 'and'
                               for _b6_opr_k2 in range(_b6_opr_cand, len(_b6_seg_ops))):
                            continue
                        _b6_opr_t = _b6_opr_cand
                        break
                if _b6_opr_t is not None:
                    _b6_opr_vals = list(ifs[:_b6_opr_t])
                    _b6_opr_node = ({'type': 'BoolOp', 'op': 'or', 'values': _b6_opr_vals}
                                    if len(_b6_opr_vals) > 1 else _b6_opr_vals[0])
                    ifs = [{'type': 'BoolOp', 'op': 'and',
                            'values': [_b6_opr_node] + list(ifs[_b6_opr_t:])}]
                else:
                    or_groups = []
                    cur_op = None
                    cur_vals = []
                    for val, o in zip(ifs, _b6_seg_ops):
                        if cur_op is None:
                            cur_op = o
                            cur_vals = [val]
                        elif o == cur_op:
                            cur_vals.append(val)
                        elif cur_op == 'and' and o == 'or':
                            cur_vals.append(val)
                            or_groups.append({'type': 'BoolOp', 'op': cur_op, 'values': cur_vals})
                            cur_op = None
                            cur_vals = []
                        else:
                            or_groups.append({'type': 'BoolOp', 'op': cur_op, 'values': cur_vals}
                                             if len(cur_vals) > 1 else cur_vals[0])
                            cur_op = o
                            cur_vals = [val]
                    if cur_vals:
                        or_groups.append({'type': 'BoolOp', 'op': cur_op, 'values': cur_vals}
                                         if len(cur_vals) > 1 else cur_vals[0])
                    result = None
                    for gnode in reversed(or_groups):
                        result = gnode if result is None else {'type': 'BoolOp', 'op': 'or', 'values': [gnode, result]}
                    ifs = [result]

        return ifs, elt_start_idx

    def _b245_comp_filter_chain(self, all_instrs: List[Instruction],
                                segments: List[Tuple[int, int, Any]],
                                elt_idx: int,
                                append_idx: int) -> Optional[Dict[str, Any]]:
        """[B245-V3R49] 推导式过滤条件的「短路跳转链」整组归约。

        ①算法依据（CPython 3.11 值栈/跳转纪律）：过滤条件是一串条件跳转，
        每条跳转的**目标**给出它被命中时的落点——落到元素起点即本轮通过
        （pass）、落到循环头或循环体末尾即跳过本轮（skip）。据此可把整串
        跳转递归还原成右嵌套布尔式：pass 段贡献 `or` 项、skip 段贡献 `and`
        项，末段按「落穿即通过」取反极性。`not (A and B)` 类取反式因此不再
        被误读成 `A and not B`（旧行为只按跳转极性给项、不看目标，把
        pass 段的 `IF_FALSE` 当成 and 成员）。
        ②归约顺序：自末段向前逐段累积——先定末段项，再把每段按其落点类别
        与累积值合成同运算符的右嵌套 BoolOp（同 op 按结合律并入同一
        BoolOp，避免多余括号改变重编译跳转极性）。
        ③唯一归属判定：仅当**每个**前向跳转的目标都等于元素起点或落点在
        追加点之后（循环体末尾）时才接管整窗；出现任何中间目标（跳转到
        另一段起点 = or 前缀握手、或三元内部）即返回 None，交既有通道
        （C3 封闭）。段集合按 (段起, 段末, 跳转) 三元组唯一归属，不产生
        游离指令。
        ④嵌套处理：各段的操作数为无跳转指令串，整体交重建器还原；同族
        括号嵌套（`a and (b or c)`）由右嵌套 BoolOp 直接表达，不再展开。
        ⑤AST 映射接口：返回单个 BoolOp/UnaryOp/Compare 节点，调用方把它
        作为该推导式的唯一过滤条件；None 表示不接管。
        ⑥反编译流程：CPython 3.11 对 `if a and not (b and c)` 发射
        `a → POP_JUMP_BACKWARD_IF_FALSE <head>`、`b → POP_JUMP_FORWARD_IF_FALSE
        <elt>`、`c → POP_JUMP_BACKWARD_IF_TRUE <head>`；旧通道只看极性，
        产出 `a and b and not c`（语义错）。本方法按目标分类后给出
        `a and (not b or not c)`，重编译回同一跳转序列。
        [C1] 只读同层段边界、跳转 opcode 与 argval（结构事实），不读
        用户名/常量值，无偏移魔数；[C2] 段≥2 且全为前置过滤段，整窗黑箱
        组合，不改动其它区域；[C3] 任何非本族形态（链式比较、握手跳转、
        单段、重建失败）一律返回 None，调用方逐位沿用旧路径。
        """
        if not segments or len(segments) < 2:
            return None
        if elt_idx >= len(all_instrs) or append_idx >= len(all_instrs):
            return None
        _elt_off = all_instrs[elt_idx].offset
        _append_off = all_instrs[append_idx].offset
        _starts = {all_instrs[_s].offset: _k
                   for _k, (_s, _e, _j) in enumerate(segments)}
        # 每段的跳转落点分类：pass（元素起点）/ skip（循环头或体尾）/
        # 握手（另一段起点，值为该段序号）。链式比较与未知落点一律交既有通道。
        _dests: List[Any] = []
        for _seg_s, _seg_e, _jmp in segments:
            _instrs = all_instrs[_seg_s:_seg_e]
            if not _instrs:
                return None
            for _ci in range(len(_instrs) - 1):
                if (_instrs[_ci].opname == 'COPY' and _instrs[_ci].arg == 2
                        and _instrs[_ci + 1].opname in
                        ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP')):
                    return None
            _tgt = getattr(_jmp, 'argval', None)
            if 'BACKWARD' in _jmp.opname:
                _dests.append('skip')
                continue
            if _tgt is None:
                return None
            if _tgt == _elt_off:
                _dests.append('pass')
            elif _tgt >= _append_off:
                _dests.append('skip')
            elif _tgt in _starts:
                _dests.append(_tgt)
            else:
                return None
        if 'pass' not in _dests and not any(
                isinstance(_d, int) for _d in _dests):
            return None

        def _cmp_node(cond: Dict[str, Any], is_not_none: bool) -> Dict[str, Any]:
            return {'type': 'Compare', 'left': cond,
                    'ops': [{'type': 'IsNot' if is_not_none else 'Is'}],
                    'comparators': [{'type': 'Constant', 'value': None}]}

        def _not(node: Dict[str, Any]) -> Dict[str, Any]:
            return {'type': 'UnaryOp', 'op': 'not', 'operand': node}

        def _falsify(node: Dict[str, Any]) -> Dict[str, Any]:
            # ¬T 化简：T 已是 not X 时直接取 X，避免双重取反多一条 UNARY_NOT。
            if isinstance(node, dict) and node.get('type') == 'UnaryOp' \
                    and node.get('op') == 'not':
                return node['operand']
            return _not(node)

        def _combine(op: str, left: Dict[str, Any],
                     right: Dict[str, Any]) -> Dict[str, Any]:
            if (isinstance(right, dict) and right.get('type') == 'BoolOp'
                    and right.get('op') == op):
                return {'type': 'BoolOp', 'op': op,
                        'values': [left] + list(right['values'])}
            return {'type': 'BoolOp', 'op': op, 'values': [left, right]}

        # 逐段落成「命中字面量」T 与其取反 ¬T：正常跳转为 cond/not cond，
        # None 检查转 Is/IsNot（与既有通道的 Compare 映射同源）。
        _taken: List[Optional[Dict[str, Any]]] = []
        for _seg_s, _seg_e, _jmp in segments:
            _cond = self.expr_reconstructor.reconstruct(all_instrs[_seg_s:_seg_e])
            if not _cond:
                return None
            _opname = _jmp.opname
            if 'IF_NOT_NONE' in _opname:
                _taken.append(_cmp_node(_cond, True))
            elif 'IF_NONE' in _opname:
                _taken.append(_cmp_node(_cond, False))
            elif 'IF_TRUE' in _opname:
                _taken.append(_cond)
            else:
                _taken.append(_not(_cond))
        _falsified = [_falsify(_t) for _t in _taken]
        _n = len(segments)

        def _parse(_i: int) -> Optional[Dict[str, Any]]:
            """[B245-V3R49] 自 i 起的短路链递归还原（含握手分组）。

            [识别条件] `_dests[i]` 为 'pass'/'skip' 时按落点直接给项；为该
            链内另一段起点偏移（握手）时，把 i..j-1 视为一个子表达式：
            末段（j-1）命中 → 'skip' 记 or 组、→ 'pass' 记 and 组，其余成员
            命中落点必须同为 j（[C1] 同层跳转目标事实）。
            [归约方式] or 组按「成员命中 = 组真、末段命中 = 组假」取项
            `T_i … ¬T_{j-1}`；and 组按「成员命中 = 组假、末段命中 = 组真」
            取项 `¬T_i … T_{j-1}`。组真后继续在 j 求值 ⇒ 与后续 'and' 合成；
            组假后继续在 j 求值 ⇒ 与后续 'or' 合成。
            [AST 映射] 返回 BoolOp/UnaryOp/Compare 节点；None 表示形态不属
            本族，调用方逐位沿用旧路径（[C3]）。
            """
            if _i >= _n:
                return None
            if _i == _n - 1:
                return _falsified[_i]
            _d = _dests[_i]
            if _d in ('pass', 'skip'):
                _rest = _parse(_i + 1)
                if _rest is None:
                    return None
                if _d == 'pass':
                    return _combine('or', _taken[_i], _rest)
                return _combine('and', _falsified[_i], _rest)
            _j = _starts[_d]
            if _j <= _i + 1:
                return None
            _last_dest = _dests[_j - 1]
            if any(_dests[_k] != _d for _k in range(_i, _j - 1)):
                return None
            if _last_dest == 'skip':
                _vals = [_taken[_k] for _k in range(_i, _j - 1)]
                _vals.append(_falsified[_j - 1])
                _group_op = 'or'
            elif _last_dest == 'pass':
                _vals = [_falsified[_k] for _k in range(_i, _j - 1)]
                _vals.append(_taken[_j - 1])
                _group_op = 'and'
            else:
                return None
            _group = {'type': 'BoolOp', 'op': _group_op, 'values': _vals}
            _rest = _parse(_j)
            if _rest is None:
                return None
            return _combine('and' if _group_op == 'or' else 'or',
                            _group, _rest)

        return _parse(0)

    def _b249_jumpif_boolchain(self,
                               segs: List[List[Instruction]],
                               jumps: List[Instruction],
                               skip_off: int,
                               tail_off: int) -> Optional[Dict[str, Any]]:
        """[B249-V3R53] 跳转判定位（过滤位 / 三元 test 位）的布尔链整组还原。

        ①算法依据（CPython 3.11 `compiler_jump_if` 纪律）：`if <E>` 与
        `t if <E> else f` 的 test 位都编译为 `compiler_jump_if(E, next, 0)`，
        next 是「判定失败」块（过滤位 = 跳过本轮、test 位 = 假值区）。该函数
        对 BoolOp 递归：`cond2 = (op == 'or')`；cond2 与 cond 不同时新建
        next2 块（位置恰在本组**最后一个成员之后**），前 n-1 个成员以
        (next2, cond2) 递归、末成员以 (next, cond) 递归；cond2 == cond 时
        不建块，全员共用 next。`UnaryOp not` 只翻转 cond。故整条链的
        「段 + 跳转」序列可按同一文法反向解析：段是直线求值串，每段一条
        条件跳转，其**落点**与**极性**唯一给出该段在文法里的位置。
        ②归约方式：自顶向下 `_parse(i, end, next, cond)`。单段即叶子：落点
        必须等于 next，极性等于 cond 时取该项、否则取该项的取反（`not` 由
        极性翻转表达；IF_NONE/IF_NOT_NONE 按 Is/IsNot 映射，与既有通道同源，
        避免双重取反多出 UNARY_NOT）。多段则枚举 cond2 ∈ {0,1} 与成员数 k，
        按成员边界切分：前 k-1 成员以 (next2, cond2) 递归、末成员以
        (next, cond) 递归，全部成功即按 `op = 'or' if cond2 else 'and'` 合成；
        同运算符嵌套按结合律并入同一 BoolOp（多出一层括号会改变重编译的
        跳转极性）。
        ③唯一归属判定：段序列必须从窗首起**连续无洞**（段末 + 1 == 下段起），
        且窗内除段跳转外不含无条件跳转；不满足即返回 None。每个段恰被一个
        成员引用一次，不产生游离指令。
        ④嵌套处理：成员自身可为叶子、组或被 `not` 包裹的组，深度即递归层数；
        段内表达式整体交既有重建器黑箱还原（含 keep-or-pop 子窗）。
        ⑤AST 映射接口：返回单个 BoolOp/UnaryOp/Compare 节点。顶层以 cond=0
        解析失败而 cond=1 成功时，文法含义变为「真即失败」⇒ 返回
        `not <结果>`，与源码 `if not (...)` 重编译字节码相同。
        ⑥反编译流程：CPython 3.11 对 `if (x and (y or z) or w)` 发射
        `x → IF_FALSE <w>`、`y/z → IF_TRUE <元素>`、`w → IF_FALSE <跳过本轮>`。
        既有 [B245] 握手模型要求同组成员落点全等（`x` 落 w、`y/z` 落元素），
        据此判定失败 ⇒ 旧产物丢 `(y or z)` 或整链退化。
        [C1] 只读段边界、跳转 opcode/argval 与段内指令（同层结构事实），
        不读用户名/常量值，无偏移魔数、无条数上限；[C2] 各段表达式交既有
        重建器黑箱还原，整窗只产出一个节点；[C3] 落点不匹配、切分不成立、
        重建失败一律返回 None，调用方逐位沿用既有通道。
        """
        _n = len(segs)
        if _n < 1 or len(jumps) != _n:
            return None

        def _cmp(node: Dict[str, Any], is_not_none: bool) -> Dict[str, Any]:
            return {'type': 'Compare', 'left': node,
                    'ops': [{'type': 'IsNot' if is_not_none else 'Is'}],
                    'comparators': [{'type': 'Constant', 'value': None}]}

        _taken: List[Optional[Dict[str, Any]]] = []
        for _seg, _jmp in zip(segs, jumps):
            _c = self.expr_reconstructor.reconstruct(
                _seg, fold_boolop_keep_or_pop=True)
            if not _c:
                return None
            if 'IF_NOT_NONE' in _jmp.opname:
                _taken.append(_cmp(_c, True))
            elif 'IF_NONE' in _jmp.opname:
                _taken.append(_cmp(_c, False))
            elif 'IF_TRUE' in _jmp.opname:
                _taken.append(_c)
            else:
                _taken.append({'type': 'UnaryOp', 'op': 'not', 'operand': _c})
        _falsified: List[Optional[Dict[str, Any]]] = []
        for _k, _t in enumerate(_taken):
            _jop = jumps[_k].opname
            if 'IF_NOT_NONE' in _jop:
                _falsified.append(_cmp(_taken[_k]['left'], False))
            elif 'IF_NONE' in _jop:
                _falsified.append(_cmp(_taken[_k]['left'], True))
            elif isinstance(_t, dict) and _t.get('type') == 'UnaryOp' \
                    and _t.get('op') == 'not':
                _falsified.append(_t['operand'])
            else:
                _falsified.append({'type': 'UnaryOp', 'op': 'not',
                                   'operand': _t})
        _starts = [_seg[0].offset for _seg in segs]

        def _tail_of(_k: int) -> Optional[int]:
            return _starts[_k] if _k < _n else tail_off

        def _merge(op: str, _vals: List[Dict[str, Any]]) -> Dict[str, Any]:
            _flat: List[Dict[str, Any]] = []
            for _v in _vals:
                if (isinstance(_v, dict) and _v.get('type') == 'BoolOp'
                        and _v.get('op') == op):
                    _flat.extend(list(_v.get('values') or []))
                else:
                    _flat.append(_v)
            if len(_flat) == 1:
                return _flat[0]
            return {'type': 'BoolOp', 'op': op, 'values': _flat}

        def _splits(_a: int, _b: int, _k: int):
            if _k == 1:
                yield [(_a, _b)]
                return
            for _cut in range(_a + 1, _b - _k + 2):
                for _rest in _splits(_cut, _b, _k - 1):
                    yield [(_a, _cut)] + _rest

        _memo: Dict[Tuple[int, int, int, int], Any] = {}

        def _parse(_i: int, _end: int, _next_off: int,
                   _cond: int) -> Optional[Dict[str, Any]]:
            _key = (_i, _end, _next_off, _cond)
            if _key in _memo:
                return _memo[_key]
            _memo[_key] = None
            if _i >= _end:
                return None
            if _end - _i == 1:
                if getattr(jumps[_i], 'argval', None) != _next_off:
                    return None
                # 叶子：`compiler_jump_if(S, next, cond)` 只在「S 的真假等于
                # cond」时跳到 next。cond=1 ⇒ S 就是「跳转已发生」的谓词
                # （_taken）；cond=0 ⇒ S 是它的取反（_falsified，已化简掉
                # 双重取反，避免多发射 UNARY_NOT）。
                _res = _taken[_i] if _cond == 1 else _falsified[_i]
                _memo[_key] = _res
                return _res
            for _cond2 in (0, 1):
                _next2 = _next_off if _cond2 == _cond else _tail_of(_end)
                if _next2 is None:
                    continue
                for _k in range(2, _end - _i + 1):
                    for _bounds in _splits(_i, _end, _k):
                        _vals: List[Dict[str, Any]] = []
                        _ok = True
                        for _m, (_a, _b) in enumerate(_bounds):
                            _e = (_parse(_a, _b, _next_off, _cond)
                                  if _m == _k - 1
                                  else _parse(_a, _b, _next2, _cond2))
                            if _e is None:
                                _ok = False
                                break
                            _vals.append(_e)
                        if _ok:
                            _res = _merge('or' if _cond2 else 'and', _vals)
                            _memo[_key] = _res
                            return _res
            return None

        _expr = _parse(0, _n, skip_off, 0)
        if _expr is None:
            _expr = _parse(0, _n, skip_off, 1)
            if _expr is not None:
                _expr = {'type': 'UnaryOp', 'op': 'not', 'operand': _expr}
        return _expr

    def _b249_filter_boolchain(self, all_instrs: List[Instruction],
                               segments: List[Tuple[int, int, Any]],
                               store_idx: int, term_idx: int
                               ) -> Optional[Dict[str, Any]]:
        """[B249-V3R53] 过滤位的跳转判定位布尔链调用适配。

        [识别条件] 仅当段集合恰覆盖 `store_idx+1 .. term_idx`（段末 + 1 ==
        下段起，最后一段的跳转就是终止跳转）且窗内无无条件跳转时接管——
        无条件跳转意味着窗内另有经典三元结构，交既有通道（[C3] 封闭）。
        [归约方式] 把段/跳转原样交给 `_b249_jumpif_boolchain`，终止跳转的
        落点作「判定失败」next、其**后一条指令**（元素起点）作「落穿」tail。
        [AST 映射] 直接返回该方法给出的单一节点；None 表示不接管。
        [C1] 只读段边界与跳转 argval；[C2] 段内表达式黑箱；[C3] 不满足
        连续性/无洞条件或越界一律 None。
        """
        if not segments or term_idx + 1 >= len(all_instrs):
            return None
        if segments[0][0] != store_idx + 1:
            return None
        if segments[-1][1] != term_idx:
            return None
        if segments[-1][2] is not all_instrs[term_idx]:
            return None
        for _k in range(len(segments) - 1):
            if segments[_k][1] + 1 != segments[_k + 1][0]:
                return None
        _skip = getattr(all_instrs[term_idx], 'argval', None)
        if _skip is None:
            return None
        for _k in range(store_idx + 1, term_idx):
            if all_instrs[_k].opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                         'JUMP_BACKWARD',
                                         'JUMP_BACKWARD_NO_INTERRUPT'):
                return None
        _segs = [all_instrs[_s:_e] for _s, _e, _j in segments]
        _jumps = [_j for _s, _e, _j in segments]
        return self._b249_jumpif_boolchain(
            _segs, _jumps, _skip, all_instrs[term_idx + 1].offset)

    def _b249_test_boolchain(self, all_instrs: List[Instruction],
                             seg_start: int, append_idx: int
                             ) -> Optional[Tuple[Dict[str, Any], int]]:
        """[B249-V3R53] 三元 test 位的跳转判定位布尔链调用适配。

        [识别条件] test 窗内取全部前向条件跳转为段边界，链路必须自
        `seg_start` 起连续无洞、且在「首段到末跳」区间内不含无条件跳转
        （含无条件跳转说明窗内另有经典三元结构，交既有通道，[C3] 封闭）。
        末跳的下一条指令即真值区起点（「落穿」tail），其 `argval` 即假值区
        起点（「判定失败」next），并要求 `tail < next`（真值区在前）。
        [归约方式] 把段/跳转原样交给 `_b249_jumpif_boolchain`，`next` 取
        末跳 `argval`、`tail` 取末跳后一条指令偏移——与过滤位同一条
        `compiler_jump_if(E, next, 0)` 文法，只是 next 由「跳过本轮」换成
        「假值区入口」。
        [AST 映射] 返回（单一 BoolOp/UnaryOp/Compare 节点, 末跳索引）；调用
        方以该节点作 IfExp.test、以末跳索引切出真值区/假值区。
        [C1] 只读段边界、跳转 opcode 与 argval；[C2] 段内表达式黑箱重建；
        [C3] 跳转少于两条、越界、含无条件跳转、落点不匹配一律 None。
        """
        # [B254-V3R56] 与 [B248-V3R52] 同一结构事实：test 链的可解析区间止于
        # 窗内第一条无条件跳转（真值臂末尾的 `JUMP_FORWARD <merge>`），其后的
        # 条件跳转属于假值臂内嵌套区域。整窗收段会把链尾定到嵌套区域的跳转上，
        # 违反 `tail < next` 门 ⇒ 恒返回 None（实测同 `base64._85encode`）。
        _cuts: List[int] = []
        for _k in range(seg_start, append_idx):
            if all_instrs[_k].opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                         'JUMP_BACKWARD',
                                         'JUMP_BACKWARD_NO_INTERRUPT'):
                break
            if (all_instrs[_k].opname in CONDITIONAL_JUMP_OPS
                    and 'BACKWARD' not in all_instrs[_k].opname
                    and all_instrs[_k].argval is not None):
                _cuts.append(_k)
        if len(_cuts) < 2 or _cuts[-1] + 1 >= len(all_instrs):
            return None
        _last = _cuts[-1]
        _tail = all_instrs[_last + 1].offset
        _next = all_instrs[_last].argval
        if _tail >= _next:
            return None
        for _k in range(seg_start, _last):
            if all_instrs[_k].opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                         'JUMP_BACKWARD',
                                         'JUMP_BACKWARD_NO_INTERRUPT'):
                return None
        _bounds = [seg_start] + [_k + 1 for _k in _cuts]
        _segs = [all_instrs[_a:_b]
                 for _a, _b in zip(_bounds[:-1], _bounds[1:])]
        if any(not _s for _s in _segs):
            return None
        _expr = self._b249_jumpif_boolchain(
            _segs, [all_instrs[_k] for _k in _cuts], _next, _tail)
        if _expr is None:
            return None
        return _expr, _last

    def _b248_ternary_test_chain(self, all_instrs: List[Instruction],
                                 seg_start: int,
                                 append_idx: int) -> Optional[Tuple[Dict[str, Any], int]]:
        """[B248-V3R52] 推导式三元 test 位的短路跳转链整组归约。

        ①算法依据（CPython 3.11 跳转纪律）：三元 test 位的布尔链与过滤位同构——
        每条条件跳转的**目标**给出它被命中时的落点：落到真值区起点即本次判定为真
        （pass）、落到假值区起点即判定为假（skip）、落到另一段起点即把当前子链
        交给外层继续求值（握手，值为该段序号）。既有 [R67-fix2] 只接受「全部
        中间跳转共享同一假出口」的 and 链（`x and y`），其余形态（or 链、混合
        链、握手嵌套）退回单段重建 ⇒ 链上操作数整段丢失或只取末项。
        ②归约顺序：按跳转把 test 窗切成「段 + 跳转」序列，每段自身是无跳转的
        直线求值串，整体交重建器还原；再按落点类别自末段向前右嵌套累积——pass
        段贡献 or 项、skip 段贡献 and 项，末段按「落穿即真」取反极性；握手段
        把 i..j-1 组成的子链与其后的续接部分合成（同运算符按结合律并入，避免
        多余括号改变重编译跳转极性）。
        ③唯一归属判定：段集合按（段起, 段末, 跳转）三元组唯一归属；任一跳转
        落点不在 {真值区起点, 假值区起点, 窗内段起点} 即不接管（[C3] 封闭），
        由调用方沿用既有单段路径。
        ④嵌套处理：同族括号嵌套（`x and (y or z)`）由右嵌套 BoolOp 与握手分组
        直接表达，不展开、不重排。
        ⑤AST 映射接口：返回 (单个 BoolOp/UnaryOp/Compare 节点, 链尾跳转索引)，
        调用方以该节点作 IfExp.test，并以链尾跳转索引切出真值区/假值区。
        ⑥反编译流程：CPython 3.11 对 `1 if x or y else 0` 发射
        `x → POP_JUMP_FORWARD_IF_TRUE <真值区>`、`y → POP_JUMP_FORWARD_IF_FALSE
        <假值区>`；旧通道在首条前向跳转处 break，cond_instrs 只切到第一个操作数，
        产物退化为 `y if not x else 0`。
        [C1] 只读同层指令 opcode / 跳转 argval / 段边界（结构事实），不读用户名
        与常量值，无偏移魔数；[C2] 每段唯一归属于 test 的一个操作数，段内整体
        交既有重建器，父区域不重入；[C3] 单跳（无链）、落点未知、任一段落
        重建失败一律返回 None，调用方逐位沿用原路径。
        """
        # [B254-V3R56] test 链的可解析区间止于**窗内第一条无条件跳转**：
        # 三元 test 位按 `compiler_jump_if(E, 假值区, 0)` 编译，链尾跳转之后
        # 紧跟真值臂，真值臂以 `JUMP_FORWARD <merge>` 收尾（A2 形态）；此后的
        # 条件跳转属于假值臂内嵌套的另一个三元/过滤器，与本次 test 链无关。
        # 调用方传入的窗口是「元素起点 .. 追加点」整窗，内含嵌套三元的全部
        # 跳转，若不截断，链尾唯一性门会把真值臂起点误判为「链中间」（实测
        # `base64._85encode` 的 `[b'z' if foldnuls and not word else ...]`，
        # 门在首跳处否决整条 `foldnuls and not word`，回落到只取末段的
        # 单段重建 ⇒ 产物丢 `foldnuls and`）。
        # ①识别条件（I.4 白名单：同层 opcode）：无条件跳转族四条 opcode。
        # ②归约顺序：只在该边界之前收段/跳转，边界之后逐字不读。
        # ③唯一归属：边界之后的条件跳转归假值臂的嵌套区域，本方法不引用。
        # ④嵌套处理：嵌套三元由假值臂递归通道（[B252]/既有 false 递归）归约。
        # ⑤入口引用：本方法仍只返回 test 这一个节点 + 链尾索引。
        # ⑥反编译流程：见上例（`<listcomp>` 15 vs 17 指令）。
        # 窗内无无条件跳转时区间即整窗，判据与归约逐位不变（C3）。
        _jump_idx: List[int] = []
        for _k in range(seg_start, append_idx):
            if all_instrs[_k].opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                         'JUMP_BACKWARD',
                                         'JUMP_BACKWARD_NO_INTERRUPT'):
                break
            if (all_instrs[_k].opname in CONDITIONAL_JUMP_OPS
                    and 'BACKWARD' not in all_instrs[_k].opname
                    and all_instrs[_k].argval is not None):
                _jump_idx.append(_k)
        if len(_jump_idx) < 2:
            return None
        # [B249-V3R53] 链尾唯一性门：段由跳转切分 ⇒ 任何「非末跳」的下一条
        # 指令必是某段起点。若 `_true_off` 落在这些段起点上，说明该跳转不是
        # 链尾（真值区尚未开始），继续向前找会得到错位的 test（实测 t265
        # `(x or y) and z or (w and v)` 在中间跳转处收尾，产物 test 退化为
        # `(not x and not y) or not z`）。只允许真值区起点不属于任何段起点。
        _seg_starts = {all_instrs[_b].offset
                       for _b in [seg_start] + [_k + 1 for _k in _jump_idx[:-1]]
                       if _b < len(all_instrs)}
        for _li in range(len(_jump_idx) - 1, 0, -1):
            _last = _jump_idx[_li]
            if _last + 1 >= len(all_instrs):
                continue
            _true_off = all_instrs[_last + 1].offset
            _false_off = all_instrs[_last].argval
            if _true_off >= _false_off or _true_off in _seg_starts:
                continue
            _cuts = [k for k in _jump_idx if k <= _last]
            _bounds = [seg_start] + [k + 1 for k in _cuts]
            _segs = [all_instrs[a:b] for a, b in zip(_bounds[:-1], _bounds[1:])]
            if any(not _s for _s in _segs):
                continue
            _starts: Dict[int, int] = {}
            for _i, _s in enumerate(_segs):
                _starts.setdefault(_s[0].offset, _i)
            _dests: List[Any] = []
            _ok = True
            for _i, _k in enumerate(_cuts):
                _tgt = all_instrs[_k].argval
                if _tgt == _true_off:
                    _dests.append('pass')
                elif _tgt == _false_off:
                    _dests.append('skip')
                elif _tgt in _starts and _starts[_tgt] > _i + 1:
                    _dests.append(_starts[_tgt])
                else:
                    _ok = False
                    break
            if not _ok:
                continue
            _expr = self._b248_chain_parse(
                _segs, [all_instrs[_k] for _k in _cuts], _dests)
            if _expr is not None:
                return _expr, _last
        return None

    def _b248_chain_parse(self, segs: List[List[Instruction]],
                          jumps: List[Instruction],
                          dests: List[Any]) -> Optional[Dict[str, Any]]:
        """[B248-V3R52] 三元 test 位短路链的右嵌套还原（握手下标递归）。

        [识别条件] dests[i] 为 'pass'/'skip' 时按落点直接给项；为链内另一段
        序号 j 时，i..j-1 构成一个子链：末段（j-1）落 'skip' 记 or 组、落
        'pass' 记 and 组，其余成员落点必须同为 j（[C1] 同层跳转目标事实）。
        [归约方式] or 组按「成员命中 = 组真、末段命中 = 组假」取项
        `T_i … ¬T_{j-1}`；and 组按「成员命中 = 组假、末段命中 = 组真」取项
        `¬T_i … T_{j-1}`。组真后继续在 j 求值 ⇒ 与后续 'and' 合成；组假后
        继续在 j 求值 ⇒ 与后续 'or' 合成。
        [AST 映射] 返回 BoolOp/UnaryOp/Compare 节点；None 表示形态不属本族，
        调用方沿用既有路径（[C3]）。
        [C1] 只读跳转 opcode 与落点分类；[C2] 各段整体交重建器黑箱还原；
        [C3] 空段、落点下标越界、重建失败一律返回 None。
        """
        _n = len(segs)
        if _n < 2:
            return None

        def _not(node: Dict[str, Any]) -> Dict[str, Any]:
            if (isinstance(node, dict) and node.get('type') == 'UnaryOp'
                    and node.get('op') == 'not'):
                return node['operand']
            return {'type': 'UnaryOp', 'op': 'not', 'operand': node}

        def _cmp(node: Dict[str, Any], is_node_not_none: bool) -> Dict[str, Any]:
            return {'type': 'Compare', 'left': node,
                    'ops': [{'type': 'IsNot' if is_node_not_none else 'Is'}],
                    'comparators': [{'type': 'Constant', 'value': None}]}

        def _combine(op: str, left: Dict[str, Any],
                     right: Dict[str, Any]) -> Dict[str, Any]:
            if (isinstance(right, dict) and right.get('type') == 'BoolOp'
                    and right.get('op') == op):
                return {'type': 'BoolOp', 'op': op,
                        'values': [left] + list(right['values'])}
            return {'type': 'BoolOp', 'op': op, 'values': [left, right]}

        _taken: List[Optional[Dict[str, Any]]] = []
        for _seg, _jmp in zip(segs, jumps):
            _cond = self.expr_reconstructor.reconstruct(_seg)
            if not _cond:
                return None
            if 'IF_NOT_NONE' in _jmp.opname:
                _taken.append(_cmp(_cond, True))
            elif 'IF_NONE' in _jmp.opname:
                _taken.append(_cmp(_cond, False))
            elif 'IF_TRUE' in _jmp.opname:
                _taken.append(_cond)
            else:
                _taken.append(_not(_cond))
        _falsified = [_not(_t) for _t in _taken]

        def _parse(_i: int) -> Optional[Dict[str, Any]]:
            if _i >= _n:
                return None
            if _i == _n - 1:
                return _falsified[_i]
            _d = dests[_i]
            if _d in ('pass', 'skip'):
                _rest = _parse(_i + 1)
                if _rest is None:
                    return None
                if _d == 'pass':
                    return _combine('or', _taken[_i], _rest)
                return _combine('and', _falsified[_i], _rest)
            _j = _d
            if not isinstance(_j, int) or _j <= _i + 1 or _j > _n:
                return None
            _last_dest = dests[_j - 1]
            if any(dests[_k] != _d for _k in range(_i, _j - 1)):
                return None
            if _last_dest == 'skip':
                _vals = [_taken[_k] for _k in range(_i, _j - 1)]
                _vals.append(_falsified[_j - 1])
                _group_op = 'or'
            elif _last_dest == 'pass':
                _vals = [_falsified[_k] for _k in range(_i, _j - 1)]
                _vals.append(_taken[_j - 1])
                _group_op = 'and'
            else:
                return None
            _group = {'type': 'BoolOp', 'op': _group_op, 'values': _vals}
            _rest = _parse(_j)
            if _rest is None:
                return None
            return _combine('and' if _group_op == 'or' else 'or',
                            _group, _rest)

        return _parse(0)

    @staticmethod
    def _b151_filter_stack_effect(instr) -> tuple:
        """[B151-V3R7] 过滤项表达式反扫用的 (push, pop) 栈效应表。

        ①算法依据：CPython 值栈纪律——表达式指令序列的净效果必须与
        「条件跳转弹出 1 个值」对齐；反扫时以 needed=1 为起点逐条回退，
        needed 首次 <= 0 处即该条件表达式的起点。
        ②归约顺序：_b151_parse_comp_filter_terms 的反扫循环调用。
        ③唯一归属判定：只按 opcode 族给表（LOAD_* 压 1；LOAD_ATTR/
        LOAD_METHOD 压 1 弹 1；COMPARE_OP/IS_OP/CONTAINS_OP/BINARY_OP/
        BINARY_SUBSCR 压 1 弹 2；UNARY_* 压 1 弹 1；BUILD_* 压 1 弹 arg；
        FORMAT_VALUE 压 1 弹 1 或 2；CALL 压 1 弹 arg+1；PRECALL/POP_TOP
        净 0；其余保守记 0）。
        ④嵌套处理：不涉及嵌套。
        ⑤AST 映射接口：返回 (push, pop) 二元组。
        ⑥反编译流程：仅供反扫定位表达式起点，不参与表达式本身的归约
        （表达式仍由 expr_reconstructor.reconstruct 生成）。
        [C1] 只读 opcode 族与 arg，不读文件名/偏移阈/条数上限；
        [C2] 纯静态表，无跨方法状态；[C3] 未列出的 opcode 保守记 0。
        """
        op = instr.opname
        if op in ('LOAD_ATTR', 'LOAD_METHOD'):
            return 1, 1
        if op.startswith('LOAD_') or op == 'COPY':
            return 1, 0
        if op in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP',
                  'BINARY_OP', 'BINARY_SUBSCR'):
            return 1, 2
        if op.startswith('UNARY_'):
            return 1, 1
        if op == 'FORMAT_VALUE':
            return 1, 1 if (instr.arg or 0) < 2 else 2
        if op == 'BUILD_STRING':
            return 1, instr.arg or 0
        if op == 'BUILD_CONST_KEY_MAP':
            return 1, (instr.arg or 0) + 1
        if op.startswith('BUILD_'):
            return 1, instr.arg or 0
        if op in ('PRECALL', 'POP_TOP'):
            return 0, 0
        if op == 'CALL':
            return 1, (instr.arg or 0) + 1
        return 0, 0

    def _b151_parse_comp_filter_terms(self, all_instrs: List[Instruction],
                                      start_idx: int,
                                      end_idx: int) -> Optional[List[tuple]]:
        """[B151-V3R7] 推导式过滤链的「项」级解析（链式比较之后的续段）。

        ①算法依据：CPython 3.11 把推导式过滤条件编译成若干「项」：一段
        表达式指令 + 一条条件跳转。项的跳转极性决定它在过滤链里的角色：
          - POP_JUMP_FORWARD_IF_TRUE（真→前向跳过本 or 组）：or 组成员；
          - POP_JUMP_FORWARD/BACKWARD_IF_FALSE（假→跳过本轮）：and 项，
            同时是它所属 or 组的最后一个成员。
        链式比较（`a < b < c`）的真值续接点是「比较链之后那条 JUMP_FORWARD
        的目标」——它跳过比较链的假值清理块（POP_TOP + JUMP_FORWARD），
        直接落到下一个过滤项的首条指令。
        ②归约顺序：_extract_comp_ifs 的链式比较分支在 early-return 之前
        调用；返回 None 表示「无后续项 / 形态不可判定」。
        ③唯一归属判定（全套 I.4 白名单）：
          (a) 续接点：start_idx 处若为 JUMP_FORWARD/JUMP_ABSOLUTE，则以其
              argval（目标偏移）为续接偏移；否则以 start_idx 处的指令偏移
              为续接偏移；目标偏移必须能在指令流中定位到下标。
          (b) 项边界：续接下标之后的第一条 CONDITIONAL_JUMP_OPS 指令为该
              项的判定跳转；该项的表达式指令由该跳转**反扫**确定（needed=1
              起步回退，needed 首次 <= 0 处为表达式起点），反扫下界不越过
              续接下标（不跨入前一项）。
          (c) 表达���可重建：反扫得到的指令子序列必须能被
              expr_reconstructor.reconstruct 归约成表达式节点，否则整体放弃。
          (d) 链尾：反扫/扫描下界为 end_idx（元素表达式的起点），不把元素
              表达式误当作过滤项。
        ④嵌套处理：不展开子区域；只读同一 code object 的指令流。
        ⑤AST 映射接口：返回 list[(expr_dict, jump_instr, expr_start_offset)]
        或 None（不可判定）。
        ⑥反编译流程：仅在链式比较分支被调用；返回 None 时调用方逐位沿用
        旧结果（C3 封闭）。
        [C1] 只读同层指令流的 opcode/argval/offset，不读文件名/函数名/
        偏移阈/条数上限；[C2] 不新增跨块跨方法状态；[C3] 上述四条判据任一
        不成立即返回 None。
        """
        if start_idx >= end_idx or start_idx >= len(all_instrs):
            return None
        cont_idx = start_idx
        _first = all_instrs[start_idx]
        if _first.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
            _tgt = _first.argval
            if not isinstance(_tgt, int):
                return None
            _found = None
            for _k in range(start_idx + 1, len(all_instrs)):
                if all_instrs[_k].offset == _tgt:
                    _found = _k
                    break
            if _found is None:
                return None
            cont_idx = _found
        if cont_idx >= end_idx:
            return None
        terms: List[tuple] = []
        idx = cont_idx
        while idx < end_idx:
            j = None
            k = idx
            while k < end_idx:
                if all_instrs[k].opname in CONDITIONAL_JUMP_OPS:
                    j = k
                    break
                k += 1
            if j is None:
                break
            needed = 1
            s = None
            for t in range(j - 1, idx - 1, -1):
                _push, _pop = self._b151_filter_stack_effect(all_instrs[t])
                needed = needed - _push + _pop
                if needed <= 0:
                    s = t
                    break
            if s is None:
                return None
            _expr = self.expr_reconstructor.reconstruct(all_instrs[s:j])
            if not _expr:
                return None
            terms.append((_expr, all_instrs[j], all_instrs[s].offset))
            idx = j + 1
        if not terms:
            return None
        return terms

    def _b151_compose_comp_filter_terms(self, terms: List[tuple]
                                        ) -> Optional[Dict[str, Any]]:
        """[B151-V3R7] 把解析出的过滤项组合成单一过滤表达式。

        ①算法依据：CPython 过滤链的求值语义——项按顺序求值，任一项为假
        即跳过本轮；一个「or 组」的成员是「真→前向跳过本组剩余成员」的
        项（POP_JUMP_FORWARD_IF_TRUE）与其后第一个「假→跳过本轮」的项。
        由此可判定的组合规则：
          (a) 一个 POP_JUMP_FORWARD_IF_TRUE 项开启一个 or 组；
          (b) 该 or 组的范围：从该项起，到「其跳转目标是某个后续项的
              表达式起点偏移」之前为止（这正是显式括号 `(A or B) and C`
              的形态——A 的真边直连 C 的检查起点）；若其跳转目标不是任何
              后续项的起点，则该 or 组延伸到过滤链末尾（`A or B and C`：
              A 的真边直连元素产出点，or 组右操作数是 `B and C`）；
          (c) or 组内：连续的 POP_JUMP_FORWARD_IF_TRUE 成员是 or 成员
              （`A or B or C`），其后余下的项以 'and' 组合成 or 组的最后
              一个操作数；
          (d) or 组之外的项以 'and' 串联成过滤链。
        ②归约顺序：_b151_parse_comp_filter_terms 之后调用；输入 None 时
        调用方逐位沿用旧结果。
        ③唯一归属判定（全套 I.4 白名单）：只读解析出的项元组（表达式、
        条件跳转 opcode/argval、表达式起点偏移）——即同层指令流的结构事实；
        不读文件名/函数名/偏移阈/条数上限。
        ④嵌套处理：项内表达式已由 expr_reconstructor 归约完毕，本方法只
        做 BoolOp 组合，不窥视表达式内部。
        ⑤AST 映射接口：返回单个表达式节点（BoolOp(and, [...]) 或其成员
        之一）；无法组合时返回 None。
        ⑥反编译流程：仅在链式比较分支被调用；None 时调用方沿用旧结果。
        [C1] 只读项元组；[C2] 不新增跨块跨方法状态；[C3] 组合规则逐条
        封闭，未命中即返回 None。
        """
        if not terms:
            return None

        def _is_or_head(jump) -> bool:
            return ('FORWARD' in jump.opname
                    and 'IF_TRUE' in jump.opname)

        n = len(terms)
        and_items: List[Dict[str, Any]] = []
        i = 0
        while i < n:
            _expr, _jump, _start = terms[i]
            if not _is_or_head(_jump):
                and_items.append(_expr)
                i += 1
                continue
            # or 组：从当前项起，到「跳转目标是某个后续项起点」之前
            grp: List[tuple] = []
            j = i
            tgt = _jump.argval
            while j < n:
                grp.append(terms[j])
                j += 1
                if j < n and isinstance(tgt, int) and terms[j][2] == tgt:
                    break
            last_true = -1
            for q, (_e2, _j2, _s2) in enumerate(grp):
                if _is_or_head(_j2):
                    last_true = q
            or_members = [grp[q][0] for q in range(0, last_true + 1)]
            trailing = [grp[q][0] for q in range(last_true + 1, len(grp))]
            if trailing:
                final = ({'type': 'BoolOp', 'op': 'and', 'values': trailing}
                         if len(trailing) > 1 else trailing[0])
                or_expr = {'type': 'BoolOp', 'op': 'or',
                           'values': or_members + [final]}
            else:
                or_expr = {'type': 'BoolOp', 'op': 'or', 'values': or_members}
            and_items.append(or_expr)
            i = j
        if len(and_items) > 1:
            return {'type': 'BoolOp', 'op': 'and', 'values': and_items}
        return and_items[0]

    def _extract_dict_comp_key_before_ternary(self, all_instrs: List[Instruction],
                                               store_idx: int,
                                               append_idx: int) -> Optional[Dict[str, Any]]:
        """Extract the dict key when a ternary is the dict value in a dict comprehension.

        When a dict comprehension has a ternary value (e.g., {k: v if v else 'N/A' for ...}),
        the key is pushed on the stack before the ternary condition. This method finds
        the key by using stack-effect-based backwards scanning from the conditional jump.
        """
        import dis
        from .region_analyzer import CONDITIONAL_JUMP_OPS

        # Find the conditional jump between store_idx+1 and append_idx
        # [B98-V3R2 键窗前导过滤器跳转甄别] 识别条件（I.4 白名单：同层指令
        # opcode）：三元条件跳转按定义是「前向跳到 false 值（true 值之后、
        # 追加点之前）」，BACKWARD 条件跳转只能是 `if 过滤器`（跳回 FOR_ITER）。
        # 寻找首个前向条件跳转作为三元 cond；不再把过滤器回跳误当 cond
        # （否则反推的键窗为空 ⇒ 键丢失）。无过滤器前导时首个条件跳转即
        # 前向跳转，逐位行为不变（[C3] 显式守卫）。
        cond_jump_idx = None
        for idx in range(store_idx + 1, append_idx):
            instr = all_instrs[idx]
            if instr.opname in CONDITIONAL_JUMP_OPS:
                if 'BACKWARD' in instr.opname:
                    continue
                cond_jump_idx = idx
                break
        if cond_jump_idx is None:
            return None

        # Use stack-effect-based backwards scan to find where the condition starts
        needed = 1  # Need 1 stack element for the condition (the jump pops 1)
        cond_start_idx = None
        for idx in range(cond_jump_idx - 1, store_idx, -1):
            instr = all_instrs[idx]
            try:
                effect = dis.stack_effect(instr.opcode, instr.arg)
            except Exception:
                effect = 0
            needed -= effect
            if needed <= 0:
                cond_start_idx = idx
                break
        if cond_start_idx is None:
            cond_start_idx = cond_jump_idx

        # Key instructions are from store_idx+1 to cond_start_idx (exclusive)
        # Skip STORE instructions
        key_instrs = []
        for idx in range(store_idx + 1, cond_start_idx):
            instr = all_instrs[idx]
            if instr.opname not in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL'):
                key_instrs.append(instr)

        if not key_instrs:
            return None

        return self.expr_reconstructor.reconstruct(key_instrs)

    def _extract_dict_comp_value_after_ternary(self, all_instrs: List[Instruction],
                                                store_idx: int,
                                                append_idx: int) -> Optional[Dict[str, Any]]:
        """[Round7-08] Extract the dict value when a ternary is the dict KEY.

        When a dict comprehension has a ternary key (e.g., `{(k if cond else m): v for ...}`),
        after the ternary's JUMP_FORWARD merge point, the value expression is pushed onto
        the stack before MAP_ADD consumes both. This method locates that merge point and
        reconstructs the value expression from the instructions between it and MAP_ADD.

        Returns None when there are no meaningful instructions between the merge point
        and MAP_ADD (i.e., the ternary is the value, not the key).
        """
        # Find the conditional jump between store_idx+1 and append_idx
        cond_jump_idx = None
        for idx in range(store_idx + 1, append_idx):
            instr = all_instrs[idx]
            if instr.opname in CONDITIONAL_JUMP_OPS:
                cond_jump_idx = idx
                break
        if cond_jump_idx is None:
            return None

        false_target_offset = all_instrs[cond_jump_idx].argval

        # Find JUMP_FORWARD within the true branch (between cond_jump and false_target)
        merge_offset = None
        for idx in range(cond_jump_idx + 1, append_idx):
            instr = all_instrs[idx]
            if instr.offset >= false_target_offset:
                break
            if instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD'):
                if hasattr(instr, 'argval') and instr.argval is not None:
                    merge_offset = instr.argval
                break
        if merge_offset is None:
            return None

        # Collect meaningful instructions between merge_offset and append_idx
        value_instrs = []
        for idx in range(cond_jump_idx + 1, append_idx):
            instr = all_instrs[idx]
            if instr.offset < merge_offset:
                continue
            if instr.offset >= all_instrs[append_idx].offset:
                break
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            value_instrs.append(instr)
        if not value_instrs:
            return None

        return self.expr_reconstructor.reconstruct(value_instrs)

    def _b247_mixed_boolchain(self, instrs: List[Instruction]) -> Optional[Dict[str, Any]]:
        """[B247-V3R51] 元素位「keep-or-pop + 假出口弹跳」混合布尔链整组归约。

        [识别条件]（I.4 白名单：同层指令 opcode / 跳转 argval，无名字或偏移阈值）
          (1) 窗内同时含 keep-or-pop 族（JUMP_IF_FALSE_OR_POP / JUMP_IF_TRUE_OR_POP）
              与前向假出口弹跳族（POP_JUMP_FORWARD_IF_FALSE / _IF_TRUE）两种跳转；
          (2) 窗内无任何无条件跳转（经典三元形的真分支必有 JUMP_FORWARD，其
              推进归既有三元通道）与其它条件跳转族（NONE / BACKWARD / 异常匹配）；
          (3) 每条弹跳的 argval 恰为窗内某段的起始偏移（弹跳只落到段起点，
              不落到表达式中部），每条 keep-or-pop 的 argval 大于自身偏移。
        [归约方式] CPython 3.11 的 BoolOp 以「每个非末位操作数后一条跳转」发射，
          跳转后即该节点的一段操作数。两类跳转的位置语义不同：keep-or-pop 的
          argval 是**取值点**（该节点的汇合点，在窗外汇合块之前），假出口弹跳的
          argval 是**续接点**（弹出该操作数后父链从这里继续求值，故恰为某段起点）。
          故以统一帧栈按段推进：帧记「运算符 / 已归约操作数 / 归属段号 end」，
          end = 该节点闭合后父链继续求值的段号（取值点在窗外记 None）。keep-or-pop
          的 end 随父帧（根为 None），弹跳的 end 取其续接段号。处理第 end 段时
          栈顶帧的操作数已全部归约完 ⇒ 闭合该帧并把闭合值按本跳转重新归入父链
          （可级联；同一运算符同段号即父节点的普通操作数）。闭合节点按运算符与
          同运算符子链合并，保持 `x and y and w` 的扁平形态。汇合点（全部
          keep-or-pop argval 的最大值）之后的窗内指令作后缀，以「前导压栈项 +
          链值」为初栈逐条处理。CPython 3.11 实证：`x and (y or z) or w` 的首跳
          弹跳 argval 24 是 `w` 的起点（续接点），而 keep-or-pop 的 argval 26 是
          汇合点；把两者当同一坐标系会把 `(x or y) and (z or w) and v` 的第二个
          弹跳组整体丢掉。
        [唯一归属判定] 闭合只产出值、不落挂载点，每个段恰被一个节点引用一次；
          节点栈排空后栈上恰一个根，不满足即返回 None 逐字回落既有通道（[C3]
          显式封闭）。
        [嵌套处理] 段内表达式走通用重建；混合链的嵌套由节点栈与同 end 嵌套节点
          表达，深度即嵌套层数；段内若另含跳转（三元等）由既有通道承担。
        [入口引用语义] 父推导式（LIST_APPEND / SET_ADD / YIELD_VALUE 协议）只
          引用归约后的单一节点；后缀运算整体附着在同一节点上。
        [反编译流程] CPython 3.11 对 `[x and (y or z) and w for x in xs]`、
          `[(x or y) and z or (w and v) ...]` 等元素位发射「keep-or-pop 与弹跳混排」
          形态（既有通道只按首跳分派，产物丢前导操作数或整体退化为三元）。
        """
        _kop_names = ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP')
        _bounce_names = ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE')
        n = len(instrs)
        if n < 3:
            return None
        # 窗首经典三元前缀：`('p' if x else 'q') and (y or z)` 的元素位以
        # `<cond> POP_JUMP_.. <真分支> JUMP_FORWARD <假分支>` 开头，三元自身的
        # JUMP_FORWARD 目标恰为链首 keep-or-pop 的偏移 ⇒ 前缀整体成一个值，
        # 与链首跳转配对。判定只读「首个 keep-or-pop 之前恰一条弹跳 + 一条
        # 无条件前向跳转，且后者目标 == 该 keep-or-pop 偏移」。
        _prefix_expr: Optional[Dict[str, Any]] = None
        _pre: List[Instruction] = []
        _scan = instrs
        _first_kop_off = None
        for _ins in instrs:
            if _ins.opname in _kop_names:
                _first_kop_off = _ins.offset
                break
        if _first_kop_off is not None:
            _cand = [i for i in instrs if i.offset < _first_kop_off]
            _cand_cond = [i for i in _cand if i.opname in _bounce_names]
            _cand_uf = [i for i in _cand if i.opname == 'JUMP_FORWARD']
            if (len(_cand_cond) == 1 and len(_cand_uf) == 1
                    and 'IF_FALSE' in _cand_cond[0].opname
                    and _cand_uf[0].argval == _first_kop_off):
                _cpos = _cand.index(_cand_cond[0])
                _jfpos = _cand.index(_cand_uf[0])
                _cond_seq = _cand[:_cpos]
                _then_seq = _cand[_cpos + 1:_jfpos]
                _else_seq = _cand[_jfpos + 1:]
                # 假分支入口 = 真分支 JUMP_FORWARD 之后的第一条指令（结构判据，
                # 不比对偏移算术）。
                if (_cond_seq and _then_seq and _else_seq
                        and _cand_cond[0].argval == _else_seq[0].offset):
                    def _one(seq):
                        self.expr_reconstructor.reset()
                        _v = self.expr_reconstructor.reconstruct(seq)
                        _st = [s for s in self.expr_reconstructor.stack
                               if not (isinstance(s, dict)
                                       and s.get('type') == 'PUSH_NULL')]
                        if _v is None or len(_st) != 1:
                            return None
                        return _st[0]

                    _t = _one(_cond_seq)
                    _b = _one(_then_seq)
                    _f = _one(_else_seq)
                    if _t is None or _b is None or _f is None:
                        return None
                    _prefix_expr = {'type': 'IfExp', 'test': _t,
                                    'body': _b, 'orelse': _f}
                    _pre = _cand
                    _scan = [i for i in instrs if i.offset >= _first_kop_off]
        _n_kop = 0
        _n_bounce = 0
        _merge = None
        for _ins in _scan:
            _op = _ins.opname
            if _op in _kop_names:
                _n_kop += 1
                _target = getattr(_ins, 'argval', None)
                if _target is None or _target <= _ins.offset:
                    return None
                if _merge is None or _target > _merge:
                    _merge = _target
            elif _op in _bounce_names:
                _n_bounce += 1
            elif _op in CONDITIONAL_JUMP_OPS:
                return None
            elif _op in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                         'JUMP_BACKWARD_NO_INTERRUPT'):
                return None
        if not _n_kop or not _n_bounce or _merge is None:
            return None
        # 汇合点之前的窗内指令是链本体，之后的指令是该值的后缀运算。
        _chain_instrs = [i for i in _scan if i.offset < _merge]
        _suffix = [i for i in _scan if i.offset >= _merge]
        if not _chain_instrs:
            return None
        _segments: List[List[Instruction]] = []
        _jumps: List[Optional[Instruction]] = []
        # 首段以窗首三元前缀（若有）起始：前缀整体是一个操作数，与链首跳转配对，
        # 其内部的弹跳/无条件跳转不再参与切段。
        _cur: List[Instruction] = list(_pre)
        for _ins in _chain_instrs:
            if _ins.opname in _kop_names or _ins.opname in _bounce_names:
                if not _cur:
                    return None
                _segments.append(_cur)
                _jumps.append(_ins)
                _cur = []
            else:
                _cur.append(_ins)
        if not _cur:
            return None
        _segments.append(_cur)
        _jumps.append(None)
        _starts = {seg[0].offset for seg in _segments}
        for _j in _jumps:
            if _j is None:
                continue
            _target = getattr(_j, 'argval', None)
            if _j.opname in _bounce_names:
                if _target not in _starts:
                    return None
            elif _target is None:
                return None

        if _prefix_expr is not None:
            _first = _prefix_expr
            _b247_prefix = []
        else:
            # 首段可能带前导压栈项（如 `'%s' % (链)` 的格式串）：以重建后的栈取
            # 「栈顶为链首操作数、其余为前导项」。
            self.expr_reconstructor.reset()
            self.expr_reconstructor.reconstruct(_segments[0])
            _stack0 = [s for s in self.expr_reconstructor.stack
                       if not (isinstance(s, dict) and s.get('type') == 'PUSH_NULL')]
            if not _stack0:
                return None
            _b247_prefix = _stack0[:-1]
            _first = _stack0[-1]
        if _first is None:
            return None

        _roots: List[Dict[str, Any]] = []

        def _combine(node):
            _vals = list(node.get('values') or [])
            if not _vals:
                return None
            if len(_vals) == 1:
                return _vals[0]
            _op = node.get('op')
            _merged: List[Dict[str, Any]] = []
            for _v in _vals:
                if (isinstance(_v, dict) and _v.get('type') == 'BoolOp'
                        and _v.get('op') == _op):
                    _merged.extend(list(_v.get('values') or []))
                else:
                    _merged.append(_v)
            return {'type': 'BoolOp', 'op': _op, 'values': _merged}

        _seg_at: Dict[int, int] = {}
        for _i, _seg in enumerate(_segments):
            _seg_at.setdefault(_seg[0].offset, _i)
        _frames: List[Dict[str, Any]] = []

        def _close_top():
            return _combine(_frames.pop())

        def _place(val, op, i_next, root_end):
            """把闭合值归入帧栈，父链自第 i_next 段继续求值。

            frames 为空时以 root_end 作新帧的归属段号（keep-or-pop 的取值点
            在窗外汇合点，记 None；假出口弹跳的续接点记该段号）；否则归属
            段号随父帧，保持同一节点层次。
            """
            while True:
                if not _frames:
                    _frames.append({'op': op, 'values': [val], 'end': root_end})
                    return True
                _parent = _frames[-1]
                if _parent['end'] != i_next:
                    _frames.append({'op': op, 'values': [val],
                                    'end': _parent['end']})
                    return True
                _parent['values'].append(val)
                val = _close_top()
                if val is None:
                    return False

        for _i in range(len(_segments)):
            if _i == 0:
                _seg_expr = _first
            else:
                self.expr_reconstructor.reset()
                self.expr_reconstructor.reconstruct(_segments[_i])
                _stk = [s for s in self.expr_reconstructor.stack
                        if not (isinstance(s, dict) and s.get('type') == 'PUSH_NULL')]
                if len(_stk) != 1:
                    return None
                _seg_expr = _stk[0]
            _jump = _jumps[_i]
            if _jump is None:
                if _frames:
                    _frames[-1]['values'].append(_seg_expr)
                else:
                    _roots.append(_seg_expr)
                continue
            _op = ('and' if _jump.opname in ('JUMP_IF_FALSE_OR_POP',
                                            'POP_JUMP_FORWARD_IF_FALSE') else 'or')
            _bounce = _jump.opname in _bounce_names
            _end = _seg_at.get(_jump.argval) if _bounce else None
            if _bounce and _end is None:
                return None
            _next = _i + 1
            if not _frames:
                _frames.append({'op': _op, 'values': [_seg_expr], 'end': _end})
                continue
            _top = _frames[-1]
            if _top['op'] == _op and _top['end'] == _end:
                _top['values'].append(_seg_expr)
            elif _top['end'] == _next:
                # 栈顶节点的归属段已到：本段是它的末位操作数，闭合后按本跳转
                # 重新派发（同运算符同段号 ⇒ 并入父帧的普通操作数）。
                _top['values'].append(_seg_expr)
                _closed = _close_top()
                if _closed is None:
                    return None
                if _bounce and _frames:
                    return None
                if not _place(_closed, _op, _next, _end if _bounce else None):
                    return None
            else:
                # 新节点层次：弹跳的归属段是其续接点，keep-or-pop 随父帧。
                _frames.append({'op': _op, 'values': [_seg_expr],
                                'end': _end if _bounce else _top['end']})

        while _frames:
            _expr = _close_top()
            if _expr is None:
                return None
            if _frames:
                _frames[-1]['values'].append(_expr)
            else:
                _roots.append(_expr)
        if len(_roots) != 1:
            return None
        _value = _roots[0]
        if not _suffix:
            if _b247_prefix:
                return None
            return _value
        self.expr_reconstructor.reset()
        self.expr_reconstructor.stack = list(_b247_prefix) + [_value]
        for _ins in _suffix:
            self.expr_reconstructor._process_instruction(_ins)
        _out = [s for s in self.expr_reconstructor.stack
                if not (isinstance(s, dict) and s.get('type') == 'PUSH_NULL')]
        if len(_out) == 1:
            return _out[0]
        return None

    def _b237_kop_window(self, instrs: List[Instruction]) -> Optional[Dict[str, Any]]:
        """[B237-V3R40] 元素位 `(A and B) or C` 的 keep-or-pop 整组归约。

        [识别条件]（I.4 白名单：同层指令 opcode / 跳转目标，无名字或偏移阈值）
          (1) 窗内首个跳转是前向 IF_FALSE 型条件跳转（含 IF_FALSE、不含
              IF_TRUE / NONE / BACKWARD），且其目标偏移落在窗内的假值区 ——
              这正是 `A and B or C` 的短路出口（A 为假直落 C）；
          (2) 条件跳转与 C 入口之间存在 JUMP_IF_TRUE_OR_POP 终结符 —— B 为
              真时保留 B 作结果并跳到汇合点、B 为假时弹出 B 落到 C；
          (3) 真值区内无其它条件跳转，也无无条件前向跳转（那是经典三元形，
              交回 `_detect_comp_ternary` 既有通道）。
        [归约方式] 条件区逐条压栈、取栈顶为 A（其余为前导压栈项 F）；真值区
          重建为 B、假值区重建为 C；合成 BoolOp(or, [BoolOp(and, [A, B]), C])。
          汇合点之后还有后缀指令（如 BINARY_OP）时，以 `F... + [值]` 作初栈
          逐条处理后缀，栈上唯一项即元素表达式。
        [唯一归属判定] 前导项、A/B/C 三段与后缀运算整体归属单一元素表达式，
          不留下游离指令，也不产生独立语句。
        [嵌套处理] 真值区/假值区内的同族形态递归调用本方法，深度即嵌套层数。
        [入口引用语义] 父推导式（LIST_APPEND / SET_ADD / YIELD_VALUE 协议）
          引用归约后的单一节点。
        [反编译流程] CPython 3.11 对 `[x and y or 'e' for x in xs]` 与
          `'%s' % (x and y or 'e')` 的元素位发射本形态（去掉 keep-or-pop 建模
          时产物退化为 `y if x else 'e'`，B 为假时丢掉 C）。判据不命中返回
          None，由调用方逐字回落既有通道（[C3] 显式封闭）。
        """
        n = len(instrs)
        if n < 3:
            return None
        # [B247-V3R51] keep-or-pop 与假出口弹跳混排的整组归约（未命中回 None，
        # 由下方既有「首跳即假出口」通道逐字接管）。
        _b247_expr = self._b247_mixed_boolchain(instrs)
        if _b247_expr is not None:
            return _b247_expr
        # 首个跳转必须是前向 IF_FALSE 型条件跳转（keep-or-pop 开头 = 纯短路，
        # 由通用元素窗重建处理；无条件跳转 = 经典三元形，交回既有通道）。
        j = None
        for k in range(n):
            op = instrs[k].opname
            if op in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                # [B242-V3R45] 前导 keep-or-pop 跳转不是本形态的终结符：它属于
                # 位于本 kop 窗口之上的短路链（`x or ((y and z) or w)` 的
                # `x or ...` 边界）。跳过并由条件区栈建模保留为外链，首个普通
                # 前向条件跳转才是内层 kop 窗口的起点。
                continue
            if op in CONDITIONAL_JUMP_OPS:
                if 'BACKWARD' in op:
                    return None
                j = k
                break
            if op in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                      'JUMP_BACKWARD_NO_INTERRUPT'):
                return None
        if j is None:
            return None
        cond_ins = instrs[j]
        if 'IF_TRUE' in cond_ins.opname or 'NONE' in cond_ins.opname:
            return None
        target = getattr(cond_ins, 'argval', None)
        if target is None or target <= cond_ins.offset:
            return None
        # 真值区终结符：只接受 JUMP_IF_TRUE_OR_POP（B 为真保留 B）。
        term_idx = None
        for k in range(j + 1, n):
            ins = instrs[k]
            if ins.offset >= target:
                return None
            if ins.opname == 'JUMP_IF_TRUE_OR_POP':
                term_idx = k
                break
            if ins.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_FORWARD',
                              'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                              'JUMP_BACKWARD_NO_INTERRUPT'):
                return None
            if ins.opname in CONDITIONAL_JUMP_OPS:
                return None
        if term_idx is None:
            return None
        else_idx = None
        for k in range(term_idx + 1, n):
            if instrs[k].offset >= target:
                else_idx = k
                break
        if else_idx is None or else_idx >= n:
            return None
        merge = getattr(instrs[term_idx], 'argval', None)
        if merge is None or merge < target:
            return None
        merge_idx = n
        for k in range(else_idx, n):
            if instrs[k].offset >= merge:
                merge_idx = k
                break
        if merge_idx <= else_idx:
            return None
        # 条件区：逐条压栈取栈顶为 A，其余为前导压栈项 F。
        # [B242-V3R45] 条件区可能带有一条 keep-or-pop 外链（
        # `x or ((y and z) or w)` 的 `x or <本 kop 窗口>`）：以开启同族归约的
        # 栈建模处理，栈上出现 (Pending, A) 时把 Pending 记为外链、A 仍作条件，
        # 本窗口结果随后并入外链的最后一个操作数。
        self.expr_reconstructor.reset()
        _b242_saved_fold = self.expr_reconstructor._fold_boolop_keep_or_pop
        self.expr_reconstructor._fold_boolop_keep_or_pop = True
        for _b237_i in instrs[:j]:
            self.expr_reconstructor._process_instruction(_b237_i)
        self.expr_reconstructor._fold_boolop_keep_or_pop = _b242_saved_fold
        _b237_items = [s for s in self.expr_reconstructor.stack
                       if not (isinstance(s, dict) and s.get('type') == 'PUSH_NULL')]
        if not _b237_items:
            return None
        _b237_chain = None
        if (len(_b237_items) >= 2 and isinstance(_b237_items[-2], dict)
                and _b237_items[-2].get('type') == 'BoolOpPending'):
            _b237_chain = _b237_items[-2]
            _b237_a = _b237_items[-1]
            _b237_prefix = _b237_items[:-2]
        else:
            _b237_a = _b237_items[-1]
            _b237_prefix = _b237_items[:-1]
        # [B242-V3R45] 真值区是「条件跳转之后到假值区入口」的**整段**，而不是
        # 首个 keep-or-pop 终结符之前的前缀：`x and (y or z) or w` 的真值区为
        # `y; JUMP_IF_TRUE_OR_POP; z; JUMP_IF_TRUE_OR_POP`，只取到首个终结符会
        # 丢掉 `z` 及其跳转（实测产物 `x and y or w`，语义错）。整段保持
        # keep-or-pop 跳转并开启同族归约，由通用 keep-or-pop 通道按布尔优先级
        # 折叠成 `y or z`。
        _b237_t = instrs[j + 1:else_idx]
        # 真值区末尾的 keep-or-pop 是「真值区 → 假值区」的边界跳转（其右操作数
        # 即 C），不参与 B 的重建；剥掉它后区内的 keep-or-pop 才是 B 自身的短路链。
        while (_b237_t
               and _b237_t[-1].opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP')):
            _b237_t = _b237_t[:-1]
        _b237_e = instrs[else_idx:merge_idx]
        if not _b237_t or not _b237_e:
            return None
        _b237_b = self._b237_kop_window(_b237_t)
        if _b237_b is None:
            _b237_b = self.expr_reconstructor.reconstruct(
                _b237_t, fold_boolop_keep_or_pop=True)
        _b237_c = self._b237_kop_window(_b237_e)
        if _b237_c is None:
            # 假值区同样可能是 keep-or-pop 链（`(x and y) or (z and w)` 的
            # `z and w`）：开启同族归约，否则 reconstruct 只返回栈顶尾项。
            _b237_c = self.expr_reconstructor.reconstruct(
                _b237_e, fold_boolop_keep_or_pop=True)
        if _b237_b is None or _b237_c is None:
            return None
        _b237_value = {
            'type': 'BoolOp',
            'op': 'or',
            'values': [
                {'type': 'BoolOp', 'op': 'and', 'values': [_b237_a, _b237_b]},
                _b237_c,
            ],
        }
        if _b237_chain is not None:
            # 本 kop 窗口是外链的最后一个操作数：把归约结果并入外链后统一折叠。
            _b237_chain.setdefault('values', []).append(_b237_value)
            _b237_chain_folded = self.expr_reconstructor._b242_fold_boolop_pending(
                _b237_chain)
            if _b237_chain_folded is None:
                return None
            _b237_value = _b237_chain_folded
        _b237_suffix = instrs[merge_idx:]
        if not _b237_suffix:
            # 无后缀时前导项必须为空，否则该值不是元素表达式的最终值。
            if _b237_prefix:
                return None
            return _b237_value
        self.expr_reconstructor.reset()
        self.expr_reconstructor.stack = list(_b237_prefix) + [_b237_value]
        for _b237_i in _b237_suffix:
            self.expr_reconstructor._process_instruction(_b237_i)
        _b237_out = [s for s in self.expr_reconstructor.stack
                     if not (isinstance(s, dict) and s.get('type') == 'PUSH_NULL')]
        if len(_b237_out) == 1:
            return _b237_out[0]
        return None

    def _detect_comp_ternary(self, all_instrs: List[Instruction],
                             store_idx: int,
                             append_idx: int) -> Optional[Dict[str, Any]]:
        """检测推导式中的三元表达式模式

        三元模式特征：条件跳转的目标在LIST_APPEND之前（跳转到false值），
        而不是跳过整个元素表达式（过滤器模式）。
        字节码模式：condition → POP_JUMP_IF_FALSE false_value → true_value → JUMP_FORWARD merge → false_value → LIST_APPEND 支持 ternary + filter 共存：BACKWARD filter 跳转
        （跳回 FOR_ITER）会被跳过，继续寻找 FORWARD ternary cond 跳转。
        cond_instrs 从最后一个 filter 跳转之后开始，避免包含 filter 指令。

        [B6-comp]（Round 1 修复工程师二）混合 and/or 过滤链
        ``[... if A and B or C]`` 的 and→or 边界成员假边直达 or 尾成员
        （目标块仍是条件块），其「假边跳回 FOR_ITER」的回跳条件跳转位于
        目标偏移之后且与求值指令同块（前驱非跳转即同块，[C1] 同层结构
        事实）。识别条件=该「回跳条件 + 融合求值前缀」签名；归约方式=
        判定为过滤器（返回 None 交回 _extract_comp_ifs 逐段提取 + or_groups
        分组），不命中维持 R10/R67 原判据逐位不变（[C3] 显式守卫）。
        AST 映射由 _extract_comp_ifs 的 BoolOp 组合承担。"""
        append_offset = all_instrs[append_idx].offset if append_idx < len(all_instrs) else float('inf')

        # 查找STORE和LIST_APPEND之间的条件跳转
        cond_jump_idx = None
        # [B248-V3R52] 三元 test 位短路链整组归约结果（未命中保持 None，
        # 走既有单段/共享假出口通道）。
        _b248_test_expr = None
        # 记录最后一个 BACKWARD filter 跳转的索引，
        # cond_instrs 从此之后开始（跳过 filter 条件指令）。
        last_filter_end = store_idx

        # [R67-fix2 聚合布尔三元测试] 三元 test 为布尔运算链（A and B / A or B）时，CPython 3.11
        # 为每个操作数各发一条条件跳转，且这些「假出口」共享同一目标偏移（见 dis 实证）。R10 的扫描
        # 在第一条前向条件跳转处 break，cond_instrs 只截到第一个操作数，IfExp 的 test 因此丢掉其余
        # 操作数，被丢的指令区段整段从产物消失。
        # 识别条件（全部为本存储区内的结构判据，不涉及名字/文件/偏移阈值）：
        #   ① j0 处为 CONDITIONAL_JUMP_OPS 中的前向跳转（opname 不含 BACKWARD）且目标
        #      tgt0 = argval 满足 j0.offset < tgt0 < append_offset（三元特征：跳过 Then 分支落到
        #      Else 值，而非跳出整个元素）；
        #   ② j0 为「假出口」型跳转（IF_FALSE / IF_NONE，即真分支为空）；IF_TRUE 首跳不属于本规则，
        #      沿用 R10 原路径；
        #   ③ 在 (j0, tgt0) 区间内继续出现的条件跳转，其目标仍等于 tgt0 者并入链；
        #      区间内若出现 BACKWARD 条件跳转（= if 过滤器语义，R10 甄别）或跳往其它目标者，
        #      链不纯，整条三元返回 None 交回既有 genexpr 路径，保持原保守行为。
        # 归约方式：cond_jump_idx 取链上最后一条跳转索引；条件指令区仍按
        #   all_instrs[last_filter_end + 1 : cond_jump_idx] 切取（既有通道不变），于是链上每条
        #   「操作数计算段 + 其共享假出口跳转」串成一条连续指令流；假出口本身不产生值，共享假出口
        #   的连续条件跳转即在表达式重建器中折叠为 BoolOp。Else 分支定位（`for j in range
        #   (cond_jump_idx+1, ...)` 找 pop_jump_if_true 目标）与 R5 表达式切片守卫均不改动。
        # AST 映射：ast.IfExp(test=<BoolOp 折叠后的多操作数测试>, body=<Then 分支>, orelse=
        #   <Else 常量>) —— 与单操作数情形同一条 ast.IfExp 通道，仅 test 子树由单 Compare 变为
        #   BoolOp(and/or, [Compare, Compare, ...])。
        def _r67_boolop_chain_end(instrs, start_i, stop_i, append_off):
            """instrs[start_i] 为前向假出口型条件跳转时，返回与之共享假出口的最后一条条件跳转索引。

            不满足 ①②③ 者返回 None（单操作数情形由调用方沿用 R10 原索引；链不纯者返回 None 保守放弃）。
            """
            j0 = start_i
            op0 = instrs[j0].opname
            if 'BACKWARD' in op0:
                return None
            if 'IF_FALSE' not in op0 and 'IF_NONE' not in op0:
                return None
            tgt0 = instrs[j0].argval if hasattr(instrs[j0], 'argval') else None
            if tgt0 is None or tgt0 <= instrs[j0].offset or tgt0 >= append_off:
                return None
            last_j = j0
            for k in range(j0 + 1, stop_i):
                kin = instrs[k]
                if kin.offset >= tgt0:
                    break
                if kin.opname not in CONDITIONAL_JUMP_OPS:
                    continue
                kt = kin.argval if hasattr(kin, 'argval') else None
                if 'BACKWARD' in kin.opname or kt is None:
                    return None
                if kt == tgt0:
                    last_j = k
                else:
                    return None
            return last_j if last_j != j0 else None

        for idx in range(store_idx + 1, append_idx):
            instr = all_instrs[idx]
            if instr.opname in CONDITIONAL_JUMP_OPS:
                # BACKWARD 条件跳转是过滤器模式（跳回 FOR_ITER
                # 循环开始以跳过当前元素），不是三元模式。三元模式使用 FORWARD
                # 跳转跳到 false 值（在 true 值之后、LIST_APPEND 之前）。
                # 跳过 BACKWARD filter 跳转继续寻找 FORWARD
                # ternary cond 跳转，支持 ternary + filter 共存。
                if 'BACKWARD' in instr.opname:
                    last_filter_end = idx
                    continue
                # 检查跳转目标是否在LIST_APPEND之前（三元模式）
                if hasattr(instr, 'argval') and instr.argval is not None:
                    if instr.argval < append_offset:
                        # [R10] OR-filter pattern: FORWARD jump to body with BACKWARD
                        # jump after it means this is `if cond1 or cond2` filter,
                        # not ternary. CPython compiles OR in comprehension if-filter
                        # as POP_JUMP_FORWARD_IF_TRUE (skip to body if cond1 true)
                        # followed by POP_JUMP_BACKWARD_IF_FALSE (skip iteration if
                        # cond2 false). Check for BACKWARD jump between here and
                        # the forward jump target.
                        has_backward_after = False
                        for inner_idx in range(idx + 1, append_idx):
                            inner_instr = all_instrs[inner_idx]
                            if inner_instr.offset >= instr.argval:
                                break
                            if inner_instr.opname in CONDITIONAL_JUMP_OPS and 'BACKWARD' in inner_instr.opname:
                                has_backward_after = True
                                break
                        # [B6-comp 混合过滤器甄别扩展] 混合链 and→or 边界成员的
                        # 前向假边直达 or 尾成员（目标块自身仍是条件块），其
                        # 「假边跳回 FOR_ITER」的回跳条件跳转位于目标偏移之后、
                        # 且与操作数求值指令同块（前一条是非跳转指令——块为
                        # 极大直线序列，前驱非跳转即同块，[C1] 同层结构事实）。
                        # 该签名（回跳条件 + 融合求值前缀）是过滤器成员专属：
                        # 纯三元假值块为直线求值、不含条件跳转；三元作过滤器的
                        # 「回跳出口块」是裸跳转块（前驱是跳转，不同块）。命中即
                        # 判过滤器（返回 None 交回 _extract_comp_ifs 逐段提取），
                        # 不命中维持 R10/R67 原判据逐位不变（[C3] 显式守卫）。
                        if not has_backward_after:
                            for inner_idx in range(idx + 1, append_idx):
                                inner_instr = all_instrs[inner_idx]
                                if inner_instr.offset < instr.argval:
                                    continue
                                if inner_instr.offset >= append_offset:
                                    break
                                if inner_instr.opname in CONDITIONAL_JUMP_OPS and 'BACKWARD' in inner_instr.opname:
                                    if inner_idx > 0:
                                        prev_instr = all_instrs[inner_idx - 1]
                                        if (prev_instr.opname not in CONDITIONAL_JUMP_OPS
                                                and prev_instr.opname not in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                                                              'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                                                              'RETURN_VALUE', 'RETURN_CONST')):
                                            has_backward_after = True
                                            break
                        if has_backward_after:
                            return None
                        # [B253-V3R56] 元素位三元之前的「前缀 keep-or-pop 链」
                        # （`z and (<三元>)` / `z or (<三元>)`，见下方 [B251-V3R56]）
                        # 的跳转恰好也是本窗的首条短路跳转，若不从 test 链窗口剔除，
                        # 反向解析会把前缀操作数当成 test 链首成员（实测 t268 产物
                        # test = `(z and x or y) and z or (w and v)`，多出前导 z）。
                        # ①识别条件（I.4 白名单：同层 opcode / 跳转 argval）：窗内
                        #   首个普通条件跳转之前存在 keep-or-pop 跳转，且其 argval
                        #   不小于窗内全部普通条件跳转 argval 的最大值——前缀链的
                        #   落点是整个元素布尔表达式的续接点，必然位于所有三元
                        #   test 出口之后；追加点不是 MAP_ADD（dict 键/值位另有通道）。
                        # ②归约方式：只把 test 链通道（B248/B249）的窗口起点后移到
                        #   末条前缀 keep-or-pop 之后，前缀本身由 [B251-V3R56] 归约。
                        # ③唯一归属：前缀链与 test 链分属两个相邻的短路窗口。
                        # ④嵌套：前缀链自身多级时取末条 keep-or-pop 之后。
                        # ⑤入口引用：两窗由同一元素表达式持有。
                        # ⑥反编译流程：t268/t324 两条链在 `tern_in_and` 宿主各 1 例。
                        # 未命中（无前缀链 / MAP_ADD / 落点更小）时窗口起点逐字不变。
                        _b253_test_start = last_filter_end + 1
                        if (append_idx < len(all_instrs)
                                and all_instrs[append_idx].opname != 'MAP_ADD'):
                            _b253_max = 0
                            for _k in range(idx, append_idx):
                                _ki = all_instrs[_k]
                                if (_ki.opname in CONDITIONAL_JUMP_OPS
                                        and _ki.argval is not None
                                        and _ki.argval > _b253_max):
                                    _b253_max = _ki.argval
                            for _k in range(_b253_test_start, idx):
                                _ki = all_instrs[_k]
                                if (_ki.opname in ('JUMP_IF_FALSE_OR_POP',
                                                   'JUMP_IF_TRUE_OR_POP')
                                        and _ki.argval is not None
                                        and _ki.argval >= _b253_max):
                                    _b253_test_start = _k + 1
                        # [R67-fix2] 同假出口的布尔链：条件区延伸到链上最后一条跳转，
                        # 使 reconstruct 收到全部操作数；单操作数时沿用 R10 原索引。
                        _chain_end = _r67_boolop_chain_end(
                            all_instrs, idx, append_idx, append_offset)
                        _pure_false_exit = (
                            _chain_end is not None
                            and all('IF_FALSE' in all_instrs[_k].opname
                                    for _k in range(last_filter_end + 1,
                                                    _chain_end + 1)
                                    if all_instrs[_k].opname in CONDITIONAL_JUMP_OPS))
                        if _pure_false_exit:
                            cond_jump_idx = _chain_end
                        else:
                            # [B248-V3R52] 非共享假出口的短路链（or 链、混合链、
                            # 握手嵌套、极性混排）按落点分类整组归约；命中时链尾
                            # 取最后一条跳转，真值区起点即其下一条指令，假值区
                            # 即其落点。未命中回落 R67/单段原路径（[C3]）。
                            _b248 = self._b248_ternary_test_chain(
                                all_instrs, _b253_test_start, append_idx)
                            if _b248 is not None:
                                _b248_test_expr, cond_jump_idx = _b248
                            else:
                                # [B249-V3R53] test 位纯「假出口弹跳」链
                                # （`(x or y) and z or (w and v)`、
                                # `x and (y or z) or w`）：与过滤位同一条
                                # `compiler_jump_if` 文法，按「段 + 跳转」
                                # 反向解析；未命中逐字回落既有通道（[C3]）。
                                _b249_t = self._b249_test_boolchain(
                                    all_instrs, _b253_test_start, append_idx)
                                if _b249_t is not None:
                                    _b248_test_expr, cond_jump_idx = _b249_t
                                else:
                                    cond_jump_idx = idx if _chain_end is None else _chain_end
                        break
                # 跳转目标在LIST_APPEND之后 → 过滤器模式，不是三元
                return None

        if cond_jump_idx is None:
            return None

        # [B237-V3R40] 元素位 `(A and B) or C` 的 keep-or-pop 整组归约。
        # CPython 3.11 对表达式值位的 `A and B or C` 发射：
        #   cond_block:  [F;] <A 的操作数>; POP_JUMP_FORWARD_IF_FALSE <C 入口>
        #   true_block:  <B 的操作数>; JUMP_IF_TRUE_OR_POP <merge>
        #   false_block: <C 的操作数>
        #   merge:       [<后缀运算>;] LIST_APPEND/SET_ADD/YIELD_VALUE
        # 短路语义：A 为假直落 C；A 为真时 B 为真则 B 即结果（跳 merge）、
        # B 为假则弹出 B 落到 C。即 `(A and B) or C`。既有三元通道把真值区
        # 末的 keep-or-pop 当普通分支跳转、只取栈顶 ⇒ 产出 `B if A else C`
        # （B 为假时丢掉 C，语义错），前导项 F 与 merge 后缀也整段丢失。
        # ①识别条件（I.4 白名单：同层指令 opcode / 跳转目标）：
        #   (1) 首个跳转是前向 IF_FALSE 型条件跳转；
        #   (2) 其真值区终结于 keep-or-pop，且终结符跳转目标 >= C 入口偏移；
        #   (3) 追加点不是 MAP_ADD（dict 推导式 key/value 另有专用通道）。
        # ②归约顺序：条件区前导项 + 条件值作初栈 → 真值区/假值区各自递归
        #   重建 → 合成 BoolOp(or, [BoolOp(and, [A, B]), C]) → 以该值作三元
        #   位初栈逐条处理 merge 后缀 → 栈上唯一项即元素表达式。
        # ③唯一归属判定：前导项、A/B/C 三段、后缀运算整体归属单一元素表达式。
        # ④嵌套处理：真值区/假值区内的同族形态递归走本方法，深度即嵌套层数。
        # ⑤入口引用语义：父推导式（LIST_APPEND/SET_ADD/YIELD_VALUE 协议）
        #   引用归约后的单一节点，不再看到任何跳转指令。
        # ⑥反编译流程：实测 `/tmp/mini38` 的 `[x and y or 'e' for x in xs]`
        #   与 `'%s' % (x and y or 'e')` 元素位形态（29 条 vs 21 条指令）。
        # 判据不命中时逐字回落既有三元通道（C3 显式封闭）。
        # [B243-V3R46] dict 推导式键/值位的 keep-or-pop 链与经典三元同形但不同族：
        # 窗内出现 keep-or-pop 跳转即说明该窗含短路链（键位链的汇合点落在追加
        # 点之前、值位链的汇合点恰好就是追加点），而经典三元的真分支以
        # JUMP_FORWARD 直落假值区。故「有 keep-or-pop 且无无条件跳转」时交回
        # _split_dict_comp_kv 的键/值切分通道（键窗/值窗各自整组归约）。
        # 三元 test 内含 keep-or-pop（`k if (a or b) else z`）的窗内必有
        # JUMP_FORWARD，因此不在本门内，维持经典三元通道（[C3] 显式封闭）。
        if (append_idx < len(all_instrs)
                and all_instrs[append_idx].opname == 'MAP_ADD'):
            _b243_window = all_instrs[store_idx + 1:append_idx]
            _b243_kop = [i for i in _b243_window
                         if i.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP')]
            _b243_uncond = any(
                i.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                             'JUMP_BACKWARD_NO_INTERRUPT')
                for i in _b243_window)
            if _b243_kop and not _b243_uncond:
                return None

        if (append_idx < len(all_instrs)
                and all_instrs[append_idx].opname != 'MAP_ADD'):
            _b237_elem = self._b237_kop_window(
                all_instrs[last_filter_end + 1:append_idx])
            if _b237_elem is not None:
                return _b237_elem

        cond_instr = all_instrs[cond_jump_idx]
        false_target_offset = cond_instr.argval

        # 分离条件指令：从最后一个过滤器之后到条件跳转之前
        # （[R67-fix2] cond_jump_idx 可为布尔链的最后一条共享假出口跳转，见上）。
        # cond_instrs 从此之后开始（跳过 filter 条件指令）。
        cond_instrs = all_instrs[last_filter_end + 1:cond_jump_idx]

        # 找到true值和false值的指令范围
        true_start = cond_jump_idx + 1
        false_start = None
        true_end = None
        # [Round7-08] 记录 JUMP_FORWARD 的目标偏移量（merge point），
        # false 值区域只到 merge point 之前，merge point 之后是后续表达式（如
        # dict comprehension 的 value，紧跟在三元 key 之后压栈）。
        merge_offset = None

        # 在true值区域中查找JUMP_FORWARD（跳转到merge/LIST_APPEND）
        for idx in range(true_start, append_idx):
            instr = all_instrs[idx]
            if instr.offset >= false_target_offset:
                # 已到达false值区域
                if false_start is None:
                    false_start = idx
                break
            if instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD'):
                true_end = idx
                # false值从JUMP的目标偏移量开始
                false_start = idx + 1
                # 记录 merge point（JUMP 的目标偏移量）
                if hasattr(instr, 'argval') and instr.argval is not None:
                    merge_offset = instr.argval
                break

        if false_start is None:
            return None

        # [B252-V3R56] 真值臂内的嵌套经典三元（`(1 if C else 0) if w else 2`）。
        # CPython 3.11 对真值臂自身是三元时发射：
        #   <w>; POP_JUMP_FORWARD_IF_FALSE <外层 else 入口>
        #   <C 的 test 链>; 1; JUMP_FORWARD <外层 merge>; 0; JUMP_FORWARD <外层 merge>
        #   <外层 else 入口>: 2
        #   <外层 merge>: LIST_APPEND
        # 内层两臂的 JUMP_FORWARD 都直落**外层 merge**，故真值区内含两条以上指向
        # 同一 merge 的无条件跳转；上方「首个无条件跳转即真值臂终点」的切分只对
        # 单层三元成立，会把内层假值块（0）与内层 test 链整段丢给 false_instrs
        # ⇒ 产物退化为 `1 if w else 2`。
        # ①识别条件（I.4 白名单：同层跳转 argval）：条件跳转落点 `c`（外层 else
        #   入口）与当前 false_start 不等，且 `c` 前一条恰是目标为 merge_offset 的
        #   无条件跳转；命中即把外层 else 入口与真值臂终点校准到 `c`。
        # ②归约顺序：真值臂以 `_detect_comp_ternary` 在同一指令数组上、以 `c` 作
        #   窗口终点递归整组归约（内层 test 链/两臂各走既有通道），外层照常以
        #   merge 后缀收尾。
        # ③唯一归属判定：内层三元的 test 链与两臂完整落在真值臂窗内，外层 else
        #   值只在外层窗内，两层互不吞并。
        # ④嵌套处理：递归深度即真值臂嵌套层数，每层窗口严格收缩。
        # ⑤入口引用语义：外层 IfExp.body 引用递归结果这一单一节点。
        # ⑥反编译流程：实测 `/tmp/r53/tcorpus.py` 的 `t007` 等
        #   `[(1 if (x and y) else 0) if w else 2 for x in xs]`（19 vs 13 指令）。
        # 任一守卫不命中时维持原切分（C3）。
        if (false_target_offset is not None
                and all_instrs[false_start].offset != false_target_offset):
            _b252_fs = None
            for _b252_k in range(false_start, append_idx):
                if all_instrs[_b252_k].offset == false_target_offset:
                    _b252_fs = _b252_k
                    break
            if _b252_fs is not None and _b252_fs > false_start:
                _b252_term = all_instrs[_b252_fs - 1]
                if (_b252_term.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                           'JUMP_BACKWARD')
                        and _b252_term.argval == merge_offset):
                    false_start = _b252_fs
                    true_end = _b252_fs

        # true值指令：从true_start到true_end（不含JUMP）
        if true_end is not None:
            true_instrs = all_instrs[true_start:true_end]
        else:
            true_instrs = all_instrs[true_start:false_start]

        # false值指令：从false_start到append_idx
        # [Round7-08] 若有 merge_offset，false 值区域只到 merge_offset 之前。
        # merge_offset 之后是指令属于后续表达式（如 dict comp 的 value），
        # 不应作为 false 分支的一部分。
        # _merge_block_idx 标记 merge_offset 处的指令索引，
        # 用于检测 walrus(COPY 1 + STORE_*) 副作用模式。
        _merge_block_idx = None
        if merge_offset is not None:
            false_end = false_start
            for idx in range(false_start, append_idx):
                if all_instrs[idx].offset >= merge_offset:
                    _merge_block_idx = idx
                    break
                false_end = idx + 1
            false_instrs = all_instrs[false_start:false_end]
        else:
            false_instrs = all_instrs[false_start:append_idx]

        # [B98-V3R2 元素位融合 or-前缀] 识别条件（I.4 白名单：同层指令
        # opcode/跳转目标）：首条三元条件跳转为前向 IF_TRUE；真值区末指令为
        # keep-or-pop 族条件跳转（JUMP_IF_FALSE_OR_POP / JUMP_IF_TRUE_OR_POP）
        # 且其跳转目标 == 追加点（MAP_ADD/LIST_APPEND/YIELD...）偏移；真值区
        # 除末跳外无其它条件/keep-or-pop 跳转（中间或成员会引入更多条件
        # 跳转，本支不命中、逐字回落既有 IF_TRUE 取反路径，[C3] 显式封闭）。
        # 该形态即 CPython 对表达式位 `(A or B) and C` 的融合：A 真→C、
        # B 真→（弹出 B）继续到 C、B 假→保留 B 为结果。若照 IF_TRUE 取反
        # 解成 `B if not A else C`，B 为真时丢失 C 检查（假三元，element
        # 位语义错位）。归约方式：cond=A、真值区操作数=B、else 值=C，重建
        # BoolOp(and, [BoolOp(or,[A,B]), C])。
        # AST 映射：IfExp(not A, B, C) 消解为 And[Or[A,B],C]，重编译回同一
        # 字节流。
        if (_b248_test_expr is None
                and 'IF_TRUE' in cond_instr.opname
                and 'BACKWARD' not in cond_instr.opname
                and true_instrs
                and true_instrs[-1].opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP')
                and true_instrs[-1].argval is not None
                and append_idx < len(all_instrs)
                and true_instrs[-1].argval == all_instrs[append_idx].offset
                and not any(i.opname in CONDITIONAL_JUMP_OPS
                            or i.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP')
                            for i in true_instrs[:-1])):
            _oip_cond = self.expr_reconstructor.reconstruct(cond_instrs)
            _oip_true = self.expr_reconstructor.reconstruct(
                [i for i in true_instrs[:-1]
                 if i.opname not in CONDITIONAL_JUMP_OPS])
            # [B242-V3R45] 假值区内部可能自带 keep-or-pop 链
            # （`(x or y) and (z or w)` 的 `z or w`）：保留该族跳转并开启同族
            # 归约；滤掉它们时 reconstruct 只返回栈顶尾项（实测产物丢 `z`）。
            _oip_false = self.expr_reconstructor.reconstruct(
                [i for i in false_instrs
                 if i.opname not in CONDITIONAL_JUMP_OPS],
                fold_boolop_keep_or_pop=True)
            if _oip_cond is not None and _oip_true is not None and _oip_false is not None:
                return {'type': 'BoolOp', 'op': 'and', 'values': [
                    {'type': 'BoolOp', 'op': 'or', 'values': [_oip_cond, _oip_true]},
                    _oip_false]}

        # 重建条件表达式
        # [B248-V3R52] test 位短路链整组归约已给出完整 test 节点（含各操作数
        # 的取反极性），直接采用，不再走单段/共享假出口通道、也不再按链尾
        # 跳转极性整体取反（极性已逐成员消费）。
        cond_expr = _b248_test_expr
        if cond_expr is None:
            # [R21-2] 三元 test 若为共享假出口的布尔链，先按段折叠为 BoolOp(and)；
            # 判据未命中（单操作数 / 链不纯 / 段重建失败）时逐字回落原 R10 单段路径。
            cond_expr = self._r21_fold_boolop_test_chain(
                all_instrs, _b253_test_start, cond_jump_idx, false_target_offset)
        # [B236-V3R39] 记录条件表达式是否走「单段整窗重建」通道：只有该通道
        # 的重建栈上才可能留有前导压栈项（布尔链折叠通道按段切分，无前导项
        # 语义），供本方法末段的前导项 + 汇合点后缀整组归约使用。
        _b236_plain_cond = cond_expr is None
        if cond_expr is None:
            cond_expr = self.expr_reconstructor.reconstruct(cond_instrs)
        if cond_expr is None:
            return None

        # 如果条件跳转是IF_TRUE（or条件），需要取反
        if _b248_test_expr is None and 'IF_TRUE' in cond_instr.opname:
            cond_expr = {'type': 'UnaryOp', 'op': 'not', 'operand': cond_expr}

        # 重建true值表达式
        # [B237-V3R40] 真值区自身含跳转（`A if (B and C or D) else E` 的融合真值
        # 区）时，先按 keep-or-pop 整组归约重建（窗口含真值区终结跳转，让内层
        # 假值区与汇合点都在窗内）；判据不命中逐字回落原重建通道。
        true_expr = None
        # [B252-V3R56] 真值臂内的嵌套经典三元：两臂的无条件跳转都直落同一外层
        # merge（真值臂内因此出现 2 条以上目标为 merge_offset 的无条件跳转）。
        # 以条件跳转的落点 `c`（外层 else 入口）作窗口终点，在同一指令数组上
        # 递归整组归约真值臂；内层 test 链与两臂全部落在窗内，外层 else 值不在。
        if (merge_offset is not None and false_start is not None
                and all_instrs[false_start].offset == false_target_offset):
            _b252_uncond = [i for i in true_instrs
                            if i.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                            'JUMP_BACKWARD')
                            and getattr(i, 'argval', None) == merge_offset]
            if len(_b252_uncond) >= 2:
                _b252_nested = self._detect_comp_ternary(
                    all_instrs, true_start - 1, false_start)
                if (isinstance(_b252_nested, dict)
                        and _b252_nested.get('type') == 'IfExp'):
                    true_expr = _b252_nested
        if any(i.opname in CONDITIONAL_JUMP_OPS
               or i.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP')
               for i in true_instrs):
            _b237_twindow = (all_instrs[true_start:false_start]
                             if false_start is not None else true_instrs)
            if true_expr is None:
                true_expr = self._b237_kop_window(_b237_twindow)
        if true_expr is None:
            # [B242-V3R45] 真值区自身可能就是 keep-or-pop 链（`x and y if c else z`
            # 的 `x and y`）：开启同族归约，否则 reconstruct 只返回栈顶尾操作数
            # （实测产物丢 `x and`）。
            true_expr = self.expr_reconstructor.reconstruct(
                true_instrs, fold_boolop_keep_or_pop=True)
        if true_expr is None:
            return None

        # 重建false值表达式。嵌套三元链归约（innermost→outermost）：CPython 对
        # `a if c else (b if d else e)` 在 false 区域内再生成一次「条件 → 前向条件跳转
        # → true 臂 → JUMP_FORWARD 到同一个 merge」，即 false 区域本身又是一个三元区域。
        # 识别条件：false_instrs 内含至少一条前向条件跳转（BACKWARD 条件是推导式的 filter
        # 回边，不算）。归约方式：以 false_start 为新的扫描起点递归调用本方法，先把内层
        # 三元归约为一个 IfExp 抽象节点，再由外层持有为 orelse——内层区域整体作为父节点的
        # 一个抽象结点，符合「每块唯一归属」。AST 映射：IfExp(test, body, IfExp(...))。
        # 递归返回 None（内层并非三元，或通用重建器本就能处理）时逐字回落到原路径，
        # 因此该判据是严格附加的，不改变任何现有可正常重建的产物结构。
        false_expr = None
        if any(_fi.opname in CONDITIONAL_JUMP_OPS and 'BACKWARD' not in _fi.opname
               for _fi in false_instrs):
            false_expr = self._detect_comp_ternary(all_instrs, false_start - 1, append_idx)
        if false_expr is None:
            # [B242-V3R45] 假值区同样可能是 keep-or-pop 链
            # （`x if c else y and z` 的 `y and z`）：开启同族归约。
            false_expr = self.expr_reconstructor.reconstruct(
                false_instrs, fold_boolop_keep_or_pop=True)
            if false_expr is None:
                return None

        # walrus(ternary) 模式检测：ternary merge 块后跟
        # COPY 1 + STORE_* 序列（walrus 副作用捕获），将 IfExp 包装为
        # NamedExpr(target, IfExp)。
        # 字节码: <ternary merge> → COPY 1 → STORE_* n → LIST_APPEND/SET_ADD/YIELD_VALUE
        # 依「每块唯一归属」：COPY+STORE 块属于父推导式的 walrus 表达式，
        # 通过 NamedExpr 包装让 walrus 副作用保留在元素表达式中，避免
        # walrus 副作用指令被父推导式重复或丢失。
        if _merge_block_idx is not None:
            _post_merge = all_instrs[_merge_block_idx:append_idx]
            if (len(_post_merge) >= 2
                    and _post_merge[0].opname == 'COPY'
                    and _post_merge[0].arg == 1
                    and _post_merge[1].opname in (
                        'STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL')
                    and _post_merge[1].argval != '.0'):
                _walrus_target_name = _post_merge[1].argval
                return {
                    'type': 'NamedExpr',
                    'target': {
                        'type': 'Name',
                        'id': _walrus_target_name,
                        'ctx': 'Store',
                    },
                    'value': {
                        'type': 'IfExp',
                        'test': cond_expr,
                        'body': true_expr,
                        'orelse': false_expr,
                    },
                }

        # [B251-V3R56] 三元之前的「前缀 keep-or-pop 链」（`z and (<三元>)` /
        # `z or (<三元>)`）。CPython 3.11 对元素位 `z and (A if c else B)` 发射：
        #   cond_block:  <z 的操作数>; JUMP_IF_FALSE_OR_POP <merge>;  <c 的操作数>;
        #                POP_JUMP_FORWARD_IF_FALSE <B 入口>
        #   true_block:  A; JUMP_FORWARD <merge>
        #   false_block: B
        #   merge:       LIST_APPEND/SET_ADD/YIELD_VALUE
        # 短路语义：z 为假时 z 本身留在栈上直落 merge（结果即 z）；z 为真时弹出 z
        # 继续求值三元，三元值即结果 ⇒ 整组是 `z and <IfExp>`。既有通道把该跳转
        # 当普通条件跳转、cond_instrs 只取到栈顶（三元 test）⇒ 前缀 z 整段丢失
        # （实测产物 `['p' if x and y else 'q' ...]`，`CODE-LEN 17 vs 15`）。
        # ①识别条件（I.4 白名单：同层 opcode / 跳转 argval）：
        #   (1) cond_instrs 内的 keep-or-pop 跳转非空，且每条 argval 都等于该三元
        #       的汇合点偏移——这正是「短路时前缀自身即结果」的唯一落点（test 位
        #       自身是链式时由 cond_expr 携带整条 test，栈顶只留链末操作数）；
        #   (2) 追加点不是 MAP_ADD（dict 推导式键/值位另有专用通道）。
        # ②归约顺序：cond_instrs 内「末条 keep-or-pop 跳转」是前缀链与三元 test 链
        #   的唯一分界——前缀链（值位置 BoolOp）只发射 keep-or-pop，三元 test 由
        #   compiler_jump_if 发射、只含 POP_JUMP_* 弹跳（判定位无 keep-or-pop）。
        #   故只把 `cond_instrs[:末条 kop+1]` 以同族归约逐条处理（得单一 Pending），
        #   再把 IfExp 压顶、处理汇合点后缀并 flush，栈上唯一项即整组归约结果。
        #   把三元 test 链也一并逐条处理会让栈残留 test 操作数（实测 t004 得
        #   `[Pending, x, y]` 三项），违反「汇合前恰一项」契约。
        # ③唯一归属判定：前缀链、三元、汇合点后缀整体归属单一元素表达式。
        # ④嵌套处理：三元臂内/前缀内的同族形态由既有递归通道（B236/B250/
        #   假值区递归）各自归约，本段只做一层前缀。
        # ⑤入口引用语义：父推导式（append 协议）引用归约后的单一节点。
        # ⑥反编译流程：实测 `/tmp/r53/tcorpus.py` 的 `t004`/`t012` 等
        #   `[z and ("p" if (x and y) else "q") for x in xs]`（17 vs 15 指令）。
        # 任一守卫不命中时逐字返回原 IfExp（C3）。
        _b251_cut = None
        for _b251_ci, _b251_i in enumerate(cond_instrs):
            if _b251_i.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                _b251_cut = _b251_ci + 1
        if (_b251_cut is not None and merge_offset is not None
                and all(getattr(_i, 'argval', None) == merge_offset
                        for _i in cond_instrs[:_b251_cut]
                        if _i.opname in ('JUMP_IF_FALSE_OR_POP',
                                         'JUMP_IF_TRUE_OR_POP'))
                and append_idx < len(all_instrs)
                and all_instrs[append_idx].opname != 'MAP_ADD'):
            self.expr_reconstructor.reset()
            _b251_saved = self.expr_reconstructor._fold_boolop_keep_or_pop
            self.expr_reconstructor._fold_boolop_keep_or_pop = True
            try:
                for _b251_i in cond_instrs[:_b251_cut]:
                    self.expr_reconstructor._process_instruction(_b251_i)
                _b251_out = [s for s in self.expr_reconstructor.stack
                             if not (isinstance(s, dict)
                                     and s.get('type') == 'PUSH_NULL')]
                if (len(_b251_out) == 1 and isinstance(_b251_out[0], dict)
                        and _b251_out[0].get('type') == 'BoolOpPending'):
                    self.expr_reconstructor.stack = _b251_out + [{
                        'type': 'IfExp',
                        'test': cond_expr,
                        'body': true_expr,
                        'orelse': false_expr,
                    }]
                    if (_merge_block_idx is not None
                            and _merge_block_idx < append_idx):
                        for _b251_s in all_instrs[_merge_block_idx:append_idx]:
                            self.expr_reconstructor._process_instruction(_b251_s)
                    self.expr_reconstructor._b242_flush_boolop_pending()
                    _b251_final = [s for s in self.expr_reconstructor.stack
                                   if not (isinstance(s, dict)
                                           and s.get('type') == 'PUSH_NULL')]
                    if len(_b251_final) == 1:
                        return _b251_final[0]
            finally:
                self.expr_reconstructor._fold_boolop_keep_or_pop = _b251_saved

        # [B236-V3R39] 元素位三元的「前导压栈项 + 汇合点后缀消费」整组归约。
        # CPython 3.11 对元素位 ``F % (A if c else B)`` 发射：
        #   cond_block:  [STORE_<target>;] LOAD_CONST F; <c 的操作数>;
        #                POP_JUMP_FORWARD_IF_TRUE <B 入口>
        #   true_block:  LOAD_CONST A; JUMP_FORWARD <merge>
        #   false_block: LOAD_CONST B
        #   merge:       BINARY_OP %; YIELD_VALUE/LIST_APPEND/SET_ADD
        # 即前缀 F 在条件求值前压栈、三元值在 merge 块被 BINARY_OP 消费，二者
        # 共同构成元素表达式。本方法的 cond_instrs 从目标存储之后切起，
        # reconstruct 只返回栈顶（条件）⇒ 前缀 F 被静默丢弃；merge 块后缀除
        # walrus 外从不重建 ⇒ 产物只剩裸三元（`<genexpr>` 丢 '%-14s' 常量与
        # 尾部 %，co_consts 少该项、FOR_ITER 目标偏移前移）。
        # ①识别条件（I.4 白名单：同层指令 opcode / 栈净效应）：
        #   (1) 条件走单段整窗重建通道（布尔链折叠通道无前导项语义）；
        #   (2) cond_instrs 重建后非 PUSH_NULL 栈深 >= 2——栈顶是条件，其余
        #       是三元求值前压入的前导项；
        #   (3) merge 偏移到追加点之间存在后缀指令窗（非空）；
        #   (4) 追加点不是 MAP_ADD（dict 推导式 key/value 另有专用通道）。
        # ②归约顺序：前导项 + 三元值作初栈 → 逐条处理后缀指令 → 栈上唯一
        #   非 PUSH_NULL 项即整组归约结果；三元整体作为父节点的一个抽象
        #   子结点被外层运算消费。
        # ③唯一归属判定：前缀项、三元、后缀运算整体归属单一元素表达式，
        #   不留下游离指令。
        # ④嵌套处理：外层三元由父级同一通道递归处理，深度即嵌套层数。
        # ⑤入口引用语义：元素父（推导式 append 协议）引用归约后的单一节点。
        # ⑥反编译流程：实测 `scripts/pyc_verify.py::cmd_compare` 的
        #   ``'%-14s' % ('-' if ... else ...)`` 元素位形态（162 vs 156 字节）。
        # 任一守卫不命中时逐字返回原 IfExp（C3）。
        if (_b236_plain_cond and _merge_block_idx is not None
                and append_idx < len(all_instrs)
                and all_instrs[append_idx].opname != 'MAP_ADD'):
            self.expr_reconstructor.reset()
            for _b236_i in cond_instrs:
                self.expr_reconstructor._process_instruction(_b236_i)
            _b236_pre = [s for s in self.expr_reconstructor.stack
                         if not (isinstance(s, dict) and s.get('type') == 'PUSH_NULL')]
            _b236_suffix = all_instrs[_merge_block_idx:append_idx]
            if len(_b236_pre) >= 2 and _b236_suffix:
                _b236_seed = list(_b236_pre[:-1]) + [{
                    'type': 'IfExp',
                    'test': cond_expr,
                    'body': true_expr,
                    'orelse': false_expr,
                }]
                self.expr_reconstructor.reset()
                self.expr_reconstructor.stack = list(_b236_seed)
                for _b236_i in _b236_suffix:
                    self.expr_reconstructor._process_instruction(_b236_i)
                _b236_out = [s for s in self.expr_reconstructor.stack
                             if not (isinstance(s, dict) and s.get('type') == 'PUSH_NULL')]
                if len(_b236_out) == 1:
                    return _b236_out[0]

        # [B250-V3R55] 链式 test 的三元作元素位首个操作数、merge 块以 keep-or-pop
        # 打开后缀链（`("p" if x and y else "q") and z`、`z and (...)` 与
        # `(1 if <链> else 0) if w else 2` 的内层）。CPython 3.11 发射：
        #   <test 链段 + 各段假出口跳转>; 'p'; JUMP_FORWARD <merge>;
        #   'q'; merge: JUMP_IF_FALSE_OR_POP <listappend 前>; z
        # 上方 B236 通道只接「单段整窗」的 plain cond（其 cond_instrs 重建后栈上
        # 有前导压栈项）；链式 test 的 cond_instrs 各段本身就是 test 操作数，不能
        # 当前导项，故以三元值单独作初栈，开启同族 keep-or-pop 归约逐条处理后缀，
        # 栈上恰一项即整组结果（否则逐字返回裸 IfExp，[C3] 封闭）。
        if (not _b236_plain_cond and _merge_block_idx is not None
                and _merge_block_idx < append_idx
                and append_idx < len(all_instrs)
                and all_instrs[append_idx].opname != 'MAP_ADD'
                and all_instrs[_merge_block_idx].opname in (
                    'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP')):
            self.expr_reconstructor.reset()
            self.expr_reconstructor.stack = [{
                'type': 'IfExp',
                'test': cond_expr,
                'body': true_expr,
                'orelse': false_expr,
            }]
            _b250_saved = self.expr_reconstructor._fold_boolop_keep_or_pop
            self.expr_reconstructor._fold_boolop_keep_or_pop = True
            try:
                for _b250_i in all_instrs[_merge_block_idx:append_idx]:
                    self.expr_reconstructor._process_instruction(_b250_i)
                self.expr_reconstructor._b242_flush_boolop_pending()
            finally:
                self.expr_reconstructor._fold_boolop_keep_or_pop = _b250_saved
            _b250_out = [s for s in self.expr_reconstructor.stack
                         if not (isinstance(s, dict)
                                 and s.get('type') == 'PUSH_NULL')]
            if len(_b250_out) == 1:
                return _b250_out[0]

        # 构建IfExp节点
        return {
            'type': 'IfExp',
            'test': cond_expr,
            'body': true_expr,
            'orelse': false_expr,
        }

    def _r21_fold_boolop_test_chain(self, all_instrs: List[Instruction],
                                    seg_start: int,
                                    cond_jump_idx: int,
                                    false_target_offset: Any) -> Optional[Dict[str, Any]]:
        """[R21-2] 推导式三元 test 的「共享假出口布尔链」折叠（and 链）。

        [识别条件] 三元 test 指令区 [seg_start, cond_jump_idx) 内存在至少一条
          「前向、假出口型（opname 含 IF_FALSE / IF_NONE）、argval == 末端跳转的
          假出口偏移」的条件跳转，且末端跳转（索引 cond_jump_idx）本身也是假出口
          型。这正是 CPython 3.11 为 ``X if (A and B) else Y`` 发射的结构：每条操
          作数求值段之后各接一条指向同一 Else 出口的条件跳转。[R67-fix2]
          （本文件 :2253-2302）已识别该链并把条件区延伸到链尾，但它把整段交给
          通用重建器并假定「重建器会折叠为 BoolOp」——实测该假定不成立：
          ExpressionReconstructor.reconstruct 收到含中间假出口跳转的整段时只产出
          末端那一条 Compare，前段操作数连同其假出口跳转整段从产物消失
          （wizard_quant_api `get_DMI.calculate_di` 两个 <genexpr> 副本各丢 14 条
          指令 / 1 条 POP_JUMP_FORWARD_IF_FALSE，判据 Different control flow）。
        [归约方式] 以每条中间假出口跳转为界把条件区切成 n 段（n = 中间跳转数 + 1），
          每段自身是直线求值序列，逐段交回与单操作数情形完全相同的重建通道，再
          以 {'type': 'BoolOp', 'op': 'and', 'values': [...]} 组合；n < 2、任一段为空
          或任一段重建失败 ⇒ 返回 None，调用方逐字维持原单段路径（不猜、不降级）。
          区内出现回跳（BACKWARD）条件跳转或混合极性（IF_TRUE）⇒ 链不纯，返回 None。
        [AST 映射] ast.IfExp(test=ast.BoolOp(and, [Compare, Compare, ...]),
          body=Then, orelse=Else)——与单操作数情形同一条 IfExp 通道，仅 test 子树
          由单 Compare 变为 BoolOp；BoolOp dict 由 ast_converter._convert_boolop_full
          (:1195) 与 code_generator (:5252/:5327) 既有通道发射。
        [C1] 只读本推导式内层指令流的同层结构事实（opname / argval / 偏移），不读
          用户名、不读文件名、无偏移魔数；[C2] 每段唯一归属于 BoolOp 的一个操作数，
          中间假出口跳转不产生值、不归属任何节点，父区域不重入子区域；[C3] 严格附
          加：单操作数（无中间同假出口跳转）返回 None，产物逐字节不变。
        """
        if cond_jump_idx >= len(all_instrs):
            return None
        _FALSE_EXIT = ('IF_FALSE', 'IF_NONE')
        _tail = all_instrs[cond_jump_idx]
        if _tail.opname not in CONDITIONAL_JUMP_OPS:
            return None
        if not any(_t in _tail.opname for _t in _FALSE_EXIT):
            return None
        _cuts = []
        for _k in range(seg_start, cond_jump_idx):
            _i = all_instrs[_k]
            if _i.opname not in CONDITIONAL_JUMP_OPS:
                continue
            if 'BACKWARD' in _i.opname:
                return None
            if not any(_t in _i.opname for _t in _FALSE_EXIT):
                return None
            if _i.argval != false_target_offset:
                return None
            _cuts.append(_k)
        if not _cuts:
            return None
        _bounds = [seg_start] + [_c + 1 for _c in _cuts] + [cond_jump_idx]
        _values = []
        for _s, _e in zip(_bounds[:-1], _bounds[1:]):
            _seg = all_instrs[_s:_e]
            if not _seg:
                return None
            _node = self.expr_reconstructor.reconstruct(_seg)
            if _node is None:
                return None
            _values.append(_node)
        if len(_values) < 2:
            return None
        return {'type': 'BoolOp', 'op': 'and', 'values': _values}

    def _b256_filter_boolchain(self, all_instrs: List[Instruction],
                               store_idx: int, append_idx: int
                               ) -> Optional[Tuple[Dict[str, Any], int]]:
        """[B256-V3R58] 过滤器位「块划分 + compiler_jump_if 递归下降」整窗还原。

        ①算法依据（CPython 3.11 `compiler_jump_if` 文法，`compile.c`
        2897–2991 行）：过滤位每个 `if` 子句以 `compiler_jump_if(E, skip, 0)`
        发射，skip 为共用「跳过本轮」块。文法按表达式形状递归：`UnaryOp
        not` 只翻转 cond；`BoolOp` 取 `cond2 = (op == 'or')`，前 n-1 成员以
        (next2, cond2) 递归、末成员以 (next, cond) 递归（cond2 == cond 时
        不新建块、全员共用 next）；`IfExp` 的 test 以 (next2, 0) 递归、两臂
        各以 (next, cond) 递归并以 `JUMP end` 收尾；其余为叶子，发射
        `<值>; POP_JUMP_* next`。故窗内每条跳转的**极性**（cond）与**落点**
        （next / next2 / end / skip / 元素起点）唯一给出该段在文法里的位置。
        ②归约方式：先把窗按「跳转目标」与「跳转下一条」切成语义块（块内无
        外部入口、块只被一段引用），再自顶向下 `_parse(i, end, next, cond)`
        递归：叶子要求末条条件跳转的 argval == next；单块无条件跳转视为常量
        折叠臂（落点 == next 即假、否则为真）；多块则枚举 `nc`（本段末跳的
        「跳转发生」真值）与成员数 k 切分 BoolOp；IfExp 则枚举 test/body/
        orelse 三段边界（两臂各自的 `JUMP end` 蹦床可落到 end 或元素起点）。
        ③唯一归属判定：整窗必须从 `store_idx+1` 起连续覆盖到元素起点之前，
        且顶层落点集合只含 skip（与折叠臂直落元素起点这两个出口）；窗内
        其余跳转一律不得越出「窗内 ∪ {skip, 元素起点}」，否则整体放弃。
        ④嵌套处理：块划分与递归深度都不设上限（深度即真实嵌套层数），
        组内任何成员可再是组/三元/叶子，逐层黑箱还原。
        ⑤AST 映射接口：返回单个 BoolOp/UnaryOp/IfExp/Compare 节点与元素窗
        起点索引；调用方以既有 `[B98-V3R2]` 元素通道独立重建元素。
        ⑥反编译流程：CPython 3.11 对 `if (a if b else c) or d`、`if not (a if
        b else c)`、`if (a if b else c) and (d or a)`、`if ((a if b else c) if d
        else a)` 等发射的跳转落点同时落在「另一段起点」（握手）、「元素起点」
        （通过）、「跳过本轮」（失败）三类上；既有 `_extract_comp_ifs` 只按
        极性给项、`_detect_comp_ternary_as_filter` 只取三元本体，均会产生
        语义错或丢项。
        [C1] 只读窗内指令的 opname/argval/offset 与块边界（同层结构事实），
        不读用户名/常量值，无偏移魔数、无条数/深度上限；[C2] 每个块恰归属
        一个文法位置，段内表达式整体交既有重建器黑箱还原；[C3] 切块失败、
        落点越界、元素窗重建失败一律返回 None，调用方逐位沿用既有通道。
        """
        _UNCOND = ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                   'JUMP_BACKWARD_NO_INTERRUPT')

        def _is_jump(_i: Instruction) -> bool:
            return (_i.opname in CONDITIONAL_JUMP_OPS
                    or _i.opname in _UNCOND)

        _start = store_idx + 1
        if _start >= append_idx or append_idx >= len(all_instrs):
            return None
        _start_off = all_instrs[_start].offset
        _append_off = all_instrs[append_idx].offset

        # 跳过本轮落点：窗内条件跳转落到窗外的偏移。多个不同落点说明窗内
        # 另有结构（交既有通道，[C3]）。
        _skip_set = set()
        for _k in range(_start, append_idx):
            _i = all_instrs[_k]
            if _i.opname in CONDITIONAL_JUMP_OPS and _i.argval is not None:
                if not (_start_off <= _i.argval < _append_off):
                    _skip_set.add(_i.argval)
        if len(_skip_set) != 1:
            return None
        _skip = next(iter(_skip_set))

        # 块划分：以跳转目标偏移与跳转下一条为边界。
        _jump_idx = [_k for _k in range(_start, append_idx)
                     if _is_jump(all_instrs[_k])]
        _targets = set()
        for _k in _jump_idx:
            if all_instrs[_k].argval is not None:
                _targets.add(all_instrs[_k].argval)
        _bounds = {_start, append_idx}
        for _k in range(_start + 1, append_idx):
            if all_instrs[_k].offset in _targets:
                _bounds.add(_k)
        for _k in _jump_idx:
            _bounds.add(_k + 1)
        _bounds = sorted(_b for _b in _bounds if _start <= _b <= append_idx)
        _blocks = [(_bounds[_m], _bounds[_m + 1])
                   for _m in range(len(_bounds) - 1)]
        if not _blocks:
            return None
        _n = len(_blocks)
        _state = {'elt': None}

        def _blk_off(_bi: int) -> int:
            if _bi < _n:
                return all_instrs[_blocks[_bi][0]].offset
            return _append_off

        def _leaf_value(_bi: int, _bj: int) -> Optional[Dict[str, Any]]:
            """[bi, bj) 段（段末为跳转）整段还原为单个值。"""
            _s = _blocks[_bi][0]
            _e = _blocks[_bj - 1][1]
            if _e <= _s:
                return None
            if not _is_jump(all_instrs[_e - 1]):
                return None
            _seg = all_instrs[_s:_e - 1]
            if not _seg:
                return None
            for _k in range(_s, _e - 1):
                _i = all_instrs[_k]
                if _is_jump(_i):
                    if _i.argval is None:
                        return None
                    if not any(all_instrs[_k2].offset == _i.argval
                               for _k2 in range(_s, _e - 1)):
                        return None
            try:
                _v = self.expr_reconstructor.reconstruct(
                    _seg, fold_cond_jump_ternary=True,
                    fold_boolop_keep_or_pop=True,
                    fold_value_boolchain=True)
                _nl = len(self.expr_reconstructor.stack)
            except Exception:
                return None
            if _v is None or _nl != 1:
                return None
            return _v

        def _pred_of(_jmp: Instruction, _val: Dict[str, Any]
                     ) -> Tuple[Dict[str, Any], int]:
            """(_val 在跳转发生处的谓词, 该谓词为真时是否发生跳转)。"""
            if 'IF_NOT_NONE' in _jmp.opname:
                return ({'type': 'Compare', 'left': _val,
                         'ops': [{'type': 'IsNot'}],
                         'comparators': [{'type': 'Constant', 'value': None}]}, 1)
            if 'IF_NONE' in _jmp.opname:
                return ({'type': 'Compare', 'left': _val,
                         'ops': [{'type': 'Is'}],
                         'comparators': [{'type': 'Constant', 'value': None}]}, 1)
            return (_val, 1 if 'IF_TRUE' in _jmp.opname else 0)

        # 单比较器取反等价于翻转运算符：CPython 3.11 把 `is None` / `in`
        # 与紧随的 POP_JUMP 折叠成 IF_NOT_NONE/IF_NONE、CONTAINS_OP 反转
        # （compile.c 8870–8905 行），故 `not (a is None)` 与 `a is not None`
        # 在过滤位的跳转上下文里重编译字节码逐条相同；`COMPARE_OP` 族
        # （Eq/Lt/…）无此折叠，取反后字节码不同，不在本翻转集合内。
        _FLIP = {'Is': 'IsNot', 'IsNot': 'Is', 'is': 'is not', 'is not': 'is',
                 'In': 'NotIn', 'NotIn': 'In', 'in': 'not in', 'not in': 'in'}

        def _wrap(_expr: Dict[str, Any], _taken: int,
                  _cond: int) -> Dict[str, Any]:
            if _taken == _cond:
                return _expr
            if isinstance(_expr, dict) and _expr.get('type') == 'Compare':
                _ops = _expr.get('ops') or []
                _cmps = _expr.get('comparators') or []
                if len(_ops) == 1 and len(_cmps) == 1:
                    _op = _ops[0]
                    _name = _op.get('type') if isinstance(_op, dict) else _op
                    if _name in _FLIP:
                        _new = dict(_expr)
                        _new['ops'] = [{'type': _FLIP[_name]}]
                        return _new
            return {'type': 'UnaryOp', 'op': 'not', 'operand': _expr}

        def _tramp_ok(_bt: Instruction, _end: int) -> bool:
            _want = _blk_off(_end)
            _tgt = _bt.argval
            if _tgt == _want:
                return True
            # 常量折叠臂的 `JUMP end` 直接落到通过点（元素起点）
            if _state['elt'] is not None and _tgt == _state['elt']:
                return True
            if _end < _n:
                _s, _e = _blocks[_end]
                if (_e - _s == 1 and all_instrs[_s].opname in _UNCOND
                        and all_instrs[_s].argval == _tgt):
                    return True
            return False

        def _arm_const(_bi: int, _next_off: int):
            """折叠成裸无条件跳转的臂：落点为 next 即假常量，否则为真常量。"""
            if _bi >= _n:
                return None
            _s, _e = _blocks[_bi]
            if _e - _s != 1:
                return None
            _j = all_instrs[_s]
            if _j.opname not in _UNCOND or _j.argval is None:
                return None
            return ({'type': 'Constant',
                     'value': False if _j.argval == _next_off else True},
                    frozenset([_j.argval]))

        def _allowed(_next_off: Optional[int]) -> set:
            _out = {_skip}
            if _next_off is not None:
                _out.add(_next_off)
            if _state['elt'] is not None:
                _out.add(_state['elt'])
            return _out

        def _merge(_op: str, _vals: List[Dict[str, Any]]) -> Dict[str, Any]:
            _flat: List[Dict[str, Any]] = []
            for _v in _vals:
                if (isinstance(_v, dict) and _v.get('type') == 'BoolOp'
                        and _v.get('op') == _op):
                    _flat.extend(list(_v.get('values') or []))
                else:
                    _flat.append(_v)
            if len(_flat) == 1:
                return _flat[0]
            return {'type': 'BoolOp', 'op': _op, 'values': _flat}

        def _splits(_a: int, _b: int, _k: int):
            if _k == 1:
                yield [(_a, _b)]
                return
            for _cut in range(_a + 1, _b - _k + 2):
                for _rest in _splits(_cut, _b, _k - 1):
                    yield [(_a, _cut)] + _rest

        _memo: Dict[Tuple[int, int, Optional[int], int], Any] = {}

        def _try_boolop(_i: int, _end: int, _next_off: Optional[int],
                        _cond: int) -> Optional[Tuple[Dict[str, Any], frozenset]]:
            _len = _end - _i
            if _len < 2:
                return None
            for _nc in (_cond, 1 - _cond):
                for _cond2 in (0, 1):
                    _next2 = (_next_off if _cond2 == _nc else _blk_off(_end))
                    for _k in range(2, _len + 1):
                        for _cuts in _splits(_i, _end, _k):
                            _vals: List[Dict[str, Any]] = []
                            _tg = set()
                            _ok = True
                            for _m, (_a, _b) in enumerate(_cuts):
                                _nx = _next_off if _m == _k - 1 else _next2
                                _cd = _nc if _m == _k - 1 else _cond2
                                _r = _parse(_a, _b, _nx, _cd)
                                if _r is None:
                                    _ok = False
                                    break
                                _e, _t = _r
                                if _m != _k - 1 and not set(_t) <= {_nx}:
                                    _ok = False
                                    break
                                _vals.append(_e)
                                if _m == _k - 1:
                                    _tg |= set(_t)
                            if _ok:
                                _expr = _merge('or' if _cond2 else 'and', _vals)
                                return (_wrap(_expr, _nc, _cond),
                                        frozenset(_tg))
            return None

        def _try_ifexp(_i: int, _end: int, _next_off: Optional[int],
                       _cond: int) -> Optional[Tuple[Dict[str, Any], frozenset]]:
            if _end - _i < 2:
                return None
            _allow = _allowed(_next_off)
            for _nc in (_cond, 1 - _cond):
                for _t in range(_i + 1, _end):
                    for _j in range(_t, _end):
                        for _has_tramp in (True, False):
                            _o = _j + 1 if _has_tramp else _j
                            if _o > _end:
                                continue
                            if _has_tramp:
                                if _j >= _end:
                                    continue
                                _bt = all_instrs[_blocks[_j][1] - 1]
                                if _bt.opname not in _UNCOND:
                                    continue
                                if _blocks[_j][0] + 1 != _blocks[_j][1]:
                                    continue
                                if not _tramp_ok(_bt, _end):
                                    continue
                            _orelse_off = _blk_off(_o)
                            _rt = _parse(_i, _t, _orelse_off, 0)
                            if _rt is None:
                                continue
                            _et, _tt = _rt
                            if set(_tt) != {_orelse_off}:
                                continue
                            if _t == _j:
                                _rb = _arm_const(_j, _next_off)
                            else:
                                _rb = _parse(_t, _j, _next_off, _nc)
                            if _rb is None:
                                continue
                            _eb, _tb = _rb
                            if _o == _end:
                                _ro = _arm_const(_end, _next_off)
                            else:
                                _ro = _parse(_o, _end, _next_off, _nc)
                            if _ro is None:
                                continue
                            _eo, _to = _ro
                            if not (set(_tb) <= _allow and set(_to) <= _allow):
                                continue
                            _node = {'type': 'IfExp', 'test': _et,
                                     'body': _eb, 'orelse': _eo}
                            return (_wrap(_node, _nc, _cond),
                                    frozenset(set(_tb) | set(_to)))
            return None

        def _parse(_i: int, _end: int, _next_off: Optional[int],
                   _cond: int) -> Optional[Tuple[Dict[str, Any], frozenset]]:
            _key = (_i, _end, _next_off, _cond)
            if _key in _memo:
                return _memo[_key]
            _memo[_key] = None
            _res = _parse_impl(_i, _end, _next_off, _cond)
            _memo[_key] = _res
            return _res

        def _parse_impl(_i: int, _end: int, _next_off: Optional[int],
                        _cond: int
                        ) -> Optional[Tuple[Dict[str, Any], frozenset]]:
            if _i > _end or _i >= _n or _end > _n:
                return None
            if _i == _end:
                return ({'type': 'Constant', 'value': True if _cond == 0 else False},
                        frozenset())
            _last = all_instrs[_blocks[_end - 1][1] - 1]
            if _is_jump(_last):
                if _last.opname in CONDITIONAL_JUMP_OPS:
                    if _next_off is None or _last.argval == _next_off:
                        _v = _leaf_value(_i, _end)
                        if _v is not None:
                            _base, _taken = _pred_of(_last, _v)
                            return (_wrap(_base, _taken, _cond),
                                    frozenset([_last.argval]))
                else:
                    if (_end - _i == 1
                            and _blocks[_i][0] + 1 == _blocks[_i][1]
                            and (_last.argval == _next_off
                                 or _next_off is None)):
                        return ({'type': 'Constant',
                                 'value': False if _cond == 0 else True},
                                frozenset([_last.argval]))
            _r = _try_boolop(_i, _end, _next_off, _cond)
            if _r is not None:
                return _r
            return _try_ifexp(_i, _end, _next_off, _cond)

        _best: Optional[Tuple[Dict[str, Any], int]] = None
        for _e in range(1, _n + 1):
            _elt_off = _blk_off(_e)
            _state['elt'] = _elt_off
            _memo.clear()
            _r = _parse(0, _e, _skip, 0)
            if _r is None:
                continue
            _expr, _tg = _r
            if not set(_tg) <= {_skip, _elt_off}:
                continue
            if _skip not in set(_tg):
                continue
            # 跳转越界守卫：窗内每条跳转只许落到窗内或两个出口
            _ok = True
            for _bi in range(_e):
                _s, _en = _blocks[_bi]
                _li = all_instrs[_en - 1]
                if _is_jump(_li) and _li.argval is not None:
                    _t = _li.argval
                    if not (all_instrs[_s].offset <= _t < _elt_off):
                        if _t != _skip and _t != _elt_off:
                            _ok = False
                            break
            if not _ok:
                continue
            _elt_idx = _blocks[_e][0] if _e < _n else append_idx
            if _elt_idx >= append_idx:
                continue
            _seg = all_instrs[_elt_idx:append_idx]
            _bad = False
            for _i in _seg:
                if _is_jump(_i) and _i.argval is not None:
                    if _i.argval < _seg[0].offset or _i.argval >= _append_off:
                        _bad = True
            if _bad:
                continue
            try:
                _ve = self.expr_reconstructor.reconstruct(
                    _seg, fold_cond_jump_ternary=True,
                    fold_boolop_keep_or_pop=True)
                _nl = len(self.expr_reconstructor.stack)
            except Exception:
                continue
            if _ve is None or _nl != 1:
                continue
            _best = (_expr, _elt_idx)
        return _best

    def _detect_comp_ternary_as_filter(self, all_instrs: List[Instruction],
                                        store_idx: int,
                                        append_idx: int) -> Optional[Tuple[Dict[str, Any], int]]:
        """ 检测推导式中「三元作 if-filter」模式。

        模式: ``[elt for x in iter if (a if c else b)]``

        字节码特征:
            LOAD c
            POP_JUMP_FORWARD_IF_FALSE false_branch   # FORWARD 三元 cond
            LOAD a
            POP_JUMP_BACKWARD_IF_FALSE FOR_ITER       # filter skip
            JUMP_FORWARD merge
            false_branch:
            LOAD b
            POP_JUMP_BACKWARD_IF_FALSE FOR_ITER       # filter skip
            merge:
            <elt 表达式指令>                          # 元素（不属于三元）
            LIST_APPEND / YIELD_VALUE

        区分依据: BOTH 真假分支均以 ``POP_JUMP_BACKWARD_IF_FALSE → FOR_ITER``
        结束（filter skip 模式），且 merge 块与 LIST_APPEND 之间有元素指令。

        返回 ``(ternary_expr, elt_start_idx)`` 或 None。
        依「父引用子入口」：父推导式通过 merge 块的 elt 指令引用三元子节点
        作为 if-filter 条件，元素独立重建。
        """
        append_offset = all_instrs[append_idx].offset if append_idx < len(all_instrs) else float('inf')
        # async comprehension 内层用 GET_ANEXT 而非 FOR_ITER，
        # filter skip 跳回目标可能是 GET_ANEXT/SEND 块而非 FOR_ITER。
        # 此处不再强制要求 FOR_ITER 存在（async comp 由调用方上下文保证
        # 是推导式）。依「算法驱动」：守卫只看 BACKWARD 跳转特征，
        # 不硬编码跳转目标类型。

        # 查找 FORWARD 条件跳转（三元 cond）
        cond_jump_idx = None
        last_filter_end = store_idx
        for idx in range(store_idx + 1, append_idx):
            instr = all_instrs[idx]
            if instr.opname in CONDITIONAL_JUMP_OPS:
                if 'BACKWARD' in instr.opname:
                    last_filter_end = idx
                    continue
                if hasattr(instr, 'argval') and instr.argval is not None:
                    if instr.argval < append_offset:
                        cond_jump_idx = idx
                        break
                    return None
        if cond_jump_idx is None:
            return None

        cond_instr = all_instrs[cond_jump_idx]
        false_target_offset = cond_instr.argval
        cond_instrs = all_instrs[last_filter_end + 1:cond_jump_idx]

        # 在真值区域中查找 JUMP_FORWARD（标记 true_end 与 merge_offset）
        true_end = None
        false_start = None
        merge_offset = None
        for idx in range(cond_jump_idx + 1, append_idx):
            instr = all_instrs[idx]
            if instr.offset >= false_target_offset:
                if false_start is None:
                    false_start = idx
                break
            if instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD'):
                true_end = idx
                false_start = idx + 1
                if hasattr(instr, 'argval') and instr.argval is not None:
                    merge_offset = instr.argval
                break
        if true_end is None or false_start is None or merge_offset is None:
            # [B98-V3R2 修复] 折叠真值 orelse 的三元过滤器变体：
            # ``[elt for x in iter if (a if c else True)]``。CPython 将 filter
            # 位三元表达式的真值常量 orelse 折叠——cond 假路径直达通过点
            # （元素表达式起点），无假臂指令、无真臂尾 JUMP_FORWARD 融合标记
            # （Pattern B 型），真臂（含 filter 回跳）直接坠入通过点。
            # 识别条件（I.4 白名单：本窗内 opcode/跳转目标）：
            #   ① 无前导 filter 成员（last_filter_end 未被 BACKWARD 跳转推进，
            #      排除 ``A and (b if c else True)`` 多成员混合形）；
            #   ② cond 跳转为前向 IF_FALSE（IF_TRUE 是 R10 or-过滤器首成员
            #      与 B6-comp 混合链真臂尾跳的形态，均排除）；
            #   ③ 真臂（cond_jump 至 false_target 之间）非空、除末指令外无
            #      条件跳转（直线求值），末指令为 BACKWARD IF_FALSE 型
            #      filter 回跳（IF_TRUE 型真臂 = ``not b`` 极性，不在本支）；
            #   ④ false_target 即通过点：其后至 append 间无 BACKWARD 条件
            #      跳转（否则目标指向另一过滤器成员——B6-comp 混合链 or 尾
            #      成员 / Pattern B 假臂，均非折叠形态）。
            # 归约方式：IfExp(test=cond, body=真臂剥尾跳, orelse=Constant(True))
            # ——filter 位真值常量折叠不可分辨（True/1/"x" 同码），取规范真值
            # True。AST 映射：IfExp 过滤条件重编译回同一字节流（真值常量
            # orelse 在 filter 位由 CPython 编译器折叠，[C1] 编译器结构保证）。
            if (last_filter_end == store_idx
                    and 'IF_FALSE' in cond_instr.opname
                    and 'BACKWARD' not in cond_instr.opname):
                _folded_arm = all_instrs[cond_jump_idx + 1:false_start]
                _folded_pass_clean = not any(
                    _fi.opname in CONDITIONAL_JUMP_OPS and 'BACKWARD' in _fi.opname
                    for _fi in all_instrs[false_start:append_idx])
                if (_folded_arm
                        and _folded_arm[-1].opname in CONDITIONAL_JUMP_OPS
                        and 'BACKWARD' in _folded_arm[-1].opname
                        and 'IF_FALSE' in _folded_arm[-1].opname
                        and not any(_ai.opname in CONDITIONAL_JUMP_OPS
                                    for _ai in _folded_arm[:-1])
                        and _folded_pass_clean):
                    _fo_cond = self.expr_reconstructor.reconstruct(cond_instrs)
                    _fo_true = self.expr_reconstructor.reconstruct(_folded_arm[:-1])
                    if _fo_cond is not None and _fo_true is not None:
                        return (
                            {'type': 'IfExp', 'test': _fo_cond,
                             'body': _fo_true,
                             'orelse': {'type': 'Constant', 'value': True}},
                            false_start)
            return None

        true_instrs = all_instrs[cond_jump_idx + 1:true_end]
        false_end = false_start
        for idx in range(false_start, append_idx):
            if all_instrs[idx].offset >= merge_offset:
                break
            false_end = idx + 1
        false_instrs = all_instrs[false_start:false_end]

        # 关键守卫: BOTH 真假分支必须以 BACKWARD 条件跳转（filter skip）结束。
        # 否则不是 Pattern B（可能是普通元素三元 Pattern A，如 R9-19 walrus）。
        if not true_instrs or not false_instrs:
            return None
        true_last = true_instrs[-1]
        false_last = false_instrs[-1]
        if (true_last.opname not in CONDITIONAL_JUMP_OPS
                or 'BACKWARD' not in true_last.opname):
            return None
        # [E04f] 假值常量折叠变体：``[elt for x in iter if (a if c else 0)]``
        # 的 orelse 为恒假常量（0/False/None）时，CPython 把假臂折叠为
        # 无条件 JUMP_BACKWARD→循环头（comp_cond @22 实测；真值常量折叠
        # 已由上方 B98-V3R2 支取规范 True）。判据：假臂剥噪恰为单条无条
        # 件回跳且目标 = 循环头（FOR_ITER 偏移）→ orelse 取规范假值 0。
        _e04f_folded_false = False
        if (false_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                  'JUMP_ABSOLUTE')
                and len(false_instrs) == 1
                and false_last.argval is not None
                and any(i.opname == 'FOR_ITER' and i.offset == false_last.argval
                        for i in all_instrs[:store_idx + 1])):
            _e04f_folded_false = True
        if not _e04f_folded_false and (
                false_last.opname not in CONDITIONAL_JUMP_OPS
                or 'BACKWARD' not in false_last.opname):
            return None

        # 重建三元表达式（剥掉末尾 BACKWARD 跳转）
        cond_expr = self.expr_reconstructor.reconstruct(cond_instrs)
        if cond_expr is None:
            return None
        if 'IF_TRUE' in cond_instr.opname:
            cond_expr = {'type': 'UnaryOp', 'op': 'not', 'operand': cond_expr}
        true_expr = self.expr_reconstructor.reconstruct(true_instrs[:-1])
        if true_expr is None:
            return None
        # [E04f] 假值常量折叠：假臂是单条回循环头直跳（orelse=0/False/None
        # 恒假，编译器折叠）时跳过重建，取规范假值 0（重编译在 filter 位再
        # 次折叠为同一直跳，字节精确）。
        if _e04f_folded_false:
            false_expr = {'type': 'Constant', 'value': 0}
        else:
            false_expr = self.expr_reconstructor.reconstruct(false_instrs[:-1])
        if false_expr is None:
            return None

        ternary_expr = {
            'type': 'IfExp',
            'test': cond_expr,
            'body': true_expr,
            'orelse': false_expr,
        }

        # elt_start_idx: merge_offset 之后的第一条指令（元素表达式起点）
        elt_start_idx = None
        for idx in range(false_end, append_idx):
            if all_instrs[idx].offset >= merge_offset:
                elt_start_idx = idx
                break
        if elt_start_idx is None:
            return None

        # [B255-V3R57] 过滤器位的三元作为 and 链成员
        # （`(A if c else B) and D` / `D and (A if c else B)`）。
        # ①算法依据（CPython 3.11 `compiler_jump_if`，Python/compile.c
        #   2905–2944 行）：BoolOp(and) 的非末成员与末成员**共用同一 `next`**
        #   （`cond2 == cond` ⇒ `next2 = next`），故 and 链任一成员的「假」
        #   分支都直跳过滤器跳过点；IfExp 分支按同一函数 2926–2944 行发射，
        #   两臂同样以该 `next` 收尾。因此同一窗内依次出现：条件跳转之前的
        #   若干「前置 and 成员段」、三元本体、三元 `end` 汇合点之后的若干
        #   「续接 and 成员段」，最后才是元素表达式。
        # ②识别条件（I.4 白名单：同层 opcode / 跳转方向与 argval）：成员段
        #   以 BACKWARD 条件跳转收尾（过滤器位 skip 侧的唯一形态）、段内无
        #   条件跳转与无条件跳转；续接段自三元汇合点起逐段收集，最后一个
        #   跳转之后到追加点之间的余段**不得含任何跳转**（即元素窗为直线
        #   求值，无跳转歧义）；任一守卫不命中即保持既有 Pattern B 结果，
        #   不接管（C3）。
        # ③归约顺序：前置成员按源序 and-左折叠在三元之前、续接成员按源序
        #   and-右折叠在三元之后（同 `and` 按结合律并入单个 BoolOp）。
        # ④唯一归属判定：每段恰归属一个成员表达式；元素余段不参与过滤式，
        #   回给调用方作元素窗。
        # ⑤入口引用语义：父推导式引用单个 BoolOp 节点作唯一过滤条件。
        # ⑥反编译流程：实测 edge e31/e39（`(a if b else c) and b` /
        #   `a and (b if c else a)`；旧通道只取三元本体，and 成员整段流失，
        #   产物 18 vs 16 指令、FOR_ITER 36 vs 32）。
        def _b255_and_member(_seg_s: int, _seg_e: int,
                             _jmp: Any) -> Optional[Dict[str, Any]]:
            """[B255-V3R57] 过滤器 and 成员段 → 成员表达式（无跳转直线段）。"""
            if 'BACKWARD' not in _jmp.opname:
                return None
            if 'IF_NONE' in _jmp.opname or 'IF_NOT_NONE' in _jmp.opname:
                return None
            _seg = all_instrs[_seg_s:_seg_e]
            if not _seg:
                return None
            if any(_i.opname in CONDITIONAL_JUMP_OPS for _i in _seg):
                return None
            if any(_i.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                   for _i in _seg):
                return None
            _val = self.expr_reconstructor.reconstruct(_seg)
            if _val is None:
                return None
            if 'IF_TRUE' in _jmp.opname:
                return {'type': 'UnaryOp', 'op': 'not', 'operand': _val}
            return _val

        _b255_prefix_vals: List[Dict[str, Any]] = []
        _b255_prefix_ok = True
        if last_filter_end > store_idx:
            _b255_seg_s = store_idx + 1
            for _b255_k in range(store_idx + 1, last_filter_end + 1):
                if all_instrs[_b255_k].opname not in CONDITIONAL_JUMP_OPS:
                    continue
                _b255_m = _b255_and_member(
                    _b255_seg_s, _b255_k, all_instrs[_b255_k])
                if _b255_m is None:
                    _b255_prefix_ok = False
                    break
                _b255_prefix_vals.append(_b255_m)
                _b255_seg_s = _b255_k + 1
            if _b255_seg_s != last_filter_end + 1:
                _b255_prefix_ok = False
        if not _b255_prefix_ok:
            _b255_prefix_vals = []

        _b255_suffix_vals: List[Dict[str, Any]] = []
        _b255_suffix_ok = False
        _b255_merge_idx = None
        for _b255_k in range(false_end, append_idx):
            if all_instrs[_b255_k].offset >= merge_offset:
                _b255_merge_idx = _b255_k
                break
        if _b255_merge_idx is not None:
            _b255_seg_s = _b255_merge_idx
            _b255_seg_vals: List[Dict[str, Any]] = []
            _b255_last_jump = None
            for _b255_k in range(_b255_merge_idx, append_idx):
                if all_instrs[_b255_k].opname not in CONDITIONAL_JUMP_OPS:
                    continue
                _b255_m = _b255_and_member(
                    _b255_seg_s, _b255_k, all_instrs[_b255_k])
                if _b255_m is None:
                    _b255_seg_vals = []
                    break
                _b255_seg_vals.append(_b255_m)
                _b255_seg_s = _b255_k + 1
                _b255_last_jump = _b255_k
            else:
                _b255_leftover = all_instrs[_b255_seg_s:append_idx]
                _b255_clean = not any(
                    _i.opname in CONDITIONAL_JUMP_OPS
                    or _i.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                     'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                    for _i in _b255_leftover)
                if _b255_last_jump is not None and _b255_clean:
                    _b255_suffix_vals = _b255_seg_vals
                    _b255_suffix_ok = True
                    elt_start_idx = _b255_seg_s

        if _b255_prefix_vals or _b255_suffix_ok:
            ternary_expr = {
                'type': 'BoolOp',
                'op': 'and',
                'values': (list(_b255_prefix_vals)
                           + [ternary_expr]
                           + (_b255_suffix_vals if _b255_suffix_ok else [])),
            }

        return (ternary_expr, elt_start_idx)

    def _build_comp_result(self, code_obj: Any, elt_expr: Dict, generators: List[Dict]) -> Optional[Dict]:
        func_name = code_obj.co_name
        result = None
        if func_name == '<listcomp>':
            result = {'type': 'ListComp', 'elt': elt_expr, 'generators': generators}
        elif func_name == '<setcomp>':
            result = {'type': 'SetComp', 'elt': elt_expr, 'generators': generators}
        elif func_name == '<dictcomp>':
            if isinstance(elt_expr, tuple) and len(elt_expr) == 2:
                key_expr, value_expr = elt_expr
            else:
                key_expr = elt_expr
                value_expr = {'type': 'Constant', 'value': None}
            result = {'type': 'DictComp', 'key': key_expr, 'value': value_expr, 'generators': generators}
        elif func_name == '<genexpr>':
            result = {'type': 'GeneratorExp', 'elt': elt_expr, 'generators': generators}
        if result is None:
            return None
        # [B96] async 推导式标注（co_flags 元数据白名单，单一产出点）：
        # 编译器对含 await / async for 的推导式 code object 置
        # CO_COROUTINE(0x80) / CO_ASYNC_GENERATOR(0x200) 位（inspect 常量；
        # Python 3.11 实测：async <listcomp>/<setcomp>/<dictcomp> 恒置
        # 0x80，含 await 的 <genexpr> 恒置 0x200），并在调用点自动补发
        # GET_AWAITABLE+SEND 协议——源码不可能显式写 await(<推导式>)
        # （推导式求值为容器不可 await，唯一合法形态即 async 推导式的
        # 隐式协议）。标注供 CFGASTConverter._convert_await_expr_full 剥除
        # 该编译器补发的 Await 包装（a_three 形 ``acc.extend({k: await g(v)
        # for ...})``）；同步推导式（位为零）不标注，用户级 await 语义
        # 保持 ASTAwaitable 包裹（C3 显式豁免）。本方法是一切推导式
        # dict 的唯一组装点（convert_comprehension_objects / 表达式重建
        # / generate_comprehension_function 三路汇聚），单点标注全覆盖。
        if getattr(code_obj, 'co_flags', 0) & self._B96_ASYNC_COMP_FLAG_MASK:
            result['is_async_comp'] = 1
        return result

    def generate_comprehension_function(self, cfg) -> Dict[str, Any]:
        func_name = cfg.name
        comp_type_map = {
            '<listcomp>': 'ListComp',
            '<dictcomp>': 'DictComp',
            '<setcomp>': 'SetComp',
            '<genexpr>': 'GeneratorExp',
        }
        comp_type = comp_type_map.get(func_name, 'ListComp')

        code_obj = getattr(cfg, 'code', None)
        if code_obj is not None:
            iter_expr = {'type': 'Name', 'id': '.0', 'ctx': 'Load'}
            comp_ast = self.parse_comprehension_inner(code_obj, iter_expr)
            if comp_ast:
                return {'type': 'Module', 'body': [{'type': 'Expr', 'value': comp_ast}]}

        blocks = sorted(cfg.blocks.values(), key=lambda b: b.start_offset)
        all_instrs = []
        for block in blocks:
            all_instrs.extend(block.instructions)

        all_instrs = [i for i in all_instrs if i.opname not in ('RESUME', 'RETURN_VALUE', 'RETURN_CONST')]
        expr = self.expr_reconstructor.reconstruct(all_instrs)
        if expr:
            return {'type': 'Module', 'body': [{'type': 'Expr', 'value': expr}]}

        return {'type': 'Module', 'body': [{'type': 'Pass'}]}
