"""Repro 06-05: Duplicate statements (same statement emitted twice).

Defect: A single source statement is emitted twice in the decompiled
output, e.g. `error_no = e2.code` appearing twice.

Root cause: statement emission does not deduplicate consecutive
identical statements when a block is referenced by multiple parents
(unique-block-ownership violation).
"""


def handle(e2):
    error_no = e2.code
    if not e2.response:
        error_info = None
    else:
        try:
            error_info = parse(e2.response.body)
        except ValueError:
            error_info = str(e2.response.body)
    return error_no, error_info
