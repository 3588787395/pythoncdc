"""Nested code objects whose bodies hold if/elif chains.

Targets ASTGeneratorV2._generate_if_ast (opcode wordings PRINT_ITEM /
PRINT_NEWLINE / PRINT_EXPR / GET_ATTR / BINARY_* and BINARY_OR/BINARY_AND
membership tests).  Nested code objects are the only documented bridge from
the region pipeline into generate_ast_v2.
"""


def pj_entry(n):
    """Zero-arg-callable entry: nested def with a two-arm if/elif chain."""

    def inner(v):
        if v > 1:
            return v * 2
        elif v == 1:
            return v + 1
        return 0

    return inner(n)


def pj_entry_deep(n):
    """Zero-arg-callable entry: if/elif chain over mixed binary operators."""

    def inner(v):
        if v % 2 == 0:
            return v // 2
        elif v / 2 > 1:
            return v / 2
        elif v - 1:
            return v - 1
        return v

    return inner(n)


def pj_entry_comp(ns=(1, 2, 3)):
    """Zero-arg entry: comprehension code objects with if filters."""
    a = [x for x in ns if x > 1]
    b = [y * 2 for y in ns if y % 2 and y or y + 1]
    return a, b


def pj_entry_lambda():
    """Zero-arg entry: lambda code objects holding conditional expressions."""
    f = lambda x: (x + 1) if x > 0 else (x - 1)
    g = lambda y: y and y or 0
    return f(1), g(2)


def main():
    return pj_entry(2), pj_entry_deep(4), pj_entry_comp(), pj_entry_lambda()


if __name__ == "__main__":
    main()
