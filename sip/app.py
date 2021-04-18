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
app.secret_key = 'FUTURE SECRET KEY'

KEY_ACCESS_TOKEN = 'access_token'
KEY_SECRET = 'secret'


@app.route('/')
@redirect_for_session(session_has={KEY_ACCESS_TOKEN: 'friends'})
def root():
    return render_template_string('<h1>Earnest the Jortfort Splitwise</h1>')


@app.route('/login')
def login():
    wise = Splitwise('consumer_key', 'consumer_secret')
    url, secret = wise.getAuthorizeURL()
    session[KEY_SECRET] = secret
    return redirect(url)


@app.route('/authorize')
@redirect_for_session(session_needs={KEY_SECRET: 'root'})
def authorize():
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')

    wise = Splitwise('consumer_key', 'consumer_secret')
    access_token = wise.getAccessToken(oauth_token, session[KEY_SECRET], oauth_verifier)
    session[KEY_ACCESS_TOKEN] = access_token

    return redirect(url_for('friends'))


@app.route('/friends')
@redirect_for_session(session_needs={KEY_ACCESS_TOKEN: 'home'})
def friends():
    wise = Splitwise('consumer_key', 'consumer_secret')
    wise.setAccessToken(session[KEY_ACCESS_TOKEN])

    friend_names = [' '.join(filter(None, (f.first_name, f.last_name))) for f in wise.getFriends()]
    template = f"<ul>{''.join(f'<li>{name}</li>' for name in friend_names)}</ul>"
    return render_template_string(template)


if __name__ == '__main__':
    app.run(debug=True)
