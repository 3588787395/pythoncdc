"""
Match Pattern解析器模块

职责：从字节码构建pattern AST节点，消除区域分析器中的跨职责逻辑。

提取自 region_analyzer.py 的 match pattern 解析逻辑，实现单一职责原则。
"""

from typing import List, Dict, Set, Optional, Any
from collections import deque

from .basic_block import BasicBlock, Instruction


class PatternParser:
    """Match Pattern解析器 - 职责：从字节码构建pattern AST节点"""

    # [P4-白名单] Pattern匹配相关操作码集合
    # 这些操作码用于识别match-case语句的pattern部分
    PATTERN_OPS = ('GET_LEN', 'UNPACK_SEQUENCE', 'COMPARE_OP',
                   'LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
                   'STORE_GLOBAL', 'STORE_DEREF',
                   'COPY', 'MATCH_KEYS', 'MATCH_MAPPING_KEYS')

    # 条件跳转操作码集合
    COND_JUMP_OPS = ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
                     'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE',
                     'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE',
                     'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE')

    # STORE操作码集合
    STORE_OPS = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')

    # LOAD变量操作码集合
    LOAD_VAR_OPS = ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF')

    # MATCH_*操作码集合
    MATCH_OPS = ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                 'MATCH_KEYS', 'MATCH_MAPPING_KEYS')

    def __init__(self):
        # UNPACK_EX上下文标记，用于跟踪扩展解包状态
        self._in_unpack_ex = False
        self._unpack_ex_fixed_count = 0
        self._unpack_store_idx = 0

    def parse_case_pattern(self, case_block: BasicBlock) -> Dict[str, Any]:
        """
        解析单个case的pattern，返回AST格式的pattern节点

        Args:
            case_block: 包含MATCH_*指令的case header块

        Returns:
            {
                'type': 'MatchSequence',  # 或 MatchClass/MatchMapping/MatchValue/MatchOr/MatchAs
                'patterns': [...],         # MatchSequence的子patterns
                'cls': {...},              # MatchClass的类引用
                'keys': [...],             # MatchMapping的键
                'as_name': str,            # 可选的as绑定
                ...
            }
        """
        return self._extract_case_pattern(case_block)

    def parse_case_guard(self, pattern_blocks: List[BasicBlock], allow_in_header_block: bool = False,
                         fail_case_offset: Optional[int] = None) -> Optional[Dict]:
        """
        解析guard条件，返回Compare AST节点或None

        Args:
            pattern_blocks: 模式相关的块列表
            allow_in_header_block: 允许 guard 与 case 头同块时提取（[B16] --
            仅当头块不归属任何 case body 时安全：体以独立块收集，头块内
            的守卫指令不会在体中重复发射）
            fail_case_offset: 守卫失败边目标（下一 case 头块偏移，[B16-C3]
            -- 供臂链极性判定：臂跳转目标 == fail 边 ⇔ 该臂以「测试失败」
            离开守卫）

        Returns:
            Compare类型的AST节点字典，或None
        """
        return self._extract_case_guard_from_blocks(pattern_blocks, allow_in_header_block,
                                                    fail_case_offset)

    def collect_pattern_blocks(self, case_block: BasicBlock, all_blocks: Set[BasicBlock]) -> List[BasicBlock]:
        """
        收集case的所有模式相关块（包括pattern continuation）

        用于Guard条件提取，因为STORE_FAST可能在后续块中

        Args:
            case_block: case header块
            all_blocks: 所有块的集合

        Returns:
            模式相关的块列表
        """
        return self._collect_pattern_blocks(case_block, all_blocks)

    def _collect_pattern_blocks(self, case_block: BasicBlock, all_blocks: Set[BasicBlock]) -> List[BasicBlock]:
        """收集case的所有模式相关块（包括pattern continuation）"""
        blocks = [case_block]
        visited = {case_block}

        last_instr = case_block.get_last_instruction()
        jump_target_offset = None
        if last_instr and last_instr.opname in self.COND_JUMP_OPS:
            jump_target_offset = last_instr.argval

        worklist = []
        for succ in case_block.successors:
            if jump_target_offset is not None and succ.start_offset == jump_target_offset:
                continue
            if succ not in visited:
                worklist.append(succ)
        CASE_HEADER_OPS = frozenset({
            'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
            'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
        })
        NEW_CASE_OPS = frozenset({
            'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
        })

        while worklist:
            current = worklist.pop()
            if current in visited:
                continue
            if current not in all_blocks:
                continue

            meaningful = [i for i in current.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            if not meaningful:
                visited.add(current)
                continue

            if any(i.opname in CASE_HEADER_OPS for i in meaningful):
                if any(i.opname in NEW_CASE_OPS for i in meaningful):
                    _first_real = next((i for i in meaningful if i.opname not in ('POP_TOP',)), meaningful[0])
                    if _first_real.opname in CASE_HEADER_OPS or _first_real.opname == 'COPY':
                        continue
                    if _first_real.opname in ('LOAD_NAME', 'LOAD_GLOBAL'):
                        _rest = meaningful[meaningful.index(_first_real)+1:]
                        if any(i.opname in NEW_CASE_OPS for i in _rest):
                            continue
                visited.add(current)
                blocks.append(current)
                cur_last = current.get_last_instruction()
                cur_jt_offset = None
                if cur_last and cur_last.opname in self.COND_JUMP_OPS:
                    cur_jt_offset = cur_last.argval
                for s in current.successors:
                    if s in visited:
                        continue
                    if s.start_offset == jump_target_offset:
                        continue
                    if cur_jt_offset is not None and s.start_offset == cur_jt_offset:
                        continue
                    meaningful_s = [i for i in s.instructions if i.opname not in ('RESUME','NOP','CACHE','PUSH_NULL')]
                    if meaningful_s and any(i.opname in NEW_CASE_OPS for i in meaningful_s):
                        _first_real_s = next((i for i in meaningful_s if i.opname not in ('POP_TOP',)), meaningful_s[0])
                        if _first_real_s.opname in CASE_HEADER_OPS or _first_real_s.opname == 'COPY':
                            continue
                        if _first_real_s.opname in ('LOAD_NAME', 'LOAD_GLOBAL'):
                            _rest_s = meaningful_s[meaningful_s.index(_first_real_s)+1:]
                            if any(i.opname in NEW_CASE_OPS for i in _rest_s):
                                continue
                    worklist.append(s)
                continue

            first_meaningful = meaningful[0] if meaningful else None
            if first_meaningful and first_meaningful.opname == 'COPY':
                continue

            is_pattern_block = False
            has_definitive_pattern = False
            is_guard_like = False
            DEFINITIVE_PATTERN_OPS = frozenset({
                'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
                'GET_LEN', 'UNPACK_SEQUENCE', 'UNPACK_EX',
                'UNPACK_EXTRACT',
            })
            for i in current.instructions:
                if i.opname in DEFINITIVE_PATTERN_OPS:
                    is_pattern_block = True
                    has_definitive_pattern = True
                    break

            if not has_definitive_pattern:
                meaningful = [i for i in current.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                has_compare_and_jump = (
                    any(i.opname in ('COMPARE_OP', 'IS_OP') for i in meaningful) and
                    any(i.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
                                    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE') for i in meaningful)
                )
                if has_compare_and_jump:
                    BODY_OPS = frozenset({
                        'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_MULTIPLY',
                        'BINARY_TRUE_DIVIDE', 'BINARY_FLOOR_DIVIDE', 'BINARY_MODULO',
                        'BINARY_POWER', 'BINARY_LSHIFT', 'BINARY_RSHIFT',
                        'BINARY_AND', 'BINARY_OR', 'BINARY_XOR',
                        'BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT',
                        'INPLACE_MULTIPLY', 'CALL', 'CALL_FUNCTION',
                        'GET_ITER', 'FOR_ITER', 'SEND',
                    })
                    has_body_op = any(i.opname in BODY_OPS for i in meaningful)
                    has_backward_jump = any(
                        i.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                                     'JUMP_BACKWARD')
                        for i in meaningful
                    )
                    _cond_jump_target = None
                    for i in meaningful:
                        if i.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
                                        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE'):
                            _cond_jump_target = i.argval
                            break
                    _jumps_within_body = (
                        _cond_jump_target is not None and
                        jump_target_offset is not None and
                        _cond_jump_target < jump_target_offset and
                        _cond_jump_target > current.start_offset
                    )
                    # 区域归约算法：guard块可能包含函数调用（如 len(x) > 0）
                    # 区分guard块与body块的关键：guard块的条件跳转目标指向下一个case
                    # （>= case的跳转目标），而body内的if语句跳转目标在body内（< case的跳转目标）
                    _jumps_to_next_case = (
                        _cond_jump_target is not None and
                        jump_target_offset is not None and
                        _cond_jump_target >= jump_target_offset
                    )
                    if not has_backward_jump and not _jumps_within_body:
                        if not has_body_op or _jumps_to_next_case:
                            is_pattern_block = True
                            is_guard_like = True

            # 识别简单变量 guard 块
            # 例如 `case Point(x=1, y=2) if z:` 的 guard `if z` 字节码为
            # LOAD_NAME z / POP_JUMP_FORWARD_IF_FALSE → after_match
            # 此类块无 DEFINITIVE_PATTERN_OPS 也无 COMPARE_OP，需要专门识别。
            # 关键判据：条件跳转目标 >= case 的跳转目标（指向下一个 case/after-match），
            # 与 body 内 if 语句（跳转目标在 body 内）区分。
            if not is_pattern_block:
                meaningful = [i for i in current.instructions
                              if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                if (len(meaningful) >= 2 and
                        meaningful[0].opname in self.LOAD_VAR_OPS and
                        meaningful[-1].opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
                                                   'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE')):
                    middle = meaningful[1:-1]
                    middle_ok = all(m.opname in ('POP_TOP',) for m in middle) or not middle
                    if middle_ok:
                        _simple_guard_jump_target = meaningful[-1].argval
                        _simple_jumps_to_next_case = (
                            _simple_guard_jump_target is not None and
                            jump_target_offset is not None and
                            _simple_guard_jump_target >= jump_target_offset
                        )
                        if _simple_jumps_to_next_case:
                            is_pattern_block = True
                            is_guard_like = True

            if not is_pattern_block:
                meaningful = [i for i in current.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in meaningful)
                if has_return:
                    is_pattern_block = False
                else:
                    has_store_only = all(
                        i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                    'LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
                                    'STORE_GLOBAL', 'STORE_DEREF',
                                    'UNPACK_SEQUENCE', 'UNPACK_EX',
                                    'POP_TOP', 'COPY', 'SWAP',
                                    'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                    'EXTENDED_ARG')
                        for i in current.instructions
                    )
                    if has_store_only:
                        is_pattern_block = True

            if is_pattern_block:
                visited.add(current)
                blocks.append(current)
                if not is_guard_like:
                    for s in current.successors:
                        if s not in visited:
                            worklist.append(s)
                else:
                    cur_last = current.get_last_instruction()
                    cur_jt_offset = None
                    if cur_last and cur_last.opname in self.COND_JUMP_OPS:
                        cur_jt_offset = cur_last.argval
                    CASE_HEADER_OPS = frozenset({
                        'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                        'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
                    })
                    for s in current.successors:
                        if s in visited:
                            continue
                        if s.start_offset == jump_target_offset:
                            continue
                        if cur_jt_offset is not None and s.start_offset == cur_jt_offset:
                            continue
                        meaningful_s = [i for i in s.instructions if i.opname not in ('RESUME','NOP','CACHE','PUSH_NULL')]
                        if meaningful_s and any(i.opname in CASE_HEADER_OPS for i in meaningful_s):
                            continue
                        worklist.append(s)

        return blocks

    def _extract_case_guard_from_blocks(self, pattern_blocks: List[BasicBlock],
                                        allow_in_header_block: bool = False,
                                        fail_case_offset: Optional[int] = None) -> Optional[Dict[str, Any]]:
        all_instrs = []
        for block in pattern_blocks:
            for instr in block.instructions:
                if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    all_instrs.append(instr)

        if not all_instrs:
            return None

        # 计算 case header 块（pattern_blocks[0]）的指令数。
        # 如果 guard 指令位于 case header 块内（guard_start < first_block_instr_count），
        # 说明 guard 与 case header 在同一基本块中（如 `case _ if x > 0` 的字节码：
        # LOAD_NAME x / POP_TOP / LOAD_NAME x / LOAD_CONST 0 / COMPARE_OP > / POP_JUMP_IF_FALSE）。
        # 此时不提取 guard，因为 body 收集以块为单位，无法从同一块中分离 guard 指令，
        # 提取后会导致 guard 在 body 中重复生成。对于 guard 在独立块的 case（如
        # `case Point(...) if z` 或 `case 1 if y > 0`），guard_start 在后续块中，
        # 不受此限制。
        first_block_instr_count = 0
        if pattern_blocks:
            first_block_instr_count = sum(
                1 for i in pattern_blocks[0].instructions
                if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
            )

        store_indices = []
        for i, instr in enumerate(all_instrs):
            if instr.opname in self.STORE_OPS:
                store_indices.append(i)

        search_start = 0
        if store_indices:
            search_start = store_indices[-1] + 1
        else:
            pattern_end_ops = ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                              'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
                              'UNPACK_SEQUENCE', 'UNPACK_EX', 'UNPACK_EXTRACT',
                              'COPY', 'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE',
                              'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE')
            for i in range(len(all_instrs) - 1, -1, -1):
                if all_instrs[i].opname in pattern_end_ops:
                    search_start = i + 1
                    break

        if search_start >= len(all_instrs):
            return None

        guard_start = None
        guard_end = None

        for i in range(search_start, len(all_instrs)):
            instr = all_instrs[i]

            if instr.opname in self.LOAD_VAR_OPS and guard_start is None:
                is_var_const = (
                    i + 2 < len(all_instrs) and
                    all_instrs[i + 1].opname == 'LOAD_CONST' and
                    all_instrs[i + 2].opname == 'COMPARE_OP'
                )
                is_var_var = (
                    i + 2 < len(all_instrs) and
                    all_instrs[i + 1].opname in self.LOAD_VAR_OPS and
                    all_instrs[i + 2].opname == 'COMPARE_OP'
                )
                is_is_op = (
                    i + 2 < len(all_instrs) and
                    all_instrs[i + 1].opname == 'LOAD_CONST' and
                    all_instrs[i + 2].opname == 'IS_OP'
                )
                # [B16-C3] 真值臂：LOAD x + POP_JUMP_*（``case a if not (a or y):``
                # 的臂为裸真值测试，极性由臂链提取器按跳转方向/目标判定）
                is_truthiness = (
                    i + 1 < len(all_instrs) and
                    all_instrs[i + 1].opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
                                                 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE')
                )
                # [B18] 算术/调用混合臂：LOAD_VAR 开头的表达式段（LOAD_*/
                # LOAD_CONST/BINARY_OP/COMPARE_OP/IS_OP/CONTAINS_OP/UNARY_*/
                # PRECALL/CALL），被极性条件跳转终止（``case Point(x=x, y=y)
                # if abs(x) + abs(y) <= 1:`` 的守卫臂含 CALL + BINARY_OP——
                # 简单比较形态不覆盖，守卫整体丢失）。段内含 COMPARE_OP 或
                # CALL（守卫必然是比较或调用真值），段界 = 首个条件跳转。
                _GUARD_EXPR_SCAN_OPS = frozenset({
                    'BINARY_OP', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP',
                    'UNARY_NEGATIVE', 'UNARY_NOT', 'UNARY_INVERT',
                    'PRECALL', 'CALL',
                })
                _is_expr_chain = False
                if i + 2 < len(all_instrs):
                    _k = i + 1
                    _has_cmp_or_call = False
                    while _k < len(all_instrs):
                        _op = all_instrs[_k].opname
                        if _op in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
                                   'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE'):
                            _is_expr_chain = _has_cmp_or_call
                            break
                        if (_op in _GUARD_EXPR_SCAN_OPS or _op in self.LOAD_VAR_OPS
                                or _op == 'LOAD_CONST'):
                            if _op in ('COMPARE_OP', 'CALL'):
                                _has_cmp_or_call = True
                            _k += 1
                            continue
                        break

                if (is_var_const or is_var_var or is_is_op or is_truthiness
                        or _is_expr_chain):
                    if is_var_const:
                        compare_op = all_instrs[i + 2].argval
                        if compare_op == '==' or compare_op == 2:
                            prev_instrs = all_instrs[:i]
                            has_store_or_unpack = any(
                                x.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                            'UNPACK_SEQUENCE', 'UNPACK_EX', 'MATCH_CLASS', 'MATCH_SEQUENCE',
                                            'MATCH_MAPPING', 'MATCH_KEYS')
                                for x in prev_instrs
                            )
                            if has_store_or_unpack:
                                # [B16] 捕获名重读例外：左操作数是先前 STORE
                                # 绑定的捕获名的重读（`case a if a == 1 or …`
                                # 的守卫臂 a == 1）——该比较是守卫臂而非模式
                                # 材料。栈协议：捕获 STORE 后守卫臂重读同名
                                # 变量参与比较；模式材料比较的操作数来自
                                # COPY 的栈顶副本（无 LOAD 重读）。
                                _left_is_capture_reload = (
                                    all_instrs[i].opname in self.LOAD_VAR_OPS
                                    and any(x.opname in self.STORE_OPS
                                            and x.argval == all_instrs[i].argval
                                            for x in prev_instrs))
                                if not _left_is_capture_reload:
                                    continue
                    guard_start = i
                    for j in range(i + 3, len(all_instrs)):
                        if all_instrs[j].opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
                                                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE'):
                            guard_end = j
                            break

        if guard_start is not None and guard_end is not None:
            # guard 位于 case header 块内时不提取（避免与 body 重复）
            # [B16] allow_in_header_block 例外：头块不归属任何 case body 时
            # （体以独立块收集，如捕获+守卫头 `case n if n < 0:` 与 break 块
            # 分离），头块内的守卫指令由 case_guards 消费，不会在体中重复
            # 发射——此时不提取反而丢失守卫（C3 守卫封闭）。
            if guard_start < first_block_instr_count and not allow_in_header_block:
                return None

            # [B16-C3] 守卫臂链提取（or/and/not 混合链的统一协议）。
            # 臂形态（CPython 短路链编译协议，均为同层结构事实）：
            #   (a) LOAD x, [LOAD_CONST c | LOAD y], (COMPARE|IS_OP) op, POP_JUMP_DIR → G
            #   (b) LOAD x, POP_JUMP_DIR → G（真值臂）
            # 极性结构事实（fail_case_offset = 下一 case 头偏移）：
            #   G == fail 边 ⇔ 该臂以「测试失败」离开守卫；G != fail ⇔ 以
            #   「测试成功」进入 case 体。臂贡献 = T（跳转方向与角色一致）
            #   或 UnaryOp(not, T)（方向与角色相反：IF_TRUE→fail 或
            #   IF_FALSE→pass）。链 op = 'and'（首臂目标 == fail 边）否则
            #   'or'。fail_case_offset 未知时回退首臂跳转方向启发式
            #   （first_jump_is_true，原行为：真→or/正臂，假→and/正臂）。
            # 终止：臂形状不再匹配（体材料的指令形态必然不同）。
            # [C1] 只读 pattern_blocks 的指令序列与跳转目标；[C2] 不窥视
            # 子/父区域；[C3] fail 边（下一 case 头）是 case 链的显式结构
            # 事实，极性判定与 case 位置/嵌套深度无关。
            _POP_TRUE = ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE')
            _POP_FALSE = ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE')
            _POP_ALL = _POP_TRUE + _POP_FALSE

            def _mr_guard_arm(pos):
                """从 pos 解析一个守卫臂 → (test, jump_dir_is_true, target, next_pos) 或 None"""
                if pos >= len(all_instrs) or all_instrs[pos].opname not in self.LOAD_VAR_OPS:
                    return None
                # 形态 a: LOAD x, LOAD_CONST c, COMPARE/IS_OP, POP_JUMP → G
                if (pos + 3 < len(all_instrs)
                        and all_instrs[pos + 1].opname == 'LOAD_CONST'
                        and all_instrs[pos + 2].opname in ('COMPARE_OP', 'IS_OP')
                        and all_instrs[pos + 3].opname in _POP_ALL):
                    test = {
                        'type': 'Compare',
                        'left': {'type': 'Name', 'id': all_instrs[pos].argval},
                        'ops': [{'type': 'CompareOp', 'op': all_instrs[pos + 2].argval}],
                        'right': {'type': 'Constant', 'value': all_instrs[pos + 1].argval},
                    }
                    return (test, all_instrs[pos + 3].opname in _POP_TRUE,
                            all_instrs[pos + 3].argval, pos + 4)
                # 形态 a': LOAD x, LOAD y, COMPARE, POP_JUMP → G（变量-变量比较）
                if (pos + 3 < len(all_instrs)
                        and all_instrs[pos + 1].opname in self.LOAD_VAR_OPS
                        and all_instrs[pos + 2].opname in ('COMPARE_OP', 'IS_OP')
                        and all_instrs[pos + 3].opname in _POP_ALL):
                    test = {
                        'type': 'Compare',
                        'left': {'type': 'Name', 'id': all_instrs[pos].argval},
                        'ops': [{'type': 'CompareOp', 'op': all_instrs[pos + 2].argval}],
                        'right': {'type': 'Name', 'id': all_instrs[pos + 1].argval},
                    }
                    return (test, all_instrs[pos + 3].opname in _POP_TRUE,
                            all_instrs[pos + 3].argval, pos + 4)
                # 形态 b: LOAD x, POP_JUMP → G（真值臂）
                if (pos + 1 < len(all_instrs)
                        and all_instrs[pos + 1].opname in _POP_ALL):
                    test = {'type': 'Name', 'id': all_instrs[pos].argval}
                    return (test, all_instrs[pos + 1].opname in _POP_TRUE,
                            all_instrs[pos + 1].argval, pos + 2)
                # 形态 c: [B16] 算术臂（LOAD x; <表达式段>; POP_JUMP → G）。
                # 守卫臂含计算（`case n if n > 0 and x % 2 == 0:` 的第二臂
                # `x % 2 == 0` = LOAD x; LOAD_CONST 2; BINARY_OP; LOAD_CONST 0;
                # COMPARE; POP_JUMP）——形态 a/a' 只覆盖单比较臂，算术臂使
                # 臂链在此截断（守卫退化为首臂，and 尾臂整体丢失）。识别
                # 条件 = LOAD_VAR 开头的表达式段（仅 LOAD_*/LOAD_CONST/
                # BINARY_OP/COMPARE_OP/IS_OP/CONTAINS_OP/UNARY_*）被极性
                # 条件跳转终止，且段内含计算指令（BINARY_OP/CONTAINS_OP/
                # UNARY_*——纯比较段已由形态 a/a' 消费，不重复进入）。
                # 归约方式 = _eval_guard_expr_stack 的操作数栈求值（与
                # _extract_arithmetic_guard 同一归约器）；AST 映射 = Compare/
                # BinOp/UnaryOp 守卫子表达式。
                # [C1] 只读 all_instrs 指令流；[C2] 不窥视子/父区域；
                # [C3] 段边界由操作码集合与跳转极性封闭，无名字/位置特例。
                if (pos + 1 < len(all_instrs)
                        and all_instrs[pos].opname in self.LOAD_VAR_OPS):
                    _EXPR_SCAN_OPS = frozenset({
                        'BINARY_OP', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP',
                        'UNARY_NEGATIVE', 'UNARY_NOT', 'UNARY_INVERT',
                        'PRECALL', 'CALL',
                    })
                    _COMPUTE_OPS = frozenset({
                        'BINARY_OP', 'CONTAINS_OP', 'UNARY_NEGATIVE',
                        'UNARY_NOT', 'UNARY_INVERT', 'CALL',
                    })
                    _j = pos + 1
                    while (_j < len(all_instrs)
                           and (all_instrs[_j].opname in _EXPR_SCAN_OPS
                                or all_instrs[_j].opname in self.LOAD_VAR_OPS
                                or all_instrs[_j].opname == 'LOAD_CONST')):
                        _j += 1
                    if (_j < len(all_instrs) and _j > pos + 1
                            and all_instrs[_j].opname in _POP_ALL
                            and any(all_instrs[_k].opname in _COMPUTE_OPS
                                    for _k in range(pos, _j))):
                        _expr = self._eval_guard_expr_stack(all_instrs[pos:_j])
                        if _expr is not None:
                            return (_expr, all_instrs[_j].opname in _POP_TRUE,
                                    all_instrs[_j].argval, _j + 1)
                return None

            first_jump_is_true = (
                all_instrs[guard_end].opname in _POP_TRUE
            )
            _first_target = all_instrs[guard_end].argval

            comparisons = []
            _pos = guard_start
            _first_arm_target = None
            while True:
                _arm = _mr_guard_arm(_pos)
                if _arm is None:
                    break
                _test, _dir_true, _target, _pos = _arm
                if _first_arm_target is None:
                    _first_arm_target = _target
                if fail_case_offset is not None:
                    _to_fail = (_target == fail_case_offset)
                    _inverted = (( _dir_true and _to_fail)
                                 or ((not _dir_true) and (not _to_fail)))
                else:
                    # 回退：首臂方向启发式，臂一律正臂（原行为）
                    _inverted = False
                if _inverted:
                    _test = {'type': 'UnaryOp', 'op': 'not', 'operand': _test}
                comparisons.append(_test)

            if not comparisons:
                return None

            if fail_case_offset is not None and _first_arm_target is not None:
                _chain_op = 'and' if _first_arm_target == fail_case_offset else 'or'
            else:
                _chain_op = 'or' if first_jump_is_true else 'and'

            if len(comparisons) == 1:
                result = comparisons[0]
            else:
                result = {
                    'type': 'BoolOp',
                    'op': _chain_op,
                    'values': comparisons
                }

            return result

        if guard_start is None:
            for i in range(search_start, len(all_instrs)):
                instr = all_instrs[i]
                if instr.opname in self.LOAD_VAR_OPS:
                    if (i + 1 < len(all_instrs) and
                        all_instrs[i + 1].opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE')):
                        # guard 位于 case header 块内时不提取
                        if i < first_block_instr_count:
                            break
                        # 简单变量 guard（如 `if z`）允许外部变量
                        # _collect_pattern_blocks 已通过跳转目标分析区分 guard 与 body if
                        var_name = instr.argval
                        return {'type': 'Name', 'id': var_name}

        if guard_start is None and search_start > 0:
            # [B12 伴生修复] capture+guard 算术守卫链回退（如
            # `case v if v % 2 == 0:` → 守卫 v % 2 == 0）。识别/归约/映射三要素
            # 与 [C1]/[C2]/[C3] 条款见 _extract_arithmetic_guard docstring。
            # 守卫与模式头同块（capture+guard 形态守卫紧跟模式头 STORE），
            # case 体在后续块（守卫跳转终止头块），不与 body 重复生成；
            # search_start > 0（头块存在模式头 STORE）排除通配+guard 形态
            # （守卫前无 STORE，链起点在头块且该块即 body 载体，维持原
            # 「不提取」行为避免重复）。
            _arith = self._extract_arithmetic_guard(
                all_instrs, search_start, first_block_instr_count)
            if _arith is not None:
                return _arith

        if guard_start is None:
            for i in range(search_start, len(all_instrs)):
                instr = all_instrs[i]
                if instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL') and i + 1 < len(all_instrs):
                    func_name = instr.argval
                    call_idx = None
                    for j in range(i + 1, min(i + 10, len(all_instrs))):
                        if all_instrs[j].opname == 'CALL':
                            call_idx = j
                            break
                        if all_instrs[j].opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
                                                    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE'):
                            break
                    if call_idx is not None and call_idx + 3 < len(all_instrs):
                        if (all_instrs[call_idx + 1].opname == 'LOAD_CONST' and
                            all_instrs[call_idx + 2].opname == 'COMPARE_OP' and
                            all_instrs[call_idx + 3].opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE')):
                            compare_op = all_instrs[call_idx + 2].argval
                            right_val = all_instrs[call_idx + 1].argval
                            call_args = []
                            for j in range(i + 1, call_idx):
                                if all_instrs[j].opname in self.LOAD_VAR_OPS:
                                    call_args.append({'type': 'Name', 'id': all_instrs[j].argval})
                            return {
                                'type': 'Compare',
                                'left': {
                                    'type': 'Call',
                                    'func': {'type': 'Name', 'id': func_name},
                                    'args': call_args
                                },
                                'ops': [{'type': 'CompareOp', 'op': compare_op}],
                                'right': {'type': 'Constant', 'value': right_val}
                            }

        return None

    def _extract_arithmetic_guard(self, all_instrs: List['Instruction'],
                                  search_start: int,
                                  first_block_instr_count: int) -> Optional[Dict[str, Any]]:
        """[B12 伴生修复] capture+guard 算术守卫链提取（`case v if v % 2 == 0:`）。

        【识别条件】模式头 STORE 之后（search_start 起）的**首个模式块内**
        存在 LOAD_VAR 开头的守卫表达式链：仅含 LOAD_VAR / LOAD_CONST /
        BINARY_OP / COMPARE_OP / IS_OP / CONTAINS_OP，链被 fail 极性条件跳转
        （IF_FALSE/IF_NONE/IF_NOT_NONE——模式失败→下一 case 的结构边）终止；
        多段链（and/or 组合，段间以条件跳转分界）按段收集。守卫与模式头同块
        是 capture+guard 的字节码形态（``COPY; STORE v; <守卫>; JUMP_FALSE→
        下一case``），守卫跳转终止头块 ⇒ case 体在后续块，提取不与 body 重复；
        search_start > 0（头块存在模式头 STORE）排除通配+guard 形态（该形态
        头块即 body 载体，维持原「不提取」行为防重复）。

        【归约方式】CPython 3.11 栈式字节码的后缀表达式结构事实：操作数栈
        求值（LOAD_*→Name/Constant，BINARY_OP→BinOp，COMPARE_OP/IS_OP/
        CONTAINS_OP→Compare）；多段按既有约定组合——首段跳转为 IF_TRUE
        （or-guard 成功边）⇒ BoolOp 'or'，否则 'and'。

        【AST 映射】→ Compare / BoolOp 守卫 dict（与既有 guard 词汇一致），
        由 ast_converter._convert_expression 转换为守卫表达式。

        [C1] 只读 pattern_blocks 指令流（L(A) 局部）；[C2] 守卫是 match_case
        的接口组成部分，不窥视任何子区域内部；[C3] 链边界由操作码集合与
        fail 边极性驱动（跳转极性是操作码语义，不是 case 位置特例），链起点
        以「模式头 STORE 在前」封闭（显式守卫排除通配形态），任意嵌套深度/
        case 链位置同判——嵌套无感。
        """
        EXPR_OPS = frozenset({
            'BINARY_OP', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP',
            'UNARY_NEGATIVE', 'UNARY_NOT', 'UNARY_INVERT',
        })
        FAIL_OPS = frozenset({
            'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
            'POP_JUMP_BACKWARD_IF_FALSE',
            'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE',
            'POP_JUMP_BACKWARD_IF_NONE',
            'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE',
            'POP_JUMP_BACKWARD_IF_NOT_NONE',
        })
        TRUE_OPS = frozenset({
            'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE',
            'POP_JUMP_BACKWARD_IF_TRUE',
        })
        n = len(all_instrs)
        for i in range(search_start, min(n, first_block_instr_count)):
            if all_instrs[i].opname not in self.LOAD_VAR_OPS:
                continue
            segments = []  # (expr, jump_opname)
            cur = i
            j = i
            aborted = False
            while j < min(n, first_block_instr_count):
                op = all_instrs[j].opname
                if op in ('PRECALL', 'CALL'):
                    # [B18] 调用协议操作码属守卫表达式段（与
                    # _eval_guard_expr_stack 的 CALL/PRECALL 支持一致）
                    j += 1
                    continue
                if op in FAIL_OPS or op in TRUE_OPS:
                    expr = self._eval_guard_expr_stack(all_instrs[cur:j])
                    if expr is None:
                        aborted = True
                        break
                    segments.append((expr, op))
                    j += 1
                    # 守卫链继续条件：跳转后紧跟 LOAD_VAR（and/or 组合段）
                    if j < min(n, first_block_instr_count) and all_instrs[j].opname in self.LOAD_VAR_OPS:
                        cur = j
                        continue
                    break
                if op in EXPR_OPS or op in self.LOAD_VAR_OPS or op == 'LOAD_CONST':
                    j += 1
                    continue
                break
            if aborted or not segments:
                continue
            if len(segments) == 1:
                return segments[0][0]
            first_jump_is_true = segments[0][1] in TRUE_OPS
            return {
                'type': 'BoolOp',
                'op': 'or' if first_jump_is_true else 'and',
                'values': [seg[0] for seg in segments],
            }
        return None

    _BINARY_OP_ARG_MAP = {
        # CPython 3.11+ BINARY_OP argval 是 NB 表整数 arg（0=NB_ADD…），非符号
        # 字符串；与 region_ast_generator._binary_op_arg_to_str 同表同义。
        0: '+',   1: '&',   2: '//',  3: '<<',  4: '@',   5: '*',
        6: '%',   7: '|',   8: '**',  9: '>>',  10: '-',  11: '/',  12: '^',
    }

    def _eval_guard_expr_stack(self, instrs: List['Instruction']) -> Optional[Dict[str, Any]]:
        """[B12 伴生修复] 对守卫表达式链做操作数栈求值（见
        _extract_arithmetic_guard docstring 的识别/归约/映射三要素与
        C1/C2/C3 条款）。链中出现任何非表达式操作码（STORE/POP_TOP/跳转等）
        即判非纯表达式返回 None（保守回退，不猜测）。"""
        stack = []
        for ins in instrs:
            op = ins.opname
            if op in self.LOAD_VAR_OPS:
                stack.append({'type': 'Name', 'id': ins.argval})
            elif op == 'LOAD_CONST':
                stack.append({'type': 'Constant', 'value': ins.argval})
            elif op == 'PRECALL':
                # 3.11 调用协议前置标记（参数个数），无栈效果
                continue
            elif op == 'CALL':
                # [B18] 调用：弹出 argval 个实参与可调用对象 → Call 节点
                #（``case Point(x=x, y=y) if abs(x) + abs(y) <= 1:`` 的守卫
                # 臂含函数调用——纯比较求值器不覆盖即返回 None，守卫整体
                # 丢失）。LOAD_GLOBAL/LOAD_NAME 已由 LOAD_VAR_OPS 分支压入
                # Name 节点，实参同理；求值顺序 = 操作数栈后缀结构事实。
                # [C1] 只读指令流；[C2] 不窥视子/父区域；[C3] CALL/PRECALL
                # 是 CPython 调用协议操作码，非位置特例。
                _nargs = ins.argval if isinstance(ins.argval, int) else 0
                if len(stack) < _nargs + 1:
                    return None
                _args = [stack.pop() for _ in range(_nargs)]
                _func = stack.pop()
                _args.reverse()
                stack.append({'type': 'Call', 'func': _func, 'args': _args})
            elif op == 'BINARY_OP':
                if len(stack) < 2:
                    return None
                right = stack.pop()
                left = stack.pop()
                opval = self._BINARY_OP_ARG_MAP.get(ins.argval, ins.argval) \
                    if isinstance(ins.argval, int) else ins.argval
                stack.append({'type': 'BinOp', 'left': left, 'op': opval, 'right': right})
            elif op in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP'):
                if len(stack) < 2:
                    return None
                right = stack.pop()
                left = stack.pop()
                opval = ins.argval
                if op == 'IS_OP':
                    opval = 'is' if not ins.argval else 'is not'
                elif op == 'CONTAINS_OP':
                    opval = 'in' if not ins.argval else 'not in'
                stack.append({
                    'type': 'Compare',
                    'left': left,
                    'ops': [{'type': 'CompareOp', 'op': opval}],
                    'right': right,
                })
            else:
                return None
        # [B18] 段结果节点类型放宽：Compare（比较臂）/ Call（调用真值臂）/
        # BinOp/Name/Constant 均为合法守卫子表达式——求值器只保证「段是单一
        # 纯表达式节点」，类型判定交由臂链装配。
        if len(stack) == 1 and isinstance(stack[0], dict):
            return stack[0]
        return None

    def _find_real_match_header(self, partial_block: BasicBlock) -> Optional[BasicBlock]:
        """
        向前查找包含MATCH_*指令的真正case header

        当_collect_match_body错误地将pattern中间的块（如LOAD_CONST+COMPARE_OP）识别为
        独立的case header时，使用此方法找到真正的case header（包含MATCH_SEQUENCE等）

        Args:
            partial_block: 只包含部分pattern指令的块

        Returns:
            包含MATCH_*指令的真正case header，如果找不到则返回None
        """
        MATCH_OPS = {'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                    'MATCH_KEYS', 'MATCH_MAPPING_KEYS'}

        # [B16] 前驱 BFS 限定「fall-through 连续边」：partial 块必须是候选
        # header 经 fall-through（非条件跳转目标）路径连续可达的后继——
        # 结构型模式（MATCH_SEQUENCE 后接 GET_LEN/UNPACK 检查块）的
        # continuation 块经 header 的真值路径（fall-through）到达；而链上
        # **下一个 case** 的检查块经前一个 case 的条件跳转目标（false 边）
        # 到达。不限定边极性时，match 嵌套在结构型 match 内的多 case 字面量
        # 链（`case 'num':`）会把外层/前序 case 的 MATCH_* 头误认为本块
        # header，模式被改写为序列形状（r4_12 nested_match_seq 形态）。
        # [C1] 只读前驱边与块指令；[C2] 不窥视区域内部；[C3] 跳转边极性
        # （false 目标 = 下一 case）是编译器显式结构事实，嵌套无感。
        def _connected_by_fallthrough(header_block: BasicBlock) -> bool:
            visited_f = {partial_block}
            worklist_f = [partial_block]
            while worklist_f:
                cur = worklist_f.pop()
                if cur is header_block:
                    return True
                for pred in cur.predecessors:
                    if pred in visited_f:
                        continue
                    pred_last = pred.get_last_instruction()
                    if (pred_last is not None
                            and pred_last.opname in self.COND_JUMP_OPS
                            and pred_last.argval is not None
                            and cur.start_offset == pred_last.argval):
                        continue  # cur 是 pred 的条件跳转目标（false 边）——非 continuation
                    visited_f.add(pred)
                    worklist_f.append(pred)
            return False

        # BFS向前搜索（通过前驱块）
        visited = {partial_block}
        worklist = list(partial_block.predecessors)

        while worklist:
            current = worklist.pop()
            if current in visited:
                continue
            visited.add(current)

            # 检查是否包含MATCH_*指令
            if any(i.opname in MATCH_OPS for i in current.instructions):
                if _connected_by_fallthrough(current):
                    return current
                # 非 fall-through 连续的 MATCH_* 块是别的 case 的头，继续向前
                # 搜索（保持旧行为的搜索范围，只是不接受该候选）

            # 继续向前搜索
            worklist.extend(current.predecessors)

        return None

    def _collect_all_pattern_instrs(self, case_block: BasicBlock) -> List[Instruction]:
        """
        从case_block开始，沿成功路径收集所有pattern相关指令

        核心算法：沿"成功"路径（非跳转目标）BFS收集，直到遇到body指令。
        关键改进：对于混合了pattern和body指令的块，只提取pattern部分。

        Args:
            case_block: case header块

        Returns:
            按偏移量排序的pattern指令列表
        """
        all_instrs = []
        seen_offsets = set()

        # 从case_block开始，沿成功路径收集所有指令
        # 成功路径：每个条件跳转块的"fall-through"后继（非跳转目标）
        visited = set()
        queue = deque([case_block])

        while queue:
            blk = queue.popleft()
            if blk in visited:
                continue
            visited.add(blk)

            for instr in blk.instructions:
                if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    continue
                if instr.offset not in seen_offsets:
                    seen_offsets.add(instr.offset)
                    all_instrs.append(instr)

            # 确定要继续搜索的后继块
            last = blk.get_last_instruction()
            if last and last.opname in self.COND_JUMP_OPS:
                # 条件跳转块：沿fall-through路径继续（非跳转目标的后继）
                jump_target = last.argval
                for succ in blk.successors:
                    if succ.start_offset != jump_target:
                        queue.append(succ)
                        break
                # 也沿跳转目标继续（可能包含更多pattern指令）
                for succ in blk.successors:
                    if succ.start_offset == jump_target:
                        # 检查跳转目标是否是pattern块（而非下一个case或body）
                        if self._is_pattern_continuation_block(succ, blk):
                            queue.append(succ)
                        break
            elif last and last.opname not in ('RETURN_VALUE', 'RETURN_CONST',
                                               'JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                # 非条件跳转块：检查所有后继
                for succ in blk.successors:
                    queue.append(succ)

        # 按偏移量排序
        all_instrs.sort(key=lambda i: i.offset)
        return all_instrs

    def _is_pattern_continuation_block(self, block: BasicBlock, pred: BasicBlock) -> bool:
        """
        判断块是否是pattern的延续（而非下一个case header或body）

        基于字节码特征：pattern延续块包含UNPACK、COMPARE_OP、STORE_等指令，
        但不包含MATCH_*指令（那会是新的case header）。
        """
        instrs = [i for i in block.instructions
                 if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        if not instrs:
            return False

        # 如果只有POP_TOP（或全是noise指令），这不是pattern continuation
        # POP_TOP单独出现表示在丢弃match失败的值，是隐式default的开始
        if len(instrs) == 1 and instrs[0].opname == 'POP_TOP':
            return False

        # 包含MATCH_*指令的是新的case header，不是pattern延续
        if any(i.opname in self.MATCH_OPS for i in instrs):
            return False

        # 包含pattern相关指令的是pattern延续
        pattern_indicators = {'UNPACK_SEQUENCE', 'UNPACK_EX', 'UNPACK_EXTRACT',
                             'MATCH_KEYS', 'MATCH_MAPPING_KEYS', 'GET_LEN'}
        if any(i.opname in pattern_indicators for i in instrs):
            return True

        # 只包含STORE_/LOAD_CONST/COMPARE_OP/POP_TOP/COPY/SWAP的块是pattern延续
        pure_pattern_ops = {'LOAD_CONST', 'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                           'STORE_DEREF', 'COMPARE_OP', 'IS_OP', 'POP_TOP',
                           'COPY', 'SWAP', 'UNPACK_SEQUENCE'}
        pure_pattern_ops.update(set(self.COND_JUMP_OPS))
        if all(i.opname in pure_pattern_ops for i in instrs):
            return True

        return False

    def _extract_case_pattern(self, case_block: BasicBlock) -> Dict[str, Any]:
        """提取case的pattern并构建AST"""
        instrs = [i for i in case_block.instructions
                 if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]

        last_instr = instrs[-1] if instrs else None
        if last_instr and last_instr.opname in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE'):
            as_name = self._find_as_binding(case_block)
            result = {'type': 'MatchSingleton', 'value': None}
            if as_name:
                result = {'type': 'MatchAs', 'pattern': result, 'name': as_name}
            return result

        # 智能查找真正的case header
        # 如果当前块只有部分pattern指令（如LOAD_CONST+COMPARE_OP），向前查找完整的case header
        original_block = case_block  # 保存原始块引用
        used_real_header = False
        if (len(instrs) >= 3 and
            instrs[0].opname == 'LOAD_CONST' and
            instrs[1].opname == 'COMPARE_OP' and
            instrs[2].opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE')):
            # 这是一个不完整的case block，向前查找包含MATCH_*的真正header
            real_header = self._find_real_match_header(case_block)
            if real_header:
                case_block = real_header
                instrs = [i for i in case_block.instructions
                         if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                used_real_header = True

        # [B16] 捕获 case 头先于跨块收集判定。块自身不含任何模式匹配指令
        # （MATCH_*/COMPARE_OP/IS_OP/GET_LEN/UNPACK_*）且首条有效指令为
        # STORE_* 时，是捕获 case（`case n:`）的头块：STORE 是模式绑定
        # （消费前序 case 失败路径留在栈上的被匹配值副本），其后同块指令
        # 属于 case 体。此判定必须在 `_collect_all_pattern_instrs` 的跨块
        # 收集之前——match 嵌套在循环体内时，捕获体尾的 JUMP_BACKWARD 回边
        # 会让跨块收集沿后继走进循环头与下一 case 的检查块，把下一 case 的
        # COPY+LOAD_CONST+COMPARE 误拼为本 case 的 pattern（`case n:` →
        # `case 0`，r4_12 match_in_for_break 形态）。[C1] 只读本块指令；
        # [C2] 不窥视子/父区域；[C3] 栈平衡结构事实（STORE 消费副本），
        # 与 case 位置/嵌套深度无关。
        _cap_head_name = self._extract_capture_head_store(case_block)
        if _cap_head_name is not None:
            return {'type': 'MatchAs', 'name': _cap_head_name}

        # [B16/B18] 捕获+守卫 case 头（`case n if n < 0:`）：
        # COPY 1; STORE <cap>; LOAD <cap>; <guard 引用 cap>; ...; COND_JUMP。
        # 结构事实：COPY+STORE 是捕获绑定（被匹配值副本入变量）；其后紧跟
        # LOAD 同名变量是守卫对捕获名的重读——walrus（:=）是 COPY; STORE
        # 后直接以栈顶原值参与后续运算、不重读绑定名，二者以此区分（块须
        # 以条件跳转结尾，进一步约束到 case 头形态）。pattern =
        # MatchAs(name)；守卫表达式由 parse_case_guard 经
        # collect_pattern_blocks 单独提取，此处分派只负责模式本体。
        # [C1] 只读 case_block.instructions；[C2] 不窥视子/父区域；
        # [C3] COPY+STORE+LOAD 同名是编译器捕获绑定的栈协议，与 case
        # 位置/嵌套深度无关（嵌套无感）。
        if not any(i.opname in ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                                'MATCH_KEYS', 'MATCH_MAPPING_KEYS') for i in instrs):
            for _ci, _cinstr in enumerate(instrs[:-2]):
                if (_cinstr.opname == 'COPY'
                        and instrs[_ci + 1].opname in self.STORE_OPS
                        and instrs[_ci + 2].opname in self.LOAD_VAR_OPS
                        and instrs[_ci + 2].argval == instrs[_ci + 1].argval
                        and instrs and instrs[-1].opname in self.COND_JUMP_OPS):
                    return {'type': 'MatchAs', 'name': instrs[_ci + 1].argval}

        has_sequence = any(i.opname == 'MATCH_SEQUENCE' for i in instrs)
        has_class = any(i.opname == 'MATCH_CLASS' for i in instrs)
        has_mapping = any(i.opname == 'MATCH_MAPPING' for i in instrs)

        has_literal_compare = False
        literal_compare_pos = -1
        for i in range(len(instrs)):
            if (instrs[i].opname == 'LOAD_CONST' and
                i + 1 < len(instrs) and
                instrs[i + 1].opname in ('COMPARE_OP', 'IS_OP')):
                has_literal_compare = True
                literal_compare_pos = i
                break
        has_copy = any(i.opname == 'COPY' for i in instrs)
        is_literal_match = has_literal_compare and not has_sequence and not has_class and not has_mapping

        if is_literal_match and literal_compare_pos > 0:
            pre_compare_instrs = instrs[:literal_compare_pos]
            store_before_compare = [i for i in pre_compare_instrs if i.opname in self.STORE_OPS]
            if store_before_compare:
                store_target = store_before_compare[-1].argval
                post_store_loads = [i for i in pre_compare_instrs[pre_compare_instrs.index(store_before_compare[-1]):]
                                    if i.opname in self.LOAD_VAR_OPS and i.argval == store_target]
                has_copy_after_load = any(i.opname == 'COPY' for i in pre_compare_instrs[pre_compare_instrs.index(post_store_loads[0]):]) if post_store_loads else False
                if post_store_loads and not has_copy_after_load:
                    store_instr = store_before_compare[-1]
                    is_for_iter_store = False
                    for pred in case_block.predecessors:
                        if any(i.opname == 'FOR_ITER' for i in pred.instructions):
                            pred_last = pred.get_last_instruction()
                            if pred_last and pred_last.opname == 'FOR_ITER':
                                if store_instr.opname in ('STORE_NAME', 'STORE_FAST'):
                                    is_for_iter_store = True
                                    break
                    if not is_for_iter_store:
                        is_literal_match = False
            # 区域归约算法原则 2（每块唯一归属）：通配符
            # case 带守卫（``case _ if <guard>:`）编译为 LOAD subject;
            # POP_TOP（通配符丢弃）; <guard>; LOAD_CONST; COMPARE_OP;
            # POP_JUMP_IF_FALSE。LOAD_CONST + COMPARE_OP 是 guard 而非
            # pattern，前导的 LOAD + POP_TOP 标识通配符 pattern。
            # 检测前导 LOAD + POP_TOP（subject discard）以区分 guard
            # 与 literal pattern，避免将 guard 误判为 case 0:。
            if is_literal_match:
                _has_wildcard_discard = False
                for _i in range(literal_compare_pos):
                    if (instrs[_i].opname in self.LOAD_VAR_OPS
                            and _i + 1 < literal_compare_pos
                            and instrs[_i + 1].opname == 'POP_TOP'):
                        _has_wildcard_discard = True
                        break
                if _has_wildcard_discard:
                    is_literal_match = False

        if is_literal_match:
            result = self._extract_or_or_literal_pattern(instrs)
            if result.get('type') in ('MatchValue', 'MatchSingleton', 'MatchOr'):
                as_name = self._find_as_binding(case_block)
                if as_name:
                    result = {'type': 'MatchAs', 'pattern': result, 'name': as_name}
            return result

        # 使用改进的指令收集方法：沿成功路径收集所有pattern指令
        all_pattern_instrs = self._collect_all_pattern_instrs(case_block)

        if has_mapping or has_class:
            all_pattern_instrs.extend(
                self._collect_pattern_bindings_from_successor(case_block, all_pattern_instrs))

        if not (has_sequence or has_class or has_mapping):
            # 检查是否是字面量匹配（LOAD_CONST + COMPARE_OP）
            has_literal_compare = False
            for i in range(len(all_pattern_instrs)):
                if (all_pattern_instrs[i].opname == 'LOAD_CONST' and
                    i + 1 < len(all_pattern_instrs) and
                    all_pattern_instrs[i + 1].opname == 'COMPARE_OP'):
                    has_literal_compare = True
                    break

            # 检查是否有COPY指令（可能是OR pattern的一部分）
            has_copy = any(i.opname == 'COPY' for i in all_pattern_instrs)

            if has_copy and has_literal_compare:
                # 这可能是一个OR pattern或literal match
                return self._extract_or_or_literal_pattern(all_pattern_instrs)

        if has_sequence:
            result = self._extract_sequence_pattern(all_pattern_instrs)
        elif has_class:
            result = self._extract_class_pattern(all_pattern_instrs)
        elif has_mapping:
            result = self._extract_mapping_pattern(all_pattern_instrs)
        else:
            result = {'type': 'MatchAs'}
            # [B14 修复] 捕获头 STORE 归属：裸捕获 case（`case other:`）的
            # 头块首条有效指令是 STORE_*（CPython 在 case 入口直接 STORE
            # 被匹配值副本），该 STORE 属于模式绑定而非 case 体。
            _cap_name = self._extract_capture_head_store(case_block)
            if _cap_name:
                result['name'] = _cap_name

        if result.get('type') in ('MatchValue', 'MatchSingleton', 'MatchOr'):
            as_name = self._find_as_binding(case_block)
            if as_name:
                result = {'type': 'MatchAs', 'pattern': result, 'name': as_name}
        elif result.get('type') == 'MatchAs' and not result.get('name'):
            as_name = self._find_as_binding(case_block)
            if as_name:
                result['name'] = as_name

        return result

    def _extract_capture_head_store(self, case_block: BasicBlock) -> Optional[str]:
        """[B14 修复] 捕获模式 `case <name>:` 的模式头 STORE 归属。

        【识别条件】case 头块**不含任何模式匹配指令**（MATCH_* /
        COMPARE_OP / IS_OP / GET_LEN / UNPACK_*），且首条非 NOISE 指令为
        STORE_*。字节码依据：CPython 把 `case <name>:` 编译为在 case 入口
        直接 ``STORE_<name>``（前序 case 的失败跳转把被匹配值副本留在栈上，
        STORE 消费它）——该 STORE 是模式头的绑定动作，其后同块指令（LOAD /
        BUILD_TUPLE / RETURN…）才是 case 体。裸捕获单 case（``match x:
        case val:``）头块首条指令是 LOAD subject，不满足本判据，维持既有
        字节等价降级路径（``val = x``）不变。

        【归约方式】块内首条 STORE 的 argval 即捕获名；后续 STORE 全部
        归属 case 体（模式头 STORE 属于模式绑定，后续 STORE 属于 case 体
        ——每块唯一归属：一条 STORE 一个归属）。

        【AST 映射】→ {'type': 'MatchAs', 'name': <name>}（ast.MatchAs
        捕获模式），由 code_generator 渲染 `case <name>:`。

        [C1] 只读 case_block.instructions（L(A) 局部）；[C2] 不窥视子/父
        区域；[C3] 判据是「模式匹配指令不存在 ∧ 首条有效指令为 STORE」的
        结构事实，与 case 在链中位置无关（首 case/中间/尾 case 同判），
        捕获名绑定语义由编译器 STORE 槽位保证，嵌套无感。
        """
        PATTERN_OPS = frozenset({
            'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
            'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
            'COMPARE_OP', 'IS_OP', 'GET_LEN',
            'UNPACK_SEQUENCE', 'UNPACK_EX', 'UNPACK_EXTRACT',
        })
        instrs = [i for i in case_block.instructions
                  if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        if not instrs:
            return None
        if any(i.opname in PATTERN_OPS for i in instrs):
            return None
        # [B14 修复] 允许前导 POP_TOP：前序 case 的 COPY 1 留下的被匹配值副本
        # 由失败路径的 POP_TOP 清理，其后紧跟的 STORE_* 才是捕获绑定（STORE
        # 直接消费栈顶被匹配值副本——栈平衡的结构事实；case 体 STORE 前必有
        # 加载指令，故「POP_TOP* 后紧跟 STORE」唯一对应捕获头）。
        for ins in instrs:
            if ins.opname == 'POP_TOP':
                continue
            if ins.opname in self.STORE_OPS:
                return ins.argval
            return None
        return None

    def _has_as_binding_copy(self, filtered) -> bool:
        """区域归约算法原则 2（每块唯一归属）：区分 as-binding COPY 与
        pattern-matching COPY。

        as-binding COPY 出现在首个 MATCH_*/COMPARE_OP 模式指令**之前**
        （保存 subject 供后续 as 绑定 STORE）。pattern-matching COPY 出现在
        MATCH_CLASS **之后**（复制 match 结果供 POP_JUMP_IF_NONE 检查）。

        class pattern 无参数（``case P():``）的 COPY 在 MATCH_CLASS 之后，
        是 pattern-matching COPY——不应触发 as-binding 搜索，否则 case body
        的 STORE_NAME y（``y = 1``）被误判为 as 绑定（违反每块唯一归属）。
        """
        pattern_start_idx = None
        for i, instr in enumerate(filtered):
            if instr.opname in self.MATCH_OPS or instr.opname in ('COMPARE_OP', 'IS_OP'):
                pattern_start_idx = i
                break
        if pattern_start_idx is None:
            return any(i.opname == 'COPY' for i in filtered)
        for i in range(pattern_start_idx):
            if filtered[i].opname == 'COPY':
                return True
        return False

    def _find_as_binding(self, case_block) -> Optional[str]:
        """
        查找case的as绑定名称

        算法：
        1. 在case_block内查找COMPARE_OP/IS_OP后紧跟的STORE_指令
        2. 在case_block的fall-through后继中查找STORE_指令
        3. BFS搜索后续pattern块，查找最后一个STORE_指令（as绑定通常在pattern最后）
        4. 检查COPY指令（as绑定会在case header前用COPY保存subject）

        关键改进：as绑定的STORE_通常在所有pattern匹配之后、body之前，
        所以需要沿成功路径搜索更深的后继块。
        """
        # 策略0：查找COMPARE_OP之前的capture pattern STORE_（case n if n > 0: 模式）
        filtered = [i for i in case_block.instructions
                   if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        for i, instr in enumerate(filtered):
            if instr.opname in self.STORE_OPS:
                store_target = instr.argval
                remaining = filtered[i + 1:]
                has_guard_load = any(
                    r.opname in self.LOAD_VAR_OPS and r.argval == store_target
                    for r in remaining
                )
                has_compare = any(r.opname in ('COMPARE_OP', 'IS_OP') for r in remaining)
                has_copy_between = any(r.opname == 'COPY' for r in remaining[:next((j for j, r in enumerate(remaining) if r.opname in ('COMPARE_OP', 'IS_OP')), len(remaining))])
                if has_guard_load and has_compare and not has_copy_between:
                    is_for_iter_store = False
                    for pred in case_block.predecessors:
                        if any(pi.opname == 'FOR_ITER' for pi in pred.instructions):
                            is_for_iter_store = True
                            break
                    if not is_for_iter_store:
                        return store_target

        # 策略1：在case_block内查找
        filtered = [i for i in case_block.instructions
                   if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        for i, instr in enumerate(filtered):
            if instr.opname in ('COMPARE_OP', 'IS_OP'):
                for j in range(i + 1, len(filtered)):
                    if filtered[j].opname in self.COND_JUMP_OPS:
                        continue
                    if filtered[j].opname in self.STORE_OPS:
                        return filtered[j].argval
                    break
                # 在fall-through后继中查找
                last = case_block.get_last_instruction()
                if last and last.opname in self.COND_JUMP_OPS:
                    for succ in case_block.successors:
                        if succ.start_offset != last.argval:
                            for sinstr in succ.instructions:
                                if sinstr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                                    continue
                                if sinstr.opname in self.STORE_OPS:
                                    return sinstr.argval
                                break
                            break

        # 策略2：沿成功路径BFS查找最后一个STORE_指令
        # as绑定的STORE_通常在pattern匹配链的最后（所有COMPARE_OP之后）
        # 区域归约算法原则 2（每块唯一归属）：as 绑定协议要求
        # case header 用 COPY 保存 subject，随后在 fall-through 块 STORE。
        # 若 case_block 无 COPY，则 fall-through 块中的 STORE 属于 case body
        # 赋值（如 `for i in r: match i: case 1: x = 1` 中 case body 的
        # STORE_NAME x），不是 as 绑定。无 COPY 时跳过本策略，避免吞并 body
        # 赋值（与策略3的 has_copy_for_as 守卫一致）。
        # 区域归约算法原则 2（每块唯一归属）：as-binding COPY 出现在
        # MATCH_*/COMPARE_OP 之前，pattern-matching COPY 出现在之后（如
        # `case P():` 的 COPY 在 MATCH_CLASS 之后）。仅 as-binding COPY 触发
        # 本策略，避免 case body 的 STORE 被误判为 as 绑定。
        has_copy_in_case = self._has_as_binding_copy(filtered)
        if has_copy_in_case:
            store_after_pattern = self._find_last_store_on_success_path(case_block)
            if store_after_pattern:
                return store_after_pattern

        # 策略3：检查COPY指令 - 如果case_block有COPY，说明有as绑定
        # COPY保存subject用于后续的as绑定STORE_
        has_copy_for_as = self._has_as_binding_copy(filtered)
        if has_copy_for_as:
            # 沿所有后继路径查找STORE_指令
            as_name = self._find_store_in_successors(case_block)
            if as_name:
                _subject_var = None
                for fi in filtered:
                    if fi.opname in self.LOAD_VAR_OPS and fi.offset < next((x.offset for x in filtered if x.opname == 'COPY'), float('inf')):
                        _subject_var = fi.argval
                        break
                if _subject_var and as_name == _subject_var:
                    as_name = None
            if as_name:
                return as_name

        return None

    def _fail_jump_target_offsets(self, block: BasicBlock) -> set:
        """[B14 修复] 计算块内 fail 极性条件跳转的目标偏移集合。

        【识别条件】match 模式匹配链中，模式失败沿条件跳转离开当前 case：
        fail 极性跳转 = IF_FALSE 族（字面量/序列比较失败）+ IF_NONE /
        IF_NOT_NONE 族（MATCH_KEYS 键检查 / singleton None 检查失败）。
        IF_TRUE 族是 or-guard 的成功边（跳向 case 体），不属 fail 极性。

        【归约方式】as 绑定协议（每块唯一归属）：as 绑定的 STORE 在**成功
        路径**上（模式匹配成功后的 fall-through/无条件边可达）；fail 边的
        目标是下一 case 的头块（其首部 STORE 是下一 case 的模式头绑定，
        如 `case v if …:` 的 STORE v）。沿 BFS 查找 as 绑定时排除 fail 边
        目标，防止把下一 case 的捕获头 STORE 误识为当前 case 的 as 绑定
        （幻影捕获注入，如 `case 0:` → `case 0 as v:`）。

        【AST 映射】不直接产出 AST；作为 _find_last_store_on_success_path /
        _find_store_in_successors 的后继过滤守卫，保证 MatchAs.name 只取
        自本 case 的绑定。

        [C1] 只读 block.instructions/.successors（L(A) 局部）；[C2] 不窥视
        子/父区域内部；[C3] fail 边目标是模式匹配链的结构事实（跳转极性由
        操作码语义决定，不由 case 位置决定），任意嵌套深度/链位置的 case
        同判——嵌套无感。
        """
        fail_ops = frozenset({
            'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
            'POP_JUMP_BACKWARD_IF_FALSE',
            'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE',
            'POP_JUMP_BACKWARD_IF_NONE',
            'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE',
            'POP_JUMP_BACKWARD_IF_NOT_NONE',
        })
        return {i.argval for i in block.instructions if i.opname in fail_ops and i.argval is not None}

    def _find_last_store_on_success_path(self, case_block: BasicBlock) -> Optional[str]:
        """
        沿成功路径查找最后一个STORE_指令（as绑定通常在pattern最后）

        成功路径：从case_block开始，沿每个条件跳转的fall-through后继遍历，
        直到遇到非pattern块。收集路径上所有STORE_指令，返回最后一个。

        [B14 修复] 成功路径遍历排除 fail 极性条件跳转目标（见
        _fail_jump_target_offsets）：fail 边目标是下一 case 头块，其首部
        STORE 属于下一 case 的模式头绑定，不是本 case 的 as 绑定。原实现
        对「块末为无条件跳转」的块（如 or-pattern 交替块）扩展全部后继，
        会经 fail 边泄漏进下一 case 链（幻影捕获注入）。
        """
        stores = []
        visited = {case_block}
        queue = deque()

        # 从case_block的成功后继开始（排除 fail 极性跳转目标）
        excluded = self._fail_jump_target_offsets(case_block)
        for succ in case_block.successors:
            if succ.start_offset not in excluded:
                queue.append(succ)

        while queue:
            blk = queue.popleft()
            if blk in visited:
                continue
            visited.add(blk)

            # 检查是否是pattern块
            is_pattern = self._is_pattern_block_for_as(blk)
            if not is_pattern:
                continue

            # 收集此块中的STORE_指令
            for instr in blk.instructions:
                if instr.opname in self.STORE_OPS:
                    stores.append(instr.argval)

            # 继续沿成功路径（排除 fail 极性跳转目标）
            excluded = self._fail_jump_target_offsets(blk)
            for succ in blk.successors:
                if succ not in visited and succ.start_offset not in excluded:
                    queue.append(succ)

        # 返回最后一个STORE_（as绑定在pattern最后）
        if stores:
            return stores[-1]
        return None

    def _is_pattern_block_for_as(self, block: BasicBlock) -> bool:
        """判断块是否是pattern匹配相关的块（用于as绑定查找）"""
        instrs = [i for i in block.instructions
                 if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        if not instrs:
            return False

        # 包含MATCH_*的是新case header
        if any(i.opname in self.MATCH_OPS for i in instrs):
            return False

        # 包含pattern相关指令
        pattern_ops = {'UNPACK_SEQUENCE', 'UNPACK_EX', 'UNPACK_EXTRACT',
                      'GET_LEN', 'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
                      'COMPARE_OP', 'IS_OP', 'COPY', 'SWAP', 'POP_TOP'}
        pattern_ops.update(set(self.STORE_OPS))
        pattern_ops.update(set(self.COND_JUMP_OPS))

        # 允许LOAD_CONST（用于字面量匹配）
        pattern_ops.add('LOAD_CONST')

        has_pattern = any(i.opname in pattern_ops for i in instrs)
        # [B16] 计算指令排除：BINARY_OP（含全部二元算术/位运算）/CONTAINS_OP/
        # UNARY_* 是表达式求值指令，模式检查块（字面量比较 COMPARE_OP/
        # IS_OP + 结构协议 MATCH_*/UNPACK_*/COPY/SWAP）绝不包含它们。
        # case 体首语句的增广赋值（`acc += 1` → LOAD; LOAD_CONST; BINARY_OP;
        # STORE）含 BINARY_OP——此前 has_body 判据漏掉该形态（BINARY_OP 不
        # 在 body 指令表且 LOAD→STORE 邻接检查被中间 LOAD_CONST/BINARY_OP
        # 隔断），体首块被误判为 pattern continuation 块，其 STORE 被沿成功
        # 路径 BFS 误识为 as 绑定（幻影捕获 `case 1:` → `case 1 as acc:`）。
        has_body = any(i.opname in ('LOAD_GLOBAL', 'LOAD_NAME', 'CALL',
                                    'BINARY_ADD', 'BINARY_SUBTRACT',
                                    'BINARY_MULTIPLY', 'BINARY_TRUE_DIVIDE',
                                    'BINARY_SUBSCR', 'BINARY_OP', 'CONTAINS_OP',
                                    'UNARY_NEGATIVE', 'UNARY_NOT', 'UNARY_INVERT',
                                    'RETURN_VALUE', 'RETURN_CONST',
                                    'BUILD_LIST', 'BUILD_TUPLE', 'BUILD_MAP',
                                    'BUILD_SET', 'BUILD_STRING')
                      for i in instrs)

        # 区域归约算法原则 2（每块唯一归属）：case body 块（含赋值
        # 语句 `y = 1` / `x = a`）不应被误判为 pattern continuation 块。原
        # `_is_pattern_block_for_as` 仅检查 LOAD_GLOBAL/CALL/RETURN 等显式 body
        # 指令，但 case body 的赋值（LOAD_CONST + STORE_NAME / LOAD_NAME +
        # STORE_NAME）中 LOAD_CONST/STORE_NAME 均在 pattern_ops 内，被误判为
        # pattern 块，导致 _find_last_store_on_success_path 把 body 赋值的
        # STORE 当作 as 绑定（如 `case 1 | 2: y = 1` 中 STORE_NAME y 被误识为
        # as y，附加到每个 or 分支 → `case 1 as y | 2 as y` 语法错误）。
        # 判据：pattern 上下文中 LOAD_CONST 永远跟 COMPARE_OP（字面量比较）或
        # 被 UNPACK_*/MATCH_* 消费，绝不直接跟 STORE_*；LOAD_NAME 在非
        # MATCH_CLASS 上下文中跟 STORE_* 是 body 赋值。检测到此类赋值序列时，
        # 块为 body 块（返回 False）。
        if has_pattern and not has_body:
            for _bi, _bins in enumerate(instrs):
                if _bins.opname in ('LOAD_CONST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DEREF'):
                    _next_bi = instrs[_bi + 1] if _bi + 1 < len(instrs) else None
                    if _next_bi is not None and _next_bi.opname in self.STORE_OPS:
                        has_body = True
                        break

        return has_pattern and not has_body

    def _find_store_in_successors(self, case_block: BasicBlock) -> Optional[str]:
        """BFS搜索所有后继块查找STORE_指令（用于COPY场景的as绑定）

        [B14 修复] BFS 排除 fail 极性条件跳转目标（见
        _fail_jump_target_offsets docstring 的三要素与 C1/C2/C3 条款）：
        fail 边目标是下一 case 头块，其首部 STORE（下一 case 的模式头绑定，
        如 `case v if …:` 的 STORE v）不是本 case 的 as 绑定。原实现无差别
        扩展全部后继，把下一 case 的捕获名误识为本 case 的 as 绑定
        （`case 0:` → 幻影 `case 0 as v:`）。
        """
        visited = {case_block}
        queue = deque()
        excluded = self._fail_jump_target_offsets(case_block)
        for succ in case_block.successors:
            if succ.start_offset not in excluded:
                queue.append(succ)

        while queue:
            blk = queue.popleft()
            if blk in visited:
                continue
            visited.add(blk)

            if not self._is_pattern_block_for_as(blk):
                continue

            # 查找此块中的STORE_指令
            for instr in blk.instructions:
                if instr.opname in self.STORE_OPS:
                    return instr.argval

            excluded = self._fail_jump_target_offsets(blk)
            for succ in blk.successors:
                if succ not in visited and succ.start_offset not in excluded:
                    queue.append(succ)

        return None

    def _collect_pattern_bindings_from_successor(self, case_block, existing_instrs) -> list:
        result = []
        existing_offsets = {i.offset for i in existing_instrs}
        has_match_keys = any(i.opname in ('MATCH_KEYS', 'MATCH_MAPPING_KEYS') for i in existing_instrs)
        has_unpack = any(i.opname == 'UNPACK_SEQUENCE' for i in existing_instrs)
        has_match_class = any(i.opname == 'MATCH_CLASS' for i in existing_instrs)
        if not (has_match_keys or has_unpack or has_match_class):
            return result
        li = case_block.get_last_instruction()
        if not li or li.opname not in self.COND_JUMP_OPS:
            return result
        for succ in case_block.successors:
            if succ.start_offset != li.argval:
                for instr in succ.instructions:
                    if instr.offset in existing_offsets:
                        continue
                    if instr.opname in ('MATCH_KEYS', 'MATCH_MAPPING_KEYS', 'UNPACK_SEQUENCE'):
                        result.append(instr)
                    elif instr.opname in self.STORE_OPS:
                        result.append(instr)
                    elif instr.opname in ('LOAD_CONST', 'COMPARE_OP', 'IS_OP', 'COPY', 'POP_TOP', 'SWAP'):
                        result.append(instr)
                    elif instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                        continue
                    elif instr.opname in self.COND_JUMP_OPS:
                        result.append(instr)
                    else:
                        break
                break
        return result

    def _extract_sequence_pattern(self, instrs: List[Instruction],
                                  allow_own_as_store: bool = True) -> Dict[str, Any]:
        """
        从指令序列中提取MatchSequence pattern

        算法：
        1. 扫描UNPACK_SEQUENCE/UNPACK_EX确定pattern槽位数
        2. 扫描LOAD_CONST+COMPARE_OP确定字面量匹配槽位
        3. 扫描STORE_确定变量绑定槽位
        4. 扫描POP_TOP确定通配符槽位
        5. 合并所有信息构建最终pattern

        关键修复：
        - UNPACK_EX的arg参数：低8位=before个数，高8位=after个数
        - STORE_指令可能在后续块中，需要从all_pattern_instrs中查找
        - POP_TOP表示通配符（_），不消耗store_names

        [B14 修复] allow_own_as_store 参数（嵌套无感的关键）：
        【识别条件】嵌套子序列（外层 UNPACK 槽位上的 ``[...]`` 子模式）的
        as 绑定（``[[a, b] as c, d]`` 的 ``as c``）在字节码中表现为子模式
        MATCH_SEQUENCE **之前**的 COPY 1（为 as 绑定保存子值副本）——
        ``case [[a, b], c]:``（无内层 as）无该 COPY，二者 STORE 流相同
        （a, b, c…），纯 STORE 序列不可区分，COPY 前缀是唯一结构事实。
        【归约方式】allow_own_as_store=False（嵌套递归调用）时，子序列自身
        槽位消耗完（unpack_stack 空）后的 STORE 不归属本子序列的 as_name
        ——它们属于外层模式的后续槽位绑定；外层则按
        _nested_sequence_slot_consumers_end 计数跳过子模式自身的槽位消费指令
        后继续绑定余下槽位（每块唯一归属：一条 STORE 只归属一个槽位）。
        【AST 映射】→ MatchSequence.as_name 仅在 allow_own_as_store=True 且
        存在 COPY 前缀时产出。
        [C1] 只读传入指令窗口与 COPY 前缀（L(A) 局部）；[C2] 子模式作为
        抽象节点由外层跳过其内部指令，不窥视其绑定细节之外的信息；[C3]
        COPY 前缀判据由编译器按「是否确有内层 as 绑定」发射，与嵌套深度/
        槽位序号无关，嵌套无感。
        """
        patterns = []
        length_val = None
        length_compare_op = '=='
        as_name = None
        has_unpack = False
        unpack_before = 0
        unpack_after = 0
        slot_actions = {}

        filtered = [i for i in instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]

        has_binary_subscr = any(i.opname == 'BINARY_SUBSCR' for i in filtered)
        if has_binary_subscr and not any(i.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX') for i in filtered):
            return self._extract_starred_sequence_pattern(filtered)

        in_unpack_context = False
        unpack_stack = []
        seen_pattern_instr = False
        skip_until = 0
        for idx, instr in enumerate(filtered):
            if idx < skip_until:
                # [B14 修复] 已归属嵌套子模式的槽位消费指令（其 STORE/POP_TOP）
                # 不再被外层槽位绑定重复消费（每块唯一归属）。
                continue
            if instr.opname in ('MATCH_SEQUENCE', 'MATCH_CLASS', 'MATCH_MAPPING',
                                'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
                                'GET_LEN', 'UNPACK_SEQUENCE', 'UNPACK_EX',
                                'UNPACK_EXTRACT', 'COMPARE_OP', 'IS_OP'):
                seen_pattern_instr = True
            if instr.opname in self.LOAD_VAR_OPS:
                if seen_pattern_instr:
                    break
                continue
            if instr.opname == 'RETURN_VALUE':
                break
            if (instr.opname == 'LOAD_CONST' and idx + 1 < len(filtered) and
                filtered[idx + 1].opname in self.STORE_OPS and
                (has_unpack or length_val is not None)):
                if idx + 2 < len(filtered) and filtered[idx + 2].opname == 'COMPARE_OP':
                    pass
                else:
                    break
            if instr.opname == 'POP_TOP':
                if in_unpack_context and unpack_stack:
                    slot = unpack_stack.pop()
                    # 反编译逻辑：placeholder slot(-1)是非pattern栈项（如subject副本、
                    # matched value等）的清理POP_TOP，不是通配符(_)，应跳过
                    if slot != -1:
                        slot_actions.setdefault(slot, {'type': 'wildcard'})
                continue
            if instr.opname == 'SWAP':
                if in_unpack_context:
                    n = instr.argval if instr.argval else 2
                    # 反编译逻辑：SWAP n 交换 TOS 与 TOS-(n-1)。unpack_stack 只跟踪
                    # pattern槽位，但实际栈上还有其他项（subject副本、matched value等）。
                    # 当 n > len(unpack_stack) 时，需在栈底扩展 placeholder(-1) 表示
                    # 非pattern栈项，然后执行交换。这样后续 POP_TOP/STORE 能正确映射
                    # 到对应槽位。例如 [first, *rest] 的 UNPACK_EX 1 后栈为 [first, rest]，
                    # SWAP 4 会引入2个 placeholder，经多轮 SWAP 后 POP_TOP 清理 placeholder，
                    # STORE 正确绑定到 first(slot 0) 和 rest(slot 1)。
                    while len(unpack_stack) < n:
                        unpack_stack.insert(0, -1)
                    if n == 2:
                        unpack_stack[-1], unpack_stack[-2] = unpack_stack[-2], unpack_stack[-1]
                    elif n > 2:
                        unpack_stack[-1], unpack_stack[-n] = unpack_stack[-n], unpack_stack[-1]
                continue
            if instr.opname == 'GET_LEN':
                if idx + 2 < len(filtered) and filtered[idx + 1].opname == 'LOAD_CONST':
                    length_val = filtered[idx + 1].argval
                    if idx + 2 < len(filtered) and filtered[idx + 2].opname == 'COMPARE_OP':
                        length_compare_op = filtered[idx + 2].argval
            elif instr.opname == 'UNPACK_SEQUENCE':
                has_unpack = True
                in_unpack_context = True
                count = instr.argval if instr.argval is not None else 1
                unpack_stack = list(reversed(range(count)))
                for _ in range(count):
                    patterns.append({'type': 'MatchAs'})
            elif instr.opname == 'UNPACK_EX':
                has_unpack = True
                in_unpack_context = True
                arg = instr.argval if instr.argval is not None else 0
                unpack_before = arg & 0xFF
                unpack_after = (arg >> 8) & 0xFF
                total = unpack_before + 1 + unpack_after
                unpack_stack = list(reversed(range(total)))
                for _ in range(unpack_before):
                    patterns.append({'type': 'MatchAs'})
                patterns.append({'type': 'MatchStarred', 'pattern': {'type': 'MatchAs'}})
                for _ in range(unpack_after):
                    patterns.append({'type': 'MatchAs'})
            elif instr.opname in self.STORE_OPS:
                var_name = instr.argval if instr.argval else f'var_{instr.arg}'
                if in_unpack_context and unpack_stack:
                    slot = unpack_stack.pop()
                    # 反编译逻辑：placeholder slot(-1)是非pattern栈项的STORE，
                    # 不应记录为capture也不应设为as_name，直接跳过
                    if slot != -1:
                        slot_actions.setdefault(slot, {'type': 'capture', 'name': var_name})
                elif seen_pattern_instr and allow_own_as_store:
                    # 区域归约算法原则 2（每块唯一归属）：as_name 的
                    # STORE 必须出现在 pattern 匹配指令（MATCH_*/GET_LEN/UNPACK_*/
                    # COMPARE_OP）之后——as 绑定在所有 pattern 匹配成功后才 STORE
                    # 保存的 subject 副本。若 STORE 出现在 seen_pattern_instr 之前，
                    # 它是 case header 块前导的 for-target STORE（`for i in r: match
                    # s: case [a, *b]:` 中 for-target STORE_NAME i 与 match subject
                    # LOAD_NAME s 同块），不归属 pattern，不应误设为 as_name。
                    # [B14 修复] allow_own_as_store=False（嵌套子序列调用）时，
                    # 自身槽位消耗完后的 STORE 属于外层模式的后续槽位，不归属
                    # 本子序列 as_name（判据见方法 docstring）。
                    as_name = var_name
            elif instr.opname == 'LOAD_CONST' and idx + 1 < len(filtered) and filtered[idx + 1].opname == 'COMPARE_OP':
                literal_val = instr.argval
                if has_unpack:
                    if in_unpack_context and unpack_stack:
                        slot = unpack_stack.pop()
                        if slot != -1:
                            slot_actions.setdefault(slot, {'type': 'literal', 'value': literal_val})
            elif instr.opname in ('MATCH_SEQUENCE', 'MATCH_CLASS'):
                if in_unpack_context and unpack_stack:
                    slot = unpack_stack.pop()
                    if slot == -1:
                        continue
                    nested_instrs = filtered[idx:]
                    # [B14 修复] 内层 as 绑定的结构事实：子模式 MATCH_SEQUENCE
                    # 前紧邻 COPY 1（为内层 as 绑定保存子值副本）。有 COPY ⇒
                    # 内层槽位消耗完后的下一个 STORE 是内层 as 绑定；无 COPY ⇒
                    # 该 STORE 属于外层余下槽位（见方法 docstring 三要素）。
                    _own_as = idx > 0 and filtered[idx - 1].opname == 'COPY'
                    if instr.opname == 'MATCH_SEQUENCE':
                        nested_pattern = self._extract_sequence_pattern(
                            nested_instrs, allow_own_as_store=_own_as)
                    else:
                        nested_pattern = self._extract_class_pattern(nested_instrs)
                    slot_actions[slot] = {'type': 'nested', 'pattern': nested_pattern}
                    # 跳过内层子模式自身的槽位消费指令，外层继续绑定余下槽位
                    # （[[a, b], c] 的 STORE c 属于外层 slot 1，不再被丢弃）。
                    skip_until = self._nested_sequence_slot_consumers_end(
                        filtered, idx, _own_as if instr.opname == 'MATCH_SEQUENCE' else False)
                    continue

        if not has_unpack and length_val is not None:
            if length_compare_op == '==' or length_compare_op == 2:
                for _ in range(length_val):
                    patterns.append({'type': 'MatchAs'})
            elif length_compare_op == '>=' or length_compare_op == 5:
                if unpack_before > 0 or unpack_after > 0:
                    pass
                else:
                    patterns.append({'type': 'MatchStarred', 'pattern': {'type': 'MatchAs'}})

        for slot, action in slot_actions.items():
            if slot < len(patterns):
                if action['type'] == 'capture':
                    p = patterns[slot]
                    if isinstance(p, dict) and p.get('type') == 'MatchAs':
                        patterns[slot] = {'type': 'MatchAs', 'name': action['name']}
                    elif isinstance(p, dict) and p.get('type') == 'MatchStarred':
                        inner = p.get('pattern', {})
                        if isinstance(inner, dict) and inner.get('type') == 'MatchAs':
                            patterns[slot] = {
                                'type': 'MatchStarred',
                                'pattern': {'type': 'MatchAs', 'name': action['name']}
                            }
                elif action['type'] == 'literal':
                    p = patterns[slot]
                    if isinstance(p, dict) and p.get('type') == 'MatchAs':
                        patterns[slot] = {'type': 'MatchValue', 'value': {'type': 'Constant', 'value': action['value']}}
                elif action['type'] == 'nested':
                    if slot < len(patterns):
                        patterns[slot] = action['pattern']
                elif action['type'] == 'wildcard':
                    pass

        result = {
            'type': 'MatchSequence',
            'patterns': patterns,
        }

        if as_name:
            result['as_name'] = as_name

        self._in_unpack_ex = False

        return result

    def _nested_sequence_slot_consumers_end(self, filtered: List[Instruction],
                                            idx: int, own_as: bool) -> int:
        """[B14 修复] 计算嵌套子模式自身槽位消费指令的结束索引（不含）。

        【识别条件】外层 UNPACK 槽位上的嵌套子模式（MATCH_SEQUENCE/
        MATCH_CLASS）从 idx 开始；其自身槽位消费 = 子模式 UNPACK_*/UNPACK_EX
        的 argval 个槽位（每个槽位由一个 STORE_* 或 POP_TOP 消费——STORE 为
        捕获/字面量后绑定，POP_TOP 为通配），无 UNPACK 的子模式（如空序列
        ``[]``）止于首个 POP_TOP/STORE；own_as=True（子模式 MATCH_* 前紧邻
        COPY）时其后再多消费一个 STORE（内层 as 绑定）。

        【归约方式】外层循环跳过 [idx, end) 区间指令后继续绑定余下槽位，
        使子模式内部的 STORE 与外层余下槽位的 STORE 互不侵占（每块唯一
        归属：一条 STORE 只归属一个槽位）。

        【AST 映射】不直接产出 AST；保证嵌套 MatchSequence 的 slots 与
        as_name 按栈消费顺序正确切分。

        [C1] 只读传入 filtered 窗口（本 case 的模式指令窗口，L(A) 局部）；
        [C2] 子模式作为抽象节点整体跳过，外层不解释其内部绑定语义；[C3]
        消费计数由 UNPACK argval（编译器发射的槽位数）驱动，与槽位序号/
        嵌套深度无关，嵌套无感。
        """
        n = len(filtered)
        unpack_idx = None
        unpack_count = 0
        for j in range(idx + 1, n):
            op = filtered[j].opname
            if op == 'UNPACK_SEQUENCE':
                unpack_idx = j
                unpack_count = filtered[j].argval if filtered[j].argval is not None else 0
                break
            if op == 'UNPACK_EX':
                unpack_idx = j
                arg = filtered[j].argval if filtered[j].argval is not None else 0
                unpack_count = (arg & 0xFF) + 1 + ((arg >> 8) & 0xFF)
                break
            if op in self.STORE_OPS or op == 'POP_TOP':
                # 子模式无 UNPACK（如空序列 []）：其栈消费止于首个 POP_TOP/STORE
                return j + 1
        if unpack_idx is None:
            return idx + 1
        remaining = unpack_count
        j = unpack_idx + 1
        while j < n and remaining > 0:
            op = filtered[j].opname
            if op in self.STORE_OPS or op == 'POP_TOP':
                remaining -= 1
            j += 1
        # own_as：子模式 COPY 前缀 ⇒ 其后第一个 STORE 是内层 as 绑定，一并跳过
        if own_as and j < n and filtered[j].opname in self.STORE_OPS:
            j += 1
        return j

    def _extract_starred_sequence_pattern(self, filtered: List[Instruction]) -> Dict[str, Any]:
        length_val = None
        length_compare_op = '=='
        before_literals = []
        after_literals = []
        store_names = []
        as_name = None

        idx = 0
        while idx < len(filtered):
            instr = filtered[idx]
            if instr.opname == 'GET_LEN':
                if idx + 2 < len(filtered) and filtered[idx + 1].opname == 'LOAD_CONST':
                    length_val = filtered[idx + 1].argval
                    if idx + 2 < len(filtered) and filtered[idx + 2].opname == 'COMPARE_OP':
                        length_compare_op = filtered[idx + 2].argval
                idx += 1
                continue
            if instr.opname == 'COPY':
                if idx + 2 < len(filtered) and filtered[idx + 1].opname == 'LOAD_CONST' and filtered[idx + 2].opname == 'BINARY_SUBSCR':
                    subscr_idx = filtered[idx + 1].argval
                    if idx + 3 < len(filtered) and filtered[idx + 3].opname == 'LOAD_CONST':
                        if idx + 4 < len(filtered) and filtered[idx + 4].opname == 'COMPARE_OP':
                            literal_val = filtered[idx + 3].argval
                            if isinstance(subscr_idx, int):
                                before_literals.append((subscr_idx, literal_val))
                            idx += 5
                            continue
                    if idx + 3 < len(filtered) and filtered[idx + 3].opname in self.STORE_OPS:
                        var_name = filtered[idx + 3].argval
                        if isinstance(subscr_idx, int):
                            before_literals.append((subscr_idx, {'type': 'MatchAs', 'name': var_name}))
                        idx += 4
                        continue
                if idx + 1 < len(filtered) and filtered[idx + 1].opname == 'GET_LEN':
                    if idx + 4 < len(filtered) and filtered[idx + 2].opname == 'LOAD_CONST' and filtered[idx + 3].opname == 'BINARY_OP' and filtered[idx + 4].opname == 'BINARY_SUBSCR':
                        if idx + 5 < len(filtered) and filtered[idx + 5].opname == 'LOAD_CONST':
                            if idx + 6 < len(filtered) and filtered[idx + 6].opname == 'COMPARE_OP':
                                literal_val = filtered[idx + 5].argval
                                after_literals.append(literal_val)
                                idx += 7
                                continue
                        if idx + 5 < len(filtered) and filtered[idx + 5].opname in self.STORE_OPS:
                            var_name = filtered[idx + 5].argval
                            after_literals.append({'type': 'MatchAs', 'name': var_name})
                            idx += 6
                            continue
                idx += 1
                continue
            if instr.opname in self.STORE_OPS:
                store_names.append(instr.argval)
                idx += 1
                continue
            if instr.opname == 'POP_TOP':
                break
            idx += 1

        patterns = []
        before_count = 0
        after_count = len(after_literals)

        if before_literals:
            max_before_idx = max(pos for pos, _ in before_literals if isinstance(pos, int))
            before_count = max_before_idx + 1

        for i in range(before_count):
            entry = next((val for pos, val in before_literals if pos == i), None)
            if entry is not None:
                if isinstance(entry, dict):
                    patterns.append(entry)
                else:
                    patterns.append({'type': 'MatchValue', 'value': {'type': 'Constant', 'value': entry}})
            else:
                patterns.append({'type': 'MatchAs'})

        star_name = None
        if store_names:
            star_name = store_names[0]

        if star_name:
            patterns.append({'type': 'MatchStarred', 'pattern': {'type': 'MatchAs', 'name': star_name}})
        else:
            patterns.append({'type': 'MatchStarred', 'pattern': {'type': 'MatchAs'}})

        for i, val in enumerate(after_literals):
            if isinstance(val, dict):
                patterns.append(val)
            else:
                patterns.append({'type': 'MatchValue', 'value': {'type': 'Constant', 'value': val}})

        if len(store_names) > 1:
            as_name = store_names[1]

        result = {
            'type': 'MatchSequence',
            'patterns': patterns,
        }
        if as_name:
            result['as_name'] = as_name
        return result

    def _count_class_pattern_instrs(self, instrs: List[Instruction]) -> int:
        """ 计算嵌套 class pattern 消耗的指令数

        用于在 _extract_class_pattern 的属性循环中跳过内层 class pattern 的所有指令。
        内层 class pattern 结构：
            LOAD_NAME/LOAD_GLOBAL (类名)
            LOAD_CONST (tuple, keyword keys)
            MATCH_CLASS (pos_count)
            COPY
            POP_JUMP_FORWARD_IF_NONE
            UNPACK_SEQUENCE (count)
            (per attr: LOAD_CONST+COMPARE_OP+COND_JUMP 或 STORE_ 或 POP_TOP)

        Args:
            instrs: 从内层 class pattern 的 LOAD_NAME 开始的指令列表

        Returns:
            消耗的指令数
        """
        if not instrs:
            return 0

        # 找到 MATCH_CLASS
        match_class_idx = None
        for i, instr in enumerate(instrs):
            if instr.opname == 'MATCH_CLASS':
                match_class_idx = i
                break
            if i > 5:
                break

        if match_class_idx is None:
            return 0

        # 找到 UNPACK_SEQUENCE
        unpack_idx = None
        for i in range(match_class_idx + 1, len(instrs)):
            if instrs[i].opname == 'UNPACK_SEQUENCE':
                unpack_idx = i
                break
            if instrs[i].opname == 'MATCH_CLASS':
                break

        if unpack_idx is None:
            # 无 UNPACK_SEQUENCE，可能是 0 参数的 class pattern
            # 跳过到 POP_JUMP_IF_NONE 之后
            j = match_class_idx + 1
            while j < len(instrs):
                if instrs[j].opname in ('POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE'):
                    j += 1
                    break
                j += 1
            return j

        count = instrs[unpack_idx].argval if instrs[unpack_idx].argval is not None else 0
        j = unpack_idx + 1
        attr_idx = 0
        while j < len(instrs) and attr_idx < count:
            if instrs[j].opname == 'LOAD_CONST' and j + 1 < len(instrs) and instrs[j + 1].opname == 'COMPARE_OP':
                j += 2
                while j < len(instrs) and instrs[j].opname in self.COND_JUMP_OPS:
                    j += 1
                attr_idx += 1
            elif instrs[j].opname in self.STORE_OPS:
                j += 1
                attr_idx += 1
            elif instrs[j].opname == 'POP_TOP':
                j += 1
                attr_idx += 1
            else:
                j += 1

        return j

    def _extract_class_pattern(self, instrs: List[Instruction]) -> Dict[str, Any]:
        """
        构建MatchClass AST

        算法：
        1. 从MATCH_CLASS指令前查找LOAD_GLOBAL/LOAD_NAME获取类名
        2. 从MATCH_CLASS的arg获取positional参数数量
        3. 从LOAD_CONST(tuple)获取keyword参数键名
        4. 从UNPACK_SEQUENCE后的指令序列提取属性pattern

        关键修复：
        - 多属性绑定时，每个属性独立处理（LOAD_CONST+COMPARE_OP或STORE_）
        - as_name只在UNPACK_SEQUENCE count=0时从后续STORE_提取
        - keyword_keys和pos_count正确分离
        """
        cls_name = None
        patterns = []
        keyword_keys = []
        as_name = None
        pos_count = 0

        # 保留 POP_TOP 指令
        # UNPACK_SEQUENCE 之后的 POP_TOP 对应通配符 _ 位置参数（如 `Point(_, _)`），
        # 必须保留以便后续循环识别为 MatchAs 模式。此前过滤掉 POP_TOP 导致
        # `Point(_, _)` 退化为 `Point()`，重编字节码缺失 UNPACK_SEQUENCE + POP_TOP。
        filtered = [i for i in instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]

        match_class_idx = None
        for i, instr in enumerate(filtered):
            if instr.opname == 'MATCH_CLASS':
                match_class_idx = i
                break

        if match_class_idx is not None:
            for i in range(match_class_idx - 1, -1, -1):
                if filtered[i].opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                    cls_name = filtered[i].argval
                    break

        if cls_name is None:
            for i, instr in enumerate(filtered):
                if instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                    if i + 2 < len(filtered) and filtered[i + 1].opname == 'LOAD_CONST' and isinstance(filtered[i + 1].argval, tuple) and filtered[i + 2].opname == 'MATCH_CLASS':
                        cls_name = instr.argval
                        break

        if cls_name is None:
            return {'type': 'MatchAs'}

        # [Phase 3 adv16_match_class_nested_in_if] 嵌套类模式（如
        # Outer(x=Inner(1))）字节码含多个 MATCH_CLASS（外层 + 内层）。
        # 外层类的 keyword_keys 是首个 MATCH_CLASS 前紧邻的
        # LOAD_CONST(tuple)，pos_count 是首个 MATCH_CLASS.arg。此前循环
        # 遍历所有指令并覆盖 keyword_keys/pos_count，导致内层类的 () 和 1
        # 覆盖外层的 ('x',) 和 0，输出 Outer(Inner(1)) 而非
        # Outer(x=Inner(1))。修正：遇到首个 MATCH_CLASS 即停止，仅用其前
        # 紧邻的 LOAD_CONST(tuple) 作为外层 keyword_keys。内层类的信息由
        # 递归调用 _extract_class_pattern(nested_instrs) 独立处理。
        for i, instr in enumerate(filtered):
            if instr.opname == 'MATCH_CLASS':
                pos_count = instr.argval if instr.argval is not None else 0
                for k in range(i - 1, -1, -1):
                    if filtered[k].opname == 'LOAD_CONST' and isinstance(filtered[k].argval, tuple):
                        keyword_keys = list(filtered[k].argval)
                        break
                break

        if cls_name is None:
            return {'type': 'MatchAs'}

        total_attrs = len(keyword_keys) + pos_count

        unpack_idx = None
        for i, instr in enumerate(filtered):
            if instr.opname == 'UNPACK_SEQUENCE':
                unpack_idx = i
                break

        if unpack_idx is not None:
            count = filtered[unpack_idx].argval if filtered[unpack_idx].argval is not None else 0
            if count == 0:
                # 没有属性需要解包，检查是否有as绑定
                # 区域归约算法原则 2（每块唯一归属）：as 绑定 STORE
                # 紧跟 UNPACK_SEQUENCE 0（无中间指令）。``case P() as y:`` 编译
                # 为 ``UNPACK_SEQUENCE 0; STORE_FAST y``。``case P():``（无 as）
                # 编译为 ``UNPACK_SEQUENCE 0; LOAD_CONST <val>; STORE_*``——
                # LOAD_CONST 是 case body 赋值的值加载，其后的 STORE 属于 body
                # 而非 as 绑定。仅当 UNPACK_SEQUENCE 0 的下一条指令是 STORE_*
                # 时才识别为 as 绑定，避免吞并 case body 赋值。
                if unpack_idx + 1 < len(filtered) and filtered[unpack_idx + 1].opname in self.STORE_OPS:
                    as_name = filtered[unpack_idx + 1].argval
            else:
                # [B18] 属性槽位归属 = 含 SWAP 的完整栈模拟。CPython 类模式
                # 协议：UNPACK_SEQUENCE 把 kwd/位置属性值压栈（TOS = 槽 0），
                # 各子模式按需以 SWAP k 轮转取值——字面量子模式在栈顶弹出前
                # 以 LOAD_CONST+COMPARE 测试（消耗该值），捕获子模式以 STORE
                # 绑定（弹出该值），通配以 POP_TOP 丢弃。子模式指令的**出现
                # 顺序 ≠ 槽位顺序**（编译器把测试提前、捕获延后，SWAP 重排
                # 栈序），线性归属把字面量填进错误的槽（`Point(x=x, y=0)` →
                # `Point(x=0, y=x)`）。栈模拟：栈元素 = 槽位号（0..count-1，
                # 位置槽在前、keyword 槽在后），SWAP k 交换 TOS 与 TOSk，每个
                # 测试/捕获/通配消费 TOS 槽位 → 产出按槽位号排序的子模式
                # 列表（与 keyword_keys 槽位对齐）。
                # 【识别条件】UNPACK_SEQUENCE 后的 SWAP/LOAD_CONST+COMPARE/
                # STORE_*/POP_TOP 指令序列（编译器子模式协议，操作码形态）。
                # 【归约方式】操作数栈模拟（SWAP 交换 + 消费弹出），槽位号
                # 即 keyword_keys/位置参数的排列事实。
                # 【AST 映射】槽位号 → MatchClass.patterns 下标（位置段在前、
                # keyword 段在后，与发射端 pos_count 切分一致）。
                # [C1] 只读 filtered 指令序列；[C2] 嵌套类模式经递归独立
                # 提取（抽象节点，外层只计一个槽位消费）；[C3] SWAP 是编译
                # 器子模式取值的显式栈协议，与 case 位置/嵌套深度无关。
                _total_slots = count
                _slot_patterns = {}
                _attr_stack = list(range(_total_slots - 1, -1, -1))  # TOS = 槽 0
                j = unpack_idx + 1
                while j < len(filtered) and _attr_stack:
                    instr = filtered[j]
                    # 嵌套 class pattern（如 Outer(x=Inner(1))）
                    # 字节码特征：LOAD_NAME/LOAD_GLOBAL + LOAD_CONST(tuple) + MATCH_CLASS
                    # 递归提取内层 class pattern 作为当前属性的值
                    if (instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL') and
                            j + 2 < len(filtered) and
                            filtered[j + 1].opname == 'LOAD_CONST' and
                            isinstance(filtered[j + 1].argval, tuple) and
                            filtered[j + 2].opname == 'MATCH_CLASS'):
                        nested_instrs = filtered[j:]
                        nested_pattern = self._extract_class_pattern(nested_instrs)
                        _slot_patterns[_attr_stack.pop()] = nested_pattern
                        # 跳过内层 class pattern 的所有指令
                        # 内层结构：LOAD_NAME + LOAD_CONST + MATCH_CLASS + COPY + POP_JUMP_IF_NONE +
                        #          UNPACK_SEQUENCE + (per attr: LOAD_CONST+COMPARE_OP+COND_JUMP 或 STORE_ 或 POP_TOP)
                        consumed = self._count_class_pattern_instrs(nested_instrs)
                        j += consumed
                    elif instr.opname == 'SWAP' and instr.argval is not None and instr.argval >= 2:
                        # SWAP k：交换 TOS 与 TOSk（编译器子模式取值轮转）
                        _k = instr.argval
                        if len(_attr_stack) >= _k:
                            _attr_stack[-1], _attr_stack[-_k] = _attr_stack[-_k], _attr_stack[-1]
                        j += 1
                    elif instr.opname == 'LOAD_CONST' and j + 1 < len(filtered) and filtered[j + 1].opname == 'COMPARE_OP':
                        _slot_patterns[_attr_stack.pop()] = {'type': 'MatchValue', 'value': {'type': 'Constant', 'value': instr.argval}}
                        j += 2
                        # 跳过条件跳转
                        while j < len(filtered) and filtered[j].opname in self.COND_JUMP_OPS:
                            j += 1
                    elif instr.opname in self.STORE_OPS:
                        _slot_patterns[_attr_stack.pop()] = {'type': 'MatchAs', 'name': instr.argval}
                        j += 1
                    elif instr.opname == 'POP_TOP':
                        # 通配符 _（栈非空时消费 TOS 槽位）；栈空后的 POP_TOP
                        # 是被匹配值副本丢弃（case 体协议），不占槽位
                        if _attr_stack:
                            _slot_patterns[_attr_stack.pop()] = {'type': 'MatchAs'}
                        j += 1
                    else:
                        j += 1
                # 槽位号排序输出（发射端 pos_count = len(patterns) -
                # len(keyword_keys) 按下标切分位置/keyword 段）；协议保证全
                # 槽位消费，未消费槽位（提取极限形态）以通配补位，保持与
                # keyword_keys 的下标对齐，不发生串位。
                patterns = [_slot_patterns.get(_slot, {'type': 'MatchAs'})
                            for _slot in range(_total_slots)]

        result = {'type': 'MatchClass', 'cls': {'type': 'Name', 'id': cls_name}}
        if patterns:
            result['patterns'] = patterns
        if keyword_keys:
            result['keyword_keys'] = keyword_keys
        if as_name:
            result['as_name'] = as_name
        return result

    def _extract_or_or_literal_pattern(self, instrs: List[Instruction]) -> Dict[str, Any]:
        patterns = []
        as_name = None

        found_copy = any(i.opname == 'COPY' for i in instrs)

        i = 0
        last_compare_end = -1
        capture_store_name = None
        while i < len(instrs):
            instr = instrs[i]

            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                i += 1
                continue

            if instr.opname == 'COPY':
                i += 1
                continue

            if found_copy and instr.opname in self.LOAD_VAR_OPS:
                first_copy_idx = next((j for j, x in enumerate(instrs) if x.opname == 'COPY'), len(instrs))
                if i < first_copy_idx:
                    i += 1
                    continue
                if capture_store_name and instr.argval == capture_store_name:
                    i += 1
                    continue

            if instr.opname == 'LOAD_CONST' and i + 1 < len(instrs) and instrs[i + 1].opname in ('COMPARE_OP', 'IS_OP'):
                if capture_store_name:
                    next_i = i + 2
                    while next_i < len(instrs) and instrs[next_i].opname in self.COND_JUMP_OPS:
                        next_i += 1
                    last_compare_end = next_i - 1
                    i = next_i
                    continue
                literal_val = instr.argval
                next_i = i + 2
                while next_i < len(instrs) and instrs[next_i].opname in self.COND_JUMP_OPS:
                    next_i += 1
                patterns.append({'type': 'MatchValue', 'value': {'type': 'Constant', 'value': literal_val}})
                last_compare_end = next_i - 1
                i = next_i
            elif instr.opname in ('IS_OP',):
                prev_load_const = None
                if i > 0 and instrs[i - 1].opname == 'LOAD_CONST':
                    prev_load_const = instrs[i - 1].argval
                next_i = i + 1
                while next_i < len(instrs) and instrs[next_i].opname in self.COND_JUMP_OPS:
                    next_i += 1
                if prev_load_const is not None:
                    if prev_load_const is True or prev_load_const is False:
                        patterns.append({'type': 'MatchSingleton', 'value': prev_load_const})
                    elif prev_load_const is None:
                        patterns.append({'type': 'MatchSingleton', 'value': None})
                    else:
                        patterns.append({'type': 'MatchValue', 'value': {'type': 'Constant', 'value': prev_load_const}})
                else:
                    patterns.append({'type': 'MatchSingleton', 'value': None})
                last_compare_end = next_i - 1
                i = next_i
            elif instr.opname in self.STORE_OPS:
                if last_compare_end >= 0 and i == last_compare_end + 1:
                    as_name = instr.argval if instr.argval else None
                    i += 1
                elif last_compare_end < 0:
                    copy_idx = next((j for j, x in enumerate(instrs) if x.opname == 'COPY'), len(instrs))
                    if i < copy_idx:
                        i += 1
                    else:
                        capture_store_name = instr.argval if instr.argval else None
                        as_name = capture_store_name
                        i += 1
                else:
                    i += 1
            elif instr.opname in self.LOAD_VAR_OPS:
                if found_copy:
                    break
                else:
                    i += 1
                    continue
            else:
                i += 1

        if len(patterns) == 0:
            result = {'type': 'MatchAs'}
            if as_name:
                result['name'] = as_name
            return result
        elif len(patterns) == 1:
            result = patterns[0]
            if as_name:
                result = {'type': 'MatchAs', 'pattern': result, 'name': as_name}
            return result
        else:
            result = {'type': 'MatchOr', 'patterns': patterns}
            if as_name:
                result = {'type': 'MatchAs', 'pattern': result, 'name': as_name}
            return result

    def _extract_mapping_pattern(self, instrs: List[Instruction]) -> Dict[str, Any]:
        """
        构建MatchMapping AST

        算法：
        1. 从LOAD_CONST(tuple)获取键名列表
        2. 从UNPACK_SEQUENCE后的指令序列提取值pattern
        3. 从DICT_UPDATE+STORE_FAST检测**rest绑定
        4. 从SWAP+POP_TOP+STORE_FAST检测**rest绑定（无DICT_UPDATE时）

        关键修复：
        - 值pattern：UNPACK_SEQUENCE后每个槽位可能是MatchValue（LOAD_CONST+COMPARE_OP）
          或MatchAs（STORE_）或通配符（POP_TOP）
        - **rest绑定：DICT_UPDATE后跟STORE_FAST，rest名称是DICT_UPDATE后的STORE_目标
        """
        keys = []
        patterns = []
        key_names = []
        rest_name = None

        filtered = [i for i in instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]

        # 步骤1：提取键名
        for i, instr in enumerate(filtered):
            if instr.opname == 'LOAD_CONST' and isinstance(instr.argval, tuple):
                key_names = list(instr.argval)
                for kn in key_names:
                    keys.append({'type': 'Constant', 'value': kn})
                    patterns.append({'type': 'MatchAs'})
                break

        # 步骤2：提取值pattern - 在UNPACK_SEQUENCE后查找
        unpack_idx = None
        for i, instr in enumerate(filtered):
            if instr.opname == 'UNPACK_SEQUENCE':
                unpack_idx = i
                break

        if unpack_idx is not None:
            count = filtered[unpack_idx].argval if filtered[unpack_idx].argval is not None else 0
            next_after_unpack = unpack_idx + 1
            has_nested_structural = (
                next_after_unpack < len(filtered) and
                filtered[next_after_unpack].opname in ('MATCH_SEQUENCE', 'MATCH_CLASS', 'MATCH_MAPPING')
            )
            if has_nested_structural and count == 1 and len(patterns) >= 1:
                nested_op = filtered[next_after_unpack].opname
                nested_instrs = filtered[next_after_unpack:]
                # [B14 修复] 嵌套值模式按其类型递归：MATCH_MAPPING 之前不在
                # 判据内，嵌套 mapping（{"user": {"name": n, …}}）坍缩为对
                # GET_LEN 常量的幻影 MatchValue（case {'user': 2}）。依据
                # 「嵌套即抽象节点」[C2]：嵌套值模式按类型分派递归提取，
                # mapping/sequence/class 三向同判（嵌套无感）。
                if nested_op == 'MATCH_SEQUENCE':
                    nested_pattern = self._extract_sequence_pattern(nested_instrs)
                elif nested_op == 'MATCH_MAPPING':
                    nested_pattern = self._extract_mapping_pattern(nested_instrs)
                else:
                    nested_pattern = self._extract_class_pattern(nested_instrs)
                patterns[0] = nested_pattern
            elif count > 0:
                # [B14 修复] **rest 的 STORE 归属 rest 绑定，不属于值槽位：
                # ``case {'type': t, **rest}`` 编译为 …DICT_UPDATE; …;
                # STORE rest; STORE t——rest 的 STORE 在值槽位 STORE 之前，
                # 原槽位行走把 STORE rest 误填入 slot 0（t 丢失、rest 双绑）。
                # 结构事实：DICT_UPDATE 之后首个 STORE_* 是 rest 绑定
                # （步骤3 的 DICT_UPDATE→STORE 配对判据），一条 STORE 一个
                # 归属（每块唯一归属），槽位行走跳过它。
                _rest_store_offset = None
                _last_dict_update = None
                for _i, _ins in enumerate(filtered):
                    if _ins.opname == 'DICT_UPDATE':
                        _last_dict_update = _i
                if _last_dict_update is not None:
                    for _i in range(_last_dict_update + 1, len(filtered)):
                        if filtered[_i].opname in self.STORE_OPS:
                            _rest_store_offset = filtered[_i].offset
                            break
                attr_idx = 0
                j = unpack_idx + 1
                while j < len(filtered) and attr_idx < count and attr_idx < len(patterns):
                    instr = filtered[j]
                    if instr.opname in ('SWAP', 'POP_TOP'):
                        j += 1
                        continue
                    if (_rest_store_offset is not None and
                            instr.opname in self.STORE_OPS and
                            instr.offset == _rest_store_offset):
                        j += 1
                        continue
                    if instr.opname == 'LOAD_CONST' and j + 1 < len(filtered) and filtered[j + 1].opname == 'COMPARE_OP':
                        patterns[attr_idx] = {'type': 'MatchValue', 'value': {'type': 'Constant', 'value': instr.argval}}
                        j += 2
                        while j < len(filtered) and filtered[j].opname in self.COND_JUMP_OPS:
                            j += 1
                        attr_idx += 1
                    elif instr.opname in self.STORE_OPS:
                        patterns[attr_idx] = {'type': 'MatchAs', 'name': instr.argval}
                        j += 1
                        attr_idx += 1
                    elif instr.opname == 'POP_TOP':
                        patterns[attr_idx] = {'type': 'MatchAs'}
                        j += 1
                        attr_idx += 1
                    else:
                        j += 1

        # 步骤3：检测**rest绑定
        has_dict_update = any(i.opname == 'DICT_UPDATE' for i in filtered)
        if has_dict_update:
            # DICT_UPDATE + STORE_FAST模式：**rest
            # 找到DICT_UPDATE后的第一个STORE_指令
            found_dict_update = False
            for i, instr in enumerate(filtered):
                if instr.opname == 'DICT_UPDATE':
                    found_dict_update = True
                    continue
                if found_dict_update and instr.opname in self.STORE_OPS:
                    rest_name = instr.argval
                    break
        else:
            # SWAP + POP_TOP + STORE_模式：仅在没有key绑定时检测**rest
            # 有key绑定时，SWAP+POP_TOP后的STORE_是值绑定，不是rest
            if len(key_names) == 0:
                for i, instr in enumerate(filtered):
                    if instr.opname == 'SWAP' and i + 1 < len(filtered) and filtered[i + 1].opname == 'POP_TOP':
                        for j in range(i + 2, len(filtered)):
                            if filtered[j].opname in self.STORE_OPS:
                                rest_name = filtered[j].argval
                                break
                        break

        result = {
            'type': 'MatchMapping',
            'keys': keys,
            'patterns': patterns,
        }
        if rest_name:
            result['rest'] = rest_name

        return result

