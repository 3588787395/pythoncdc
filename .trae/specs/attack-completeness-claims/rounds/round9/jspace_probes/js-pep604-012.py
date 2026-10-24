def wrapper():
    def inner() -> int | None:
        return None
    return inner
def main():
    return wrapper()()
