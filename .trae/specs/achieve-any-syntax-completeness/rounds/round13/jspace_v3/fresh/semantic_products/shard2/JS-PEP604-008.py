# Source Generated with Decompyle++ (Python version)
# File: js-pep604-008.pyc (Python 3.11)

def inner() -> int | None:
    return None
def run():
    def outer() -> int | None:
        return 9
    return (outer(), inner())
def main():
    return run()
