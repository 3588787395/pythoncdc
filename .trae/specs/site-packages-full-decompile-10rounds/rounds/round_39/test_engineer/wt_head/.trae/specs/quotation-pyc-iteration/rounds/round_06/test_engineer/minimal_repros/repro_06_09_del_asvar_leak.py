"""Repro 06-09: `del e` (as-var cleanup) leaked into handler body.

Defect: The CPython 3.11+ as-var cleanup `del e` (LOAD_CONST None →
STORE_FAST e → DELETE_FAST e) leaks as a `del e2` statement inside the
except handler body, instead of being filtered as except-mechanism
overhead.

Root cause: as-var cleanup detection only triggers when the cleanup is
followed by RETURN_VALUE/RERAISE in the same block; when followed by
other statements it leaks.
"""


def handle(e2):
    error_no = e2.code
    if not e2.response:
        error_info = None
    else:
        error_info = str(e2.response)
    return error_no, error_info
