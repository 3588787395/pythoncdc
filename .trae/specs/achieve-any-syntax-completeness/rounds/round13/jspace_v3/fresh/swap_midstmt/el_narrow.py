# Narrow the trigger: attribute-target vs lambda-value in elif branch mid-statement.
import sys, py_compile, subprocess, os
os.chdir(r'D:\temp\opencode')

def mk(name, mid1, mid2):
    return f'''\
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
        {mid1}
        {mid2}
        return h(wrapper, user_function)
    elif maxsize is not None:
        raise TypeError('bad')
    return (maxsize, typed)
'''

cases = {
 # attr target + lambda value (original trigger)
 'w1_attr_lambda':  ('wrapper = g(user_function)', "wrapper.cache_parameters = lambda : {'m': maxsize}"),
 # attr target + plain value
 'w2_attr_plain':   ('wrapper = g(user_function)', "wrapper.cache_parameters = ('m', maxsize)"),
 # local target + lambda value
 'w3_local_lambda': ('wrapper = g(user_function)', "info = lambda : {'m': maxsize}"),
 # local target + lambda value, no call assign before
 'w4_only_lambda':  ("info = lambda : {'m': maxsize}", 'info2 = 1'),
 # attr target + dict value (no lambda)
 'w5_attr_dict':    ('wrapper = g(user_function)', "wrapper.cache_parameters = {'m': maxsize}"),
 # attr target + call value
 'w6_attr_call':    ('wrapper = g(user_function)', 'wrapper.cache_parameters = g(maxsize)'),
 # lambda direct to attr, different attr name
 'w7_attr_lambda2': ('wrapper = g(user_function)', 'wrapper.p = lambda : maxsize'),
 # mid stmt pair: local lambda then attr lambda
 'w8_local_then_attr_lambda': ('info = lambda : maxsize', 'wrapper.q = lambda : typed'),
}

for name, (m1, m2) in cases.items():
    src = mk(name, m1, m2)
    open(f'{name}.py', 'w', encoding='utf-8').write(src)
    py_compile.compile(f'{name}.py', cfile=f'{name}.pyc', doraise=True)
    r = subprocess.run([sys.executable, '-X', 'utf8', r'F:\Downloads\pythoncdc-main\pycdc.py',
                        f'{name}.pyc', '-o', f'{name}_out.py'], capture_output=True, text=True)
    out = open(f'{name}_out.py', encoding='utf-8').read()
    key1 = m1.split('(')[0].strip()
    key2 = m2.split(' lambda')[0].split(' =')[0].strip()
    has1 = key1 in out
    has2 = key2 in out
    print(f'--- {name}: rc={r.returncode} mid1({key1})={"OK" if has1 else "LOST"} mid2({key2})={"OK" if has2 else "LOST"}')
