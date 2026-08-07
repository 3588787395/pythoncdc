# Source Generated with Decompyle++ (Python version)
# File: repro_21_try_except_format.pyc (Python 3.11)

def func(self, record):
    try:
        msg = record.getMessage()
    except Exception:
        msg = repr(record)
    else:
        return msg
