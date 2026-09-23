"""Round 46 line D witnesses: a statement block that follows an if/else whose else arm is a
hard exit gets forward-absorbed into the then arm, so CPython's else-skipping JUMP_FORWARD
disappears (strict seq_len short by one). Plus the controls that must stay clean."""


def probe(n):
    return (n % 2, 'm%d' % n)


def w1_post_if_after_break(n, log):
    """target shape: then arm ends, else arm breaks; `n += 1` follows the whole inner if."""
    code, msg = probe(n)
    while code != 0:
        if n < 3:
            log.info('retry')
        else:
            msg = 'gave up'
            break
        n += 1
        code, msg = probe(n)
    return code, msg


def c1_arms_converge(n, log):
    """both arms fall through to the same post-if statement (normal merge)."""
    code, msg = probe(n)
    while code != 0:
        if n < 3:
            log.info('retry')
        else:
            msg = 'gave up'
        n += 1
        code, msg = probe(n)
    return code, msg


def c2_else_returns_then_falls(n, log):
    """else arm returns, then arm has no statement after the if."""
    code, msg = probe(n)
    while code != 0:
        if n < 3:
            log.info('retry')
        else:
            return (1, 'early')
        code, msg = probe(n)
    return code, msg


def c3_no_else(n, log):
    """single-armed if inside a loop, statement after it."""
    code, msg = probe(n)
    while code != 0:
        if n >= 3:
            log.info('many')
        n += 1
        code, msg = probe(n)
    return code, msg
