# -*- coding: utf-8 -*-
"""R68-b2 synth witness #2 (body-loop path, Pattern SIG2 at region_ast_generator
L47390).

Same `SWAP N + N x STORE_DEREF` tuple-assignment shape as r68b2_cell_tuple, but
the block does NOT end in an `if` condition, so `_generate_block_statements_body`
handles the stores itself.  There SWAP is filtered by SKIP_OPS and never reaches
`stmt_instrs`, so SIG2's `not _s2_has_swap` guard cannot see it and builds the
targets in REVERSE store order (the layout without SWAP) -> the product reads
`minute, hour = (...)`, which recompiles with the two STORE_DEREF swapped.
"""


def r68b2_cell_tuple_body(time_info):
    label = str(time_info[0])
    hour, minute = int(time_info[0]), int(time_info[1])

    def wrapper():
        return label, hour, minute

    return wrapper
