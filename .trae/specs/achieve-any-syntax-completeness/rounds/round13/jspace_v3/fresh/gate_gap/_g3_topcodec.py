# Bytecode-level dossier for the top-level co_code mutants of JS-RETURN-033/070.
#   python -I -X utf8 _g3_topcodec.py
import ast
import difflib
import dis
import io
import json
import os
import sys

REPO = 'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO + '/tools/completeness')
import mutation_test as mt  # noqa: E402

CASES = {
    'JS-RETURN-033': ('test_repros/round3/e02_g1_b98_hosts.py', ['M0006', 'M0008']),
    'JS-RETURN-070': (None, ['M0006', 'M0008']),
}
OUT = 'D:/temp/opencode/cl_layout/gap/g3gap/topcodec.json'


def lines_of(code):
    out = io.StringIO()
    dis.dis(code, file=out, depth=0)
    return [line.rstrip() for line in out.getvalue().splitlines() if line.strip()]


def delta(baseline, mutant):
    return [line for line in difflib.unified_diff(baseline, mutant, 'baseline', 'mutant',
                                                  n=1, lineterm='')]


def main():
    cases_dir = REPO + '/.trae/specs/attack-completeness-claims/rounds/round9/g3_mutation'
    payload = {}
    for eid, (source_rel, ids) in CASES.items():
        with open(os.path.join(cases_dir, 'case_%s.json' % eid), encoding='utf-8-sig') as fh:
            case = json.load(fh)
        source_path = case['product']['source']
        with open(source_path, encoding='utf-8-sig') as fh:
            source = fh.read()
        tree = ast.parse(source)
        baseline_text = ast.unparse(tree) + '\n'
        listed = mt.generate_mutations(tree, skip_identity=False)
        by_id = {item['mutation_id']: item for item in listed}
        baseline_code = compile(ast.parse(baseline_text), '<baseline>', 'exec')
        base_lines = lines_of(baseline_code)
        rows = []
        for mid in ids:
            mutation = by_id[mid]
            mutant_text = mt.mutation_source(source, mutation)
            mutant_code = compile(ast.parse(mutant_text), '<mutant>', 'exec')
            diff = delta(base_lines, lines_of(mutant_code))
            rows.append({
                'mutation_id': mid, 'operator': mutation['operator'],
                'description': mutation['description'], 'lineno': mutation['lineno'],
                'path': mutation['path'],
                'source_equal': mutant_text == baseline_text,
                'co_code_equal': mutant_code.co_code == baseline_code.co_code,
                'co_consts_equal': mutant_code.co_consts == baseline_code.co_consts,
                'co_names_equal': mutant_code.co_names == baseline_code.co_names,
                'co_stacksize_equal': mutant_code.co_stacksize == baseline_code.co_stacksize,
                'baseline_co_code_len': len(baseline_code.co_code),
                'mutant_co_code_len': len(mutant_code.co_code),
                'dis_delta': diff,
                'mutant_source_excerpt': mutant_text,
            })
        payload[eid] = {
            'case_id': case['case_id'], 'source': source_path,
            'baseline_text': baseline_text,
            'mutants': rows,
        }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    for eid, info in payload.items():
        for row in info['mutants']:
            print('==', eid, row['mutation_id'], row['description'],
                  'co_code_equal=%s len %d->%d consts_eq=%s' % (
                      row['co_code_equal'], row['baseline_co_code_len'],
                      row['mutant_co_code_len'], row['co_consts_equal']))
            print('\n'.join(row['dis_delta']) or '(no module-level dis delta)')
            print()


if __name__ == '__main__':
    main()
