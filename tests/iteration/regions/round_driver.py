import sys
import os
import json
import ast
import traceback
import subprocess
from typing import List, Dict, Any, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator
from tests.iteration.regions.generators import (
    GENERATOR_MAP, REGION_ORDER, complexity_for_round,
    BASIC, MODERATE, ADVANCED, ADVERSARIAL
)

REGIONS_DIR = os.path.join(os.path.dirname(__file__))
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
MIN_BUGS_PER_ROUND = 10
MAX_ROUNDS = 20
PATTERNS_PER_BATCH = 200


def decompile_source(src: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        code = compile(src, '<iteration-test>', 'exec')
        cfg = CFGBuilder().build(code)
        analyzer = RegionAnalyzer(cfg)
        generator = RegionASTGenerator(cfg, analyzer)
        tree = generator.generate()
        decompiled = CodeGenerator().generate(tree)
        return decompiled, None
    except Exception as e:
        return None, traceback.format_exc()


def verify_pattern(src: str) -> Tuple[bool, Optional[str], Optional[str], bool]:
    is_c_class = False
    try:
        compile(src, '<iteration-test>', 'exec')
    except SyntaxError as e:
        return False, None, f'SyntaxError: {e}', False
    decompiled, exc = decompile_source(src)
    if exc:
        return False, decompiled, exc, False
    if decompiled is None:
        return False, None, 'Decompilation returned None', False
    try:
        orig_ast = ast.dump(ast.parse(src))
        dec_ast = ast.dump(ast.parse(decompiled))
    except Exception as e:
        return False, decompiled, f'Parse error: {e}', False
    if orig_ast != dec_ast:
        if 'match' in src and 'case _:' not in src and src.count('case ') == 1:
            is_c_class = True
        return False, decompiled, 'ast_mismatch', is_c_class
    return True, decompiled, None, False


def run_pytest_regression_check() -> bool:
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 'tests/control_flow_matrix/', '-x', '-q'],
        capture_output=True, text=True, timeout=300,
        cwd=os.path.join(os.path.dirname(__file__), '..', '..', '..'),
        env=env
    )
    return result.returncode == 0


class RoundDriver:
    def __init__(self, region_type: str):
        self.region_type = region_type
        self.region_dir = os.path.join(REGIONS_DIR, region_type)
        self.all_bugs = []
        self.round_results = []
        self.regression_seeds = []

    def _round_dir(self, round_num: int) -> str:
        return os.path.join(self.region_dir, f'round-{round_num}')

    def _write_round_files(self, round_num: int, patterns: List[str],
                           bugs: List[Dict], fix_log: str = ''):
        rdir = self._round_dir(round_num)
        os.makedirs(rdir, exist_ok=True)
        with open(os.path.join(rdir, 'patterns.py'), 'w', encoding='utf-8') as f:
            f.write('PATTERNS = [\n')
            for p in patterns:
                f.write(json.dumps(p) + ',\n')
            f.write(']\n')
        with open(os.path.join(rdir, 'bugs.json'), 'w', encoding='utf-8') as f:
            json.dump(bugs, f, indent=2, ensure_ascii=False)
        with open(os.path.join(rdir, 'fix_log.md'), 'w', encoding='utf-8') as f:
            f.write(fix_log or '# No fixes needed this round\n')

    def _collect_bugs(self, patterns: List[str]) -> List[Dict]:
        bugs = []
        for i, src in enumerate(patterns):
            ok, decompiled, error, is_c_class = verify_pattern(src)
            if not ok:
                bug = {
                    'id': f'{self.region_type}-r{{round}}-{i}',
                    'source': src,
                    'decompiled': decompiled,
                    'error_type': error,
                    'c_class': is_c_class,
                }
                bugs.append(bug)
        return bugs

    def _verify_fixes(self, bug_patterns: List[str]) -> bool:
        for src in bug_patterns:
            ok, _, _, _ = verify_pattern(src)
            if not ok:
                return False
        return True

    def run_round(self, round_num: int) -> Dict[str, Any]:
        complexity = complexity_for_round(round_num)
        gen_cls = GENERATOR_MAP[self.region_type]
        gen = gen_cls(
            seed=round_num * 1000 + 42,
            complexity=complexity,
            regression_seeds=self.regression_seeds if complexity == ADVERSARIAL else []
        )
        all_patterns = []
        all_bugs = []
        non_c_class_count = 0
        batch = 0
        max_batches = 25

        while non_c_class_count < MIN_BUGS_PER_ROUND and batch < max_batches:
            batch += 1
            patterns = gen.generate(PATTERNS_PER_BATCH)
            valid_patterns = []
            for p in patterns:
                try:
                    compile(p, '<t>', 'exec')
                    valid_patterns.append(p)
                except SyntaxError:
                    continue
            all_patterns.extend(valid_patterns)
            bugs = self._collect_bugs(valid_patterns)
            for b in bugs:
                if not b['c_class']:
                    non_c_class_count += 1
            all_bugs.extend(bugs)
            if non_c_class_count >= MIN_BUGS_PER_ROUND:
                break

        round_valid = non_c_class_count >= MIN_BUGS_PER_ROUND
        bug_count = len(all_bugs)
        c_class_count = sum(1 for b in all_bugs if b['c_class'])

        for b in all_bugs:
            b['id'] = b['id'].replace('{{round}}', str(round_num))

        fix_log = ''
        if round_valid:
            fix_log = f'## Round {round_num} ({complexity})\n\nBugs found: {bug_count} (C-class: {c_class_count})\n\nAwaiting fixes...\n'
            for b in all_bugs[:20]:
                fix_log += f'- [{b["id"]}] {b["error_type"]}: {b["source"][:80]}\n'
        else:
            fix_log = f'## Round {round_num} ({complexity})\n\nInsufficient bugs: {bug_count} (C-class: {c_class_count}), need {MIN_BUGS_PER_ROUND}. Round does not count.\n'

        self._write_round_files(round_num, all_patterns, all_bugs, fix_log)

        result = {
            'round': round_num,
            'complexity': complexity,
            'total_patterns': len(all_patterns),
            'bug_count': bug_count,
            'c_class_count': c_class_count,
            'non_c_class_count': bug_count - c_class_count,
            'round_valid': round_valid,
            'bugs': all_bugs,
        }
        self.round_results.append(result)
        self.all_bugs.extend(all_bugs)

        if round_valid:
            for b in all_bugs:
                if not b['c_class']:
                    self.regression_seeds.append(b['source'])

        return result

    def verify_round_fixes(self, round_num: int) -> bool:
        rdir = self._round_dir(round_num)
        bugs_file = os.path.join(rdir, 'bugs.json')
        if not os.path.exists(bugs_file):
            return True
        with open(bugs_file, 'r', encoding='utf-8') as f:
            bugs = json.load(f)
        non_c_bugs = [b for b in bugs if not b.get('c_class', False)]
        if not non_c_bugs:
            return True
        bug_patterns = [b['source'] for b in non_c_bugs]
        return self._verify_fixes(bug_patterns)

    def update_fix_log(self, round_num: int, fixes_applied: str):
        rdir = self._round_dir(round_num)
        log_file = os.path.join(rdir, 'fix_log.md')
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(fixes_applied)

    def run_all_rounds(self) -> Dict[str, Any]:
        valid_rounds = 0
        for round_num in range(1, MAX_ROUNDS + 1):
            result = self.run_round(round_num)
            status = 'VALID' if result['round_valid'] else 'INVALID (insufficient bugs)'
            print(f'  Round {round_num} ({result["complexity"]}): '
                  f'{result["bug_count"]} bugs ({result["c_class_count"]} C-class), '
                  f'{result["total_patterns"]} patterns — {status}')

            if result['round_valid']:
                print(f'  >>> Round {round_num} has ≥{MIN_BUGS_PER_ROUND} non-C-class bugs. PAUSING for fixes.')
                print(f'  >>> Fix the bugs, then call verify_round_fixes({round_num}) to continue.')
                return {
                    'status': 'paused_for_fixes',
                    'round_num': round_num,
                    'result': result,
                    'valid_rounds_so_far': valid_rounds,
                }

            if result['bug_count'] == 0 and result['total_patterns'] >= PATTERNS_PER_BATCH * 5:
                consecutive_zero = 0
                for r in reversed(self.round_results):
                    if r['bug_count'] == 0:
                        consecutive_zero += 1
                    else:
                        break
                if consecutive_zero >= 5:
                    print(f'  >>> Region {self.region_type} is clean (5 consecutive zero-bug rounds). '
                          f'Fast-tracking remaining rounds.')
                    for fast_round in range(round_num + 1, MAX_ROUNDS + 1):
                        fr = self.run_round(fast_round)
                        print(f'  Round {fast_round} (fast-track): {fr["bug_count"]} bugs')
                    break

        return {
            'status': 'complete',
            'valid_rounds': valid_rounds,
            'total_bugs': len(self.all_bugs),
            'c_class_bugs': sum(1 for b in self.all_bugs if b.get('c_class', False)),
        }

    def save_summary(self):
        os.makedirs(RESULTS_DIR, exist_ok=True)
        summary = {
            'region_type': self.region_type,
            'total_rounds': len(self.round_results),
            'total_bugs': len(self.all_bugs),
            'c_class_bugs': sum(1 for b in self.all_bugs if b.get('c_class', False)),
            'round_summaries': [
                {
                    'round': r['round'],
                    'complexity': r['complexity'],
                    'bug_count': r['bug_count'],
                    'c_class_count': r['c_class_count'],
                    'round_valid': r['round_valid'],
                    'total_patterns': r['total_patterns'],
                }
                for r in self.round_results
            ],
        }
        path = os.path.join(RESULTS_DIR, f'{self.region_type}_summary.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        return path
