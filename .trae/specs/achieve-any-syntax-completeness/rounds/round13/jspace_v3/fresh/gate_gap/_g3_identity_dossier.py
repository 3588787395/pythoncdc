# Byte-level dossier for the two identity/no-op mutants (JS-BREAK-001 / JS-WHILE-040).
import ast
import hashlib
import json
import os
import sys

REPO = 'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO + '/tools/completeness')
import mutation_test as mt  # noqa: E402

WORK = 'D:/temp/opencode/cl_layout/gap/g3gap'
OUT = WORK + '/identity_dossier.json'


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def main():
    payload = {}
    for eid in ('JS-BREAK-001', 'JS-WHILE-040'):
        case_path = (REPO + '/.trae/specs/attack-completeness-claims/rounds/round9/'
                     'g3_mutation/case_%s.json' % eid)
        case = json.load(open(case_path, encoding='utf-8-sig'))
        source_path = case['product']['source']
        source = open(source_path, encoding='utf-8-sig').read()
        tree = ast.parse(source)
        baseline_text = ast.unparse(tree) + '\n'
        listed = mt.generate_mutations(tree, skip_identity=False)
        mutation = [m for m in listed if m['mutation_id'] == 'M0014'][0]
        mutant_text = mt.mutation_source(source, mutation)
        baseline_code = compile(ast.parse(baseline_text), '<x>', 'exec')
        mutant_code = compile(ast.parse(mutant_text), '<x>', 'exec')
        base_lines = baseline_text.splitlines()
        mut_lines = mutant_text.splitlines()
        changed = [(i + 1, a, b) for i, (a, b) in enumerate(zip(base_lines, mut_lines)) if a != b]
        report = json.load(open(os.path.join(WORK, 'mut_identity', 'mut_%s.json' % eid),
                                encoding='utf-8'))
        record = [m for m in report['mutants'] if m['mutation_id'] == 'M0014'][0]
        payload[eid] = {
            'source': source_path,
            'mutation_id': 'M0014',
            'operator': mutation['operator'],
            'description': mutation['description'],
            'lineno': mutation['lineno'],
            'path': mutation['path'],
            'source_bytes_identical': mutant_text == baseline_text,
            'baseline_sha256': sha(baseline_text),
            'mutant_sha256': sha(mutant_text),
            'baseline_len': len(baseline_text),
            'mutant_len': len(mutant_text),
            'changed_lines': [{'line': n, 'baseline': a, 'mutant': b} for n, a, b in changed],
            'compiled_code_identical': mt._code_identity(baseline_code) == mt._code_identity(mutant_code),
            'co_code_equal': baseline_code.co_code == mutant_code.co_code,
            'co_consts_equal': baseline_code.co_consts == mutant_code.co_consts,
            'co_code_len': len(baseline_code.co_code),
            'reported_status': record['status'],
            'reported_semantic_status': record['semantic_status'],
            'reported_diffs': record['diffs'],
        }
        print(eid, payload[eid]['source_bytes_identical'],
              payload[eid]['compiled_code_identical'],
              payload[eid]['changed_lines'], record['status'])
    json.dump(payload, open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
