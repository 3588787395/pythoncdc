# Source Generated with Decompyle++ (Python version)
# File: ann_repro.pyc (Python 3.11)

from __future__ import annotations
def wrapper(*args: object, **kwargs: object) -> object:
    return func(*args, **(kwargs))
def rep(self, **kwargs: Unpack[VersionReplace]) -> Self:
    return self
def plain(x: int, *rest: str, **opts: float) -> None:
    return None
print(wrapper.__annotations__)
print(rep.__annotations__)
print(plain.__annotations__)
