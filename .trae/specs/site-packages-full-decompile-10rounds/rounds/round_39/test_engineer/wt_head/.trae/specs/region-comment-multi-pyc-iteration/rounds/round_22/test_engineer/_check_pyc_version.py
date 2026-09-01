"""R23: check pyc file Python versions"""
import json, struct

with open(r'f:/Downloads/pythoncdc-main/pyc_index.json', 'r') as f:
    index = json.load(f)

magic_map = {
    3413: '3.8', 3423: '3.8', 3424: '3.8', 3425: '3.8', 3430: '3.8',
    3495: '3.9', 3496: '3.9', 3497: '3.9',
    3512: '3.9', 3513: '3.9',
    3531: '3.10', 3532: '3.10', 3533: '3.10', 3536: '3.10', 3537: '3.10', 3538: '3.10', 3539: '3.10', 3540: '3.10',
    3551: '3.11', 3552: '3.11', 3553: '3.11', 3556: '3.11', 3557: '3.11', 3558: '3.11', 3559: '3.11', 3560: '3.11', 3561: '3.11', 3562: '3.11',
    3570: '3.12', 3571: '3.12', 3572: '3.12', 3573: '3.12', 3575: '3.12', 3576: '3.12', 3577: '3.12', 3578: '3.12', 3579: '3.12',
    3613: '3.13', 3614: '3.13', 3615: '3.13',
}

version_counts = {}
for entry in index:
    try:
        with open(entry['path'], 'rb') as f:
            magic = f.read(4)
            magic_int = struct.unpack('<H', magic[:2])[0]
            ver = magic_map.get(magic_int, f'unknown({magic_int})')
            version_counts[ver] = version_counts.get(ver, 0) + 1
    except:
        pass

print(f'Python version distribution:')
for ver, count in sorted(version_counts.items()):
    print(f'  {ver}: {count} files')
