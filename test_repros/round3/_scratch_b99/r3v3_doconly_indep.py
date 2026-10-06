# 独立复核（评审工程师 Task 3.3 闭环）：整改前后 region_analyzer.py 剥离注释与 docstring 后 AST 恒等（零算法改动）
# 父版本内容直接由 `git show 7090ad96:core/cfg/region_analyzer.py` 取（只读，不依赖本地副本）。
import ast
import io
import subprocess
import sys
import tokenize

CUR = r'f:\Downloads\pythoncdc-main\core\cfg\region_analyzer.py'
ROOT = r'f:\Downloads\pythoncdc-main'
PARENT_REV = '7090ad96'


def strip_docstrings(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return tree


def exec_tokens(src):
    out = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE,
                        tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING,
                        tokenize.ENDMARKER, tokenize.STRING):
            continue
        out.append((tok.type, tok.string))
    return out


pre = subprocess.run(['git', 'show', '%s:core/cfg/region_analyzer.py' % PARENT_REV],
                     cwd=ROOT, capture_output=True).stdout.decode('utf-8-sig')
cur = open(CUR, encoding='utf-8-sig').read()

a_cur = ast.dump(strip_docstrings(ast.parse(cur)))
a_pre = ast.dump(strip_docstrings(ast.parse(pre)))
print('LOGIC_AST_EQUAL =', a_cur == a_pre)
print('cur_len=%d pre_len=%d delta=%d' % (len(cur), len(pre), len(cur) - len(pre)))

code_c, code_p = exec_tokens(cur), exec_tokens(pre)
print('EXEC_TOKEN_EQUAL =', code_c == code_p)
if code_c != code_p:
    for i, (x, y) in enumerate(zip(code_c, code_p)):
        if x != y:
            print('first diff at', i, x, y)
            break
    print('len', len(code_c), len(code_p))
    sys.exit(1)
