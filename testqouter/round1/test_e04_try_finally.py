def test():
    x = 0
    try:
        x = 1
    finally:
        x += 10
    return x
