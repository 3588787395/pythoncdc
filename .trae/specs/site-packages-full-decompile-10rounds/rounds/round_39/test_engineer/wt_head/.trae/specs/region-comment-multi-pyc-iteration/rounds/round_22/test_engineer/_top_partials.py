"""R22: find partial files with highest potential for improvement"""
import sys, os, json
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

with open(r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_22/batch_results.json', 'r') as f:
    results = json.load(f)

partials = [(r['total'] - r['match'], r['total'], r['match'], os.path.basename(r['path']))
            for r in results['results'] if r.get('status') == 'partial']
partials.sort(reverse=True)

print(f'Top 20 partial files by unmatched functions:')
for unmatched, total, matched, name in partials[:20]:
    rate = matched / total * 100 if total else 0
    print(f'  {name}: {matched}/{total} ({rate:.1f}%) - {unmatched} unmatched')

total_unmatched = sum(u for u, _, _, _ in partials)
print(f'\nTotal unmatched functions in partial files: {total_unmatched}')
