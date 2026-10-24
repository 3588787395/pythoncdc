def run(flag):
    v: int | None = 7 if flag else None
    return v
def main():
    return run(True), run(False)
