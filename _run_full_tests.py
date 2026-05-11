import subprocess
import sys
import os

os.chdir(r"d:\Desktop\ptrade相关\pythoncdc")
sys.path.insert(0, '.')

result_te = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/exhaustive/try_except/', '-v', '--tb=no', '-q'],
    capture_output=True, text=True, timeout=300
)
print("=== TRY_EXCEPT TESTS ===")
print(result_te.stdout[-2000:] if len(result_te.stdout) > 2000 else result_te.stdout)
print(result_te.stderr[-1000:] if result_te.stderr else "")

result_w = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/exhaustive/with_region/', '-v', '--tb=no', '-q'],
    capture_output=True, text=True, timeout=300
)
print("\n=== WITH_REGION TESTS ===")
print(result_w.stdout[-2000:] if len(result_w.stdout) > 2000 else result_w.stdout)
print(result_w.stderr[-1000:] if result_w.stderr else "")
