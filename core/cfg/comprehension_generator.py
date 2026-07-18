from typing import List, Dict, Any, Optional, Tuple, Union

from .basic_block import Instruction
from .region_analyzer import (
    CONDITIONAL_JUMP_OPS,
)


class ComprehensionGenerator:
    def __init__(self, expr_reconstructor):
        self.expr_reconstructor = expr_reconstructor

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
                        comp_indices.append((idx, code_val))

        if not comp_indices:
            return None

        all_stmts = []
        prev_end = 0

        for comp_idx, comp_code in comp_indices:
            pre_comp_instrs = instrs[prev_end:comp_idx - 1]
            if pre_comp_instrs:
                pre_stmts = self._generate_pre_comp_stmts(pre_comp_instrs, instrs, prev_end, region_ast_gen=region_ast_gen)
                all_stmts.extend(pre_stmts)

            get_iter_idx = None
            for idx in range(comp_idx + 1, len(instrs)):
                if instrs[idx].opname == 'GET_ITER':
                    get_iter_idx = idx
                    break

            if get_iter_idx is None:
                continue

            iter_instrs = instrs[comp_idx + 1:get_iter_idx]
            iter_expr = self.expr_reconstructor.reconstruct(iter_instrs)
            if iter_expr is None:
                iter_expr = {'type': 'Name', 'id': '<iterator>'}

            comp_ast = self.parse_comprehension_inner(comp_code, iter_expr)
            if comp_ast is None:
                continue

            gen_call_end = get_iter_idx + 1
            for idx in range(get_iter_idx + 1, len(instrs)):
                if instrs[idx].opname in ('PRECALL', 'CALL'):
                    gen_call_end = idx + 1
                    if instrs[idx].opname == 'CALL':
                        break

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

            store_instr = None
            for instr in instrs[wrapper_end:]:
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    store_instr = instr
                    break

            if store_instr:
                all_stmts.append({
                    'type': 'Assign',
                    'targets': [{'type': 'Name', 'id': store_instr.argval, 'ctx': 'Store'}],
                    'value': comp_value,
                })
                store_idx = instrs.index(store_instr)
                prev_end = store_idx + 1
            else:
                last_instr = instrs[-1]
                if last_instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    all_stmts.append({'type': 'Return', 'value': comp_value})
                else:
                    all_stmts.append({'type': 'Expr', 'value': comp_value})
                prev_end = len(instrs)

        remaining_instrs = instrs[prev_end:]
        if remaining_instrs:
            remaining_stmts = self._generate_remaining_stmts(remaining_instrs)
            all_stmts.extend(remaining_stmts)

        return all_stmts if all_stmts else None

    def _generate_pre_comp_stmts(self, pre_instrs, all_instrs, start_idx, region_ast_gen=None):
        stmts = []
        current_instrs = []
        _import_pending = False
        for instr in pre_instrs:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP'):
                if current_instrs:
                    continue
                continue
            if instr.opname == 'IMPORT_NAME':
                _import_pending = True
                current_instrs.append(instr)
                continue
            if instr.opname == 'IMPORT_FROM':
                current_instrs.append(instr)
                continue
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                if _import_pending:
                    current_instrs.append(instr)
                    expr = self.expr_reconstructor.reconstruct(current_instrs)
                    if expr:
                        if expr.get('type') == 'Import':
                            stmts.append({'type': 'Import', 'names': expr.get('names', [])})
                        elif expr.get('type') == 'ImportFrom':
                            stmts.append(expr)
                        else:
                            stmts.append({
                                'type': 'Assign',
                                'targets': [{'type': 'Name', 'id': instr.argval, 'ctx': 'Store'}],
                                'value': expr,
                            })
                    current_instrs = []
                    _import_pending = False
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
            current_instrs.append(instr)
        return stmts

    def _generate_remaining_stmts(self, remaining_instrs):
        stmts = []
        current_instrs = []
        for instr in remaining_instrs:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP'):
                continue
            if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                if current_instrs:
                    value_expr = self.expr_reconstructor.reconstruct(current_instrs)
                    if value_expr:
                        stmts.append({'type': 'Return', 'value': value_expr})
                    current_instrs = []
                continue
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                current_instrs.append(instr)
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
            current_instrs.append(instr)
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

        all_instrs = []
        for b in nested_cfg.get_blocks_in_order():
            all_instrs.extend(b.instructions)
        all_instrs.sort(key=lambda i: i.offset)

        # [Round5-03] 多 for 子句检测：统计 FOR_ITER 数量。
        # 多 for 子句（如 `{x+y for x in a for y in b}`）字节码含多个 FOR_ITER，
        # 每个 FOR_ITER 后接 STORE_* target，最后一个 FOR_ITER 的 body 含 element + APPEND。
        # 单 for 路径保留原逻辑；多 for 走新路径分别提取每个 generator。
        for_iter_indices = [i for i, instr in enumerate(all_instrs) if instr.opname == 'FOR_ITER']
        if len(for_iter_indices) > 1:
            return self._parse_multi_for_comprehension(code_obj, all_instrs, iter_expr, for_iter_indices)

        target_name = self._find_comp_target_names(all_instrs, first_only=True)
        if target_name is None:
            return None

        target = self._build_comprehension_target(all_instrs)
        if target is None:
            return None

        append_op, append_idx = self._find_comp_append_op(all_instrs)
        if append_op is None:
            return None

        _, store_idx = self._find_comp_append_op(all_instrs, target_name)
        if store_idx is None:
            return None

        # 检测三元模式：条件跳转的目标在LIST_APPEND之前
        ternary_info = self._detect_comp_ternary(all_instrs, store_idx, append_idx)
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
            ifs = []
        else:
            ifs, elt_start_idx = self._extract_comp_ifs(all_instrs, store_idx, append_idx)
            if append_op == 'MAP_ADD':
                key_expr, value_expr = self._split_dict_comp_kv(all_instrs, elt_start_idx, append_idx)
                if key_expr is None:
                    key_expr = {'type': 'Name', 'id': target_name, 'ctx': 'Load'}
                if value_expr is None:
                    value_expr = {'type': 'Constant', 'value': None}
                elt_expr = (key_expr, value_expr)
            else:
                elt_instrs = all_instrs[elt_start_idx:append_idx]
                elt_expr = self.expr_reconstructor.reconstruct(elt_instrs)
                if elt_expr is None:
                    elt_expr = {'type': 'Name', 'id': target_name, 'ctx': 'Load'}

        is_async = 0
        for instr in all_instrs:
            if instr.opname == 'GET_AITER':
                is_async = 1
                break

        generators = [{
            'type': 'comprehension',
            'target': target,
            'iter': iter_expr,
            'ifs': ifs,
            'is_async': is_async,
        }]

        return self._build_comp_result(code_obj, elt_expr, generators)

    def _parse_multi_for_comprehension(self, code_obj, all_instrs, iter_expr, for_iter_indices):
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
        """
        append_op, append_idx = self._find_comp_append_op(all_instrs)
        if append_op is None:
            return None

        is_async = 0
        for instr in all_instrs:
            if instr.opname == 'GET_AITER':
                is_async = 1
                break

        generators = []
        for gen_idx, fi_idx in enumerate(for_iter_indices):
            # target = STORE_* right after FOR_ITER
            if fi_idx + 1 >= len(all_instrs):
                return None
            store_instr = all_instrs[fi_idx + 1]
            if store_instr.opname not in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL'):
                return None
            target = {
                'type': 'Name',
                'id': store_instr.argval,
                'ctx': 'Store',
            }

            if gen_idx == 0:
                # 第一个 for 的 iter 来自外部传入
                gen_iter_expr = iter_expr
            else:
                # 后续 for 的 iter 来自前一个 STORE_* 之后、本 FOR_ITER 之前的 LOAD_* + GET_ITER
                # 定位本 FOR_ITER 之前的 GET_ITER
                get_iter_idx = None
                for j in range(fi_idx - 1, -1, -1):
                    if all_instrs[j].opname == 'GET_ITER':
                        get_iter_idx = j
                        break
                    if all_instrs[j].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL'):
                        break
                if get_iter_idx is None:
                    return None
                # iter 表达式指令范围：从上一个 STORE_* 之后到 GET_ITER 之前
                start_idx = 0
                for j in range(get_iter_idx - 1, -1, -1):
                    if all_instrs[j].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL'):
                        start_idx = j + 1
                        break
                iter_instrs = [i for i in all_instrs[start_idx:get_iter_idx]
                               if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                gen_iter_expr = self.expr_reconstructor.reconstruct(iter_instrs) if iter_instrs else None
                if gen_iter_expr is None:
                    gen_iter_expr = {'type': 'Name', 'id': '<iterator>'}

            generators.append({
                'type': 'comprehension',
                'target': target,
                'iter': gen_iter_expr,
                'ifs': [],
                'is_async': is_async,
            })

        # 最内层 FOR_ITER 的 STORE_* 索引（用于元素提取）
        innermost_fi_idx = for_iter_indices[-1]
        innermost_store_idx = innermost_fi_idx + 1
        # 元素提取：从 innermost_store_idx + 1 到 append_idx
        elt_start_idx = innermost_store_idx + 1

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
        else:
            ifs, elt_start_idx = self._extract_comp_ifs(all_instrs, innermost_store_idx, append_idx)
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

        best_key_end = self._find_dict_kv_split_point(filtered_instrs, num_values)

        if best_key_end is not None and best_key_end > 0:
            key_instrs = filtered_instrs[:best_key_end]
            value_instrs = filtered_instrs[best_key_end:]
        else:
            key_instrs = []
            value_instrs = filtered_instrs

        key_expr = self.expr_reconstructor.reconstruct(key_instrs) if key_instrs else None
        value_expr = self.expr_reconstructor.reconstruct(value_instrs) if value_instrs else None

        # [Round10-05] walrus 的 COPY+STORE 已由 expr_reconstructor 识别为
        # NamedExpr（reconstruct 中 COPY 1 + STORE_* 会生成 NamedExpr 节点），
        # 无需根据 _walrus_var 手动包裹 value_expr。这样 key 位置和 value 位置
        # 的 walrus 都能被正确归约到对应的表达式上。

        return key_expr, value_expr

    def _find_dict_kv_split_point(self, instrs: List[Instruction], num_values: int) -> Optional[int]:
        if len(instrs) < 2:
            return None

        stack_depth = 0
        depth_history = []

        for i, instr in enumerate(instrs):
            delta = self._get_stack_delta(instr)
            stack_depth += delta
            depth_history.append((i, stack_depth))

        final_depth = stack_depth
        if final_depth < 1:
            return None

        for i in range(len(depth_history) - 1):
            idx, depth = depth_history[i]
            next_idx, next_depth = depth_history[i + 1]
            if depth == 1 and next_depth > 1 and i > 0:
                return i + 1

        for i in range(len(depth_history) - 1):
            idx, depth = depth_history[i]
            next_idx, next_depth = depth_history[i + 1]
            if depth == 1 and i > 0:
                return i + 1

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
            return 1 - instr.arg if instr.arg else 0
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
        names = []
        for instr in all_instrs:
            if instr.opname in ('STORE_FAST', 'STORE_DEREF', 'STORE_NAME'):
                if instr.argval != '.0' and instr.argval not in names:
                    if first_only:
                        return instr.argval
                    names.append(instr.argval)
        return names if not first_only else None

    def _build_comprehension_target(self, all_instrs: List[Instruction]) -> Optional[Dict]:
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

    def _find_comp_append_op(self, all_instrs: List[Instruction], target_name: str = None) -> Tuple[Optional[str], Optional[int]]:
        if target_name:
            for idx, instr in enumerate(all_instrs):
                if instr.opname in ('STORE_FAST', 'STORE_DEREF', 'STORE_NAME') and instr.argval == target_name:
                    return 'STORE', idx
        for idx, instr in enumerate(all_instrs):
            if instr.opname in ('LIST_APPEND', 'SET_ADD', 'MAP_ADD', 'DICT_MERGE'):
                return instr.opname, idx
        for idx, instr in enumerate(all_instrs):
            if instr.opname == 'YIELD_VALUE':
                return 'YIELD_VALUE', idx
        return None, None

    def _extract_comp_ifs(self, all_instrs: List[Instruction], store_idx: int,
                          append_idx: int) -> Tuple[List[Dict], int]:
        ifs = []
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
                        # 跳转目标在LIST_APPEND之前 → 三元模式，不提取为过滤条件
                        # 重置elt_start_idx以包含条件指令
                        elt_start_idx = store_idx + 1
                        return ifs, elt_start_idx
                segments.append((current_start, idx, instr))
                current_start = idx + 1

        if segments:
            for seg_start, seg_end, jump_instr in segments:
                cond_instrs = all_instrs[seg_start:seg_end]
                if cond_instrs:
                    cond_expr = self.expr_reconstructor.reconstruct(cond_instrs)
                    if cond_expr:
                        if 'IF_TRUE' in jump_instr.opname:
                            cond_expr = {'type': 'UnaryOp', 'op': 'not', 'operand': cond_expr}
                        ifs.append(cond_expr)
            elt_start_idx = current_start

        # Multiple if conditions in comprehension are connected by 'and' (short-circuit).
        # In Python bytecode, `if a and b` and `if a if b` produce identical bytecode,
        # so we combine multiple conditions into a single BoolOp to match the more common
        # source form and produce correct BoolOp AST nodes.
        if len(ifs) > 1:
            ifs = [{'type': 'BoolOp', 'op': 'and', 'values': ifs}]

        return ifs, elt_start_idx

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
        cond_jump_idx = None
        for idx in range(store_idx + 1, append_idx):
            instr = all_instrs[idx]
            if instr.opname in CONDITIONAL_JUMP_OPS:
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

    def _detect_comp_ternary(self, all_instrs: List[Instruction],
                             store_idx: int,
                             append_idx: int) -> Optional[Dict[str, Any]]:
        """检测推导式中的三元表达式模式

        三元模式特征：条件跳转的目标在LIST_APPEND之前（跳转到false值），
        而不是跳过整个元素表达式（过滤器模式）。
        字节码模式：condition → POP_JUMP_IF_FALSE false_value → true_value → JUMP_FORWARD merge → false_value → LIST_APPEND
        """
        append_offset = all_instrs[append_idx].offset if append_idx < len(all_instrs) else float('inf')

        # 查找STORE和LIST_APPEND之间的条件跳转
        cond_jump_idx = None
        for idx in range(store_idx + 1, append_idx):
            instr = all_instrs[idx]
            if instr.opname in CONDITIONAL_JUMP_OPS:
                # 检查跳转目标是否在LIST_APPEND之前（三元模式）
                if hasattr(instr, 'argval') and instr.argval is not None:
                    if instr.argval < append_offset:
                        cond_jump_idx = idx
                        break
                # 跳转目标在LIST_APPEND之后 → 过滤器模式，不是三元
                return None

        if cond_jump_idx is None:
            return None

        cond_instr = all_instrs[cond_jump_idx]
        false_target_offset = cond_instr.argval

        # 分离条件指令、true值指令、false值指令
        # 条件指令：从store_idx+1到cond_jump_idx（不含跳转指令本身）
        cond_instrs = all_instrs[store_idx + 1:cond_jump_idx]

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

        # true值指令：从true_start到true_end（不含JUMP）
        if true_end is not None:
            true_instrs = all_instrs[true_start:true_end]
        else:
            true_instrs = all_instrs[true_start:false_start]

        # false值指令：从false_start到append_idx
        # [Round7-08] 若有 merge_offset，false 值区域只到 merge_offset 之前。
        # merge_offset 之后是指令属于后续表达式（如 dict comp 的 value），
        # 不应作为 false 分支的一部分。
        if merge_offset is not None:
            false_end = false_start
            for idx in range(false_start, append_idx):
                if all_instrs[idx].offset >= merge_offset:
                    break
                false_end = idx + 1
            false_instrs = all_instrs[false_start:false_end]
        else:
            false_instrs = all_instrs[false_start:append_idx]

        # 重建条件表达式
        cond_expr = self.expr_reconstructor.reconstruct(cond_instrs)
        if cond_expr is None:
            return None

        # 如果条件跳转是IF_TRUE（or条件），需要取反
        if 'IF_TRUE' in cond_instr.opname:
            cond_expr = {'type': 'UnaryOp', 'op': 'not', 'operand': cond_expr}

        # 重建true值表达式
        true_expr = self.expr_reconstructor.reconstruct(true_instrs)
        if true_expr is None:
            return None

        # 重建false值表达式
        false_expr = self.expr_reconstructor.reconstruct(false_instrs)
        if false_expr is None:
            return None

        # 构建IfExp节点
        return {
            'type': 'IfExp',
            'test': cond_expr,
            'body': true_expr,
            'orelse': false_expr,
        }

    def _build_comp_result(self, code_obj: Any, elt_expr: Dict, generators: List[Dict]) -> Optional[Dict]:
        func_name = code_obj.co_name
        if func_name == '<listcomp>':
            return {'type': 'ListComp', 'elt': elt_expr, 'generators': generators}
        if func_name == '<setcomp>':
            return {'type': 'SetComp', 'elt': elt_expr, 'generators': generators}
        if func_name == '<dictcomp>':
            if isinstance(elt_expr, tuple) and len(elt_expr) == 2:
                key_expr, value_expr = elt_expr
            else:
                key_expr = elt_expr
                value_expr = {'type': 'Constant', 'value': None}
            return {'type': 'DictComp', 'key': key_expr, 'value': value_expr, 'generators': generators}
        if func_name == '<genexpr>':
            return {'type': 'GeneratorExp', 'elt': elt_expr, 'generators': generators}
        return None

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
