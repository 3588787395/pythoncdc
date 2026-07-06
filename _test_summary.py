import sys
sys.path.insert(0, '.')
from tests.control_flow_matrix.run_tests import discover_test_classes, run_single_test

classes = discover_test_classes()
levels = {}
failed = []
for name, cls, level in classes:
    status, error, duration = run_single_test(cls)
    if level not in levels:
        levels[level] = {'p': 0, 'f': 0, 't': 0}
    levels[level]['t'] += 1
    if status == 'passed':
        levels[level]['p'] += 1
    else:
        levels[level]['f'] += 1
        failed.append((level, name, error[:80] if error else ''))

print(f'Total: {len(classes)}')
for k in sorted(levels.keys()):
    v = levels[k]
    print(f'{k}: {v["p"]}/{v["t"]} passed ({v["p"]*100//max(v["t"],1)}%), {v["f"]} failed')

print(f'\nPassed: {sum(v["p"] for v in levels.values())}')
print(f'Failed: {sum(v["f"] for v in levels.values())}')
print(f'\nFailed tests ({len(failed)}):')
for level, name, error in failed:
    print(f'  [{level}] {name}: {error}')