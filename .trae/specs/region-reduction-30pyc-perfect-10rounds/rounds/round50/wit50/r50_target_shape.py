def shape_exit_then_ternary_stmt(a, b):
    if a is None:
        return 0
    if not b:
        log('v={v} w={w}'.format(v='p' if a > 1 else 'q', w='r' if b else 's'))
    return a


def shape_exit_then_two_ternary_kw(a, b):
    if a is None:
        return 0
    if b > 2:
        log('x={x} y={y} z={z}'.format(x='u' if a else 'v', y='w' if b else 't',
                                       z=str(a) if b else str(1)))
    return a


def shape_exit_then_ternary_pos(a, b):
    if a is None:
        return 0
    log.info('{}'.format('yes' if a and b else 'no'))
    return a
