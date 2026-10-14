def check(n):
    if n not in ('w', 'mo'):
        try:
            tmp = int(n)
        except BaseException:
            assert False, 'bad int'
        else:
            assert tmp > 0, 'bad pos'
