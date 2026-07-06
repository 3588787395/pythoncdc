import sys
import os
import json
import time
import random
import traceback
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.iteration.decompile_tester import verify_decompilation, decompile_source
from tests.iteration.pattern_generator import GEN_FUNCS

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')


def run_round(region_type: str, round_num: int, seed: int, min_bugs: int = 10,
              pattern_batch_size: int = 50) -> dict:
    """
    Run one round of iteration testing for a region type.
    
    Protocol:
    1. Generate patterns using seed
    2. Test all patterns, collect bugs (failures)
    3. If >= min_bugs found, round counts
    4. Return results dict
    
    Returns:
        {
            'region_type': str,
            'round': int,
            'seed': int,
            'total_patterns': int,
            'bugs_found': int,
            'bugs': list of {source, decompiled, error, category},
            'passed': int,
            'round_counts': bool (True if >= min_bugs),
            'duration_sec': float,
        }
    """
    start = time.time()
    gen_func = GEN_FUNCS[region_type]
    rng = random.Random(seed)
    
    patterns = gen_func(rng=rng, count=pattern_batch_size)
    
    bugs = []
    passed = 0
    
    for src in patterns:
        result = verify_decompilation(src)
        if result['ok']:
            passed += 1
        else:
            bugs.append({
                'source': src,
                'decompiled': result['decompiled'],
                'error': result['error'],
                'category': result['category'],
            })
    
    duration = time.time() - start
    round_counts = len(bugs) >= min_bugs
    
    return {
        'region_type': region_type,
        'round': round_num,
        'seed': seed,
        'total_patterns': len(patterns),
        'bugs_found': len(bugs),
        'passed': passed,
        'round_counts': round_counts,
        'bugs': bugs,
        'duration_sec': round(duration, 2),
    }


def run_all_rounds(region_type: str, num_rounds: int = 20, min_bugs: int = 10,
                   base_seed: int = 1000, pattern_batch_size: int = 50) -> list:
    """
    Run all rounds for a region type.
    Returns list of round results.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    all_results = []
    for r in range(num_rounds):
        seed = base_seed + r * 1000 + hash(region_type) % 10000
        print(f'\n=== {region_type} Round {r+1}/{num_rounds} (seed={seed}) ===')
        
        result = run_round(region_type, r + 1, seed, min_bugs, pattern_batch_size)
        all_results.append(result)
        
        status = 'COUNTS' if result['round_counts'] else 'DOES NOT COUNT'
        print(f'  Patterns: {result["total_patterns"]}, Passed: {result["passed"]}, '
              f'Bugs: {result["bugs_found"]}/{min_bugs} → {status} ({result["duration_sec"]}s)')
        
        if result['bugs_found'] > 0:
            for i, bug in enumerate(result['bugs'][:5]):
                print(f'  Bug {i+1}: [{bug["category"]}] {bug["error"][:120]}')
            if len(result['bugs']) > 5:
                print(f'  ... and {len(result["bugs"]) - 5} more')
    
    # Save summary
    summary_path = os.path.join(RESULTS_DIR, f'{region_type}_summary.json')
    summary = []
    for r in all_results:
        summary.append({
            'round': r['round'],
            'seed': r['seed'],
            'total_patterns': r['total_patterns'],
            'bugs_found': r['bugs_found'],
            'passed': r['passed'],
            'round_counts': r['round_counts'],
            'duration_sec': r['duration_sec'],
        })
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Save full bugs for first round that counts
    for r in all_results:
        if r['round_counts'] or r['bugs_found'] > 0:
            bugs_path = os.path.join(RESULTS_DIR, f'{region_type}_round{r["round"]}_bugs.json')
            with open(bugs_path, 'w') as f:
                json.dump(r['bugs'], f, indent=2, default=str)
    
    # Print final summary
    counting_rounds = sum(1 for r in all_results if r['round_counts'])
    total_bugs = sum(r['bugs_found'] for r in all_results)
    print(f'\n=== {region_type} FINAL: {counting_rounds}/{num_rounds} rounds count, '
          f'{total_bugs} total bugs ===')
    
    return all_results


def run_single_region(region_type: str, num_rounds: int = 20, min_bugs: int = 10):
    return run_all_rounds(region_type, num_rounds, min_bugs)


def run_all_regions(num_rounds: int = 20, min_bugs: int = 10, region_types: list = None):
    if region_types is None:
        region_types = list(GEN_FUNCS.keys())
    
    grand_results = {}
    for rt in region_types:
        print(f'\n{"="*60}')
        print(f'  REGION TYPE: {rt.upper()}')
        print(f'{"="*60}')
        grand_results[rt] = run_all_rounds(rt, num_rounds, min_bugs)
    
    print(f'\n{"="*60}')
    print(f'  GRAND SUMMARY')
    print(f'{"="*60}')
    for rt, results in grand_results.items():
        counting = sum(1 for r in results if r['round_counts'])
        bugs = sum(r['bugs_found'] for r in results)
        print(f'  {rt}: {counting}/{num_rounds} rounds count, {bugs} total bugs')
    
    return grand_results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--region', type=str, default=None,
                        help='Region type to test (if, loop, tryexcept, with, match, assert, boolop, ternary)')
    parser.add_argument('--rounds', type=int, default=20)
    parser.add_argument('--min-bugs', type=int, default=10)
    parser.add_argument('--batch-size', type=int, default=50)
    parser.add_argument('--all', action='store_true', help='Run all region types')
    args = parser.parse_args()
    
    if args.region:
        run_all_rounds(args.region, args.rounds, args.min_bugs,
                       pattern_batch_size=args.batch_size)
    elif args.all:
        run_all_regions(args.rounds, args.min_bugs)
    else:
        print('Specify --region <type> or --all')
        print(f'Types: {list(GEN_FUNCS.keys())}')
