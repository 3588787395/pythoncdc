import json

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

total = len(data)
ok_count = 0
partial_count = 0
failed_count = 0

for entry in data:
    status = entry.get('decompile_status', '')
    if status == 'ok':
        ok_count += 1
    elif status == 'partial':
        partial_count += 1
    elif status == 'failed':
        failed_count += 1

print(f"=== Current State (R39) ===")
print(f"Total: {total}")
print(f"OK: {ok_count}")
print(f"Partial: {partial_count}")
print(f"Failed: {failed_count}")

# List partial files sorted by match rate (lowest first)
print("\n=== Partial files with LOWEST match rates (top 20) ===")
partials = []
for entry in data:
    if entry.get('decompile_status') == 'partial':
        rate = entry.get('bytecode_match_rate', 0.0)
        path = entry.get('path', '').split('/')[-1]
        round_num = entry.get('last_tested_round', 0)
        partials.append((rate, path, round_num))

partials.sort()
for rate, path, rnd in partials[:20]:
    print(f"  {path}: {rate*100:.2f}% (round {rnd})")

# Count files near 100%
near_100 = [p for p in partials if p[0] >= 0.95]
print(f"\nFiles >= 95%: {len(near_100)}")
near_90 = [p for p in partials if p[0] >= 0.90]
print(f"Files >= 90%: {len(near_90)}")
near_80 = [p for p in partials if p[0] >= 0.80]
print(f"Files >= 80%: {len(near_80)}")
