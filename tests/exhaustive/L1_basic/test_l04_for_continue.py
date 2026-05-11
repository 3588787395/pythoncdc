def test_l04_for_continue():
    for i in range(100):
        if skip(i):
            continue
        process(i)
