import dis

def test1():
    if tmp_dividends and symbol not in tmp_dividends:
        pass

def test2():
    if tmp_dividends and not (symbol in tmp_dividends):
        pass

print("=== test1: if tmp_dividends and symbol not in tmp_dividends ===")
dis.dis(test1)
print()
print("=== test2: if tmp_dividends and not (symbol in tmp_dividends) ===")
dis.dis(test2)
