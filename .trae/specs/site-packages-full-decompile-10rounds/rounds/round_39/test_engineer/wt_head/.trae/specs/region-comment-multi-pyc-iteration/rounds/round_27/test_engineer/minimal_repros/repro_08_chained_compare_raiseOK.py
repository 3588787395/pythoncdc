# Source Generated with Decompyle++ (Python version)
# File: repro_08_chained_compare_raise.cpython-311.pyc (Python 3.11)

__doc__ = """R27 repro_08: if-raise-elif-raise pattern (order_target_percent exact pattern)
   def f(percent):
       percent = float(percent)
       if not 0 <= percent <= 1:
           raise ValueError("percent should between 0 and 1")
       return percent
"""
def f(percent):
    percent = float(percent)
    if not 0 <= percent <= 1:
        raise ValueError('percent should between 0 and 1')
    return percent
