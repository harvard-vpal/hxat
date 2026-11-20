"""Settings for the container image built by the Dockerfile.

In the image, gunicorn receives requests directly, with no web server such as
nginx in front of Django. These settings are hxat.settings.base with two
changes for that case:

1. Repeated slashes in the request path are merged into one, as nginx does by
   default. The vendored hxighlighter CSS requests its fonts at
   /static//hxighlighter/fonts/..., and WhiteNoise does not match that path.
   If the hxighlighter build stops writing those paths, remove this change.
2. WhiteNoise runs before the other middleware. Static files return before
   Django checks the Host header and before the session middleware creates a
   django_session row. So a load balancer health check can request a static
   file, for example /static/health.txt, with any Host header.

These settings also send all logs to stdout only, with no log file.
"""

import re

from .base import *  # noqa: F401,F403


class MergeSlashesMiddleware:
    """Replace each run of slashes in the request path with one slash."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "//" in request.path_info:
            request.path_info = re.sub("/{2,}", "/", request.path_info)
            request.path = re.sub("/{2,}", "/", request.path)
        return self.get_response(request)


_WHITENOISE = "whitenoise.middleware.WhiteNoiseMiddleware"
_OTHERS = tuple(m for m in MIDDLEWARE if m != _WHITENOISE)  # noqa: F405
MIDDLEWARE = ("hxat.settings.container.MergeSlashesMiddleware", _WHITENOISE) + _OTHERS

# Log to stdout only. The container platform collects stdout, and a log
# file inside the container grows until the container stops.
del LOGGING["handlers"]["default"]  # noqa: F405
for _logger in [LOGGING["root"], *LOGGING["loggers"].values()]:  # noqa: F405
    _logger["handlers"] = ["console"]
