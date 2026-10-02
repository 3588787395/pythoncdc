"""Round5 复核变体探针：B24（try 包 return 推导式）修复的变体攻击。"""


def t_except_return_comp(xs, log):
    """try/except（无 finally）包 return [comp]。"""
    try:
        return [x * 2 for x in xs]
    except TypeError:
        log.append(1)


def t_finally_dict(xs, log):
    """try/finally 包 return {dict comp}。"""
    try:
        return {x: x * 2 for x in xs}
    finally:
        log.append(len(xs))


def t_nested_try(xs, log):
    """嵌套 try 包 return comp。"""
    try:
        try:
            return [x for x in xs]
        finally:
            log.append(1)
    finally:
        log.append(2)


def t_finally_set(xs, log):
    """try/finally 包 return {set comp}。"""
    try:
        return {x for x in xs}
    finally:
        log.append(len(xs))
