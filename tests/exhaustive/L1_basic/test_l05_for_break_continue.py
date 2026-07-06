def test_l05_for_break_continue():
    for i in range(100):
        if should_stop(i):
            break
        if should_skip(i):
            continue
        work(i)
