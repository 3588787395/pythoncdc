#!/usr/bin/env python
"""
Run all BOOL_OP exhaustive tests.
Usage: python run_tests.py [-v] [--pattern PATTERN]
"""
import sys
import os
import unittest
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def main():
    parser = argparse.ArgumentParser(description='Run BOOL_OP exhaustive tests')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='verbose output')
    parser.add_argument('--pattern', default='test_bool*.py',
                        help='test file pattern (default: test_bool*.py)')
    args = parser.parse_args()

    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern=args.pattern)

    runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(main())
