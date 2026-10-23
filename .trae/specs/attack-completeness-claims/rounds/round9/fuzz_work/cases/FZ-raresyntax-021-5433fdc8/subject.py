def main(x: int | None = None, /, *, y: "int" = 2) -> int | None:
    return x if x is not None else y
