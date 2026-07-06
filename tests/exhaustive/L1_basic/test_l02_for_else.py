def test_l02_for_else():
    for i in items:
        if found(i):
            break
    else:
        not_found_handler()
