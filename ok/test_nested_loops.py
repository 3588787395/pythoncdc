# Test nested loops
def test_loops(items):
    for item in items:
        for i, v in enumerate(item):
            if i == 0:
                print(v)
            else:
                print(f"other: {v}")