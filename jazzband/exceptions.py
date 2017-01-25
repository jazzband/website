from werkzeug.exceptions import Aborter, HTTPException
from werkzeug._compat import integer_types


class Ejecter(Aborter):

    def __call__(self, code, *args, **kwargs):
        if not args and not kwargs and not isinstance(code, integer_types):
            raise HTTPException(response=code)
        if code not in self.mapping:
            raise LookupError('no exception for %r' % code)
        return self.mapping[code](*args, **kwargs)


def eject(status, *args, **kwargs):
    """
    A version of werkzeug.exceptions.abort that puts the description
    in the response status code to help PyPI.
    """
    ejection = _ejecter(status, *args, **kwargs)
    description = kwargs.get('description')
    if description is not None:
        ejection.code = '%s %s' % (ejection.code, description)
    raise ejection


_ejecter = Ejecter()
