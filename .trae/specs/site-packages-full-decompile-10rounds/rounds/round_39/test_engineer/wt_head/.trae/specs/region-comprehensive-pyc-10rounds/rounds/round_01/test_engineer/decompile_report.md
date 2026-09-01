# Round 01 Decompile Report

## Test Target
`python_syntax_comprehensive_test.pyc`

## Baseline Results
- Total functions: 79
- Matched: 74
- Success rate: 93.67%
- Mismatches: 5

## Mismatched Functions

| Function | true_diffs | jump_diffs | Root Cause |
|----------|-----------|-----------|------------|
| `<module>` | 1 | 0 | Multiline string with special escape chars (\t\n\r'"\\) not properly quoted in code generator |
| `control_flow_examples` | 47 | 28 | for-else + while-else + nested if/elif/else control flow reconstruction |
| `exception_handling_examples` | 60 | 16 | try/except/else/finally + nested try exception handling |
| `multiple_coroutines` | 18 | 0 | async function body dropped (asyncio.gather call missing) |
| `complex_expressions` | 0 | 1 | Minor jump target difference (jump_only) |

## Minimal Repro Instances

| # | Name | Status | Detail |
|---|------|--------|--------|
| 1 | repro_01_s1_multiline_string_escapes | DEFECT-REPRO | <module>: 1td/0jd |
| 2 | repro_02_s2_string_backslash_quotes | ERROR | [Errno 2] No such file or directory: 'F:\\Downloads\\pythoncdc-main\\.trae\\specs\\region-comprehensive-pyc-10rounds\\rounds\\round_01\\test_engineer\\minimal_repros\\repro_02_s2_string_backslash_quotes.pyc' |
| 3 | repro_03_cf1_for_else_break | NO_DEFECT | All functions match |
| 4 | repro_04_cf2_while_else_break | DEFECT-REPRO | <module>.test: 13td/5jd |
| 5 | repro_05_cf3_nested_for_else_while_else | DEFECT-REPRO | <module>.test: 22td/11jd |
| 6 | repro_06_cf4_for_continue_elif | NO_DEFECT | All functions match |
| 7 | repro_07_te1_try_except_else_finally | DEFECT-REPRO | <module>.test: 29td/5jd |
| 8 | repro_08_te2_nested_try_except | NO_DEFECT | All functions match |
| 9 | repro_09_te3_multi_except_else | NO_DEFECT | All functions match |
| 10 | repro_10_as1_async_await_body | DEFECT-REPRO | <module>.test: 16td/0jd |
| 11 | repro_11_as2_async_gather | DEFECT-REPRO | <module>.gather_results: 16td/0jd |
| 12 | repro_12_ce1_chained_compare_ternary | NO_DEFECT | All functions match |

**Summary**: 12 total, 5 NO_DEFECT, 6 DEFECT-REPRO, 1 ERROR

## Success Rate

- Current: 74/79 = 93.67%
- Target: 79/79 = 100%
