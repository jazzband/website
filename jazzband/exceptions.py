from werkzeug.exceptions import Aborter


class RateLimit(Exception):
    def __init__(self, response):
        self.response = response
        try:
            message = response.json()["message"]
        except Exception:
            message = getattr(response, "content", response)
        super().__init__(message)


class Rollback(Exception):
    """Raising to manually rollback current (nested) transaction.

    Raising a ``Rollback`` will always rollback the current most recent
    transaction. By default (not setting `propagate`), subtransaction-driven
    (`nested=False`) nested transaction will rollback and re-raise the same
    ``Rollback`` exception object, while savepoint-driven (`nested=True`)
    nested transaction will rollback and stop the exception from propagating.

    You can manually override the behavior by setting `propagate` to `True`
    (always re-raise) or `False` (always swallow the exception) on need.
    Caution, setting to `False` can be sometimes dangerous, because it may be
    misleading when the code runs successfully without any errors but code
    after `raise Rollback(propagate=False)` is never executed, and the data is
    not persisted at all, silently. It is the same situation to use
    `raise Rollback()` in a savepoint-driven nested transaction (root
    transaction is never affected, unless explicitly set `propagate` to
    `False`, the exception is always re-raised.)
    """

    def __init__(self, propagate=None):
        self.propagate = propagate


def eject(status, *args, **kwargs):
    """
    A version of werkzeug.exceptions.abort that puts the description
    in the response status code to help PyPI.
    """
    try:
        _ejecter(status, *args, **kwargs)
    except Exception as ejection:
        description = kwargs.get("description")
        if description is not None:
            ejection.code = f"{ejection.code} {description}"
        raise ejection


_ejecter: Aborter = Aborter()
