import dis
src = open('.trae/specs/attack-completeness-claims/rounds/round4/_probes/cp_assert_message.py', encoding='utf-8').read()
c = compile(src, 'x', 'exec')
f = [k for k in c.co_consts if hasattr(k, 'co_code')][0]
print('--- f bytecode (assert 1, "boom") ---')
for i in dis.get_instructions(f):
    print(' ', i.opname, repr(i.argval))
print('co_consts =', f.co_consts)

src2 = src.replace('assert 1,', 'assert 0,')
c2 = compile(src2, 'x', 'exec')
f2 = [k for k in c2.co_consts if hasattr(k, 'co_code')][0]
print('--- f bytecode (assert 0, "boom") ---')
for i in dis.get_instructions(f2):
    print(' ', i.opname, repr(i.argval))
print('co_consts =', f2.co_consts)
