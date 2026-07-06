# Test conditional expressions
def test_conditions(x):
    if x > 0:
        if x < 10:
            return "small"
        else:
            return "large"
    return "non-positive"