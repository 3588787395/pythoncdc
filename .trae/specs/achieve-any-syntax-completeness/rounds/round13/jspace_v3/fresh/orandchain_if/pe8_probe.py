# rr-v5r111 诊断：确认 pe8 产品多出的 `pass` 是否由 [v111-ORAND] 出口调用引入。
# 受控实验：同一 pe8.pyc 分别用 当前v111 / 去掉两处fixup调用 / HEAD 三版反编译比文本。
# 全程 try/finally 恢复 GEN，末尾断言字节一致。
import os, sys, subprocess

REPO = 'F:/Downloads/pythoncdc-main'
EV = REPO + '/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/orandchain_if'
GEN = REPO + '/core/cfg/region_ast_generator.py'
PY = 'D:/Python/python.exe'
GIT = 'E:/Program Files/PortableGit/bin/git.exe'
PYC = EV + '/regress_v111/pe8.pyc'

cur = open(GEN, encoding='utf-8').read()
head = subprocess.run([GIT, '-C', REPO, 'show', 'HEAD:core/cfg/region_ast_generator.py'],
                      capture_output=True).stdout.decode('utf-8')
assert 'v111-ORAND' in cur and 'v111-ORAND' not in head

# 变体 1：两处出口调用改为 no-op（方法体保留，仅不调用）
nocall = cur.replace('result = self._v111_fixup_if_node(result)',
                     'result = result')
nocall = nocall.replace('if_result = self._v111_fixup_if_node(if_result)',
                        'if_result = if_result')
assert nocall != cur
print('[probe] no-call 变体替换数:',
      cur.count('self._v111_fixup_if_node(result)') +
      cur.count('self._v111_fixup_if_node(if_result)'))


def dec(tag, source):
    open(GEN, 'w', encoding='utf-8').write(source)
    out = EV + '/pe8_probe_%s.py' % tag
    with open(out, 'wb') as fo, open(out + '.err', 'wb') as fe:
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', PYC],
                       stdout=fo, stderr=fe, cwd=REPO, timeout=180)
    return open(out, 'rb').read()


try:
    a = dec('v111', cur)
    b = dec('nocall', nocall)
    c = dec('head', head)
    print('v111   == nocall :', a == b)
    print('nocall == HEAD   :', b == c)
    print('v111   == HEAD   :', a == c)
    la = a.decode('utf-8').splitlines()
    lc = c.decode('utf-8').splitlines()
    print('--- v111 独有行 ---')
    for x in la:
        if x not in lc:
            print('   +', repr(x))
    print('--- HEAD 独有行 ---')
    for x in lc:
        if x not in la:
            print('   -', repr(x))
finally:
    open(GEN, 'w', encoding='utf-8').write(cur)
    assert open(GEN, encoding='utf-8').read() == cur, 'GEN not restored!'
    print('[probe] GEN 已恢复 v111')
