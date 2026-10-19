def s_b73a(fh):
    try:
        raise OSError("x")
    except OSError as e:
        from io import StringIO as sio
        return sio(str(e))
    finally:
        from io import StringIO as sio2
        if fh:
            sio2(fh)
