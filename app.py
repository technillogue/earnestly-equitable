import json
from flask import (
    Flask,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from splitwise import Splitwise

from .decorators import redirect_for_session

app = Flask(__name__)
secrets = json.load(open("secrets.yaml"))
consumer_key = secrets["consumer_key"]
consumer_secret = secrets["consumer_secret"]
api_key = secrets["api_key"]


@app.route("/")
@redirect_for_session(session_has={"access_token": "friends"})
def root():
    return render_template_string(
        "<h1>Earnest the Jortfort Splitwise</h1>"
        f"<a href='{url_for('login')}'>login</a>"
    )


@app.route("/login")
def login():
    wise = Splitwise(consumer_key, consumer_secret)
    redirect_uri = request.host_url + "/authorize"  # url_for("autorize")?
    print(redirect_uri)
    url, state = wise.getOAuth2AuthorizeURL(redirect_uri)
    # conflicting info about whether state needs to be passed to getOAuth2AccessToken
    # is supposed to protect cross-site request forgery
    session["oauth_state"] = state
    return redirect(url)


@app.route("/authorize")
# @redirect_for_session(session_needs={KEY_SECRET: "root"}) # "oauth_state": "root"?
def authorize():
    wise = Splitwise(consumer_key, consumer_secret)
    redirect_uri = request.host_url + "/authorize"
    access_token = wise.getOAuth2AccessToken(code, redirect_uri)
    session["access_token"] = access_token
    return redirect(url_for("friends"))


@app.route("/friends")
@redirect_for_session(session_needs={"access_token": "home"})
def friends():
    wise = Splitwise(consumer_key, consumer_secret)
    wise.setAccessToken(session["access_token"])

    friend_names = [
        " ".join(filter(None, (f.first_name, f.last_name)))
        for f in wise.getFriends()
    ]
    template = f"<ul>{''.join(f'<li>{name}</li>' for name in friend_names)}</ul>"
    return render_template_string(template)


if __name__ == "__main__":
    app.run(debug=True)
