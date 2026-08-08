# Source Generated with Decompyle++ (Python version)
# File: repro_06.pyc (Python 3.11)

def repro_06():
    try:
        try:
            x = 1
        except:
            pass
        for i in range(10):
            continue
        else:
            return x
        return None
    except Exception as e:
        return None
