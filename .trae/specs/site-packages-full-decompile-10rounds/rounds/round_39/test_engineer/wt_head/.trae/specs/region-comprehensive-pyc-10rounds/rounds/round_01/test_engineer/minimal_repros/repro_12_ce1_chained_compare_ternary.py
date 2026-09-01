# Chained comparison + ternary
def test():
    x = 50
    result = "positive" if x > 0 else "non-positive"
    if 0 < x < 100:
        result = "in range"
    return result
