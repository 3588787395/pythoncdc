def test_assign_before_break(data, key):
    found = False
    for item in data:
        if item == key:
            found = True
            break
    else:
        found = False
    return found
