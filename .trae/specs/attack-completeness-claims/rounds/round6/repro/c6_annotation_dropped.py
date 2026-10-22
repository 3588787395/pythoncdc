def f(x: int, y: str = 'a') -> str:
    return str(x) + y


def main():
    print(f(1))
    print(f.__annotations__)
