"""Repro 94-01: except handler body statement lost (system_log.error call)

Defect: When an except handler contains a function call statement
(e.g., system_log.error(f'...')), the call is dropped from the
decompiled output. Only the preceding STORE_FAST and subsequent
if/return are generated.

Root cause: In _generate_handler_body_statements, when POP_TOP is
encountered after collecting CALL instructions in stmt_instrs,
the expr_reconstructor.reconstruct() fails to rebuild the call
expression (system_log.error(f'...')), and the instructions are
silently discarded.

Original bytecode pattern in except handler:
  POP_TOP               # pop exception
  LOAD_GLOBAL get_traceback_message
  CALL 0
  STORE_FAST error_info  # error_info = get_traceback_message()
  LOAD_GLOBAL system_log
  LOAD_ATTR error
  LOAD_FAST symbol
  FORMAT_VALUE
  LOAD_CONST '...'
  LOAD_FAST error_info
  FORMAT_VALUE
  BUILD_STRING 3
  CALL 1
  POP_TOP               # <--- this POP_TOP triggers Expr reconstruction
  LOAD_FAST fields
  POP_JUMP_FORWARD_IF_NOT_NONE
  ...

Expected decompiled output:
  except BaseException:
      error_info = get_traceback_message()
      system_log.error(f'{symbol} ...: {error_info}')
      history_data = ... if fields is None else ...

Actual (defective) output:
  except BaseException:
      error_info = get_traceback_message()
      history_data = ... if fields is None else ...
  (system_log.error call is MISSING)
"""
import system_log

def get_kline_by_date_one(symbol, fields=None):
    try:
        data = fetch_data(symbol)
        history_data = data if fields is None else data[fields]
    except BaseException:
        error_info = get_traceback_message()
        system_log.error(f'{symbol} data fetch error: {error_info}')
        history_data = None if fields is None else None[fields]
    return history_data
