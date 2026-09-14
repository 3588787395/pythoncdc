
import os
import subprocess

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
                    r = 1
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
