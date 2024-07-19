def monkeypatch_LogRecord_getMessage():
    """Monkey patches LogRecord.getMessages.

    Changes getMessages to also handle *args as a list of strings instead of only as
    a list of string format arguments.
    """
    from logging import LogRecord

    _getMessage = LogRecord.getMessage

    def getMessage(self: LogRecord):
        try:
            return _getMessage(self)
        except Exception:
            msg = str(self.msg)
            if self.args:
                msg = msg + " " + " ".join(self.args)
            return msg

    LogRecord.getMessage = getMessage
