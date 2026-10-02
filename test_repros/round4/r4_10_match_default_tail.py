# r4_10 attack: multi-case + default _ tail case


def match_default_tail(x):
    """Attack 1: 5-case dispatch with wildcard default tail."""
    match x:
        case "a":
            return 1
        case "b":
            return 2
        case "c":
            return 3
        case "d":
            return 4
        case _:
            return 0


def match_default_no_wildcard(x):
    """Attack 2: multi-case without wildcard (implicit fall out)."""
    result = "unset"
    match x:
        case 1:
            result = "first"
        case 2:
            result = "second"
        case 3:
            result = "third"
    return result


def match_default_tail_with_work(x):
    """Attack 3: default tail with side-effect body."""
    log = []
    match x:
        case "run":
            log.append("running")
            for i in range(2):
                log.append(i)
        case "stop":
            log.append("stopped")
        case _:
            log.append("idle")
            log.append("waiting")
    return log


def match_default_capture_tail(x):
    """Attack 4: 4 value cases then capture tail."""
    match x:
        case None:
            return "nil"
        case True:
            return "true"
        case False:
            return "false"
        case 0:
            return "zero"
        case val:
            return ("captured", val)


def match_default_nested_tail(x):
    """Attack 5: default tail body containing if/else."""
    match x:
        case 1:
            return "one"
        case 2:
            return "two"
        case _:
            if x > 100:
                return "big"
            elif x > 10:
                return "mid"
            else:
                return "small"
