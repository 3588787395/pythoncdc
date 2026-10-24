def get(flag) -> int | None:
    return 5 if flag else None
def main():
    return get(True), get(False)
