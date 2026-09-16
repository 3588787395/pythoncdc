import dis

def p8():
    if not tmp_dividends or symbol not in tmp_dividends or len(tmp_dividends[symbol]) == 0:
        early_return()
    else:
        main_body()

dis.dis(p8)
