from werkzeug.exceptions import Aborter, HTTPException
from werkzeug._compat import integer_types


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


class Ejecter(Aborter):
    def __call__(self, code, *args, **kwargs):
        if not args and not kwargs and not isinstance(code, integer_types):
            raise HTTPException(response=code)
        if code not in self.mapping:
            raise LookupError("no exception for %r" % code)
        return self.mapping[code](*args, **kwargs)


def eject(status, *args, **kwargs):
    """
    A version of werkzeug.exceptions.abort that puts the description
    in the response status code to help PyPI.
    """
    ejection = _ejecter(status, *args, **kwargs)
    description = kwargs.get("description")
    if description is not None:
        ejection.code = "%s %s" % (ejection.code, description)
    raise ejection


_ejecter = Ejecter()
