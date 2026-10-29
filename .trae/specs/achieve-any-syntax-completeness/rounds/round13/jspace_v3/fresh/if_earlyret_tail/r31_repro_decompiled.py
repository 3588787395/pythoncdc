# Source Generated with Decompyle++ (Python version)
# File: r31_repro.pyc (Python 3.11)

def f(value):
    epoch = value or 0
    if isinstance(epoch, int) and epoch >= 0:
        return epoch
    msg = f'epoch must be non-negative integer, got {epoch}'
    raise ValueError(msg)
def g(a, b):
    return (a, b)
m = {'post_l': 'post', 'post_n1': None, 'post_n2': '3'}
print('A1', f(2))
try:
    f(-1)
except ValueError as e:
    print('A2 raised:', e)
post = g(m.get('post_l'), m.get('post_n1') or m.get('post_n2'))
print('B', post)
