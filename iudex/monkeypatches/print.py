def monkeypatch_print():
    """Monkey patches print to instead use logging.info."""
    import builtins
    import logging
    import sys

    def print(*objects, sep=" ", end="\n", file=sys.stdout, flush=False):
        message = sep.join(map(str, objects)) + end

        log_method = logging.error if file is sys.stderr else logging.info

        log_method(message)

        if flush:
            file.flush()

    builtins.print = print
