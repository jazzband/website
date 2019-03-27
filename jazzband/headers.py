from flask import request
from flask_talisman import Talisman


class JazzbandTalisman(Talisman):
    def _set_content_security_policy_headers(self, headers, options):
        if request.path.startswith("/admin"):
            options["content_security_policy"] = None
        return super()._set_content_security_policy_headers(headers, options)


talisman = JazzbandTalisman()
