import io

src = r'F:\Downloads\pythoncdc-main\.trae\specs\attain-true-completeness\rounds\round4\final_verify_run_r4.py'
dst = r'F:\Downloads\pythoncdc-main\.trae\specs\attain-true-completeness\rounds\round5\final_verify_run_r5.py'
t = io.open(src, encoding='utf-8-sig').read()
t = t.replace('Round4 主代理终审全量终验编排（基线 = rr-v3r03 = 69132f55 冻结树）',
              'Round5 主代理终审全量终验编排（基线 = rr-v3r04 = 71fda309 冻结树）')
t = t.replace("'rounds', 'round4')", "'rounds', 'round5')")
t = t.replace("BASE_COMMIT = '69132f55'", "BASE_COMMIT = '71fda309'")
t = t.replace("BASE_COMMIT + '..HEAD', '--', 'core/'", "BASE_COMMIT, '--', 'core/'")
assert "'rounds', 'round5')" in t and "'71fda309'" in t and "BASE_COMMIT, '--', 'core/'" in t
io.open(dst, 'w', encoding='utf-8-sig', newline='\n').write(t)
print('OK chars=%d lines=%d' % (len(t), t.count('\n')))
