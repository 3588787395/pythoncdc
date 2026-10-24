def inner() -> int | None:
    return None
def run():
    def outer() -> int | None:
        return 9
    return outer(), inner()
def main():
    return run()
