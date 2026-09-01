"""Repro 09-04: D3 variant — chained compare with double COMPARE_OP + SWAP+COPY.

CPython 3.11 lowers `a <= x <= b` into a SWAP+COPY shape that shares
the middle operand `x` between two COMPARE_OP instructions. This repro
exercises the SWAP+COPY+COMPARE_OP+POP_JUMP_FORWARD_IF_FALSE pattern
explicitly with a non-trivial middle operand (subscript + slice).

The defect fires when _identify_conditional_regions does not recognize
the IfRegion because the preceding except-handler framework
(PUSH_EXC_INFO / CHECK_EXC_MATCH) confuses the region detector.

Expected defect: `if <trailing operand>:` (chained compare collapsed).
"""


def handler(data):
    try:
        process(data)
    except HTTPError as e:
        log_error(get_traceback_message())
        if 100 <= data['code'] <= 200:
            handle_range(e)
        else:
            handle_other(e)
