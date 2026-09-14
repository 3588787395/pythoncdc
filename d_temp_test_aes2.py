
import os
import subprocess
import re
from binascii import b2a_hex, a2b_hex
from py_compile import compile, PyCompileError
class CompileError(Exception):
    pass
def get_code_setup(x):
    return ''
def verify_user_py_code(x):
    return None
def code_encrypt_so(f_name, path_setup, path_so):
    code_setup = get_code_setup(path_setup)
    setup_file_path = '%s/setup.py' % path_setup
    with open(setup_file_path, 'w') as file_setup:
        file_setup.write(code_setup)
        os.chmod(setup_file_path, 511)
    file_path = f'{path_so!s}/{f_name!s}.py'
    file_c_path = f'{path_so!s}/{f_name!s}.c'
    setup_file_path = '%s/setup.py' % path_setup
    try:
        with subprocess.Popen(['python3', setup_file_path, 'build_ext'], stderr=subprocess.PIPE) as proc:
            error = proc.stderr.read().decode('utf-8')
            if error:
                l = error.find('Error compiling Cython file:')
                if l != -1:
                    r = error.index('Traceback (most recent call last):')
                    error = error[l:r]
                    error_lines = error.split('
')
                    for i in range(len(error_lines) - 1, -1, -1):
                        if error_lines[i].find('%s.py' % f_name) > -1:
                            line_info = error_lines[i]
                            break
                        continue
                    info = line_info.split(':')
                    info[0] = 'str1'
                    info[1] = str(int(info[1]) - 3)
                    line_info = ':'.join(info)
                    error_lines[i] = line_info
                    error = '
'.join(error_lines)
                    error = CompileError(error)
            else:
                error = None
    except BaseException:
        error = verify_user_py_code(file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(file_c_path):
        os.remove(file_c_path)
    return error
