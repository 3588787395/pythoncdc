import dis

def test_not_and3():
    if not (tmp_dividends and symbol not in tmp_dividends and len(tmp_dividends[symbol]) == 0):
        return early()
    else:
        return main()

dis.dis(test_not_and3)
