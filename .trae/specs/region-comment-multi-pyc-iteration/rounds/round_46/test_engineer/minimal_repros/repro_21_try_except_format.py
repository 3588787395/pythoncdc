def func(self, record):
    try:
        msg = record.getMessage()
    except Exception:
        msg = repr(record)
    return msg
