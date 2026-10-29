import dis, types, sys
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
code = compile(open(r'D:\temp\opencode\tern_repro.py', encoding='utf-8').read(), 'tern_repro', 'exec')
print('=== module bytecode ===')
dis.dis(code)
