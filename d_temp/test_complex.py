import dis

def test_complex():
    if not (tmp_dividends and symbol not in tmp_dividends):
        early_return()
    else:
        main_body()

print("=== not (tmp_dividends and symbol not in tmp_dividends) ===")
dis.dis(test_complex)

# What about: if tmp_dividends and symbol in tmp_dividends:?
def test_simple():
    if tmp_dividends and symbol in tmp_dividends:
        main_body()
    else:
        early_return()

print("\n=== tmp_dividends and symbol in tmp_dividends ===")
dis.dis(test_simple)
