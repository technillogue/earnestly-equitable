import json
import csv
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

# import splitwise # namespace import i think?
import splitwise
from splitwise import Splitwise
from splitwise.expense import Expense, ExpenseUser

secrets = json.load(open("secrets.json"))
consumer_key = secrets["consumer_key"]
consumer_secret = secrets["consumer_secret"]
api_key = secrets.get("api_key")


app = Flask(__name__)
app.secret_key = secrets["flask_secret_key_for_cookies"]


def index() -> str:
    header = "<h1>Earnest the Jortfort Splitwise</h1>" + (
        "api key enabled" if api_key else ""
    )
    links = [
        f"<li><a href='{url_for(method)}'>{method}</a>"
        for method in ["login", "logout", "friends", "debts", "expense_route"]
    ]
    return render_template_string("\n".join([header, *links]))


#redirect_uri = "http://localhost:5000/authorize"


def login() -> Response:
    wise = Splitwise(consumer_key, consumer_secret, api_key=api_key)
    redirect_uri = url_for("authorize", _external=True)
    print(redirect_uri)
    url, state = wise.getOAuth2AuthorizeURL(redirect_uri)
    # conflicting info about whether state needs to be passed to getOAuth2AccessToken
    # is supposed to protect cross-site request forgery
    session["oauth_state"] = state
    return redirect(url)


def logout() -> Response:
    if "oauth_session" in state:
        del session["oauth_state"]
    if "access_token" in state:
        del session["access_token"]


# @app.route("/authorize")
def authorize() -> Response:
    wise = Splitwise(consumer_key, consumer_secret, api_key=api_key)
    redirect_uri = url_for("authorize", _external=True)
    code = request.args.get("code")
    if request.args.get("state") != session["oauth_state"]:
        print("oauth state bad")
    # prettyprint an authorization failure for debugging
    access_token = wise.getOAuth2AccessToken(code, redirect_uri)
    session["access_token"] = access_token
    return redirect(url_for("friends"))


# @app.route("/friends")
# @redirect_for_session(session_needs={"access_token": "home"})
def friends() -> Union[Response, str]:  # idk about this one
    wise = Splitwise(consumer_key, consumer_secret, api_key=api_key)
    if session.get("access_token"):
        wise.setAccessToken(session["access_token"])

    friend_names = [
        " ".join(filter(None, (f.first_name, f.last_name)))
        for f in wise.getFriends()
    ]
    template = f"<ul>{''.join(f'<li>{name}</li>' for name in friend_names)}</ul>"
    return render_template_string(template)


def expenses() -> str:
    wise = Splitwise(consumer_key, consumer_secret, api_key=api_key)
    if session.get("access_token"):
        wise.setAccessToken(session["access_token"])
    group = wise.getGroups()[0]
    expense = Expense()
    expense.setCost("10")
    expense.setDescription("Testing")


app.add_url_rule("/", view_func=index)
app.add_url_rule("/login", view_func=login)
app.add_url_rule("/logout", view_func=logout)
app.add_url_rule("/authorize", view_func=authorize)
app.add_url_rule("/friends", view_func=friends)

import functools


@functools.cache
def get_user_name(user_id):
    return S.getUser(user_id).first_name


@app.route("/expense")
def expense_route():
    ex, err = mkexpense(**request.args)
    if err:
        return repr(err)
    return f"success: {ex}"

## example with api_key!
S = Splitwise(consumer_key, consumer_secret, api_key=api_key)

earnest = S.getGroups()[1]  # 0 is non-group
@app.route("/debts")
def debts() -> str:
    debts = [
        f"{get_user_name(debt.getFromUser())} owes {debt.getAmount()} to {get_user_name(debt.getToUser())}"
        for debt in earnest.simplified_debts
    ]
    return "\n".join(f"<li>{line}</li>" for line in debts)

user_ids = {member.first_name: member.id for member in earnest.getMembers()}
#shares = dict(csv.reader(open("shares.csv")))

shares = {
    "Sylvie": 23,
    "Hameed": 21,
    "Stef": 17,
}  # this is with stef at 3120 effective income
real_shares = {**shares, "Leigh": 17}


def mkexpense(cost=10, desc="Testing", group_id=earnest.id, shares=shares):
    expense = Expense()
    expense.setCost(cost)
    expense.setDescription(desc)
    expense.setGroupId(group_id)
    total_shares = sum(shares.values())
    print(cost)

    def mkUser(name, share):
        user = ExpenseUser()
        user.setId(user_ids[name])
        user.setFirstName(name)
        user.setOwedShare(share / total_shares * cost)
        user.setPaidShare(cost if name == "Sylvie" else 0)
        return user

    users = [mkUser(name, share) for name, share in shares.items()]
    expense.setUsers(users)
    nExpense, errors = S.createExpense(expense)
    print(nExpense, errors)
    return (nExpense, errors)


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
    elif "--mkexpense" in sys.argv:
        mkexpense()
    else:
        app.run(debug=True, int(os.environ.get("PORT", 8080)))
