import json

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# List partial files sorted by match rate (highest first, near 100%)
partials = []
for entry in data:
    if entry.get('decompile_status') == 'partial':
        rate = entry.get('bytecode_match_rate', 0.0)
        path = entry.get('path', '')
        partials.append((rate, path))

partials.sort(reverse=True)

print("=== Partial files NEAREST to 100% (top 15) ===")
for rate, path in partials[:15]:
    basename = path.split('/')[-1]
    print(f"  {basename}: {rate*100:.2f}% - {path}")
