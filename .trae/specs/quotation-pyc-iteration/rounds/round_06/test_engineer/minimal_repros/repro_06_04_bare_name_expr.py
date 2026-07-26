"""Repro 06-04: Bare Name Expr orphan (LOAD_FAST without STORE).

Defect: A LOAD_FAST that is not part of a Call/Assign/Return leaks as
an orphan expression statement `prod` (or `stocks`), which is a no-op.

Root cause: _build_effective_stmts / _generate_block_statements does not
suppress orphan LOAD_FAST Expr that isn't consumed by a following
CALL/STORE/RETURN.
"""


def process(data, prod_code):
    prod = data.get(prod_code)
    prod
    for item in prod:
        total = sum(item)
    return total
