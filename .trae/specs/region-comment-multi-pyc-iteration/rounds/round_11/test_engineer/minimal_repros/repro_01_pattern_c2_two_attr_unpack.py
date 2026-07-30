"""[R11 repro_01] Pattern C2: 2-tuple unpack no-SWAP (attr loads).

Mirrors IQEngine/main.pyc `_adjust_start_date` line:
    origin_start_date, origin_end_date = config.strategy.start_date, config.strategy.end_date

In Python 3.11 function-body context, the peephole optimizer removes the
SWAP 2, leaving LOAD/LOAD/STORE/STORE in reversed store order.
Expected decompiled output MUST be the tuple-unpack assignment, not a
single assignment with the wrong attribute.
"""


def f(config):
    if config.strategy.run_type != 1:
        origin_start_date, origin_end_date = config.strategy.start_date, config.strategy.end_date
        return origin_start_date
