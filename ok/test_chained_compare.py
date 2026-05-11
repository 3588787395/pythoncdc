# Test chained comparisons
def test_chains(x, y, z):
    if x < y < z:
        return "ascending"
    if x > y > z:
        return "descending"
    return "other"