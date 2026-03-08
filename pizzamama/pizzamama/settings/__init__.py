import os

DJANGO_ENV = os.getenv("DJANGO_ENV", "dev").lower()

if DJANGO_ENV in {"prod", "production"}:
    from .prod import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403
