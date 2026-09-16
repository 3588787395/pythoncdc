import dis

def test_guard():
    if not tmp_dividends or symbol not in tmp_dividends or len(tmp_dividends[symbol]) == 0:
        early_return()
    else:
        main_body()

print("=== not A or B not in C or D == 0 ===")
dis.dis(test_guard)
