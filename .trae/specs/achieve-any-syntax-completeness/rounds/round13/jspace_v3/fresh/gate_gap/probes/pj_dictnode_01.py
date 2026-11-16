"""Module-level statement carrier for the dict-AST entry.

Covers node_type arms: Module / Assign / AnnAssign / AugAssign / Expr /
Pass / Delete / Global / Import / ImportFrom / Assert / FunctionDef /
AsyncFunctionDef / ClassDef / AsyncFor / Nonlocal.
"""
import os
import sys as _sys
from collections import OrderedDict

GLOBAL_SLOT = 0


def pj_entry():
    """Zero-arg entry: statement soup in a function body."""
    global GLOBAL_SLOT
    GLOBAL_SLOT = 1
    total = 0
    total += 1
    note: int = total
    del note
    if False:
        pass
    assert total == 1
    return OrderedDict([("a", 1), ("b", {"nested": [1, 2]})])


async def pj_entry_async(seq=()):
    """Zero-arg entry with an async-for over a dict/set literal."""
    async for item in seq:
        if item:
            return {"seen": item}
    return {}


def pj_entry_local():
    """Zero-arg entry with a nonlocal rebind."""
    slot = 0

    def inner():
        nonlocal slot
        slot = 1
        return slot

    return inner()


class PJHolder:
    """Zero-arg class whose body carries a dict literal statement."""

    TABLE = {"k": 1, "j": {2, 3}}
    PAIR = (1, 2)

    def method(self):
        return self.TABLE


def main():
    return pj_entry(), pj_entry_local(), PJHolder(), os.getcwd(), _sys.version_info


if __name__ == "__main__":
    main()
