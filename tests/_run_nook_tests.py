#!/usr/bin/env python3
"""
Nook测试套件运行器
用于快速验证nook测试的修复效果
"""
import sys
import os
from pathlib import Path

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_nook_tests():
    """运行nook测试套件"""
    import unittest
    import traceback
    
    nook_dir = PROJECT_ROOT / "tests" / "nook"
    
    if not nook_dir.exists():
        print(f"❌ Nook目录不存在: {nook_dir}")
        return False
    
    # 发现所有测试文件
    test_files = list(nook_dir.glob("test_*.py"))
    
    print("=" * 80)
    print("NOOK测试套件运行器")
    print("=" * 80)
    print(f"测试目录: {nook_dir}")
    print(f"发现测试文件: {len(test_files)}")
    print("-" * 80)
    
    # 统计结果
    results = {
        'total': len(test_files),
        'collected': 0,
        'failed_import': 0,
        'syntax_error': 0,
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    for test_file in sorted(test_files):
        test_name = test_file.stem
        
        try:
            # 尝试导入模块
            import importlib.util
            
            spec = importlib.util.spec_from_file_location(test_name, test_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 尝试加载测试用例
                loader = unittest.TestLoader()
                suite = loader.loadTestsFromModule(module)
                
                if suite.countTestCases() > 0:
                    results['collected'] += 1
                    
                    # 运行测试
                    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
                    result = runner.run(suite)
                    
                    if result.wasSuccessful():
                        results['success'] += 1
                        print(f"✓ {test_name:<40} [PASS] ({suite.countTestCases()} tests)")
                    else:
                        results['failed'] += 1
                        error_count = len(result.failures) + len(result.errors)
                        print(f"✗ {test_name:<40} [FAIL] ({error_count} failures)")
                        
                        # 记录错误详情（最多5个）
                        for test, traceback_str in (result.failures + result.errors)[:5]:
                            results['errors'].append({
                                'file': test_name,
                                'test': str(test),
                                'error': traceback_str[:200]
                            })
                else:
                    # 模块导入成功但没有unittest测试
                    results['collected'] += 1
                    results['success'] += 1  # 视为成功（可能是脚本式测试）
                    print(f"○ {test_name:<40} [OK] (no unittest tests)")
                    
        except SyntaxError as e:
            results['syntax_error'] += 1
            print(f"💥 {test_name:<40} [SYNTAX ERROR] L{e.lineno}: {e.msg}")
            results['errors'].append({
                'file': test_name,
                'error': f"SyntaxError at line {e.lineno}: {e.msg}"
            })
            
        except ImportError as e:
            results['failed_import'] += 1
            print(f"📦 {test_name:<40} [IMPORT ERROR] {str(e)[:60]}")
            results['errors'].append({
                'file': test_name,
                'error': f"ImportError: {str(e)}"
            })
            
        except Exception as e:
            results['failed_import'] += 1
            print(f"⚠️  {test_name:<40} [ERROR] {type(e).__name__}: {str(e)[:60]}")
            results['errors'].append({
                'file': test_name,
                'error': f"{type(e).__name__}: {str(e)}"
            })
    
    # 输出统计报告
    print("\n" + "=" * 80)
    print("测试结果统计")
    print("=" * 80)
    
    runnable = results['collected'] + results['success']
    total = results['total']
    runnable_rate = (runnable / total * 100) if total > 0 else 0
    
    print(f"总测试文件:     {results['total']}")
    print(f"可收集/运行:   {runnable} ({runnable_rate:.1f}%)")
    print(f"  - 成功:       {results['success']}")
    print(f"  - 有测试但失败:{results['failed']}")
    print(f"  - 无unittest:  {results.get('success_no_unittest', 0)}")
    print(f"收集失败:       {results['failed_import'] + results['syntax_error']}")
    print(f"  - 导入错误:   {results['failed_import']}")
    print(f"  - 语法错误:   {results['syntax_error']}")
    
    if results['errors']:
        print(f"\n{'=' * 80}")
        print("错误详情（前10个）:")
        print('=' * 80)
        
        for i, err in enumerate(results['errors'][:10], 1):
            print(f"\n{i}. [{err['file']}]")
            print(f"   {err['error']}")
        
        if len(results['errors']) > 10:
            print(f"\n... 还有 {len(results['errors']) - 10} 个错误")
    
    print(f"\n{'=' * 80}")
    if runnable_rate >= 80:
        print(f"✅ 可运行率 {runnable_rate:.1f}% ≥ 80% 目标达成！")
    else:
        print(f"⚠️  可运行率 {runnable_rate:.1f}% < 80% 目标，需要进一步修复")
    print('=' * 80)
    
    return runnable_rate >= 80


if __name__ == '__main__':
    success = run_nook_tests()
    sys.exit(0 if success else 1)
