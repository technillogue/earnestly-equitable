import functools

from flask import redirect, session, url_for


def redirect_for_session(session_needs=None, session_has=None):
    """
    View func decorator to automatically redirect if the session does or does not have
    certain keys. Arguments are in a session key to endpoint name mapping structure.

    :param session_needs: If any key *is not* in the session, redirects to the value endpoint
    :param session_has: If any key *is* in the session, redirects to the value endpoint
    """

    if session_needs is None:
        session_needs = dict()
    if session_has is None:
        session_has = dict()
    if not isinstance(session_needs, dict):
        raise AttributeError("session_needs should be a dict")
    if not isinstance(session_has, dict):
        raise AttributeError("session_has should be a dict")

    def wrapper(f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            for k, v in session_needs.items():
                if k not in session:
                    return redirect(url_for(v))
            for k, v in session_has.items():
                if k in session:
                    return redirect(url_for(v))

            return f(*args, **kwargs)

        return inner

    return wrapper
