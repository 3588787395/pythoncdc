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
