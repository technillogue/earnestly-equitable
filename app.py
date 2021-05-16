import json
import sys
import subprocess
import shlex
from typing import cast, Union
from types import SimpleNamespace
from urllib import parse
from flask import (
    Flask,
    Request,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from werkzeug.wrappers import Response
from splitwise import Splitwise

secrets = json.load(open("secrets.json"))
consumer_key = secrets["consumer_key"]
consumer_secret = secrets["consumer_secret"]
api_key = secrets["api_key"]  # idk what this does


app = Flask(__name__)
app.secret_key = secrets["flask_secret_key_for_cookies"]

# @app.route("/")
# @redirect_for_session(session_has={"access_token": "friends"})
def index() -> str:
    header = "<h1>Earnest the Jortfort Splitwise</h1>"
    _friends = f"<a href='{url_for('friends')}'>friends</a>"
    _login = f"<a href='{url_for('login')}'>friends</a>"
    link = _friends if "access_token" in session else _login
    return render_template_string("\n".join([header, link]))


redirect_uri = "http://localhost:5000/authorize"

# @app.route("/login")
def login() -> Response:
    wise = Splitwise(consumer_key, consumer_secret)
    # redirect_uri = url_for("authorize", _external=True)
    print(redirect_uri)
    url, state = wise.getOAuth2AuthorizeURL(redirect_uri)
    # conflicting info about whether state needs to be passed to getOAuth2AccessToken
    # is supposed to protect cross-site request forgery
    session["oauth_state"] = state
    return redirect(url)


# @app.route("/authorize")
# @redirect_for_session(session_needs={KEY_SECRET: "root"}) # "oauth_state": "root"? # no
def authorize() -> Response:
    wise = Splitwise(consumer_key, consumer_secret)
    # redirect_uri = url_for("authorize", _external=True)
    code = request.args.get("code")
    if request.args.get("state") != session["oauth_state"]:
        print("oauth state bad")
    access_token = wise.getOAuth2AccessToken(code, redirect_uri)
    session["access_token"] = access_token
    return redirect(url_for("friends"))


# @app.route("/friends")
# @redirect_for_session(session_needs={"access_token": "home"})
def friends() -> Union[Response, str]:  # idk about this one
    if "access_token" not in session:
        return redirect(url_for("index"))
    wise = Splitwise(consumer_key, consumer_secret)
    wise.setAccessToken(session["access_token"])

    friend_names = [
        " ".join(filter(None, (f.first_name, f.last_name)))
        for f in wise.getFriends()
    ]
    template = f"<ul>{''.join(f'<li>{name}</li>' for name in friend_names)}</ul>"
    return render_template_string(template)


app.add_url_rule("/", view_func=index)
app.add_url_rule("/login", view_func=login)
app.add_url_rule("/authorize", view_func=authorize)
app.add_url_rule("/friends", view_func=friends)


if __name__ == "__main__":
    if "--help" in sys.argv:
        print(
            "by default run debug on 0.0.0.0:5000. --cli, don't use flask, redirect manually."
        )
    elif "--cli" in sys.argv:
        # whoops this needs a real flask context to work
        def url_for(target: str) -> str:  # type: ignore
            return f"example.com/{target}"

        url = login().headers["Location"]
        try:
            subprocess.run(
                shlex.split(f"fish -c 'echo \"{url}\"|clip'"),
                shell=True,
                check=True,
            )
        except:
            print(f"go to {url}, log in, then copy the redirected uri")
        redirect_uri = input("redirected uri> ")
        request = cast(
            Request,
            SimpleNamespace(
                args=parse.parse_qs(parse.urlsplit(redirect_uri).query)
            ),
        )
        session = {}
        print(repr(authorize()))
        print(repr(friends()))
    else:
        app.run(debug=True, host="localhost", port="5000")
