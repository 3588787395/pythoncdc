"""Repro 06-01: Lost `return` keyword in except handler.

Defect: `return (a, b)` in except handler body becomes bare `(a, b)` Expr
statement when the return value construction (BUILD_TUPLE) and the
POP_EXCEPT + as-var cleanup + RETURN_VALUE are split across separate
basic blocks.

Root cause: _generate_handler_body_statements falls back to
_generate_block_statements when len(user_stores) >= 2 and the bool
_find_return_through_cleanup_chain returns False (it only checks the
current block, not the successor chain).
"""
def fetch(token_value):
    try:
        response = do_request()
        return_data = response.json()
    except ConnectionRefusedError as e1:
        system_log.error(get_traceback_message())
        error_no = -1
        error_info = e1
        return ({'error_no': error_no, 'error_info': error_info}, {})
    return ({'error_no': 0, 'error_info': ''}, return_data)
