# Source Generated with Decompyle++ (Python version)
# File: repro_01_try_for_else_break_return.pyc (Python 3.11)

__doc__ = '复现01: try-except内嵌for-else，break后return False被错误放置'
def validate_data(data):
    if not data:
        return False
    else:
        try:
            for item in data:
                if isinstance(item, int):
                    if item < 0:
                        continue
                else:
                    break
                if item < 0:
                    continue
                elif item > 100:
                    break
            else:
                return True
        except Exception as e:
            return False
            return False
        return False
