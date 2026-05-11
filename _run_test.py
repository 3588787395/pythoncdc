import subprocess
import sys

test_file = sys.argv[1]
result = subprocess.run(
    [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=long'],
    capture_output=True, text=True, cwd=r'd:\Desktop\ptrade相关\pythoncdc'
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print(f"Exit code: {result.returncode}")
