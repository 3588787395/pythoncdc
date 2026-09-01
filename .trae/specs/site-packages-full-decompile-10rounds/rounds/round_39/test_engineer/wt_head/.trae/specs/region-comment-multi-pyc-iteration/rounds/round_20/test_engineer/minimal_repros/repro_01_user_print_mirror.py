# R20 repro_01: user_print 精确镜像（logger/__init__.pyc::user_print）
# kwonly args + *vararg，kwonly 位于 varnames 前部，vararg 位于其后。
def user_print(*args, sep=' ', end='', file=None, flush=None):
    message = sep.join(map(str, args)) + end
    print(message)


def main():
    user_print('a', 'b', sep='-', end='!')
