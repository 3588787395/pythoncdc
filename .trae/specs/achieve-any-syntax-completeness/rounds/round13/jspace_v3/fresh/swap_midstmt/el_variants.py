# elif-branch body mid-statement loss repro (REAL46-003 functools.lru_cache shape)
# v1: full shape (and-condition elif + call-assign + attr-target lambda-assign + return)
# variants isolate the trigger.
import sys, py_compile, subprocess, os
os.chdir(r'D:\temp\opencode')

v1 = '''\
def g(*a):
    return None

def h(*a):
    return None

def f(maxsize, typed):
    if isinstance(maxsize, int):
        if maxsize < 0:
            maxsize = 0
    elif callable(maxsize) and isinstance(typed, bool):
        user_function, maxsize = maxsize, 128
        wrapper = g(user_function, maxsize, typed)
        wrapper.cache_parameters = lambda : {'maxsize': maxsize, 'typed': typed}
        return h(wrapper, user_function)
    elif maxsize is not None:
        raise TypeError('Expected first argument to be an integer, a callable, or None')
    return (maxsize, typed)
'''

# v2: single condition (no `and`)
v2 = '''\
def g(*a):
    return None

def h(*a):
    return None

def f(maxsize, typed):
    if isinstance(maxsize, int):
        if maxsize < 0:
            maxsize = 0
    elif callable(maxsize):
        user_function, maxsize = maxsize, 128
        wrapper = g(user_function, maxsize, typed)
        wrapper.cache_parameters = lambda : {'maxsize': maxsize, 'typed': typed}
        return h(wrapper, user_function)
    elif maxsize is not None:
        raise TypeError('bad')
    return (maxsize, typed)
'''

# v3: middle stmt plain local assign (no attribute target, no lambda)
v3 = '''\
def g(*a):
    return None

def h(*a):
    return None

def f(maxsize, typed):
    if isinstance(maxsize, int):
        if maxsize < 0:
            maxsize = 0
    elif callable(maxsize) and isinstance(typed, bool):
        user_function, maxsize = maxsize, 128
        wrapper = g(user_function, maxsize, typed)
        info = (maxsize, typed)
        return h(wrapper, user_function)
    elif maxsize is not None:
        raise TypeError('bad')
    return (maxsize, typed)
'''

# v4: no nested-if in first branch
v4 = '''\
def g(*a):
    return None

def h(*a):
    return None

def f(maxsize, typed):
    if isinstance(maxsize, int):
        maxsize = 0
    elif callable(maxsize) and isinstance(typed, bool):
        user_function, maxsize = maxsize, 128
        wrapper = g(user_function, maxsize, typed)
        wrapper.cache_parameters = lambda : {'maxsize': maxsize, 'typed': typed}
        return h(wrapper, user_function)
    elif maxsize is not None:
        raise TypeError('bad')
    return (maxsize, typed)
'''

# v5: no trailing elif raise
v5 = '''\
def g(*a):
    return None

def h(*a):
    return None

def f(maxsize, typed):
    if isinstance(maxsize, int):
        if maxsize < 0:
            maxsize = 0
    elif callable(maxsize) and isinstance(typed, bool):
        user_function, maxsize = maxsize, 128
        wrapper = g(user_function, maxsize, typed)
        wrapper.cache_parameters = lambda : {'maxsize': maxsize, 'typed': typed}
        return h(wrapper, user_function)
    return (maxsize, typed)
'''

# v6: no tuple-assign first stmt (branch starts with call-assign)
v6 = '''\
def g(*a):
    return None

def h(*a):
    return None

def f(maxsize, typed):
    if isinstance(maxsize, int):
        if maxsize < 0:
            maxsize = 0
    elif callable(maxsize) and isinstance(typed, bool):
        wrapper = g(maxsize, typed)
        wrapper.cache_parameters = lambda : {'maxsize': maxsize, 'typed': typed}
        return h(wrapper)
    elif maxsize is not None:
        raise TypeError('bad')
    return (maxsize, typed)
'''

CHECK = ('wrapper = g(', 'wrapper.cache_parameters = lambda', 'info = (',
         'return h(')

for name, src in [('el1_full', v1), ('el2_noand', v2), ('el3_plainmid', v3),
                  ('el4_nonested', v4), ('el5_notrailing', v5), ('el6_notuple', v6)]:
    open(f'{name}.py', 'w', encoding='utf-8').write(src)
    py_compile.compile(f'{name}.py', cfile=f'{name}.pyc', doraise=True)
    r = subprocess.run([sys.executable, '-X', 'utf8', r'F:\Downloads\pythoncdc-main\pycdc.py',
                        f'{name}.pyc', '-o', f'{name}_out.py'], capture_output=True, text=True)
    out = open(f'{name}_out.py', encoding='utf-8').read()
    # check mid statements present in the elif branch (search whole body region)
    missing = [c for c in CHECK if c.split(' =')[0] in src and c not in out]
    print(f'--- {name}: rc={r.returncode}')
    # print the def f body
    grab = False
    for l in out.split('\n'):
        if l.startswith('def f('):
            grab = True
        elif l.startswith('def ') and grab:
            break
        if grab:
            print('   |', l)
    print('   MISSING:', missing if missing else 'none')
