import dis

def test3():
    if tmp_dividends:
        if symbol not in tmp_dividends:
            pass

def test4():
    if not (tmp_dividends and symbol in tmp_dividends):
        pass

def test5():
    if not tmp_dividends or symbol in tmp_dividends:
        pass

print("=== test3: if tmp_dividends: if symbol not in tmp_dividends ===")
dis.dis(test3)
print()
print("=== test4: if not (tmp_dividends and symbol in tmp_dividends) ===")
dis.dis(test4)
print()
print("=== test5: if not tmp_dividends or symbol in tmp_dividends ===")
dis.dis(test5)
