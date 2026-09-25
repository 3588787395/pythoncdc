# -*- coding: utf-8 -*-
"""R68-b2 synth witness (scheduler::run_daily shape, if-condition prefix path).

CPython 3.11 emits `SWAP N + N x STORE_DEREF` for a tuple assignment whose targets
are closure cell variables, and stores them in SOURCE order.  When the block ends
in an `if` condition, the statement prefix is rebuilt by
`_build_statements_from_instructions` (via `_if_extract_cond_instructions`); there
each STORE_* flushes the accumulated value expression, so the first STORE consumes
both RHS values and the second STORE finds an empty pending list and is dropped
-> the second target, its MAKE_CELL and its LOAD_CLOSURE all disappear from the
recompiled product.  The `label` store in front keeps the whole-block detectors
(SWAP-unpack at L45664 / SIG2 in the body loop) from taking a different path.
"""


def r68b2_cell_tuple(time_info, flag):
    label = str(time_info[0])
    hour, minute = int(time_info[0]), int(time_info[1])

    def wrapper():
        return label, hour, minute

    if flag:
        return wrapper
    return None
