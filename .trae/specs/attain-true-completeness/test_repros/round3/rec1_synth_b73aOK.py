# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b73a.pyc (Python 3.11)

def s_b73a(fh):
    try:
        raise OSError('x')
    except OSError as e:
        from io import StringIO as sio
        return sio(str(e))
    finally:
        from io import StringIO as sio2
        if fh:
            sio2(fh)
