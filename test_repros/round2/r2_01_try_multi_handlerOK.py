# Source Generated with Decompyle++ (Python version)
# File: r2_01_try_multi_handler.pyc (Python 3.11)

def f(x, items):
    total = 0
    for i in items:
        try:
            total += i // x
        except (TypeError, ValueError) as e:
            total += 1
        except ZeroDivisionError:
            break
        except:
            pass
    else:
        total += 100
    return total
def g(d, k):
    try:
        return d[k]
        return None
    except KeyError as e:
        return None
    except (TypeError, IndexError):
        return -1
    except:
        return 'bare'
