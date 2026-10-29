# Repro: vararg/kwarg annotations dropped (PEP 563 + Unpack).
from __future__ import annotations

def wrapper(*args: object, **kwargs: object) -> object:
    return func(*args, **kwargs)

def rep(self, **kwargs: Unpack[VersionReplace]) -> Self:
    return self

def plain(x: int, *rest: str, **opts: float) -> None:
    pass

print(wrapper.__annotations__)
print(rep.__annotations__)
print(plain.__annotations__)
