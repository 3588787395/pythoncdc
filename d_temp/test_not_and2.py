import dis

def test_not_and_v2():
    if not (a and b not in c):
        then_body()
    else:
        else_body()

print("=== if not (a and b not in c): then_body() else: else_body() ===")
dis.dis(test_not_and_v2)
