"""R20 diag: verify Python 3.11 varnames layout for *args + kwonly."""
import dis


def f1(*args, sep=' ', end='', file=None, flush=None):
    message = sep.join(map(str, args)) + end
    return message


print('=== f1 co_varnames ===')
print('co_argcount:', f1.__code__.co_argcount)
print('co_kwonlyargcount:', f1.__code__.co_kwonlyargcount)
print('co_flags:', hex(f1.__code__.co_flags))
print('co_varnames:', f1.__code__.co_varnames)
print('has CO_VARARGS:', bool(f1.__code__.co_flags & 0x04))
print()
dis.dis(f1)
