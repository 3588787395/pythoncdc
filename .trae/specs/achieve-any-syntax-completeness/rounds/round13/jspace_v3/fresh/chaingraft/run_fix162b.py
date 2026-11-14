# run_fix162b.py: 原样复用 fix162b.py 的 ANCHOR/GUARD 文本，仅修正其第 70 行
# 的标记计数断言（应用后应为 2 而非 1；该断言在写入前触发，故原脚本未落盘）。
import io
import py_compile

SRC = r'D:/temp/opencode/cl_layout/r162/fix162b.py'
code = io.open(SRC, encoding='utf-8').read()
head = code.split("assert s.count(ANCHOR)")[0]
ns = {}
exec(compile(head, SRC, 'exec'), ns)

PATH, ANCHOR, GUARD, s, orig = ns['PATH'], ns['ANCHOR'], ns['GUARD'], ns['s'], ns['orig']

assert s.count(ANCHOR) == 1, 'anchor %d' % s.count(ANCHOR)
assert s.count('v162-CHAINGRAFT') == 1, 'pre-marker %d' % s.count('v162-CHAINGRAFT')

s2 = s.replace(ANCHOR, GUARD + ANCHOR, 1)
assert s2 != orig
assert s2.count('v162-CHAINGRAFT') == 2, 'post-marker %d' % s2.count('v162-CHAINGRAFT')
assert s2.count(ANCHOR) == 1

io.open(PATH, 'w', encoding='utf-8-sig', newline='').write(s2)
py_compile.compile(PATH, doraise=True)
print('fix162b applied: markers=%d' % s2.count('v162-CHAINGRAFT'))
print('syntax OK')
