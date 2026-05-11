"""
最终验证逻辑运算测试
"""
import sys
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

from merged_four_rounds_test import MergedFourRoundsTest

test = MergedFourRoundsTest()

# 逻辑运算测试用例
source = '''
a = True and False
b = True or False
c = not True
'''

test.add_test('逻辑运算', source, '测试')
success = test.run_all_tests()

if success:
    print("\n✅ 逻辑运算测试通过！")
else:
    print("\n❌ 逻辑运算测试失败！")

sys.exit(0 if success else 1)
