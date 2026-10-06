def one_star():
    try:
        pass
    except* ValueError:
        pass


def two_star():
    try:
        pass
    except* ValueError:
        pass
    except* TypeError:
        pass


def three_star():
    try:
        pass
    except* ValueError:
        pass
    except* TypeError:
        pass
    except* KeyError:
        pass


def normal_handlers():
    try:
        pass
    except ValueError:
        pass
    except TypeError:
        pass


def normal_finally():
    try:
        pass
    except ValueError:
        pass
    finally:
        pass


def star_else_finally():
    try:
        pass
    except* ValueError:
        pass
    else:
        pass
    finally:
        pass


def nested_star():
    try:
        try:
            pass
        except* ValueError:
            pass
        except* TypeError:
            pass
    except Exception:
        pass