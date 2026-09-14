def test_nested_if_break(data, key1, key2):
    found = False
    for item in data:
        if item == key1:
            if key2 is not None:
                found = True
                break
    else:
        found = False
    return found
