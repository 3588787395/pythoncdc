import re

def parse_batch(filepath):
    results = {}
    current_path = None
    with open(filepath, 'r', encoding='utf-16', errors='replace') as f:
        for line in f:
            line = line.strip()
            m = re.match(r'\[(\d+)/\d+\]\s+(.+\.pyc)', line)
            if m:
                current_path = m.group(2).split('/')[-1].replace('.pyc', '')
                continue
            if current_path and 'matched' in line:
                m2 = re.search(r'(\w+):\s+(\d+)\s+funcs,\s+(\d+)\s+matched.*rate=([\d.]+)%', line)
                if m2:
                    results[current_path] = {
                        'status': m2.group(1),
                        'total': int(m2.group(2)),
                        'matched': int(m2.group(3)),
                        'rate': float(m2.group(4))
                    }
                current_path = None
    return results

r38 = parse_batch('_r38_batch_out.txt')
r39 = parse_batch('_r39_batch_out.txt')

print(f"R38 parsed: {len(r38)} files")
print(f"R39 parsed: {len(r39)} files")

print("\n=== Files with CHANGED results (R38 -> R39) ===")
changed = 0
improved = 0
regressed = 0
for name in sorted(set(r38.keys()) | set(r39.keys())):
    r38_val = r38.get(name)
    r39_val = r39.get(name)
    if r38_val != r39_val:
        changed += 1
        r38_m = r38_val['matched'] if r38_val else 0
        r39_m = r39_val['matched'] if r39_val else 0
        delta = r39_m - r38_m
        if delta > 0:
            improved += 1
        elif delta < 0:
            regressed += 1
        print(f"  {name}: {r38_m}->{r39_m} matched ({'+' if delta >= 0 else ''}{delta})")
if changed == 0:
    print("  No changes detected")

print(f"\nTotal changed: {changed} (improved: {improved}, regressed: {regressed})")

# Summary
r38_total_matched = sum(v['matched'] for v in r38.values())
r39_total_matched = sum(v['matched'] for v in r39.values())
r38_total_funcs = sum(v['total'] for v in r38.values())
r39_total_funcs = sum(v['total'] for v in r39.values())
print(f"\nR38: {r38_total_matched}/{r38_total_funcs} = {r38_total_matched/r38_total_funcs*100:.2f}%")
print(f"R39: {r39_total_matched}/{r39_total_funcs} = {r39_total_matched/r39_total_funcs*100:.2f}%")
