# Nested try-except
def test():
    try:
        try:
            risky_call()
        except ValueError:
            print("inner")
    except Exception:
        print("outer")
    return "done"
