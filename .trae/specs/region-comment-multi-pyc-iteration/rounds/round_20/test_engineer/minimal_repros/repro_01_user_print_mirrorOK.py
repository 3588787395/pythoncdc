# Source Generated with Decompyle++ (Python version)
# File: repro_01_user_print_mirror.pyc (Python 3.11)

def user_print(*args, sep=' ', end='', file=None, flush=None):
    message = sep.join(map(str, args)) + end
    print(message)
def main():
    user_print('a', 'b', sep='-', end='!')
