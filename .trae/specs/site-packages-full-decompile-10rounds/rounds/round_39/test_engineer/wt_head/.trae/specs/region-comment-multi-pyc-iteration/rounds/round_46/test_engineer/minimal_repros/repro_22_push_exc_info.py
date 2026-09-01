def func(exc):
    try:
        return str(exc)
    except Exception:
        return "error"
