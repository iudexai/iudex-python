from opentelemetry.sdk._logs import LoggingHandler


def monkeypatch_print(logging_handler: LoggingHandler):
    import builtins
    import inspect
    import logging
    import sys
    import traceback
    from collections.abc import Mapping
    from typing import Optional

    print_logger = logging.getLogger("print")
    print_logger.setLevel(logging.INFO)
    print_logger.propagate = False

    # Attach print-style formatter (i.e., no LEVEL: prefix)
    print_logger.addHandler(logging_handler)

    def custom_print(
        *objects,
        sep=" ",
        end="\n",
        file=sys.stdout,
        flush=False,
        extra: Optional[Mapping[str, object]] = None
    ):
        level = logging.ERROR if file is sys.stderr else logging.INFO
        message = sep.join(map(str, objects)) + end
        frame = inspect.currentframe()

        # Move up in the stack to find the first non-monkeypatch frame (the original caller of print)
        while frame and inspect.getsourcefile(frame) == __file__:
            frame = frame.f_back

        if frame:
            fn = frame.f_code.co_filename
            lno = frame.f_lineno
            func = frame.f_code.co_name
            # Capture stack trace from caller's frame
            sinfo = "".join(traceback.format_stack(frame))
        else:
            fn, lno, func, sinfo = "(unknown)", 0, "(unknown)", None

        record = print_logger.makeRecord(
            name=print_logger.name,
            level=level,
            fn=fn,
            lno=lno,
            msg=message,
            args=(),  # print API doesn't use this
            exc_info=None,  # print API doesn't use this
            func=func,
            extra=extra,
            sinfo=sinfo,
        )
        print_logger.handle(record)

        # Write to the file if needed
        if file is sys.stdout or file is sys.stderr:
            file.write(message)
            if flush:
                file.flush()

    builtins.print = custom_print
