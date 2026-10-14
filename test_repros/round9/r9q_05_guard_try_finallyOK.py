# Source Generated with Decompyle++ (Python version)
# File: r9q_05_guard_try_finally.pyc (Python 3.11)

def fetch(stocks, n):
    if not stocks:
        return []
    data = []
    try:
        for s in stocks:
            data.append(s * n)
    finally:
        close(stocks)
    return data
