def pick(flag) -> int | None:
    return 3 if flag else None
_cur: int | None = pick(True)
def main():
    return _cur
