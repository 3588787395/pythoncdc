"""R49 Repro 06: try-except-else with return in else"""
def func():
    try:
        x = 1 + 2
    except Exception:
        x = 0
    else:
        return x
