"""R21: Generate 10+ minimal repro .py files for try-else pattern where
handler exits via continue/break/return and try body JUMP_FORWARDs past
handler to else clause. Compile each to .pyc then decompile and verify."""
import py_compile
import os
import sys
import textwrap

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

REPRO_DIR = r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_21/test_engineer/minimal_repros'

# Pattern TE (Try-Else): handler exits loop via continue/break/return,
# try body JUMP_FORWARDs over handler to else clause.
SOURCES = {
    'te001_loop_continue.py': '''
def f(items):
    for item in items:
        try:
            x = process(item)
        except ValueError:
            continue
        else:
            save(x)
''',
    'te002_loop_break.py': '''
def f(items):
    for item in items:
        try:
            x = process(item)
        except ValueError:
            break
        else:
            save(x)
''',
    'te003_loop_return.py': '''
def f(items):
    for item in items:
        try:
            x = process(item)
        except ValueError:
            return None
        else:
            save(x)
''',
    'te004_loop_continue_multi_handler.py': '''
def f(items):
    for item in items:
        try:
            x = process(item)
        except (IOError, EOFError):
            continue
        except ValueError:
            continue
        else:
            save(x)
''',
    'te005_nested_try_else.py': '''
def f(data):
    for d in data:
        try:
            x = parse(d)
        except ValueError:
            continue
        else:
            try:
                y = transform(x)
            except KeyError:
                continue
            else:
                save(y)
''',
    'te006_else_with_if.py': '''
def f(items):
    for item in items:
        try:
            x = read(item)
        except IOError:
            continue
        else:
            if x is not None:
                save(x)
''',
    'te007_else_with_multiple_stmts.py': '''
def f(items):
    for item in items:
        try:
            buf = get_buf(item)
            text = buf.read()
        except IOError:
            continue
        else:
            msg = encode(text)
            write(msg)
            flush()
''',
    'te008_while_loop_continue.py': '''
def f():
    while running():
        try:
            data = read_stream()
        except IOError:
            continue
        else:
            process(data)
''',
    'te009_else_assign_and_call.py': '''
def f(items):
    for item in items:
        try:
            result = compute(item)
        except ValueError:
            continue
        else:
            msg = format(result)
            send(msg)
''',
    'te010_handler_with_logic_continue.py': '''
def f(items):
    for item in items:
        try:
            x = process(item)
        except ValueError:
            log("error")
            continue
        else:
            save(x)
''',
    'te011_nested_if_in_else.py': '''
def f(items):
    for item in items:
        try:
            x = process(item)
        except ValueError:
            continue
        else:
            if x > 0:
                save(x)
            else:
                discard(x)
''',
    'te012_else_with_for.py': '''
def f(items):
    for item in items:
        try:
            data = read(item)
        except IOError:
            continue
        else:
            for d in data:
                write(d)
''',
}


def main():
    os.makedirs(REPRO_DIR, exist_ok=True)
    results = []
    for name, src in SOURCES.items():
        src = textwrap.dedent(src).strip() + '\n'
        py_path = os.path.join(REPRO_DIR, name)
        with open(py_path, 'w', encoding='utf-8') as f:
            f.write(src)
        # Compile
        pyc_path = py_compile.compile(py_path, doraise=True)
        results.append((name, 'compiled', pyc_path))
        print(f'  {name}: OK -> {pyc_path}')
    print(f'\nGenerated {len(results)} minimal repro files.')


if __name__ == '__main__':
    main()
