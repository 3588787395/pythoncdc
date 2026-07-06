import subprocess
import sys

# Run while_loop suite, capture output
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/exhaustive/while_loop/', '-v', '--tb=short'],
    capture_output=True, text=True, cwd=r'd:\Desktop\ptrade相关\pythoncdc'
)
# Print only FAILED and PASSED lines plus summary
lines = result.stdout.split('\n')
for line in lines:
    if 'FAILED' in line or 'PASSED' in line or 'passed' in line or 'failed' in line or '===' in line:
        print(line)
