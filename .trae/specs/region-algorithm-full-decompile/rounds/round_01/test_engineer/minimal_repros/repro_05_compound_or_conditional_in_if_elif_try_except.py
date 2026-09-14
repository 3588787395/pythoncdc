def create(strategy, mode=None, reloads=False):
    try:
        if mode or mode == 'mode2' or reloads and reloads:
            name = 'strategy'
            path = os.path.join('/tmp', name + '.py')
            with open(path, 'w') as f:
                f.write(strategy)
            os.chmod(path, 511)
            if reloads:
                old = open(path).read()
                with open(path, 'w') as f2:
                    f2.write(old.replace('old', name))
            if mode == 'mode1':
                error = encrypt(name)
            elif mode == 'mode2':
                error = compile_so(name)
            else:
                error = verify(path)
            if error is not None:
                if isinstance(error, str):
                    print(error)
                else:
                    raise error
        elif mode == 'mode0':
            if not reloads:
                src = '/src/%s' % name
                dst = '/dst/%s' % name
                os.system('cp %s %s' % (src, dst))
                upload = get_upload(name)
                with open('/tmp/strategy.py', 'w') as fw:
                    fw.write(upload)
                error = encrypt('strategy')
                if error is not None:
                    print('compile failed')
    except CompileError as e:
        raise e
    except Exception:
        print('unexpected')
