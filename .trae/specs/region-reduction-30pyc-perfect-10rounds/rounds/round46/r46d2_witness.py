"""Round 46 line D witnesses, v2 — the ANALYZER-layer shape.

v1 (r46d_witness.py) turned out to exercise a different layer: its region tree is
already clean (then arm = 1 block) and the extra statements come from the emitter.
The corpus target (`<module>.TradeAccount.init_connection`) shows
IfRegion(then=[B112, B160], merge=B176) where B160 is the post-if statement block,
i.e. the analyzer forward-absorbs it. That needs the post-if block to be a *separate*
block that is not the loop back edge — so the loop body must continue with another
statement/branch after it.
"""


def probe(n):
    return (n % 2, 'm%d' % n)


def w2_break_arm_and_tail_if(n, log):
    """else arm breaks out of the loop; post-if statements end with their own if."""
    code, msg = probe(n)
    while code != 0:
        if n < 3:
            log.info('retry')
        else:
            msg = 'gave up'
            break
        n += 1
        if n > 2:
            log.warn('after %d' % n)
    return code, msg


def w3_return_arm_and_tail_stmt(n, log):
    """else arm returns; then arm ends, post-if statement ends with a bare call."""
    while n < 5:
        if n < 3:
            log.info('retry')
        else:
            return (1, 'early')
        n += 1
        log.warn('after %d' % n)
    return n


def k1_both_arms_converge(n, log):
    """neither arm is a sink: both fall through to the same post-if tail (normal merge)."""
    while n < 5:
        if n < 3:
            log.info('retry')
        else:
            msg = 'gave up'
        n += 1
        if n > 2:
            log.warn('after %d' % n)
    return n


def k2_no_else_in_loop(n, log):
    """sink-free single-armed if: the post-if tail is the loop back edge itself."""
    while n < 5:
        if n >= 3:
            log.info('many')
        n += 1
    return n


def k3_plain_if_no_else(n, log):
    """single-armed if inside a loop with a real post-if statement."""
    while n < 5:
        if n >= 3:
            log.info('many')
        n += 1
        log.warn('tail %d' % n)
    return n


def k4_post_if_at_function_level(flag, v, log):
    """sink else arm outside any loop, post-if statement at function level."""
    if flag:
        v = v + 1
    else:
        log.info('no')
        return v
    v = v * 2
    return v


def k5_two_sink_arms_with_tail(n, log):
    """both arms of the outer if hard-exit, inner if after them is unreachable tail."""
    while n < 5:
        if n < 3:
            log.info('retry')
            n += 1
        else:
            return n
        if n > 2:
            log.warn('after %d' % n)
    return n
