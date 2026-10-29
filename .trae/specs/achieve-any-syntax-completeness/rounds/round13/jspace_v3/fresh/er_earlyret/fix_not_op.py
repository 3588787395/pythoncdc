# Fix Not op string to lowercase 'not' for ast_converter compatibility.
P = r'F:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'
raw = open(P, 'rb').read().decode('utf-8')
src = raw.replace('\r\n', '\n')
old = "test_expr = {'type': 'UnaryOp', 'op': 'Not', 'operand': test_expr}"
new = "test_expr = {'type': 'UnaryOp', 'op': 'not', 'operand': test_expr}"
cnt = src.count(old)
print('occurrences:', cnt)
assert cnt == 1
src = src.replace(old, new)
open(P, 'wb').write(src.replace('\n', '\r\n').encode('utf-8'))
print('fixed')
