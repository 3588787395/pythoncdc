# dbg162.py: 临时在门控处插桩，跑 cg5/cg7/cg8 取证，随后从 r162a 备份还原并重放补丁
import io
import os
import shutil
import subprocess

REPO = r'F:\Downloads\pythoncdc-main'
PY = r'D:/Python/python.exe'
D = r'D:\temp\opencode\cl_layout\r162'
PATH = os.path.join(REPO, 'core', 'cfg', 'region_analyzer.py')
BAK = os.path.join(D, 'region_analyzer_r162a.bak')

DBG_POINT = "                if _v162_es_is_cond:\n"
DBG = """                import sys as _v162_dbg_sys
                print('[V162DBG] cond=%s block=@%s then=%s else=%s esucc=@%s tsucc=@%s reach=%s'
                      % (_v162_es_is_cond,
                         getattr(block, 'start_offset', None),
                         sorted(getattr(b, 'start_offset', -1) for b in then_blocks),
                         sorted(getattr(b, 'start_offset', -1) for b in else_blocks),
                         getattr(else_succ, 'start_offset', None),
                         getattr(then_succ, 'start_offset', None),
                         [getattr(t, 'start_offset', None) for t in then_blocks
                          if else_succ in t.successors]),
                      file=_v162_dbg_sys.stderr)
"""

s = io.open(PATH, encoding='utf-8-sig').read()
assert s.count(DBG_POINT) == 1
io.open(PATH, 'w', encoding='utf-8-sig', newline='').write(s.replace(DBG_POINT, DBG + DBG_POINT, 1))
try:
    for name in ('cg5_elif_continue', 'cg7_with_guard_then_ifelse', 'cg8_with_guard_then_if'):
        out = os.path.join(D, 'new', 'dbg_' + name + '.py')
        if os.path.isfile(out):
            os.remove(out)
        r = subprocess.run([PY, '-I', '-X', 'utf8', os.path.join(REPO, 'pycdc.py'),
                            os.path.join(D, name + '.pyc'), '-o', out],
                           capture_output=True, cwd=REPO, timeout=300)
        print('=' * 60)
        print('CASE', name, 'rc=%s' % r.returncode)
        for L in r.stderr.decode('utf-8', 'replace').splitlines():
            if 'V162DBG' in L:
                print('  ' + L)
finally:
    shutil.copyfile(BAK, PATH)
    subprocess.run([PY, '-I', '-X', 'utf8', os.path.join(D, 'run_fix162b.py')], check=True)
print('restored+reapplied')
