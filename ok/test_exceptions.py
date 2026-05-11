# Test exception handling
def test_exception():
    try:
        risky()
    except ValueError:
        handle_value_error()
    except TypeError:
        handle_type_error()
    finally:
        cleanup()