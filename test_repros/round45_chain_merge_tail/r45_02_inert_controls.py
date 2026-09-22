"""Round 45 line E G0 extension: shapes where the LANDED core is already correct and
R45-A must not change a single byte (over-firing controls)."""


def w_chain_in_loop(items, log):
    """chain inside a loop body, post-chain statement still inside the loop"""
    for it in items:
        if it < 0:
            log.info('neg')
            continue
        elif it > 100:
            log.info('big')
        log.warn('after chain %d' % it)
    return items


def w_plain_if_tail(flag, v):
    """single-armed if whose merge is a real statement (no elif anywhere)"""
    if flag:
        v = v + 1
    v = v * 2
    return v


def w_chain_merge_implicit(items):
    """chain arms fall off the end -> merge is the implicit return None"""
    if not items:
        return 0
    elif len(items) == 1:
        return 1


def w_elif_else_tail(flag, other):
    """if/elif/else chain followed by a real post-chain statement"""
    if flag:
        r = 1
    elif other:
        r = 2
    else:
        r = 3
    return r * 10


def w_nested_chain_in_arm(flag, other, v):
    """outer if whose arm contains an inner chain with its own tail"""
    if flag:
        if other:
            v = 1
        elif v:
            v = 2
        v = v + 3
    return v


def w_chain_tail_jump(a, b):
    """chain whose post-chain tail is reached from arms that do not return"""
    if a:
        b = b + 1
    elif b > 3:
        b = b - 1
    for i in (1, 2):
        b += i
    return b


def w_all_return_no_tail(a, b):
    """every arm returns; nothing follows the chain (target of drop must stay absent)"""
    if a:
        return 1
    elif b:
        return 2
    return 3
