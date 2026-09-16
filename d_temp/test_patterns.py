import dis

def test_a():
    if tmp_dividends and symbol not in tmp_dividends and len(tmp_dividends[symbol]) == 0:
        pass

def test_b():
    if not (tmp_dividends and symbol not in tmp_dividends and len(tmp_dividends[symbol]) == 0):
        pass

def test_c():
    if not tmp_dividends or symbol in tmp_dividends or len(tmp_dividends[symbol]) != 0:
        pass

print("=== A and B not in C and D == 0 ===")
dis.dis(test_a)
print()
print("=== not (A and B not in C and D == 0) ===")
dis.dis(test_b)
print()
print("=== not A or B in C or D != 0 ===")
dis.dis(test_c)
