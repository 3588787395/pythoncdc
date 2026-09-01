"""Repro 06-12: `del e` (as-var cleanup) leaked into handler body.

The CPython 3.11+ as-var cleanup (LOAD_CONST None + STORE_FAST e +
DELETE_FAST e) leaks as a `del e` statement inside the except handler
body when the handler falls through (no explicit return/reraise at the
end of the body block).

Pattern in quotation.pyc api_get_financial HTTPError handler:
  error_no = e2.code
  if not e2.response:
      error_info = None
      del e2          # <- leaked as-var cleanup
"""


def handle(e2):
    error_no = e2.code
    if not e2.response:
        error_info = None
    else:
        error_info = str(e2.response)
    return ({'error_no': error_no, 'error_info': error_info}, {})
