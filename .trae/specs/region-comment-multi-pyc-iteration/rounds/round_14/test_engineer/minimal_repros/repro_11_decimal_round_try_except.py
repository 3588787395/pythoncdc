"""R14 CTRL 11: try/except with return (decimal_round).

CTRL (NO-DEFECT): mirrors tools.pyc decimal_round — a try/except where the
try body returns and the except body returns. Simple structure that the
decompiler already handles correctly (one of the 5/6 matching functions).
"""
from decimal import Decimal


def decimal_round(data, n):
    try:
        return float(str(round(Decimal(data), n)))
    except BaseException:
        return float(str(round(data, n)))
