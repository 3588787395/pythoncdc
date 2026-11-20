# fix_jspace_source.py — 修 J 记录里 12 条「散文当路径」的 source 字段（JS-PEP604-*），
# 源码其实就在 pyc 旁边的同名 .py。只改 source（旧值存入 source_note），其余字段逐字不变。
import io
import json
import os
import shutil
import sys

SPACE = r'.trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json'
BACKUP_DIR = r'.trae/specs/achieve-any-syntax-completeness/rounds/round13/row_fix'


def load(path):
    with io.open(path, encoding='utf-8') as fh:
        return json.load(fh)


def dump(path, data):
    with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write('\n')


def main():
    revert = '--revert' in sys.argv
    raw = io.open(SPACE, encoding='utf-8').read()
    data = json.loads(raw)
    entries = data['entries']
    changed = 0
    for x in entries:
        if revert:
            note = x.pop('source_note', None)
            if note is not None:
                x['source'] = note
                changed += 1
            continue
        src = x.get('source') or ''
        if os.path.exists(src.split(':')[0]):
            continue
        pyc = x.get('pyc') or ''
        cand = os.path.splitext(pyc)[0] + '.py'
        if pyc and os.path.exists(cand):
            x['source_note'] = src
            x['source'] = cand.replace('\\', '/')
            changed += 1
    missing = [x['id'] for x in entries
               if not x.get('excluded') and not os.path.exists((x.get('source') or '').split(':')[0])]
    excluded_missing = [x['id'] for x in entries
                        if x.get('excluded') and not os.path.exists((x.get('source') or '').split(':')[0])]
    data['jspace_row'] = {
        'total': len(entries),
        'source_missing_non_excluded': len(missing),
        'source_missing_excluded': len(excluded_missing),
        'pyc_missing': sum(1 for x in entries if not x.get('pyc') or not os.path.exists(x['pyc'])),
        'calls_missing_non_excluded': sum(
            1 for x in entries
            if not x.get('excluded') and not ((x.get('input_model') or {}).get('calls') or [])),
    }
    if not revert:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        shutil.copyfile(SPACE, os.path.join(BACKUP_DIR, 'judgment_space.before.json'))
    else:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        shutil.copyfile(SPACE, os.path.join(BACKUP_DIR, 'judgment_space.reverted.json'))
    dump(SPACE, data)
    print('changed=%d %s' % (changed, 'revert' if revert else 'apply'))
    print(json.dumps(data['jspace_row'], ensure_ascii=False))


if __name__ == '__main__':
    main()
