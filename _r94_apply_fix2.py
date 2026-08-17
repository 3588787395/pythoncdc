#!/usr/bin/env python3
"""R94: Apply fix 2 - handle multi-statement _generate_ternary in _generate_try"""

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                if _nested_ternary_for_handler is not None:
                    self._generating_regions.discard(id(_nested_ternary_for_handler))
                    self._generating_regions.add(id(_nested_ternary_for_handler))
                    try:
                        _t_stmts = self._generate_ternary(_nested_ternary_for_handler)
                    finally:
                        self._generating_regions.discard(id(_nested_ternary_for_handler))
                    _t_expr = None
                    if _t_stmts and len(_t_stmts) == 1:
                        _t_node = _t_stmts[0]
                        if (_t_node.get('type') == 'Expr'
                                and _t_node.get('value', {}).get('type') == 'IfExp'):
                            _t_expr = _t_node['value']
                        elif (_t_node.get('type') == 'Assign'
                                and _t_node.get('value', {}).get('type') == 'IfExp'):
                            _t_expr = _t_node['value']
                    if _t_expr is not None:
                        handler_node['exc_type'] = _t_expr"""

new = """                if _nested_ternary_for_handler is not None:
                    self._generating_regions.discard(id(_nested_ternary_for_handler))
                    self._generating_regions.add(id(_nested_ternary_for_handler))
                    try:
                        _t_stmts = self._generate_ternary(_nested_ternary_for_handler)
                    finally:
                        self._generating_regions.discard(id(_nested_ternary_for_handler))
                    _t_expr = None
                    # [R94 fix] When _generate_ternary returns multiple
                    # statements (pre_stmts + ternary assign), the
                    # pre_stmts contain user statements that were in the
                    # ternary's condition_block (e.g. `error_info =
                    # get_traceback_message(); system_log.error(...)`).
                    # These must be added to handler_body, not discarded.
                    # 依「每块唯一归属」: pre_stmts belong to independent
                    # AST nodes, not the TernaryRegion's exc_type.
                    # Per "parent references child entry": parent
                    # ExceptHandler references ternary's IfExp as exc_type
                    # and pre_stmts as handler body predecessors.
                    if _t_stmts and len(_t_stmts) == 1:
                        _t_node = _t_stmts[0]
                        if (_t_node.get('type') == 'Expr'
                                and _t_node.get('value', {}).get('type') == 'IfExp'):
                            _t_expr = _t_node['value']
                        elif (_t_node.get('type') == 'Assign'
                                and _t_node.get('value', {}).get('type') == 'IfExp'):
                            _t_expr = _t_node['value']
                    elif _t_stmts and len(_t_stmts) > 1:
                        # Multi-statement: pre_stmts + ternary node.
                        # Extract IfExp from the last statement.
                        _last_t = _t_stmts[-1]
                        if (_last_t.get('type') == 'Assign'
                                and _last_t.get('value', {}).get('type') == 'IfExp'):
                            _t_expr = _last_t['value']
                            # Pre-stmts go into handler_body (before
                            # any existing handler_body statements).
                            _pre_stmts_for_body = _t_stmts[:-1]
                            handler_body = list(_pre_stmts_for_body) + handler_body
                        elif (_last_t.get('type') == 'Expr'
                                and _last_t.get('value', {}).get('type') == 'IfExp'):
                            _t_expr = _last_t['value']
                            _pre_stmts_for_body = _t_stmts[:-1]
                            handler_body = list(_pre_stmts_for_body) + handler_body
                    if _t_expr is not None:
                        handler_node['exc_type'] = _t_expr"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix 2 applied successfully!")
else:
    print("ERROR: Old text not found for fix 2!")
    # Try to find it
    import re
    pattern = r'if _t_stmts and len\(_t_stmts\) == 1:'
    match = re.search(pattern, content)
    if match:
        start = max(0, match.start() - 200)
        print(f"Context around match at pos {match.start()}:")
        print(repr(content[start:match.start()+100]))
