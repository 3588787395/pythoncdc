"""Find partial pyc files closest to 100% that might be easy to fix."""
import json

data = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
partials = [d for d in data if d.get('decompile_status') == 'partial']
# Sort by match rate descending, then by function count ascending (fewer functions = easier)
partials.sort(key=lambda x: (-x.get('bytecode_match_rate', 0), x.get('function_count', 0)))

print(f"Partial files: {len(partials)}")
print(f"\nTop 20 closest to 100%:")
for d in partials[:20]:
    rate = d.get('bytecode_match_rate', 0)
    fc = d.get('function_count', 0)
    matched = int(fc * rate)
    missing = fc - matched
    p = d.get('path', '').split('site-packages\\')[-1]
    print(f"  {rate:.2%} ({matched}/{fc}, {missing} missing) - {p}")

# Also check which ones have only 1 missing function
print(f"\nFiles with only 1 missing function:")
for d in partials:
    rate = d.get('bytecode_match_rate', 0)
    fc = d.get('function_count', 0)
    matched = int(fc * rate)
    missing = fc - matched
    if missing == 1:
        p = d.get('path', '').split('site-packages\\')[-1]
        print(f"  {rate:.2%} ({matched}/{fc}, {missing} missing) - {p}")
