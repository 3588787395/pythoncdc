import dis

def test_three_cond():
    if not (tmp_dividends and symbol not in tmp_dividends and len(tmp_dividends[symbol]) == 0):
        early_return()
    else:
        main_body()

print("=== not (A and B not in C and D == 0) ===")
dis.dis(test_three_cond)
