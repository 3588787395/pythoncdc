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

    def parse_case_guard(self, pattern_blocks: List[BasicBlock]) -> Optional[Dict]:
        """
        解析guard条件，返回Compare AST节点或None

        Args:
            pattern_blocks: 模式相关的块列表

        Returns:
            Compare类型的AST节点字典，或None
        """
        return self._extract_case_guard_from_blocks(pattern_blocks)

    def is_match_fallthrough(self, block: BasicBlock) -> bool:
        """
        检测block是否是match的下一个case header

        Args:
            block: 待检测的基本块

        Returns:
            True表示是下一个case header，False表示是case body或其他
        """
        return self._is_match_fallthrough(block)

    def find_real_match_header(self, partial_block: BasicBlock) -> Optional[BasicBlock]:
        """
        向前查找包含MATCH_*指令的真正case header

        当_collect_match_body错误地将pattern中间的块识别为独立的case header时，
        使用此方法找到真正的case header。

        Args:
            partial_block: 只包含部分pattern指令的块

        Returns:
            包含MATCH_*指令的真正case header，如果找不到则返回None
        """
        return self._find_real_match_header(partial_block)

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

        worklist = list(case_block.successors)
        CASE_HEADER_OPS = frozenset({
            'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
            'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
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
                continue

            first_meaningful = meaningful[0] if meaningful else None
            if first_meaningful and first_meaningful.opname == 'COPY':
                continue

            is_pattern_block = False
            has_definitive_pattern = False
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
                    is_pattern_block = True

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
                for s in current.successors:
                    if s not in visited:
                        worklist.append(s)

        return blocks

    def _extract_case_guard_from_blocks(self, pattern_blocks: List[BasicBlock]) -> Optional[Dict[str, Any]]:
        all_instrs = []
        for block in pattern_blocks:
            for instr in block.instructions:
                if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    all_instrs.append(instr)

        if not all_instrs:
            return None

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

                if is_var_const or is_var_var or is_is_op:
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
                            if not has_store_or_unpack:
                                continue
                    guard_start = i
                    for j in range(i + 3, len(all_instrs)):
                        if all_instrs[j].opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
                                                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE'):
                            guard_end = j
                            break

        if guard_start is not None and guard_end is not None:
            guard_instrs = all_instrs[guard_start:guard_end + 1]

            if len(guard_instrs) >= 4:
                left_name = guard_instrs[0].argval
                compare_op = guard_instrs[2].argval

                if guard_instrs[1].opname == 'LOAD_CONST':
                    right_val = guard_instrs[1].argval
                    result = {
                        'type': 'Compare',
                        'left': {'type': 'Name', 'id': left_name},
                        'ops': [{'type': 'CompareOp', 'op': compare_op}],
                        'right': {'type': 'Constant', 'value': right_val}
                    }
                else:
                    right_name = guard_instrs[1].argval
                    result = {
                        'type': 'Compare',
                        'left': {'type': 'Name', 'id': left_name},
                        'ops': [{'type': 'CompareOp', 'op': compare_op}],
                        'right': {'type': 'Name', 'id': right_name}
                    }

                return result

        return None

    def _is_match_fallthrough(self, block: BasicBlock) -> bool:
        """
        检测给定的block是否是match语句的下一个case header（而非case body）

        基于Python 3.11+ match字节码特征：

        Case header块的典型特征：
        1. 包含 MATCH_CLASS / MATCH_SEQUENCE / MATCH_MAPPING / MATCH_KEYS 等pattern匹配指令
        2. 或者包含字面量比较模式：LOAD_CONST + COMPARE_OP(==) + POP_JUMP_IF_FALSE
        3. 或者包含 COPY + LOAD_CONST + COMPARE_OP(==) （用于OR pattern的后续值）

        Case body块的典型特征：
        - 不包含上述pattern匹配指令
        - 包含实际的业务逻辑指令（STORE_FAST, CALL, RETURN_VALUE等）
        """
        if not block or not block.instructions:
            return False

        # 过滤掉无关指令
        instrs = [i for i in block.instructions
                 if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]

        if not instrs:
            return False

        # 特征1：包含明确的MATCH_*指令
        match_ops = {'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                    'MATCH_KEYS', 'MATCH_MAPPING_KEYS'}
        if any(i.opname in match_ops for i in instrs):
            return True

        # 特征2：检测字面量比较模式 (case 1:, case "hello": 等)
        # 模式：LOAD_CONST + COMPARE_OP(==) + POP_JUMP_IF_FALSE
        # 或：COPY + LOAD_CONST + COMPARE_OP(==) （OR pattern的后续值）
        for idx, instr in enumerate(instrs):
            # 检测 LOAD_CONST + COMPARE_OP(==) + POP_JUMP_IF_FALSE 模式
            if instr.opname == 'LOAD_CONST':
                if (idx + 2 < len(instrs) and
                    instrs[idx + 1].opname == 'COMPARE_OP' and
                    instrs[idx + 2].opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE')):
                    return True

            # 检测 COPY + LOAD_CONST + COMPARE_OP(==) 模式（OR pattern）
            if instr.opname == 'COPY':
                if (idx + 2 < len(instrs) and
                    instrs[idx + 1].opname == 'LOAD_CONST' and
                    instrs[idx + 2].opname == 'COMPARE_OP'):
                    return True

        # 特征3：包含GET_LEN或UNPACK_SEQUENCE（序列模式的一部分）
        pattern_helper_ops = {'GET_LEN', 'UNPACK_SEQUENCE'}
        if any(i.opname in pattern_helper_ops for i in instrs):
            # 需要确认这些不是在body中正常使用
            # 如果块主要包含这些操作，则认为是pattern matching
            pattern_count = sum(1 for i in instrs if i.opname in pattern_helper_ops)
            other_ops = [i for i in instrs if i.opname not in pattern_helper_ops
                        and i.opname not in ('LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
                                            'STORE_GLOBAL', 'STORE_DEREF',
                                            'COMPARE_OP', 'POP_TOP', 'COPY',
                                            'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE')]
            if pattern_count > 0 and len(other_ops) == 0:
                return True

        return False

    def _collect_blocks_bfs(self, start_block: BasicBlock) -> List[BasicBlock]:
        from collections import deque
        visited = set()
        queue = deque([start_block])
        result = []
        while queue:
            blk = queue.popleft()
            if blk in visited or not hasattr(blk, 'instructions'):
                continue
            visited.add(blk)
            result.append(blk)
            if hasattr(blk, 'successors'):
                queue.extend(blk.successors)
        return result

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
                return current

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

        has_sequence = any(i.opname == 'MATCH_SEQUENCE' for i in instrs)
        has_class = any(i.opname == 'MATCH_CLASS' for i in instrs)
        has_mapping = any(i.opname == 'MATCH_MAPPING' for i in instrs)

        has_literal_compare = False
        for i in range(len(instrs)):
            if (instrs[i].opname == 'LOAD_CONST' and
                i + 1 < len(instrs) and
                instrs[i + 1].opname in ('COMPARE_OP', 'IS_OP')):
                has_literal_compare = True
                break
        has_copy = any(i.opname == 'COPY' for i in instrs)
        is_literal_match = has_literal_compare and not has_sequence and not has_class and not has_mapping

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

        if result.get('type') in ('MatchValue', 'MatchSingleton', 'MatchOr'):
            as_name = self._find_as_binding(case_block)
            if as_name:
                result = {'type': 'MatchAs', 'pattern': result, 'name': as_name}
        elif result.get('type') == 'MatchAs' and not result.get('name'):
            as_name = self._find_as_binding(case_block)
            if as_name:
                result['name'] = as_name

        return result

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
        store_after_pattern = self._find_last_store_on_success_path(case_block)
        if store_after_pattern:
            return store_after_pattern

        # 策略3：检查COPY指令 - 如果case_block有COPY，说明有as绑定
        # COPY保存subject用于后续的as绑定STORE_
        has_copy_for_as = any(i.opname == 'COPY' for i in filtered)
        if has_copy_for_as:
            # 沿所有后继路径查找STORE_指令
            as_name = self._find_store_in_successors(case_block)
            if as_name:
                return as_name

        return None

    def _find_last_store_on_success_path(self, case_block: BasicBlock) -> Optional[str]:
        """
        沿成功路径查找最后一个STORE_指令（as绑定通常在pattern最后）

        成功路径：从case_block开始，沿每个条件跳转的fall-through后继遍历，
        直到遇到非pattern块。收集路径上所有STORE_指令，返回最后一个。
        """
        stores = []
        visited = {case_block}
        queue = deque()

        # 从case_block的fall-through后继开始
        last = case_block.get_last_instruction()
        if last and last.opname in self.COND_JUMP_OPS:
            for succ in case_block.successors:
                if succ.start_offset != last.argval:
                    queue.append(succ)
                    break
        else:
            queue.extend(case_block.successors)

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

            # 继续沿成功路径
            last = blk.get_last_instruction()
            if last and last.opname in self.COND_JUMP_OPS:
                for succ in blk.successors:
                    if succ.start_offset != last.argval:
                        queue.append(succ)
                        break
            else:
                # 非条件跳转块，检查是否还有pattern后继
                for succ in blk.successors:
                    if succ not in visited and self._is_pattern_block_for_as(succ):
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
        has_body = any(i.opname in ('LOAD_GLOBAL', 'LOAD_NAME', 'CALL',
                                    'BINARY_ADD', 'BINARY_SUBTRACT',
                                    'BINARY_MULTIPLY', 'BINARY_TRUE_DIVIDE',
                                    'RETURN_VALUE', 'RETURN_CONST',
                                    'BUILD_LIST', 'BUILD_TUPLE', 'BUILD_MAP',
                                    'BUILD_SET', 'BUILD_STRING')
                      for i in instrs)

        return has_pattern and not has_body

    def _find_store_in_successors(self, case_block: BasicBlock) -> Optional[str]:
        """BFS搜索所有后继块查找STORE_指令（用于COPY场景的as绑定）"""
        visited = {case_block}
        queue = deque(case_block.successors)

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

            queue.extend(blk.successors)

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

    def _extract_sequence_pattern(self, instrs: List[Instruction]) -> Dict[str, Any]:
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
        for idx, instr in enumerate(filtered):
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
                    slot_actions.setdefault(slot, {'type': 'wildcard'})
                continue
            if instr.opname == 'SWAP':
                if in_unpack_context and len(unpack_stack) >= 2:
                    n = instr.argval if instr.argval else 2
                    if n == 2:
                        unpack_stack[-1], unpack_stack[-2] = unpack_stack[-2], unpack_stack[-1]
                    elif n > 2 and len(unpack_stack) >= n:
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
                    slot_actions.setdefault(slot, {'type': 'capture', 'name': var_name})
                else:
                    as_name = var_name
            elif instr.opname == 'LOAD_CONST' and idx + 1 < len(filtered) and filtered[idx + 1].opname == 'COMPARE_OP':
                literal_val = instr.argval
                if has_unpack:
                    if in_unpack_context and unpack_stack:
                        slot = unpack_stack.pop()
                        slot_actions.setdefault(slot, {'type': 'literal', 'value': literal_val})

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

        filtered = [i for i in instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')]

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

        for i, instr in enumerate(filtered):
            if instr.opname == 'LOAD_CONST' and isinstance(instr.argval, tuple):
                keyword_keys = list(instr.argval)
            elif instr.opname == 'MATCH_CLASS':
                pos_count = instr.argval if instr.argval is not None else 0

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
                for j in range(unpack_idx + 1, min(unpack_idx + 3, len(filtered))):
                    if filtered[j].opname in self.STORE_OPS:
                        as_name = filtered[j].argval
                        break
                    if filtered[j].opname not in ('POP_TOP', 'LOAD_CONST'):
                        break
            else:
                # 按属性数量逐个处理
                attr_idx = 0
                j = unpack_idx + 1
                while j < len(filtered) and attr_idx < count:
                    instr = filtered[j]
                    if instr.opname == 'LOAD_CONST' and j + 1 < len(filtered) and filtered[j + 1].opname == 'COMPARE_OP':
                        patterns.append({'type': 'MatchValue', 'value': {'type': 'Constant', 'value': instr.argval}})
                        j += 2
                        # 跳过条件跳转
                        while j < len(filtered) and filtered[j].opname in self.COND_JUMP_OPS:
                            j += 1
                        attr_idx += 1
                    elif instr.opname in self.STORE_OPS:
                        patterns.append({'type': 'MatchAs', 'name': instr.argval})
                        j += 1
                        attr_idx += 1
                    elif instr.opname == 'POP_TOP':
                        # 通配符 _
                        patterns.append({'type': 'MatchAs'})
                        j += 1
                        attr_idx += 1
                    else:
                        j += 1

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

            if instr.opname == 'LOAD_CONST' and i + 1 < len(instrs) and instrs[i + 1].opname in ('COMPARE_OP', 'IS_OP'):
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
                filtered[next_after_unpack].opname in ('MATCH_SEQUENCE', 'MATCH_CLASS')
            )
            if has_nested_structural and count == 1 and len(patterns) >= 1:
                nested_op = filtered[next_after_unpack].opname
                nested_instrs = filtered[next_after_unpack:]
                if nested_op == 'MATCH_SEQUENCE':
                    nested_pattern = self._extract_sequence_pattern(nested_instrs)
                else:
                    nested_pattern = self._extract_class_pattern(nested_instrs)
                patterns[0] = nested_pattern
            elif count > 0:
                attr_idx = 0
                j = unpack_idx + 1
                while j < len(filtered) and attr_idx < count and attr_idx < len(patterns):
                    instr = filtered[j]
                    if instr.opname in ('SWAP', 'POP_TOP'):
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

    def parse_literal_pattern(self, value: Any) -> Dict[str, Any]:
        """
        解析字面量值为MatchValue AST节点

        用于处理简单字面量匹配模式（如 case 1:, case "hello":, case None:）

        Args:
            value: 字面量值（int, str, None, bool等）

        Returns:
            MatchValue类型的AST节点字典
        """
        return {'type': 'MatchValue', 'value': {'type': 'Constant', 'value': value}}

    @staticmethod
    def is_match_class_op(opname: str) -> bool:
        """检测是否是match类操作码（MATCH_CLASS, MATCH_SEQUENCE, MATCH_MAPPING）"""
        return opname in ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING')

    @staticmethod
    def is_match_key_op(opname: str) -> bool:
        """检测是否是match键操作码（MATCH_KEYS, MATCH_MAPPING_KEYS）"""
        return opname in ('MATCH_KEYS', 'MATCH_MAPPING_KEYS')

    @staticmethod
    def is_match_pattern_op(opname: str) -> bool:
        """检测是否是任何match pattern相关操作码"""
        return opname in ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                         'MATCH_KEYS', 'MATCH_MAPPING_KEYS')
