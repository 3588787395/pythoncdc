# r2_01 try/except 基础 + 多 handler 链
# 焦点：裸 except、元组类型、as 绑定、handler 内 return/break/continue


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
            continue
    else:
        total += 100
    return total


def g(d, k):
    try:
        return d[k]
    except KeyError as e:
        return None
    except (TypeError, IndexError):
        return -1
    except:
        return "bare"
