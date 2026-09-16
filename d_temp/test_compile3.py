import dis

def test6():
    if not (tmp_dividends and symbol not in tmp_dividends):
        pass

def test7():
    if not tmp_dividends or symbol in tmp_dividends:
        pass

print("=== test6: if not (tmp_dividends and symbol not in tmp_dividends) ===")
dis.dis(test6)
print()
print("=== test7: if not tmp_dividends or symbol in tmp_dividends ===")
dis.dis(test7)
