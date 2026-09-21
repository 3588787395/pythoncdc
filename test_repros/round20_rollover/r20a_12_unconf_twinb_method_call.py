from logs import system_log
from traces import get_traceback_message


def perform_rollover_b(fmt, files, count, rename, do_open):
    system_log.error(get_traceback_message())
    x = 0
    for i in xrange(files):
        src = fmt % i
        dst = fmt % (i + 1)
        try:
            rename(src, dst)
        except OSError:
            system_log.error(get_traceback_message())
    rename(fmt % 0, fmt + '.1')
    do_open('w')


def tail_loop_b(files, count, g):
    g()
    for x in xrange(count, 0, -1):
        if x in files:
            break
    else:
        g()
        return
    for i in xrange(files):
        g(i)
