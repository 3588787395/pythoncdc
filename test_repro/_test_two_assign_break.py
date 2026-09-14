def test_two_assign_break(data, key):
    found = False
    value = None
    for item in data:
        if item == key:
            found = True
            value = item
            break
    else:
        found = False
    return found
